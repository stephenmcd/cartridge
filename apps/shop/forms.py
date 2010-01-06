
from copy import copy
from datetime import datetime
from django import forms
from django.contrib.formtools.wizard import FormWizard
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe
from shop.models import Product, ProductVariation, SelectedProduct, Cart, Order
from shop.exceptions import CheckoutError
from shop.utils import shipping, payment


CARD_TYPE_CHOICES = ("Mastercard", "Visa", "Diners", "Amex")
CARD_TYPE_CHOICES = zip(CARD_TYPE_CHOICES, CARD_TYPE_CHOICES)
CARD_MONTHS = ["%02d" % i for i in range(1, 13)]
CARD_MONTHS = zip(CARD_MONTHS, CARD_MONTHS)
		

def get_add_cart_form(product):
	"""
	return the add to cart form dynamically adding the options to it using the 
	variations of the given product
	"""

	class AddCartForm(forms.Form):
		"""
		add to cart form for product
		"""

		quantity = forms.IntegerField(min_value=1)
	
		def clean(self):
			"""
			set the form's selected variation if the selected options and
			quantity are valid
			"""
			options = self.cleaned_data.copy()
			quantity = options.pop("quantity")
			error = None
			try:
				variation = product.variations.get(**options)
			except ProductVariation.DoesNotExist:
				error = "The selected options are unavailable"
			else:
				if variation.quantity is not None:
					if not variation.in_stock(quantity):
						error = "The selected quantity is currently unavailable"
					elif not variation.in_stock():
						error = "The selected options are currently not in stock"
			if error:
				raise forms.ValidationError(error)
			self.variation = variation
			return self.cleaned_data

	# create the dict of form fields for the product's selected options and 
	# add them to a newly created form type 
	option_names = [field.name for field in ProductVariation.option_fields()]
	option_values = zip(*product.variations.values_list(*option_names))
	option_fields = {}
	for i, name in enumerate(option_names):
		values = filter(None, set(option_values[i]))
		if values:
			option_fields[name] = forms.ChoiceField(choices=zip(values, values))
	return type("AddCartForm", (AddCartForm,), option_fields)

class OrderForm(forms.ModelForm):
	"""
	model form for order with billing and shipping details - step 1 of checkout
	"""

	class Meta:
		model = Order
		fields = (Order.billing_field_names() + Order.shipping_field_names() + 
			["additional_instructions"])
			
	def _fieldset(self, prefix):
		"""
		return a subset of fields by making a copy of itself containing only 
		the fields with the given prefix, storing the given prefix each time 
		it's called and when finally called with the prefix "other", returning 
		a copy with all the fields that have not yet been returned
		"""
		if not hasattr(self, "_fields_done"):
			self._fields_done = {}
		fieldset = copy(self)
		fieldset.fields = SortedDict([field for field in self.fields.items() if 
			(prefix != "other" and field[0].startswith(prefix)) or 
			(prefix == "other" and field[0] not in self._fields_done.keys())])
		self._fields_done.update(fieldset.fields)
		return fieldset
	
	def __getattr__(self, name):
		"""
		dynamic fieldset caller
		"""
		if name.startswith("fieldset_"):
			return self._fieldset(name.split("fieldset_", 1)[1])
		raise AttributeError, name
		
class ExpiryYearField(forms.ChoiceField):
	"""
	choice field for credit card expiry with years from now as choices
	"""

	def __init__(self, *args, **kwargs):
		year = datetime.now().year
		years = range(year, year + 21)
		kwargs["choices"] = zip(years, years)
		super(ExpiryYearField, self).__init__(*args, **kwargs)
		
class PaymentForm(forms.Form):
	"""
	credit card details form - step 2 of checkout
	"""	

	card_name = forms.CharField()
	card_type = forms.ChoiceField(choices=CARD_TYPE_CHOICES)
	card_number = forms.CharField()
	card_expiry_month = forms.ChoiceField(choices=CARD_MONTHS)
	card_expiry_year = ExpiryYearField()
	card_ccv = forms.CharField()
	
	def clean(self):
		try:
			payment(self)
		except CheckoutError, e:
			raise forms.ValidationError(e)
		return self.cleaned_data

class CheckoutWizard(FormWizard):
	"""
	combine the two checkout step forms into a form wizard - using parse_params
	and get_form, pass the request object to each form so that in the payment 
	form's clean method the request object can be passed to utils.payment
	"""

	def parse_params(self, request, *args, **kwargs):
		"""
		store the request for passing to each form
		"""
		self._request = request
		
	def get_form(self, *args, **kwargs):
		"""
		store the request against each form
		"""
		form = super(CheckoutWizard, self).get_form(*args, **kwargs)
		form._request = self._request
		return form
		
	def get_template(self, step):
		return "shop/%s.html" % ("billing_shipping", "payment")[int(step)]

	def done(self, request, form_list):
		"""
		create the order and remove the cart
		"""
		cart = Cart.objects.from_request(request)
		order = form_list[0].save(commit=False)
		order.shipping_total = shipping(request)
		order.item_total = cart.total_price()
		order.save()
		for item in cart:
			fields = [field.name for field in SelectedProduct._meta.fields]
			item = dict([(field, getattr(item, field)) for field in fields])
			order.items.create(**item)
		cart.delete()
		return HttpResponseRedirect(reverse("shop_complete"))

checkout_wizard = CheckoutWizard([OrderForm, PaymentForm])

#####################
#    admin widgets 
#####################

class MoneyWidget(forms.TextInput):
	"""
	renders missing decimal places for money fields
	"""
	def render(self, name, value, attrs):
		if value is not None:
			value = "%.2f" % value
		return super(MoneyWidget, self).render(name, value, attrs)

class ProductOptionWidget(forms.CheckboxSelectMultiple):
	"""
	renders some extra styling on product option checkboxes
	"""
	def render(self, name, value, **kwargs):
		rendered = super(ProductOptionWidget, self).render(name, value, **kwargs)
		rendered = rendered.replace("<li", "<li style='list-style-type:none;" \
			"float:left;margin-right:10px;'")
		rendered = rendered.replace("<label", "<label style='width:auto;'")
		return mark_safe(rendered)

class _BaseProductAdminForm(forms.ModelForm):
	"""
	base ModelForm for ProductAdminForm that is dynamically subclassed with 
	option fields below
	"""
	class Meta:
		model = Product

# build a dict of option fields for creating the final ProductAdminForm type
_fields = dict([(field.name, forms.MultipleChoiceField(
	choices=field.choices, widget=ProductOptionWidget, required=False)) 
	for field in ProductVariation.option_fields()])
ProductAdminForm = type("ProductAdminForm", (_BaseProductAdminForm,), _fields)


