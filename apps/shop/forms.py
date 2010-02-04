
from copy import copy
from datetime import datetime
from locale import localeconv

from django import forms
from django.forms.models import BaseModelForm, BaseInlineFormSet
from django.contrib.formtools.wizard import FormWizard
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from shop.models import Product, ProductVariation, SelectedProductModel, \
	Cart, Order, DiscountCode
from shop.exceptions import CheckoutError
from shop.settings import CARD_TYPES, ORDER_FROM_EMAIL
from shop.templatetags.shop_tags import thumbnail
from shop import checkout
from shop.utils import make_choices, send_mail_template, set_locale


ADD_CART_ERRORS = {
	"invalid_options": _("The selected options are currently unavailable."),
	"no_stock": _("The selected options are currently not in stock."),
	"no_stock_quantity": _("The selected quantity is currently unavailable."),
}


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
				variation = product.variations.get(unit_price__isnull=False,
					**options)
			except ProductVariation.DoesNotExist:
				error = "invalid_options"
			else:
				if variation.quantity is not None:
					if not variation.has_stock(quantity):
						error = "no_stock_quantity"
					elif not variation.has_stock():
						error = "no_stock"
			if error:
				raise forms.ValidationError(ADD_CART_ERRORS[error])
			self.variation = variation
			return self.cleaned_data

	# create the dict of form fields for the product's selected options and 
	# add them to a newly created form type 
	option_names = [field.name for field in ProductVariation.option_fields()]
	option_values = zip(*product.variations.filter(
		unit_price__isnull=False).values_list(*option_names))
	option_fields = {}
	if option_values:
		for i, name in enumerate(option_names):
			values = filter(None, set(option_values[i]))
			if values:
				option_fields[name] = forms.ChoiceField(
					choices=make_choices(values))
	return type("AddCartForm", (AddCartForm,), option_fields)

class CheckoutForm(object):
	"""
	checkout form mixin for calling custom handlers 
	"""
	def clean(self):
		try:
			self._checkout_handler(self._request, self)
		except CheckoutError, e:
			raise forms.ValidationError(e)
		return self.cleaned_data

class OrderForm(CheckoutForm, forms.ModelForm):
	"""
	model form for order with billing and shipping details - step 1 of checkout
	"""
	
	class Meta:
		model = Order
		fields = (Order.billing_detail_field_names() + 
			Order.shipping_detail_field_names() + ["additional_instructions"])
			
	def __init__(self, *args, **kwargs):
		super(OrderForm, self).__init__(*args, **kwargs)
		if not DiscountCode.objects.active().exists():
			self.fields["discount_code"].widget = forms.HiddenInput()

	def _fieldset(self, prefix):
		"""
		return a subset of fields by making a copy of itself containing only 
		the fields with the given prefix, storing the given prefix each time 
		it's called and when finally called with the prefix "other", returning 
		a copy with all the fields that have not yet been returned
		"""
		fieldset = copy(self)
		if not hasattr(self, "_fields_done"):
			self._fields_done = {}
		else:
			# ensures non-field errors only appear in the first fieldset
			fieldset.non_field_errors = lambda *args: None
		fieldset.fields = SortedDict([f for f in self.fields.items() if 
			(prefix != "other" and f[0].startswith(prefix)) or 
			(prefix == "other" and f[0] not in self._fields_done)])
		self._fields_done.update(fieldset.fields)
		return fieldset
	
	def __getattr__(self, name):
		"""
		dynamic fieldset caller
		"""
		if name.startswith("fieldset_"):
			return self._fieldset(name.split("fieldset_", 1)[1])
		raise AttributeError, name
	
	def clean_discount_code(self):
		code = self.cleaned_data.get("code", "")
		if code:
			cart = Cart.objects.from_request(self._request)
			if not DiscountCode.objects.valid(code=code, cart=cart):
				raise forms.ValidationError("The discount code entered is invalid.")
		return code

class ExpiryYearField(forms.ChoiceField):
	"""
	choice field for credit card expiry with years from now as choices
	"""
	def __init__(self, *args, **kwargs):
		year = datetime.now().year
		kwargs["choices"] = make_choices(range(year, year + 21))
		super(ExpiryYearField, self).__init__(*args, **kwargs)
		
class PaymentForm(CheckoutForm, forms.Form):
	"""
	credit card details form - step 2 of checkout
	"""	
	card_name = forms.CharField()
	card_type = forms.ChoiceField(choices=make_choices(CARD_TYPES))
	card_number = forms.CharField()
	card_expiry_month = forms.ChoiceField(
		choices=make_choices(["%02d" % i for i in range(1, 13)]))
	card_expiry_year = ExpiryYearField()
	card_ccv = forms.CharField()

class CheckoutWizard(FormWizard):
	"""
	combine the two checkout step forms into a form wizard - using parse_params
	and get_form, pass the request object to each form so that it can be sent 
	on to each of the custom handlers in the checkout module
	"""
	
	# these correspond to the custom checkout handler names in the checkout
	# module for each step as well as the template names for each step
	step_names = ("billing_shipping", "payment")

	def parse_params(self, request, *args, **kwargs):
		"""
		store the request for passing to each form
		"""
		self._request = request
		
	def get_form(self, *args, **kwargs):
		"""
		store the request and checkout handler against each form
		"""
		form = super(CheckoutWizard, self).get_form(*args, **kwargs)
		form._checkout_handler = getattr(checkout, self.step_names[int(args[0])])
		form._request = self._request
		return form
		
	def get_template(self, step):
		return "shop/%s.html" % self.step_names[int(step)]

	def done(self, request, form_list):
		"""
		create the order, remove the cart and email receipt
		"""
		cart = Cart.objects.from_request(request)
		order = form_list[0].save(commit=False)
		for shipping_field in ("shipping_type", "shipping_total"):
			if shipping_field in request.session:
				setattr(order, shipping_field, request.session[shipping_field])
				del request.session[shipping_field]
		order.item_total = cart.total_price()
		order.save()
		for item in cart:
			# decrease the product's quantity and set the purchase action
			try:
				variation = ProductVariation.objects.get(sku=item.sku)
			except ProductVariation.DoesNotExist:
				pass
			else:
				product = variation.product
				if product.quantity is not None:
					product.quantity -= item.quantity
					product.save()
				product.actions.purchased()
			# copy the cart item to the order
			fields = [field.name for field in SelectedProductModel._meta.fields]
			item = dict([(field, getattr(item, field)) for field in fields])
			order.items.create(**item)
		cart.delete()
		from_email = ORDER_FROM_EMAIL
		if from_email is None:
			from_email = "do_not_reply@%s" % request.get_host()
		send_mail_template(_("Order Receipt"), "shop/email/order_receipt", 
			from_email, order.billing_detail_email, context={"order": order, 
			"order_items": order.items.all(), "request": request})
		return HttpResponseRedirect(reverse("shop_complete"))

checkout_wizard = CheckoutWizard([OrderForm, PaymentForm])

#######################
#	admin widgets	
#######################

class ImageWidget(forms.FileInput):
	"""
	renders a visible thumbnail for image fields
	"""
	def render(self, name, value, attrs):
		rendered = super(ImageWidget, self).render(name, value, attrs)
		if value:
			orig_url = "%s%s" % (settings.MEDIA_URL, value)
			thumb_url = "%s%s" % (settings.MEDIA_URL, thumbnail(value, 48, 48))
			rendered = "<a target='_blank' href='%s'><img " \
				"style='margin-right:6px;' src='%s' /></a>%s" % (orig_url, 
				thumb_url, rendered)
		return mark_safe(rendered)

class MoneyWidget(forms.TextInput):
	"""
	renders missing decimal places for money fields
	"""
	def render(self, name, value, attrs):
		try:
			value = float(value)
		except (TypeError, ValueError):
			pass
		else:
			set_locale()
			value = ("%%.%sf" % localeconv()["frac_digits"]) % value
		return super(MoneyWidget, self).render(name, value, attrs)

# build a dict of option fields for creating the ProductAdminForm type
_fields = dict([(field.name, forms.MultipleChoiceField(choices=field.choices, 
	widget=forms.CheckboxSelectMultiple, required=False)) for field in 
	ProductVariation.option_fields()]) 
_fields["Meta"] = type("Meta", (object,), {"model": Product})
ProductAdminForm = type("ProductAdminForm", (forms.ModelForm,), _fields)

class ProductVariationAdminForm(forms.ModelForm):
	"""
	ensures the list of images for the variation are specific to the variation's 
	product
	"""
	def __init__(self, *args, **kwargs):
		super(ProductVariationAdminForm, self).__init__(*args, **kwargs)
		self.fields["image"].queryset = self.fields["image"].queryset.filter(
			product=kwargs["instance"].product)
	
class ProductVariationAdminFormset(BaseInlineFormSet):
	"""
	ensures no more than one variation is checked as default
	"""
	def clean(self):
		if len([f for f in self.forms if hasattr(f, "cleaned_data") and
			f.cleaned_data["default"]]) > 1:
			raise forms.ValidationError(
				_("Only one variation can be checked as the default."))

class SaleAdminForm(forms.ModelForm):
	"""
	ensures only one price field is given a value
	"""
	def clean_sale_price_exact(self):
		reductions = filter(None, [self.cleaned_data.get(f, None) for f in 
			("sale_price_deduct","sale_price_percent","sale_price_exact")])
		if len(reductions) > 1:
			error = _("Please enter a value for only one type of reduction.")
			raise forms.ValidationError(error)
		return self.cleaned_data["sale_price_exact"]

