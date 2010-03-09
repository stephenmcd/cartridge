
from copy import copy
from datetime import datetime
from itertools import dropwhile, takewhile
from locale import localeconv
from re import match

from django import forms
from django.forms.models import BaseModelForm, BaseInlineFormSet
from django.contrib.formtools.wizard import FormWizard
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from shop.models import Product, ProductVariation, SelectedProduct, \
    Cart, Order, DiscountCode
from shop.exceptions import CheckoutError
from shop.settings import CARD_TYPES, ORDER_FROM_EMAIL
from shop.templatetags.shop_tags import thumbnail
from shop import checkout
from shop.utils import make_choices, send_mail_template, set_locale, \
    set_cookie, sign


ADD_PRODUCT_ERRORS = {
    "invalid_options": _("The selected options are currently unavailable."),
    "no_stock": _("The selected options are currently not in stock."),
    "no_stock_quantity": _("The selected quantity is currently unavailable."),
}

address_fields = (Order.billing_detail_field_names() + 
    Order.shipping_detail_field_names())


def get_add_product_form(product):
    """
    return the add product form dynamically adding the options to it using the 
    variations of the given product and setting the minimum quantity based on 
    whether the product is being added to the cart or the wishlist
    """

    class BaseAddProductForm(forms.Form):
        """
        add product form for cart and wishlist
        """

        quantity = forms.IntegerField(min_value=1)
        
        def __init__(self, *args, **kwargs):
            self._to_cart = kwargs.pop("to_cart", True)
            super(BaseAddProductForm, self).__init__(*args, **kwargs)
    
        def clean(self):
            """
            set the form's selected variation if the selected options and
            quantity are valid
            """
            options = self.cleaned_data.copy()
            quantity = options.pop("quantity", 0)
            if self._to_cart: # ensure the product has a price if adding to cart
                options["unit_price__isnull"] = False
            error = None
            try:
                variation = product.variations.get(**options)
            except ProductVariation.DoesNotExist:
                error = "invalid_options"
            else:
                if self._to_cart:
                    if not variation.has_stock():
                        error = "no_stock"
                    elif not variation.has_stock(quantity):
                        error = "no_stock_quantity"
            if error is not None:
                raise forms.ValidationError(ADD_PRODUCT_ERRORS[error])
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
    return type("AddProductForm", (BaseAddProductForm,), option_fields)

class FormsetForm(object):
    """
    form mixin that provides template methods for iterating through sets of 
    fields by prefix, single fields and finally remaning fields that haven't 
    been iterated with each fieldset made up from a copy of the original form 
    giving access to as_* methods
    """

    def _fieldset(self, field_names):
        """
        return a subset of fields by making a copy of the form containing only 
        the given field names
        """
        fieldset = copy(self)
        if not hasattr(self, "_fields_done"):
            self._fields_done = []
        else:
            # all fieldsets will contain all non-field errors, so for fieldsets
            # other than the first ensure the call to non-field errors does nothing
            fieldset.non_field_errors = lambda *args: None
        field_names = filter(lambda f: f not in self._fields_done, field_names)
        fieldset.fields = SortedDict([(f, self.fields[f]) for f in field_names])
        self._fields_done.extend(field_names)
        return fieldset

    def __getattr__(self, name):
        """
        dynamic fieldset caller - matches requested attribute name against 
        pattern for creating the list of field names to use for the fieldset
        """
        filters = (
            ("^other_fields$", lambda: 
                self.fields.keys()),
            ("^(\w*)_fields$", lambda name: 
                [f for f in self.fields.keys() if f.startswith(name)]),
            ("^(\w*)_field$", lambda name: 
                [f for f in self.fields.keys() if f == name]),
            ("^fields_before_(\w*)$", lambda name: 
                takewhile(lambda f: f != name, self.fields.keys())),
            ("^fields_after_(\w*)$", lambda name: 
                list(dropwhile(lambda f: f != name, self.fields.keys()))[1:]),
        )
        for filter_exp, filter_func in filters:
            filter_args = match(filter_exp, name)
            if filter_args is not None:
                return self._fieldset(filter_func(*filter_args.groups()))
        raise AttributeError(name)

class CheckoutStep(FormsetForm):
    """
    checkout step providing hooks for custom handlers via clean
    """

    def clean(self):
        """
        call custom handler for step as well as storing the form data for the 
        step in the session for pre-populating
        """
        try:
            self._step_handler(self._request, self)
        except CheckoutError, e:
            raise forms.ValidationError(e)
        cleaned_data = super(CheckoutStep, self).clean()
        self._request.session["checkout_step_%s" % self._step] = cleaned_data
        return cleaned_data

class OrderForm(CheckoutStep, forms.ModelForm):
    """
    model form for order with billing and shipping details - step 1 of checkout
    """
    
    same_billing_shipping = forms.BooleanField(required=False, 
        label=_("My delivery details are the same as my billing details"))
    remember = forms.BooleanField(required=False, 
        label=_("Remember my address for next time"))
    
    class Meta:
        model = Order
        fields = address_fields + ["additional_instructions", "discount_code"]
            
    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        if DiscountCode.objects.active().count() == 0:
            self.fields["discount_code"].widget = forms.HiddenInput()
    
    def clean_discount_code(self):
        """
        validate the discount code if given and update the session with free 
        shipping and/or the discount amount
        """
        code = self.cleaned_data.get("discount_code", "")
        if code:
            cart = Cart.objects.from_request(self._request)
            try:
                discount = DiscountCode.objects.get_valid(code=code, cart=cart)
            except DiscountCode.DoesNotExist:
                raise forms.ValidationError("The discount code entered is invalid.")
            self._request.session["free_shipping"] = discount.free_shipping
            self._request.session["discount_total"] = discount.calculate(
                cart.total_price())
        return code

class ExpiryYearField(forms.ChoiceField):
    """
    choice field for credit card expiry with years from now as choices
    """
    def __init__(self, *args, **kwargs):
        year = datetime.now().year
        kwargs["choices"] = make_choices(range(year, year + 21))
        super(ExpiryYearField, self).__init__(*args, **kwargs)
        
class PaymentForm(CheckoutStep, forms.Form):
    """
    credit card details form - step 2 of checkout
    """    
    card_name = forms.CharField(label=_("Cardholder name"))
    card_type = forms.ChoiceField(label=_("Type"), choices=make_choices(CARD_TYPES))
    card_number = forms.CharField(label=_("Card number"))
    card_expiry_month = forms.ChoiceField(
        choices=make_choices(["%02d" % i for i in range(1, 13)]))
    card_expiry_year = ExpiryYearField()
    card_ccv = forms.CharField(label="CCV")

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
        
    def get_form(self, step, data=None):
        """
        pre-populate the form from the session and set some extra attributes 
        for the form
        """
        initial = self.initial.get(step, None)
        step_name = self.step_names[int(step)]
        if step_name != "payment":
            initial = self._request.session.get("checkout_step_%s" % step, None)
            # look up the billing/shipping address fields from the last order 
            # if "remember my details" was checked
            if step_name == "billing_shipping" and initial is None:
                initial = {"same_billing_shipping": True}
                parts = self._request.COOKIES.get("remember", "").split(":")
                if len(parts) == 2 and parts[0] == sign(parts[1]): 
                    initial["remember"] = True
                    previous_orders = Order.objects.filter(key=parts[1]
                        ).values(*address_fields)
                    if len(previous_orders) > 0:
                        initial.update(previous_orders[0])
                        # set initial value for "same billing/shipping" based on 
                        # whether both sets of address fields are all equal
                        ship_field = lambda f: "shipping_%s" % f[len("billing_"):]
                        if any([f for f in initial.keys() 
                            if f.startswith("billing_") and ship_field(f) in 
                            initial and initial[f] != initial[ship_field(f)]]):
                            initial["same_billing_shipping"] = False
        form = self.form_list[step](data, initial=initial, 
            prefix=self.prefix_for_step(step))
        form._request = self._request
        form._step = step
        form._step_handler = getattr(checkout, self.step_names[int(step)], 
            lambda *args: None)
        return form
        
    def get_template(self, step):
        return "shop/%s.html" % self.step_names[int(step)]

    def done(self, request, form_list):
        """
        create the order, remove the cart and email receipt
        """
        response = HttpResponseRedirect(reverse("shop_complete"))
        cart = Cart.objects.from_request(request)
        order = form_list[0].save(commit=False)
        # push session persisted fields onto the order
        for field in ("shipping_type", "shipping_total", "discount_total"):
            if field in request.session:
                setattr(order, field, request.session[field])
                del request.session[field]
        for i in range(len(form_list)):
            del request.session["checkout_step_%s" % i]
        order.item_total = cart.total_price()
        order.key = request.session.session_key
        order.save()
        if form_list[0].cleaned_data.get("remember", False):
            set_cookie(response, "remember", "%s:%s" % (sign(order.key), 
                order.key), secure=request.is_secure())
        else:
            response.delete_cookie("remember")
        for item in cart:
            # decrease the item's quantity and set the purchase action
            try:
                variation = ProductVariation.objects.get(sku=item.sku)
            except ProductVariation.DoesNotExist:
                pass
            else:
                if variation.num_in_stock is not None:
                    variation.num_in_stock -= item.quantity
                    variation.save()
                variation.product.actions.purchased()
            # copy the cart item to the order
            fields = [field.name for field in SelectedProduct._meta.fields]
            item = dict([(field, getattr(item, field)) for field in fields])
            order.items.create(**item)
        cart.delete()
        from_email = ORDER_FROM_EMAIL
        if from_email is None:
            from socket import gethostname
            from_email = "do_not_reply@%s" % gethostname()
        send_mail_template(_("Order Receipt"), "shop/email/order_receipt", 
            from_email, order.billing_detail_email, context={"order": order, 
            "order_items": order.items.all(), "request": request})
        return response

checkout_wizard = CheckoutWizard([OrderForm, PaymentForm])

#######################
#    admin widgets    
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
            attrs["style"] = "text-align:right;"
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

class DiscountAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        """
        build a clean method that validates the last discount field ensuring 
        only one discount field is given a value
        """
        super(DiscountAdminForm, self).__init__(*args, **kwargs)
        fields = [f for f in self.fields.keys() if f.startswith("discount_")]
        def clean_last_discount_field():
            reductions = filter(None, [self.cleaned_data.get(f, None) 
                for f in fields])
            if len(reductions) > 1:
                error = _("Please enter a value for only one type of reduction.")
                raise forms.ValidationError(error)
            return self.cleaned_data[fields[-1]]
        self.__dict__["clean_%s" % fields[-1]] = clean_last_discount_field

