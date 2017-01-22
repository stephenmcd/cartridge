from __future__ import unicode_literals
from future.builtins import super, zip

"""
Admin classes for all the shop models.

Many attributes in here are controlled by the ``SHOP_USE_VARIATIONS``
setting which defaults to True. In this case, variations are managed in
the product change view, and are created given the ``ProductOption``
values selected.

A handful of fields (mostly those defined on the abstract ``Priced``
model) are duplicated across both the ``Product`` and
``ProductVariation`` models, with the latter being the definitive
source, and the former supporting denormalised data that can be
referenced when iterating through products, without having to
query the underlying variations.

When ``SHOP_USE_VARIATIONS`` is set to False, a single variation is
still stored against each product, to keep consistent with the overall
model design. Since from a user perspective there are no variations,
the inlines for variations provide a single inline for managing the
one variation per product, so in the product change view, a single set
of price fields are available via the one variation inline.

Also when ``SHOP_USE_VARIATIONS`` is set to False, the denormalised
price fields on the product model are presented as editable fields in
the product change list - if these form fields are used, the values
are then pushed back onto the one variation for the product.
"""

from copy import deepcopy

from django.contrib import admin
from django.db.models import ImageField
from django.utils.translation import ugettext_lazy as _

from mezzanine.conf import settings
from mezzanine.core.admin import (
    BaseTranslationModelAdmin, ContentTypedAdmin, DisplayableAdmin,
    TabularDynamicInlineAdmin)
from mezzanine.pages.admin import PageAdmin
from mezzanine.utils.static import static_lazy as static

from cartridge.shop.fields import MoneyField
from cartridge.shop.forms import ProductAdminForm, ProductVariationAdminForm
from cartridge.shop.forms import ProductVariationAdminFormset
from cartridge.shop.forms import DiscountAdminForm, ImageWidget, MoneyWidget
from cartridge.shop.models import Category, Product, ProductImage
from cartridge.shop.models import ProductVariation, ProductOption, Order
from cartridge.shop.models import OrderItem, Sale, DiscountCode
from cartridge.shop.views import HAS_PDF


# Lists of field names.
option_fields = [f.name for f in ProductVariation.option_fields()]
_flds = lambda s: [f.name for f in Order._meta.fields if f.name.startswith(s)]
billing_fields = _flds("billing_detail")
shipping_fields = _flds("shipping_detail")


################
#  CATEGORIES  #
################

# Categories fieldsets are extended from Page fieldsets, since
# categories are a Mezzanine Page type.
category_fieldsets = deepcopy(PageAdmin.fieldsets)
category_fieldsets[0][1]["fields"][3:3] = ["content", "products"]
category_fieldsets += ((_("Product filters"), {
    "fields": ("sale", ("price_min", "price_max"), "combined"),
    "classes": ("collapse-closed",)},),)
if settings.SHOP_CATEGORY_USE_FEATURED_IMAGE:
    category_fieldsets[0][1]["fields"].insert(3, "featured_image")

# Options are only used when variations are in use, so only provide
# them as filters for dynamic categories when this is the case.
if settings.SHOP_USE_VARIATIONS:
    category_fieldsets[-1][1]["fields"] = (("options",) +
                                        category_fieldsets[-1][1]["fields"])


class CategoryAdmin(PageAdmin):
    fieldsets = category_fieldsets
    formfield_overrides = {ImageField: {"widget": ImageWidget}}
    filter_horizontal = ("options", "products",)

################
#  VARIATIONS  #
################

# If variations aren't used, the variation inline should always
# provide a single inline for managing the single variation per
# product.
variation_fields = ["sku", "num_in_stock", "unit_price",
                    "sale_price", "sale_from", "sale_to", "image"]
if settings.SHOP_USE_VARIATIONS:
    variation_fields.insert(1, "default")
    variations_max_num = None
    variations_extra = 0
else:
    variations_max_num = 1
    variations_extra = 1


class ProductVariationAdmin(admin.TabularInline):
    verbose_name_plural = _("Current variations")
    model = ProductVariation
    fields = variation_fields
    max_num = variations_max_num
    extra = variations_extra
    formfield_overrides = {MoneyField: {"widget": MoneyWidget}}
    form = ProductVariationAdminForm
    formset = ProductVariationAdminFormset
    ordering = ["option%s" % i for i in settings.SHOP_OPTION_ADMIN_ORDER]


class ProductImageAdmin(TabularDynamicInlineAdmin):
    model = ProductImage
    formfield_overrides = {ImageField: {"widget": ImageWidget}}

##############
#  PRODUCTS  #
##############

product_fieldsets = deepcopy(DisplayableAdmin.fieldsets)
product_fieldsets[0][1]["fields"].insert(2, "available")
product_fieldsets[0][1]["fields"].extend(["content", "categories"])
product_fieldsets = list(product_fieldsets)

other_product_fields = []
if settings.SHOP_USE_RELATED_PRODUCTS:
    other_product_fields.append("related_products")
if settings.SHOP_USE_UPSELL_PRODUCTS:
    other_product_fields.append("upsell_products")
if len(other_product_fields) > 0:
    product_fieldsets.append((_("Other products"), {
        "classes": ("collapse-closed",),
        "fields": tuple(other_product_fields)}))

product_list_display = ["admin_thumb", "title", "status", "available",
                        "admin_link"]
product_list_editable = ["status", "available"]

# If variations are used, set up the product option fields for managing
# variations. If not, expose the denormalised price fields for a product
# in the change list view.
if settings.SHOP_USE_VARIATIONS:
    product_fieldsets.insert(1, (_("Create new variations"),
        {"classes": ("create-variations",), "fields": option_fields}))
else:
    extra_list_fields = ["sku", "unit_price", "sale_price", "num_in_stock"]
    product_list_display[4:4] = extra_list_fields
    product_list_editable.extend(extra_list_fields)


class ProductAdmin(ContentTypedAdmin, DisplayableAdmin):

    class Media:
        js = (static("cartridge/js/admin/product_variations.js"),)
        css = {"all": (static("cartridge/css/admin/product.css"),)}

    list_display = product_list_display
    list_display_links = ("admin_thumb", "title")
    list_editable = product_list_editable
    list_filter = ("status", "available", "categories")
    filter_horizontal = ("categories",) + tuple(other_product_fields)
    search_fields = ("title", "content", "categories__title",
                     "variations__sku")
    inlines = (ProductImageAdmin, ProductVariationAdmin)
    form = ProductAdminForm
    fieldsets = product_fieldsets

    def save_model(self, request, obj, form, change):
        """
        Store the product ID for creating variations in save_formset.
        """
        super(ProductAdmin, self).save_model(request, obj, form, change)
        # We store the product ID so we can retrieve a clean copy of
        # the product in save_formset, see: GH #301.
        self._product_id = obj.id

    def save_formset(self, request, form, formset, change):
        """

        Here be dragons. We want to perform these steps sequentially:

        - Save variations formset
        - Run the required variation manager methods:
          (create_from_options, manage_empty, etc)
        - Save the images formset

        The variations formset needs to be saved first for the manager
        methods to have access to the correct variations. The images
        formset needs to be run last, because if images are deleted
        that are selected for variations, the variations formset will
        raise errors when saving due to invalid image selections. This
        gets addressed in the set_default_images method.

        An additional problem is the actual ordering of the inlines,
        which are in the reverse order for achieving the above. To
        address this, we store the images formset as an attribute, and
        then call save on it after the other required steps have
        occurred.

        """

        product = self.model.objects.get(id=self._product_id)

        # Store the images formset for later saving, otherwise save the
        # formset.
        if formset.model == ProductImage:
            self._images_formset = formset
        else:
            super(ProductAdmin, self).save_formset(request, form, formset,
                                                   change)

        # Run each of the variation manager methods if we're saving
        # the variations formset.
        if formset.model == ProductVariation:

            # Build up selected options for new variations.
            options = dict([(f, request.POST.getlist(f)) for f in option_fields
                             if request.POST.getlist(f)])
            # Create a list of image IDs that have been marked to delete.
            deleted_images = [request.POST.get(f.replace("-DELETE", "-id"))
                for f in request.POST
                if f.startswith("images-") and f.endswith("-DELETE")]

            # Create new variations for selected options.
            product.variations.create_from_options(options)
            # Create a default variation if there are none.
            product.variations.manage_empty()

            # Remove any images deleted just now from variations they're
            # assigned to, and set an image for any variations without one.
            product.variations.set_default_images(deleted_images)

            # Save the images formset stored previously.
            super(ProductAdmin, self).save_formset(request, form,
                                                 self._images_formset, change)

            # Run again to allow for no images existing previously, with
            # new images added which can be used as defaults for variations.
            product.variations.set_default_images(deleted_images)

            # Copy duplicate fields (``Priced`` fields) from the default
            # variation to the product.
            product.copy_default_variation()

            # Save every translated fields from ``ProductOption`` into
            # the required ``ProductVariation``
            if settings.USE_MODELTRANSLATION:
                from collections import OrderedDict
                from modeltranslation.utils import (build_localized_fieldname
                                                    as _loc)
                for opt_name in options:
                    for opt_value in options[opt_name]:
                        opt_obj = ProductOption.objects.get(type=opt_name[6:],
                                                            name=opt_value)
                        params = {opt_name: opt_value}
                        for var in product.variations.filter(**params):
                            for code in OrderedDict(settings.LANGUAGES):
                                setattr(var, _loc(opt_name, code),
                                        getattr(opt_obj, _loc('name', code)))
                            var.save()


class ProductOptionAdmin(BaseTranslationModelAdmin):
    ordering = ("type", "name")
    list_display = ("type", "name")
    list_display_links = ("type",)
    list_editable = ("name",)
    list_filter = ("type",)
    search_fields = ("type", "name")
    radio_fields = {"type": admin.HORIZONTAL}


class OrderItemInline(admin.TabularInline):
    verbose_name_plural = _("Items")
    model = OrderItem
    extra = 0
    formfield_overrides = {MoneyField: {"widget": MoneyWidget}}


def address_pairs(fields):
    """
    Zips address fields into pairs, appending the last field if the
    total is an odd number.
    """
    pairs = list(zip(fields[::2], fields[1::2]))
    if len(fields) % 2:
        pairs.append(fields[-1])
    return pairs


order_list_display = ("id", "billing_name", "total", "time", "status",
                      "transaction_id")
if HAS_PDF:
    order_list_display += ("invoice",)


class OrderAdmin(admin.ModelAdmin):

    class Media:
        css = {"all": (static("cartridge/css/admin/order.css"),)}

    ordering = ("status", "-id")
    list_display = order_list_display
    list_editable = ("status",)
    list_filter = ("status", "time")
    list_display_links = ("id", "billing_name",)
    search_fields = (["id", "status", "transaction_id"] +
                     billing_fields + shipping_fields)
    date_hierarchy = "time"
    radio_fields = {"status": admin.HORIZONTAL}
    inlines = (OrderItemInline,)
    formfield_overrides = {MoneyField: {"widget": MoneyWidget}}
    fieldsets = (
        (_("Billing details"), {"fields": address_pairs(billing_fields)}),
         (_("Shipping details"), {"fields": address_pairs(shipping_fields)}),
        (None, {"fields": ("additional_instructions", ("shipping_total",
            "shipping_type"), ('tax_total', 'tax_type'),
             ("discount_total", "discount_code"), "item_total",
            ("total", "status"), "transaction_id")}),
    )

    def change_view(self, *args, **kwargs):
        if kwargs.get("extra_context", None) is None:
            kwargs["extra_context"] = {}
        kwargs["extra_context"]["has_pdf"] = HAS_PDF
        return super(OrderAdmin, self).change_view(*args, **kwargs)


class SaleAdmin(admin.ModelAdmin):
    list_display = ("title", "active", "discount_deduct", "discount_percent",
        "discount_exact", "valid_from", "valid_to")
    list_editable = ("active", "discount_deduct", "discount_percent",
        "discount_exact", "valid_from", "valid_to")
    filter_horizontal = ("categories", "products")
    formfield_overrides = {MoneyField: {"widget": MoneyWidget}}
    form = DiscountAdminForm
    fieldsets = (
        (None, {"fields": ("title", "active")}),
        (_("Apply to product and/or products in categories"),
            {"fields": ("products", "categories")}),
        (_("Reduce unit price by"),
            {"fields": (("discount_deduct", "discount_percent",
            "discount_exact"),)}),
        (_("Sale period"), {"fields": (("valid_from", "valid_to"),)}),
    )


class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ("title", "active", "code", "discount_deduct",
        "discount_percent", "min_purchase", "free_shipping", "valid_from",
        "valid_to")
    list_editable = ("active", "code", "discount_deduct", "discount_percent",
        "min_purchase", "free_shipping", "valid_from", "valid_to")
    filter_horizontal = ("categories", "products")
    formfield_overrides = {MoneyField: {"widget": MoneyWidget}}
    form = DiscountAdminForm
    fieldsets = (
        (None, {"fields": ("title", "active", "code")}),
        (_("Apply to product and/or products in categories"),
            {"fields": ("products", "categories")}),
        (_("Reduce unit price by"),
            {"fields": (("discount_deduct", "discount_percent"),)}),
        (None, {"fields": (("min_purchase", "free_shipping"),)}),
        (_("Valid for"),
            {"fields": (("valid_from", "valid_to", "uses_remaining"),)}),
    )


admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
if settings.SHOP_USE_VARIATIONS:
    admin.site.register(ProductOption, ProductOptionAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(DiscountCode, DiscountCodeAdmin)
