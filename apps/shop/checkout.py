"""
checkout.py - provides handlers for each step of the checkout process, each 
handlers is passed the (cleaned) form and request objects. the cart object is 
also accessible via Cart.objects.from_request(request)

billing_shipping() should set the shipping type and total via 
shop.utils.set_shipping(request, shipping_type, shipping_total)

payment() should handle payment gateway integration

each step should raise CheckoutError where required, eg credit card declined.
"""

from shop.models import Cart
from shop.exceptions import CheckoutError
from shop.utils import set_shipping


def billing_shipping(request, billing_shipping_form):
	"""
	implement shipping handling here
	"""
	# cart is also accessible via Cart.objects.from_request(request)
	set_shipping(request, "Shipping Test", 10)
	
def payment(request, payment_form):
	"""
	implement payment gateway integration here
	"""
	# eg declined credit card: raise CheckoutError("Credit card declined")
	pass
