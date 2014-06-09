
from __future__ import division, unicode_literals
from future.builtins import str, super
from future.utils import with_metaclass

from decimal import Decimal
from functools import reduce
from operator import iand, ior

from django.core.urlresolvers import reverse
from django.db import models, connection
from django.db.models.signals import m2m_changed
from django.db.models import CharField, Q
from django.db.models.base import ModelBase
from django.dispatch import receiver
from django.utils.timezone import now
from django.utils.translation import (ugettext, ugettext_lazy as _,
                                      pgettext_lazy as __)

try:
    from django.utils.encoding import force_text
except ImportError:
    # Backward compatibility for Py2 and Django < 1.5
    from django.utils.encoding import force_unicode as force_text

from mezzanine.conf import settings
from mezzanine.core.fields import FileField
from mezzanine.core.managers import DisplayableManager
from mezzanine.core.models import Displayable, RichText, Orderable, SiteRelated
from mezzanine.generic.fields import RatingField
from mezzanine.pages.models import Page
from mezzanine.utils.models import AdminThumbMixin, upload_to

from cartridge.shop import fields, managers
from cartridge.shop.utils import clear_session


class F(models.F):
    """
    Django 1.4's F objects don't support true division, which
    we need for Python 3.x. This should be removed when we
    drop support for Django 1.4.
    """
    def __truediv__(self, other):
        return self._combine(other, self.DIV, False)


class Priced(models.Model):
    """
    Abstract model with unit and sale price fields. Inherited by
    ``Product`` and ``ProductVariation`` models.
    """

    unit_price = fields.MoneyField(_("Unit price"))
    sale_id = models.IntegerField(null=True)
    sale_price = fields.MoneyField(_("Sale price"))
    sale_from = models.DateTimeField(_("Sale start"), blank=True, null=True)
    sale_to = models.DateTimeField(_("Sale end"), blank=True, null=True)
    sku = fields.SKUField(unique=True, blank=True, null=True)
    num_in_stock = models.IntegerField(_("Number in stock"), blank=True,
                                       null=True)

    class Meta:
        abstract = True

    def on_sale(self):
        """
        Returns True if the sale price is applicable.
        """
        n = now()
        valid_from = self.sale_from is None or self.sale_from < n
        valid_to = self.sale_to is None or self.sale_to > n
        return self.sale_price is not None and valid_from and valid_to

    def has_price(self):
        """
        Returns True if there is a valid price.
        """
        return self.on_sale() or self.unit_price is not None

    def price(self):
        """
        Returns the actual price - sale price if applicable otherwise
        the unit price.
        """
        if self.on_sale():
            return self.sale_price
        elif self.has_price():
            return self.unit_price
        return Decimal("0")

    def copy_price_fields_to(self, obj_to):
        """
        Copies each of the fields for the ``Priced`` model from one
        instance to another. Used for synchronising the denormalised
        fields on ``Product`` instances with their default variation.
        """
        for field in Priced._meta.fields:
            if not isinstance(field, models.AutoField):
                setattr(obj_to, field.name, getattr(self, field.name))
        obj_to.save()


class Product(Displayable, Priced, RichText, AdminThumbMixin):
    """
    Container model for a product that stores information common to
    all of its variations such as the product's title and description.
    """

    available = models.BooleanField(_("Available for purchase"),
                                    default=False)
    image = CharField(_("Image"), max_length=100, blank=True, null=True)
    categories = models.ManyToManyField("Category", blank=True,
                                        verbose_name=_("Product categories"))
    date_added = models.DateTimeField(_("Date added"), auto_now_add=True,
                                      null=True)
    related_products = models.ManyToManyField("self",
                             verbose_name=_("Related products"), blank=True)
    upsell_products = models.ManyToManyField("self",
                             verbose_name=_("Upsell products"), blank=True)
    rating = RatingField(verbose_name=_("Rating"))

    objects = DisplayableManager()

    admin_thumb_field = "image"

    search_fields = {"variations__sku": 100}

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")

    def save(self, *args, **kwargs):
        """
        Copies the price fields to the default variation when
        ``SHOP_USE_VARIATIONS`` is False, and the product is
        updated via the admin change list.
        """
        updating = self.id is not None
        super(Product, self).save(*args, **kwargs)
        if updating and not settings.SHOP_USE_VARIATIONS:
            default = self.variations.get(default=True)
            self.copy_price_fields_to(default)

    @models.permalink
    def get_absolute_url(self):
        return ("shop_product", (), {"slug": self.slug})

    def copy_default_variation(self):
        """
        Copies the price and image fields from the default variation
        when the product is updated via the change view.
        """
        default = self.variations.get(default=True)
        default.copy_price_fields_to(self)
        if default.image:
            self.image = default.image.file.name
        self.save()


class ProductImage(Orderable):
    """
    An image for a product - a relationship is also defined with the
    product's variations so that each variation can potentially have
    it own image, while the relationship between the ``Product`` and
    ``ProductImage`` models ensures there is a single set of images
    for the product.
    """

    file = models.ImageField(_("Image"),
        upload_to=upload_to("shop.ProductImage.file", "product"))
    description = CharField(_("Description"), blank=True, max_length=100)
    product = models.ForeignKey("Product", related_name="images")

    class Meta:
        verbose_name = _("Image")
        verbose_name_plural = _("Images")
        order_with_respect_to = "product"

    def __unicode__(self):
        value = self.description
        if not value:
            value = self.file.name
        if not value:
            value = ""
        return value


class ProductOption(models.Model):
    """
    A selectable option for a product such as size or colour.
    """
    type = models.IntegerField(_("Type"),
                               choices=settings.SHOP_OPTION_TYPE_CHOICES)
    name = fields.OptionField(_("Name"))

    objects = managers.ProductOptionManager()

    def __unicode__(self):
        return "%s: %s" % (self.get_type_display(), self.name)

    class Meta:
        verbose_name = _("Product option")
        verbose_name_plural = _("Product options")


class ProductVariationMetaclass(ModelBase):
    """
    Metaclass for the ``ProductVariation`` model that dynamcally
    assigns an ``fields.OptionField`` for each option in the
    ``SHOP_PRODUCT_OPTIONS`` setting.
    """
    def __new__(cls, name, bases, attrs):
        # Only assign new attrs if not a proxy model.
        if not ("Meta" in attrs and getattr(attrs["Meta"], "proxy", False)):
            for option in settings.SHOP_OPTION_TYPE_CHOICES:
                attrs["option%s" % option[0]] = fields.OptionField(option[1])
        args = (cls, name, bases, attrs)
        return super(ProductVariationMetaclass, cls).__new__(*args)


class ProductVariation(with_metaclass(ProductVariationMetaclass, Priced)):
    """
    A combination of selected options from
    ``SHOP_OPTION_TYPE_CHOICES`` for a ``Product`` instance.
    """

    product = models.ForeignKey("Product", related_name="variations")
    default = models.BooleanField(_("Default"), default=False)
    image = models.ForeignKey("ProductImage", verbose_name=_("Image"),
                              null=True, blank=True)

    objects = managers.ProductVariationManager()

    class Meta:
        ordering = ("-default",)

    def __unicode__(self):
        """
        Display the option names and values for the variation.
        """
        options = []
        for field in self.option_fields():
            name = getattr(self, field.name)
            if name is not None:
                option = u"%s: %s" % (field.verbose_name, name)
                options.append(option)
        result = u"%s %s" % (str(self.product), u", ".join(options))
        return result.strip()

    def save(self, *args, **kwargs):
        """
        Use the variation's ID as the SKU when the variation is first
        created.
        """
        super(ProductVariation, self).save(*args, **kwargs)
        if not self.sku:
            self.sku = self.id
            self.save()

    def get_absolute_url(self):
        return self.product.get_absolute_url()

    @classmethod
    def option_fields(cls):
        """
        Returns each of the model fields that are dynamically created
        from ``SHOP_OPTION_TYPE_CHOICES`` in
        ``ProductVariationMetaclass``.
        """
        all_fields = cls._meta.fields
        return [f for f in all_fields if isinstance(f, fields.OptionField)]

    def options(self):
        """
        Returns the field values of each of the model fields that are
        dynamically created from ``SHOP_OPTION_TYPE_CHOICES`` in
        ``ProductVariationMetaclass``.
        """
        return [getattr(self, field.name) for field in self.option_fields()]

    def live_num_in_stock(self):
        """
        Returns the live number in stock, which is
        ``self.num_in_stock - num in carts``. Also caches the value
        for subsequent lookups.
        """
        if self.num_in_stock is None:
            return None
        if not hasattr(self, "_cached_num_in_stock"):
            num_in_stock = self.num_in_stock
            carts = Cart.objects.current()
            items = CartItem.objects.filter(sku=self.sku, cart__in=carts)
            aggregate = items.aggregate(quantity_sum=models.Sum("quantity"))
            num_in_carts = aggregate["quantity_sum"]
            if num_in_carts is not None:
                num_in_stock = num_in_stock - num_in_carts
            self._cached_num_in_stock = num_in_stock
        return self._cached_num_in_stock

    def has_stock(self, quantity=1):
        """
        Returns ``True`` if the given quantity is in stock, by checking
        against ``live_num_in_stock``. ``True`` is returned when
        ``num_in_stock`` is ``None`` which is how stock control is
        disabled.
        """
        live = self.live_num_in_stock()
        return live is None or quantity == 0 or live >= quantity

    def update_stock(self, quantity):
        """
        Update the stock amount - called when an order is complete.
        Also update the denormalised stock amount of the product if
        this is the default variation.
        """
        if self.num_in_stock is not None:
            self.num_in_stock += quantity
            self.save()
            if self.default:
                self.product.num_in_stock = self.num_in_stock
                self.product.save()


class Category(Page, RichText):
    """
    A category of products on the website.
    """

    featured_image = FileField(verbose_name=_("Featured Image"),
        upload_to=upload_to("shop.Category.featured_image", "shop"),
        format="Image", max_length=255, null=True, blank=True)
    products = models.ManyToManyField("Product", blank=True,
                                     verbose_name=_("Products"),
                                     through=Product.categories.through)
    options = models.ManyToManyField("ProductOption", blank=True,
                                     verbose_name=_("Product options"),
                                     related_name="product_options")
    sale = models.ForeignKey("Sale", verbose_name=_("Sale"),
                             blank=True, null=True)
    price_min = fields.MoneyField(_("Minimum price"), blank=True, null=True)
    price_max = fields.MoneyField(_("Maximum price"), blank=True, null=True)
    combined = models.BooleanField(_("Combined"), default=True,
        help_text=_("If checked, "
        "products must match all specified filters, otherwise products "
        "can match any specified filter."))

    class Meta:
        verbose_name = _("Product category")
        verbose_name_plural = _("Product categories")

    def filters(self):
        """
        Returns product filters as a Q object for the category.
        """
        # Build a list of Q objects to filter variations by.
        filters = []
        # Build a lookup dict of selected options for variations.
        options = self.options.as_fields()
        if options:
            lookup = dict([("%s__in" % k, v) for k, v in options.items()])
            filters.append(Q(**lookup))
        # Q objects used against variations to ensure sale date is
        # valid when filtering by sale, or sale price.
        n = now()
        valid_sale_from = Q(sale_from__isnull=True) | Q(sale_from__lte=n)
        valid_sale_to = Q(sale_to__isnull=True) | Q(sale_to__gte=n)
        valid_sale_date = valid_sale_from & valid_sale_to
        # Filter by variations with the selected sale if the sale date
        # is valid.
        if self.sale_id:
            filters.append(Q(sale_id=self.sale_id) & valid_sale_date)
        # If a price range is specified, use either the unit price or
        # a sale price if the sale date is valid.
        if self.price_min or self.price_max:
            prices = []
            if self.price_min:
                sale = Q(sale_price__gte=self.price_min) & valid_sale_date
                prices.append(Q(unit_price__gte=self.price_min) | sale)
            if self.price_max:
                sale = Q(sale_price__lte=self.price_max) & valid_sale_date
                prices.append(Q(unit_price__lte=self.price_max) | sale)
            filters.append(reduce(iand, prices))
        # Turn the variation filters into a product filter.
        operator = iand if self.combined else ior
        products = Q(id__in=self.products.only("id"))
        if filters:
            filters = reduce(operator, filters)
            variations = ProductVariation.objects.filter(filters)
            filters = [Q(variations__in=variations)]
            # If filters exist, checking that products have been
            # selected is neccessary as combining the variations
            # with an empty ID list lookup and ``AND`` will always
            # result in an empty result.
            if self.products.count() > 0:
                filters.append(products)
            return reduce(operator, filters)
        return products


class Order(SiteRelated):

    billing_detail_first_name = CharField(_("First name"), max_length=100)
    billing_detail_last_name = CharField(_("Last name"), max_length=100)
    billing_detail_street = CharField(_("Street"), max_length=100)
    billing_detail_city = CharField(_("City/Suburb"), max_length=100)
    billing_detail_state = CharField(_("State/Region"), max_length=100)
    billing_detail_postcode = CharField(_("Zip/Postcode"), max_length=10)
    billing_detail_country = CharField(_("Country"), max_length=100)
    billing_detail_phone = CharField(_("Phone"), max_length=20)
    billing_detail_email = models.EmailField(_("Email"))
    shipping_detail_first_name = CharField(_("First name"), max_length=100)
    shipping_detail_last_name = CharField(_("Last name"), max_length=100)
    shipping_detail_street = CharField(_("Street"), max_length=100)
    shipping_detail_city = CharField(_("City/Suburb"), max_length=100)
    shipping_detail_state = CharField(_("State/Region"), max_length=100)
    shipping_detail_postcode = CharField(_("Zip/Postcode"), max_length=10)
    shipping_detail_country = CharField(_("Country"), max_length=100)
    shipping_detail_phone = CharField(_("Phone"), max_length=20)
    additional_instructions = models.TextField(_("Additional instructions"),
                                               blank=True)
    time = models.DateTimeField(_("Time"), auto_now_add=True, null=True)
    key = CharField(max_length=40)
    user_id = models.IntegerField(blank=True, null=True)
    shipping_type = CharField(_("Shipping type"), max_length=50, blank=True)
    shipping_total = fields.MoneyField(_("Shipping total"))
    tax_type = CharField(_("Tax type"), max_length=50, blank=True)
    tax_total = fields.MoneyField(_("Tax total"))
    item_total = fields.MoneyField(_("Item total"))
    discount_code = fields.DiscountCodeField(_("Discount code"), blank=True)
    discount_total = fields.MoneyField(_("Discount total"))
    total = fields.MoneyField(_("Order total"))
    transaction_id = CharField(_("Transaction ID"), max_length=255, null=True,
                               blank=True)

    status = models.IntegerField(_("Status"),
                            choices=settings.SHOP_ORDER_STATUS_CHOICES,
                            default=settings.SHOP_ORDER_STATUS_CHOICES[0][0])

    objects = managers.OrderManager()

    # These are fields that are stored in the session. They're copied to
    # the order in setup() and removed from the session in complete().
    session_fields = ("shipping_type", "shipping_total", "discount_total",
                      "discount_code", "tax_type", "tax_total")

    class Meta:
        verbose_name = __("commercial meaning", "Order")
        verbose_name_plural = __("commercial meaning", "Orders")
        ordering = ("-id",)

    def __unicode__(self):
        return "#%s %s %s" % (self.id, self.billing_name(), self.time)

    def billing_name(self):
        return "%s %s" % (self.billing_detail_first_name,
                          self.billing_detail_last_name)

    def setup(self, request):
        """
        Set order fields that are stored in the session, item_total
        and total based on the given cart, and copy the cart items
        to the order. Called in the final step of the checkout process
        prior to the payment handler being called.
        """
        self.key = request.session.session_key
        self.user_id = request.user.id
        for field in self.session_fields:
            if field in request.session:
                setattr(self, field, request.session[field])
        self.total = self.item_total = request.cart.total_price()
        if self.shipping_total is not None:
            self.shipping_total = Decimal(str(self.shipping_total))
            self.total += self.shipping_total
        if self.discount_total is not None:
            self.total -= Decimal(self.discount_total)
        if self.tax_total is not None:
            self.total += Decimal(self.tax_total)
        self.save()  # We need an ID before we can add related items.
        for item in request.cart:
            product_fields = [f.name for f in SelectedProduct._meta.fields]
            item = dict([(f, getattr(item, f)) for f in product_fields])
            self.items.create(**item)

    def complete(self, request):
        """
        Remove order fields that are stored in the session, reduce the
        stock level for the items in the order, decrement the uses
        remaining count for discount code (if applicable) and then
        delete the cart.
        """
        self.save()  # Save the transaction ID.
        discount_code = request.session.get('discount_code')
        clear_session(request, "order", *self.session_fields)
        for item in request.cart:
            try:
                variation = ProductVariation.objects.get(sku=item.sku)
            except ProductVariation.DoesNotExist:
                pass
            else:
                variation.update_stock(item.quantity * -1)
                variation.product.actions.purchased()
        if discount_code:
            DiscountCode.objects.active().filter(code=discount_code).update(
                uses_remaining=models.F('uses_remaining') - 1)
        request.cart.delete()

    def details_as_dict(self):
        """
        Returns the billing_detail_* and shipping_detail_* fields
        as two name/value pairs of fields in a dict for each type.
        Used in template contexts for rendering each type as groups
        of names/values.
        """
        context = {}
        for fieldset in ("billing_detail", "shipping_detail"):
            fields = [(f.verbose_name, getattr(self, f.name)) for f in
                self._meta.fields if f.name.startswith(fieldset)]
            context["order_%s_fields" % fieldset] = fields
        return context

    def invoice(self):
        """
        Returns the HTML for a link to the PDF invoice for use in the
        order listing view of the admin.
        """
        url = reverse("shop_invoice", args=(self.id,))
        text = ugettext("Download PDF invoice")
        return "<a href='%s?format=pdf'>%s</a>" % (url, text)
    invoice.allow_tags = True
    invoice.short_description = ""


class Cart(models.Model):

    last_updated = models.DateTimeField(_("Last updated"), null=True)

    objects = managers.CartManager()

    def __iter__(self):
        """
        Allow the cart to be iterated giving access to the cart's items,
        ensuring the items are only retrieved once and cached.
        """
        if not hasattr(self, "_cached_items"):
            self._cached_items = self.items.all()
        return iter(self._cached_items)

    def add_item(self, variation, quantity):
        """
        Increase quantity of existing item if SKU matches, otherwise create
        new.
        """
        kwargs = {"sku": variation.sku, "unit_price": variation.price()}
        item, created = self.items.get_or_create(**kwargs)
        if created:
            item.description = force_text(variation)
            item.unit_price = variation.price()
            item.url = variation.product.get_absolute_url()
            image = variation.image
            if image is not None:
                item.image = force_text(image.file)
            variation.product.actions.added_to_cart()
        item.quantity += quantity
        item.save()

    def has_items(self):
        """
        Template helper function - does the cart have items?
        """
        return len(list(self)) > 0

    def total_quantity(self):
        """
        Template helper function - sum of all item quantities.
        """
        return sum([item.quantity for item in self])

    def total_price(self):
        """
        Template helper function - sum of all costs of item quantities.
        """
        return sum([item.total_price for item in self])

    def skus(self):
        """
        Returns a list of skus for items in the cart. Used by
        ``upsell_products`` and ``calculate_discount``.
        """
        return [item.sku for item in self]

    def upsell_products(self):
        """
        Returns the upsell products for each of the items in the cart.
        """
        if not settings.SHOP_USE_UPSELL_PRODUCTS:
            return []
        cart = Product.objects.filter(variations__sku__in=self.skus())
        published_products = Product.objects.published()
        for_cart = published_products.filter(upsell_products__in=cart)
        with_cart_excluded = for_cart.exclude(variations__sku__in=self.skus())
        return list(with_cart_excluded.distinct())

    def calculate_discount(self, discount):
        """
        Calculates the discount based on the items in a cart, some
        might have the discount, others might not.
        """
        # Discount applies to cart total if not product specific.
        products = discount.all_products()
        if products.count() == 0:
            return discount.calculate(self.total_price())
        total = Decimal("0")
        # Create a list of skus in the cart that are applicable to
        # the discount, and total the discount for appllicable items.
        lookup = {"product__in": products, "sku__in": self.skus()}
        discount_variations = ProductVariation.objects.filter(**lookup)
        discount_skus = discount_variations.values_list("sku", flat=True)
        for item in self:
            if item.sku in discount_skus:
                total += discount.calculate(item.unit_price) * item.quantity
        return total


class SelectedProduct(models.Model):
    """
    Abstract model representing a "selected" product in a cart or order.
    """

    sku = fields.SKUField()
    description = CharField(_("Description"), max_length=2000)
    quantity = models.IntegerField(_("Quantity"), default=0)
    unit_price = fields.MoneyField(_("Unit price"), default=Decimal("0"))
    total_price = fields.MoneyField(_("Total price"), default=Decimal("0"))

    class Meta:
        abstract = True

    def __unicode__(self):
        return ""

    def save(self, *args, **kwargs):
        """
        Set the total price based on the given quantity. If the
        quantity is zero, which may occur via the cart page, just
        delete it.
        """
        if not self.id or self.quantity > 0:
            self.total_price = self.unit_price * self.quantity
            super(SelectedProduct, self).save(*args, **kwargs)
        else:
            self.delete()


class CartItem(SelectedProduct):

    cart = models.ForeignKey("Cart", related_name="items")
    url = CharField(max_length=2000)
    image = CharField(max_length=200, null=True)

    def get_absolute_url(self):
        return self.url


class OrderItem(SelectedProduct):
    """
    A selected product in a completed order.
    """
    order = models.ForeignKey("Order", related_name="items")


class ProductAction(models.Model):
    """
    Records an incremental value for an action against a product such
    as adding to cart or purchasing, for sales reporting and
    calculating popularity. Not yet used but will be used for product
    popularity and sales reporting.
    """

    product = models.ForeignKey("Product", related_name="actions")
    timestamp = models.IntegerField()
    total_cart = models.IntegerField(default=0)
    total_purchase = models.IntegerField(default=0)

    objects = managers.ProductActionManager()

    class Meta:
        unique_together = ("product", "timestamp")


class Discount(models.Model):
    """
    Abstract model representing one of several types of monetary
    reductions, as well as a date range they're applicable for, and
    the products and products in categories that the reduction is
    applicable for.
    """

    title = CharField(_("Title"), max_length=100)
    active = models.BooleanField(_("Active"), default=False)
    products = models.ManyToManyField("Product", blank=True,
                                      verbose_name=_("Products"))
    categories = models.ManyToManyField("Category", blank=True,
                                        related_name="%(class)s_related",
                                        verbose_name=_("Categories"))
    discount_deduct = fields.MoneyField(_("Reduce by amount"))
    discount_percent = fields.PercentageField(_("Reduce by percent"),
                                           max_digits=5, decimal_places=2,
                                           blank=True, null=True)
    discount_exact = fields.MoneyField(_("Reduce to amount"))
    valid_from = models.DateTimeField(_("Valid from"), blank=True, null=True)
    valid_to = models.DateTimeField(_("Valid to"), blank=True, null=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title

    def all_products(self):
        """
        Return the selected products as well as the products in the
        selected categories.
        """
        filters = [category.filters() for category in self.categories.all()]
        filters = reduce(ior, filters + [Q(id__in=self.products.only("id"))])
        return Product.objects.filter(filters).distinct()


class Sale(Discount):
    """
    Stores sales field values for price and date range which when saved
    are then applied across products and variations according to the
    selected categories and products for the sale.
    """

    class Meta:
        verbose_name = _("Sale")
        verbose_name_plural = _("Sales")

    def save(self, *args, **kwargs):
        super(Sale, self).save(*args, **kwargs)
        self.update_products()

    def update_products(self):
        """
        Apply sales field value to products and variations according
        to the selected categories and products for the sale.
        """
        self._clear()
        if self.active:
            extra_filter = {}
            if self.discount_deduct is not None:
                # Don't apply to prices that would be negative
                # after deduction.
                extra_filter["unit_price__gt"] = self.discount_deduct
                sale_price = models.F("unit_price") - self.discount_deduct
            elif self.discount_percent is not None:
                sale_price = models.F("unit_price") - (
                    F("unit_price") / "100.0" * self.discount_percent)
            elif self.discount_exact is not None:
                # Don't apply to prices that are cheaper than the sale
                # amount.
                extra_filter["unit_price__gt"] = self.discount_exact
                sale_price = self.discount_exact
            else:
                return
            products = self.all_products()
            variations = ProductVariation.objects.filter(product__in=products)
            for priced_objects in (products, variations):
                update = {"sale_id": self.id,
                          "sale_price": sale_price,
                          "sale_to": self.valid_to,
                          "sale_from": self.valid_from}
                using = priced_objects.db
                if "mysql" not in settings.DATABASES[using]["ENGINE"]:
                    priced_objects.filter(**extra_filter).update(**update)
                else:
                    # Work around for MySQL which does not allow update
                    # to operate on subquery where the FROM clause would
                    # have it operate on the same table, so we update
                    # each instance individually:

    # http://dev.mysql.com/doc/refman/5.0/en/subquery-errors.html

                    # Also MySQL may raise a 'Data truncated' warning here
                    # when doing a calculation that exceeds the precision
                    # of the price column. In this case it's safe to ignore
                    # it and the calculation will still be applied, but
                    # we need to massage transaction management in order
                    # to continue successfully:

    # https://groups.google.com/forum/#!topic/django-developers/ACLQRF-71s8

                    for priced in priced_objects.filter(**extra_filter):
                        for field, value in list(update.items()):
                            setattr(priced, field, value)
                        try:
                            priced.save()
                        except Warning:
                            connection.set_rollback(False)

    def delete(self, *args, **kwargs):
        """
        Clear this sale from products when deleting the sale.
        """
        self._clear()
        super(Sale, self).delete(*args, **kwargs)

    def _clear(self):
        """
        Clears previously applied sale field values from products prior
        to updating the sale, when deactivating it or deleting it.
        """
        update = {"sale_id": None, "sale_price": None,
                  "sale_from": None, "sale_to": None}
        for priced_model in (Product, ProductVariation):
            priced_model.objects.filter(sale_id=self.id).update(**update)


@receiver(m2m_changed, sender=Sale.products.through)
def sale_update_products(sender, instance, action, *args, **kwargs):
    """
    Signal for updating products for the sale - needed since the
    products won't be assigned to the sale when it is first saved.
    """
    if action == "post_add":
        instance.update_products()


class DiscountCode(Discount):
    """
    A code that can be entered at the checkout process to have a
    discount applied to the total purchase amount.
    """

    code = fields.DiscountCodeField(_("Code"), unique=True)
    min_purchase = fields.MoneyField(_("Minimum total purchase"))
    free_shipping = models.BooleanField(_("Free shipping"), default=False)
    uses_remaining = models.IntegerField(_("Uses remaining"), blank=True,
        null=True, help_text=_("If you wish to limit the number of times a "
            "code may be used, set this value. It will be decremented upon "
            "each use."))

    objects = managers.DiscountCodeManager()

    def calculate(self, amount):
        """
        Calculates the discount for the given amount.
        """
        if self.discount_deduct is not None:
            # Don't apply to amounts that would be negative after
            # deduction.
            if self.discount_deduct <= amount:
                return self.discount_deduct
        elif self.discount_percent is not None:
            return amount / Decimal("100") * self.discount_percent
        return 0

    class Meta:
        verbose_name = _("Discount code")
        verbose_name_plural = _("Discount codes")
