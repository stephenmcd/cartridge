
from collections import defaultdict
from datetime import datetime, timedelta

from django.db.models import Manager, Q
from django.utils.datastructures import SortedDict

from mezzanine.conf import settings


class CartManager(Manager):

    def from_request(self, request):
        """
        Return a cart by ID stored in the session, creating it if not found
        as well as removing old carts prior to creating a new cart.
        """
        expiry_time = datetime.now() - timedelta(
                                    minutes=settings.SHOP_CART_EXPIRY_MINUTES)
        try:
            cart = self.get(last_updated__gte=expiry_time, 
                id=request.session.get("cart", None))
        except self.model.DoesNotExist:
            self.filter(last_updated__lt=expiry_time).delete()
            cart = self.create()
            request.session["cart"] = cart.id
        else:
            cart.save() # Update timestamp.
        return cart


class ProductOptionManager(Manager):

    def as_fields(self):
        """
        Return a dict of product options as their field names and choices.
        """
        options = defaultdict(list)
        for option in self.all():
            options["option%s" % option.type].append(option.name)
        return options        


class ProductVariationManager(Manager):

    use_for_related_fields = True
    
    def _empty_options_lookup(self, exclude=None):
        """
        Create a lookup dict of field__isnull for options fields.
        """
        if not exclude:
            exclude = {}
        return dict([("%s__isnull" % f.name, True) 
            for f in self.model.option_fields() if f.name not in exclude])

    def create_from_options(self, options):
        """
        Create all unique variations from the selected options.
        """
        if options:
            options = SortedDict(options)
            # Build all combinations of options.
            variations = [[]]
            for values_list in options.values():
                variations = [x + [y] for x in variations for y in values_list]
            for variation in variations:
                # Lookup unspecified options as null to ensure a unique filter.
                variation = dict(zip(options.keys(), variation))
                lookup = dict(variation)
                lookup.update(self._empty_options_lookup(exclude=variation))
                try:
                    self.get(**lookup)
                except self.model.DoesNotExist:
                    self.create(**variation)
                    
    def manage_empty(self):
        """
        Create an empty variation (no options) if none exist, otherwise if 
        multiple variations exist ensure there is no redundant empty variation.
        also ensure there is at least one default variation.
        """
        total_variations = self.count()
        if total_variations == 0:
            self.create()
        elif total_variations > 1:
            self.filter(**self._empty_options_lookup()).delete()
        try:
            self.get(default=True)
        except self.model.DoesNotExist:
            first_variation = self.all()[0]
            first_variation.default = True
            first_variation.save()


class ProductActionManager(Manager):
    
    use_for_related_fields = True

    def _action_for_field(self, field):
        """
        Increases the given field by datetime.today().toordinal() which 
        provides a time scaling value we can order by to determine popularity 
        over time.
        """
        action, created = self.get_or_create(
            timestamp=datetime.today().toordinal())
        setattr(action, field, getattr(action, field) + 1)
        action.save()
    
    def added_to_cart(self):
        """
        Increase total_cart when product is added to cart.
        """
        self._action_for_field("total_cart")

    def purchased(self):
        """
        Increase total_purchased when product is purchased.
        """
        self._action_for_field("total_purchase")


class DiscountCodeManager(Manager):

    def active(self, *args, **kwargs):
        """
        Items flagged as active and in valid date range if date(s) are 
        specified.
        """
        valid_from = Q(valid_from__isnull=True) | Q(valid_from__lte=datetime.now())
        valid_to = Q(valid_to__isnull=True) | Q(valid_to__gte=datetime.now())
        return self.filter(valid_from, valid_to, active=True)
    
    def get_valid(self, code, cart):
        """
        Items flagged as active and within date range as well checking that 
        the given cart contains items that the code is valid for.
        """
        discount = self.active().get(Q(min_purchase__isnull=True) | 
            Q(min_purchase__lte=cart.total_price()), code=code)
        products = discount.products.all()
        if products.count() > 0 and products.filter(variations__sku__in=
            [item.sku for item in cart]).count() == 0:
            raise self.model.DoesNotExist
        return discount
