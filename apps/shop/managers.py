
from django.db.models import Manager


class ShopManager(Manager):

	def active(self, **kwargs):
		return self.filter(active=True, **kwargs)

class CartManager(Manager):

	def from_request(self, request):
		"""
		return a cart by id stored in the session, creating it if not found
		"""
		try:
			cart = self.select_related().get(id=request.session.get("cart", None))
		except self.model.DoesNotExist:
			cart = self.create()
			request.session["cart"] = cart.id
		cart.save() # timestamp
		return cart

