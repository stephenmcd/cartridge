
from datetime import datetime
from shop.models import Cart
from shop.exceptions import CheckoutError


def shipping(request):
	"""
	implement shipping calculation here
	"""
	#cart = Cart.objects.from_request(request)
	pass
	
def payment(payment_form):
	"""
	implement payment processing here
	"""
	now = datetime.now()
	if (payment_form.cleaned_data["card_expiry_year"] == now.year and 
		payment_form.cleaned_data["card_expiry_month"] < now.month):
		raise CheckoutError("Invalid Expiry Date")

