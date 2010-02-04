
from datetime import datetime, timedelta
from operator import ior
from string import punctuation

from django.conf import settings
from django.db.models import Manager, Q
from django.utils.datastructures import SortedDict

from shop.settings import CART_EXPIRY_MINUTES


class ActiveManager(Manager):

	def active(self, *args, **kwargs):
		"""
		items flagged as active
		"""
		kwargs["active"] = True
		return self.filter(*args, **kwargs)

class CategoryManager(ActiveManager):
	pass

class ProductManager(ActiveManager):
	
	def search(self, query):
		"""
		build a queryset matching words in the given search query. treat quoted 
		terms as exact phrases and take into account + and - symbols as 
		modifiers controlling which terms to require and exclude
		"""
		if max([len(t) for t in "".join([c for c in query 
			if c == " " or c.isalnum()]).split(" ")]) < 3:
			return []
		_p = lambda s: s.strip(punctuation)
		_Q = lambda s: Q(search_text__icontains=_p(s))
		queryset = self.active()
		# remove extra spaces, put modifiers inside quoted terms and create 
		# search term list from exact phrases and then remaining words
		terms = " ".join(filter(None, query.split(" "))).replace("+ ", "+"
			).replace('+"', '"+').replace("- ", "-").replace('-"', '"-').split('"')
		terms = terms[1::2] + "".join(terms[::2]).split(" ")
		# for mysql use django search filter, for others manually create filters 
		if settings.DATABASE_ENGINE == "mysql":
			queryset = queryset.filter(search_text__search=query)
		else:
			# filter queryset by terms to require and exclude
			required = [_Q(t[1:]) for t in terms if _p(t[1:]) and t[0] == "+"]
			exclude = [~_Q(t[1:]) for t in terms if _p(t[1:]) and t[0] == "-"]
			if required or exclude:
				queryset = queryset.filter(*required + exclude)
			# filter queryset by remaining unmodified terms
			remaining = [_Q(t) for t in terms if _p(t) and t[0] not in "+-"]
			if remaining:
				queryset = queryset.filter(reduce(ior, remaining))
		# sort results by number of occurrences
		terms = set([_p(t.lower()) for t in terms])
		rank = lambda p: sum([p.search_text.lower().count(t) for t in terms])
		return sorted(queryset, key=rank, reverse=True)

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
		valid_to = Q(valid_to__isnull=True) | Q(valid_from__gte=datetime.now())
		return super(DiscountCodeManager, self).active(valid_from, valid_to)
	
	def valid(self, code, cart):
		"""
		items flagged as active and within date range as well checking that 
		the given cart contains items that the code is valid for
		"""
		try:
			discount = self.active().get(code=code)
		except self.model.DoesNotExist:
			return False
		return discount.products().filter(
			variations__sku__in=[item.sku for item in cart]).count() > 0

