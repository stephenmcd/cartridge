
from datetime import datetime, timedelta
from django.db.models import Manager
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
			cart = self.select_related().get(timestamp__gte=expiry_time, 
				id=request.session.get("cart", None))
		except self.model.DoesNotExist:
			self.filter(timestamp__lt=expiry_time).delete()
			cart = self.create()
			request.session["cart"] = cart.id
		else:
			cart.save() # update timestamp
		return cart

