
from datetime import datetime, timedelta

from django.db.models import Manager
from django.utils.datastructures import SortedDict

from shop.settings import CART_EXPIRY_MINUTES


class ShopManager(Manager):

	def active(self, **kwargs):
		return self.filter(active=True, **kwargs)

class CartManager(Manager):

	def from_request(self, request):
		"""
		return a cart by id stored in the session, creating it if not found
		as well as removing old carts prior to creating a new cart
		"""
		expiry_time = datetime.now() - timedelta(minutes=CART_EXPIRY_MINUTES)
		try:
			cart = self.select_related().get(last_updated__gte=expiry_time, 
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

