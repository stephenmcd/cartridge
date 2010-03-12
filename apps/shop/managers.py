
from datetime import datetime, timedelta
from operator import ior, iand
from string import punctuation

from django.conf import settings
from django.db.models import Manager, Q, CharField, TextField
from django.db.models.query import QuerySet
from django.utils.datastructures import SortedDict

from shop.settings import CART_EXPIRY_MINUTES


class ActiveManager(Manager):

    def active(self, *args, **kwargs):
        """
        items flagged as active
        """
        kwargs["active"] = True
        return self.filter(*args, **kwargs)

class SearchableQuerySet(QuerySet):
    
    def __init__(self, *args, **kwargs):
        self._search_ordered = False
        self._search_terms = set()
        self._search_fields = set(kwargs.pop("search_fields", []))
        super(SearchableQuerySet, self).__init__(*args, **kwargs)

    def search(self, query, search_fields=None):
        """
        Build a queryset matching words in the given search query, treating 
        quoted terms as exact phrases and taking into account + and - symbols as 
        modifiers controlling which terms to require and exclude.
        """
        
        # Use fields arg if given, otherwise check internal list which if empty, 
        # populate from model attr or char-like fields.
        if search_fields is None:
            search_fields = self._search_fields
        if len(search_fields) == 0:
        	search_fields = getattr(self.model, "search_fields", [])
        if len(search_fields) == 0:
            search_fields = [f.name for f in self.model._meta.fields
                if issubclass(f.__class__, CharField) or 
                issubclass(f.__class__, TextField)]
        if len(search_fields) == 0:
        	return self.none()
        self._search_fields.update(search_fields)

        # Remove extra spaces, put modifiers inside quoted terms.
        terms = " ".join(query.split()).replace("+ ", "+").replace('+"', '"+'
            ).replace("- ", "-").replace('-"', '"-').split('"')
        # Strip punctuation other than modifiers from terms and create term 
        # list first from quoted terms, and then remaining words.
        terms = [("" if t[0] not in "+-" else t[0]) + t.strip(punctuation) 
            for t in terms[1::2] + "".join(terms[::2]).split()]
        # Append terms to internal list for sorting when results are iterated.
        self._search_terms.update([t.lower().strip(punctuation) 
            for t in terms if t[0] != "-"])

        # Create the queryset combining each set of terms.
        excluded = [reduce(iand, [~Q(**{"%s__icontains" % f: t[1:]})
            for f in search_fields]) for t in terms if t[0] == "-"]
        required = [reduce(ior, [Q(**{"%s__icontains" % f: t[1:]})
            for f in search_fields]) for t in terms if t[0] == "+"]
        optional = [reduce(ior, [Q(**{"%s__icontains" % f: t})
            for f in search_fields]) for t in terms if t[0] not in "+-"]
        queryset = self
        if excluded:
            queryset = queryset.filter(reduce(iand, excluded))
        if required:
            queryset = queryset.filter(reduce(iand, required))
        # Optional terms aren't relevant to the filter if there are terms
        # that are explicitly required
        elif optional:
            queryset = queryset.filter(reduce(ior, optional))
        return queryset

    def _clone(self, *args, **kwargs):
        """
        Ensure attributes are copied to subsequent queries.
        """
        for attr in ("_search_terms", "_search_fields", "_search_ordered"):
            kwargs[attr] = getattr(self, attr)
        return super(SearchableQuerySet, self)._clone(*args, **kwargs)
    
    def order_by(self, *field_names):
        """
        Mark the filter as being ordered if search has occurred.
        """
        if not self._search_ordered:
            self._search_ordered = len(self._search_terms) > 0
        return super(SearchableQuerySet, self).order_by(*field_names)
        
    def iterator(self):
        """
        If search has occured and no ordering has occurred, sort the results by 
        number of occurrences of terms.
        """
        results = super(SearchableQuerySet, self).iterator()
        if self._search_terms and not self._search_ordered:
            sort_key = lambda obj: sum([getattr(obj, f).lower().count(t.lower()) 
                for f in self._search_fields for t in self._search_terms 
                if getattr(obj, f)])
            return iter(sorted(results, key=sort_key, reverse=True))
        return results

class SearchableManager(Manager):
    """
    Manager providing a chainable queryset.
    Adapted from http://www.djangosnippets.org/snippets/562/
    """
    
    def __init__(self, *args, **kwargs):
        self._search_fields = kwargs.pop("search_fields", [])
        super(SearchableManager, self).__init__(*args, **kwargs)

    def get_query_set(self):
        return SearchableQuerySet(self.model, search_fields=self._search_fields)

    def __getattr__(self, attr, *args):
        try:
            return getattr(self.__class__, attr, *args)
        except AttributeError:
            return getattr(self.get_query_set(), attr, *args)

class ProductManager(ActiveManager, SearchableManager):
    pass
    
class CartManager(Manager):

    def from_request(self, request):
        """
        return a cart by id stored in the session, creating it if not found
        as well as removing old carts prior to creating a new cart
        """
        expiry_time = datetime.now() - timedelta(minutes=CART_EXPIRY_MINUTES)
        try:
            cart = self.get(last_updated__gte=expiry_time, 
                id=request.session.get("cart", None))
        except self.model.DoesNotExist:
            self.filter(last_updated__lt=expiry_time).delete()
            cart = self.create()
            request.session["cart"] = cart.id
        else:
            cart.save() # update timestamp
        return cart

class ProductVariationManager(Manager):

    use_for_related_fields = True
    
    def _empty_options_lookup(self, exclude=None):
        """
        create a lookup dict of field__isnull for options fields
        """
        if not exclude:
            exclude = {}
        return dict([("%s__isnull" % f.name, True) 
            for f in self.model.option_fields() if f.name not in exclude])

    def create_from_options(self, options):
        """
        create all unique variations from the selected options
        """
        if options:
            options = SortedDict(options)
            # product of options
            variations = [[]]
            for values_list in options.values():
                variations = [x + [y] for x in variations for y in values_list]
            for variation in variations:
                # lookup unspecified options as null to ensure a unique filter
                variation = dict(zip(options.keys(), variation))
                lookup = dict(variation)
                lookup.update(self._empty_options_lookup(exclude=variation))
                try:
                    self.get(**lookup)
                except self.model.DoesNotExist:
                    self.create(**variation)
                    
    def manage_empty(self):
        """
        create an empty variation (no options) if none exist, otherwise if 
        multiple variations exist ensure there is no redundant empty variation.
        also ensure there is at least one default variation
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
        increases the given field by datetime.today().toordinal() which provides 
        a time scaling value we can order by to determine popularity over time
        """
        action, created = self.get_or_create(
            timestamp=datetime.today().toordinal())
        setattr(action, field, getattr(action, field) + 1)
        action.save()
    
    def added_to_cart(self):
        """
        increase total_cart when product is added to cart
        """
        self._action_for_field("total_cart")

    def purchased(self):
        """
        increase total_purchased when product is purchased
        """
        self._action_for_field("total_purchase")

class DiscountCodeManager(ActiveManager):

    def active(self, *args, **kwargs):
        """
        items flagged as active and in valid date range if date(s) are specified
        """
        valid_from = Q(valid_from__isnull=True) | Q(valid_from__lte=datetime.now())
        valid_to = Q(valid_to__isnull=True) | Q(valid_to__gte=datetime.now())
        return super(DiscountCodeManager, self).active(valid_from, valid_to)
    
    def get_valid(self, code, cart):
        """
        items flagged as active and within date range as well checking that 
        the given cart contains items that the code is valid for
        """
        discount = self.active().get(Q(min_purchase__isnull=True) | 
            Q(min_purchase__lte=cart.total_price()), code=code)
        products = discount.products.all()
        if products.count() > 0 and products.filter(variations__sku__in=
            [item.sku for item in cart]).count() == 0:
            raise self.model.DoesNotExist
        return discount

