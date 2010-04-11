
from copy import copy
from datetime import datetime
from itertools import dropwhile, takewhile
from locale import localeconv
from re import match

from django import forms
from django.forms.models import BaseInlineFormSet
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, QueryDict
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from shop.models import Product, ProductVariation, SelectedProduct, \
    Cart, Order, DiscountCode
from shop.checkout import CHECKOUT_STEP_FIRST, CHECKOUT_STEP_LAST, \
    CHECKOUT_STEP_PAYMENT
from shop.settings import CARD_TYPES, CHECKOUT_STEPS_SPLIT, \
    CHECKOUT_STEPS_CONFIRMATION
from shop.templatetags.shop_tags import thumbnail
from shop.utils import make_choices, set_locale, set_cookie


ADD_PRODUCT_ERRORS = {
    "invalid_options": _("The selected options are currently unavailable."),
    "no_stock": _("The selected options are currently not in stock."),
    "no_stock_quantity": _("The selected quantity is currently unavailable."),
}


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
    Form mixin that provides template methods for iterating through sets of 
    fields by prefix, single fields and finally remaning fields that haven't 
    been iterated with each fieldset made up from a copy of the original form 
    giving access to as_* methods.
    """

    def _fieldset(self, field_names):
        """
        Return a subset of fields by making a copy of the form containing only 
        the given field names.
        """
        fieldset = copy(self)
        if not hasattr(self, "_fields_done"):
            self._fields_done = []
        fieldset.non_field_errors = lambda *args: None
        field_names = filter(lambda f: f not in self._fields_done, field_names)
        fieldset.fields = SortedDict([(f, self.fields[f]) for f in field_names])
        self._fields_done.extend(field_names)
        return fieldset
        
    def values(self):
        """
        Return pairs of label and value for each field.
        """
        for field in self.fields:
            label = self.fields[field].label
            if label is None:
                label = field[0].upper() + field[1:].replace("_", " ")
            yield (label, self.initial.get(field, self.data.get(field, "")))
        
    def __getattr__(self, name):
        """
        Dynamic fieldset caller - matches requested attribute name against 
        pattern for creating the list of field names to use for the fieldset.
        """
        if name == "errors":
            return None
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

class OrderForm(FormsetForm, forms.ModelForm):
    """
    Main Form for the checkout process - ModelForm for Order with extra fields 
    for credit card. Used across each step of the checkout process with fields 
    being hidden across each step where applicable.
    """
    
    step = forms.IntegerField(widget=forms.HiddenInput())
    same_billing_shipping = forms.BooleanField(required=False, initial=True,
        label=_("My delivery details are the same as my billing details"))
    remember = forms.BooleanField(required=False, initial=True,
        label=_("Remember my address for next time"))
    card_name = forms.CharField(label=_("Cardholder name"))
    card_type = forms.ChoiceField(label=_("Type"), 
        choices=make_choices(CARD_TYPES))
    card_number = forms.CharField(label=_("Card number"))
    card_expiry_month = forms.ChoiceField(
        choices=make_choices(["%02d" % i for i in range(1, 13)]))
    card_expiry_year = forms.ChoiceField()
    card_ccv = forms.CharField(label="CCV")
    
    class Meta:
        model = Order
        fields = [f.name for f in Order._meta.fields if 
            f.name.startswith("billing_detail") or 
            f.name.startswith("shipping_detail")] + ["additional_instructions",     
            "discount_code"]
            
    def __init__(self, request, step, data=None, initial=None):
        """
        Handle setting shipping field values to the same as billing field 
        values in case Javascript is disabled, hiding fields for current step 
        and hiding discount_code field if there are currently no active 
        discount codes.
        """

        # Copy billing fields to shipping fields if "same" checked.
        if (step == CHECKOUT_STEP_FIRST and data is not None and 
            "same_billing_shipping" in data):
            data = copy(data)
            # Prevent second copy occuring for forcing step below when moving
            # backwards in steps.
            data["step"] = step 
            for field in data:
                billing = field.replace("shipping_detail", "billing_detail")
                if "shipping_detail" in field and billing in data:
                    data[field] = data[billing]

        if initial is not None:
            initial["step"] = step
        # Force the specified step in the posted data - this is required to
        # allow moving backwards in steps. 
        if data is not None and int(data["step"]) != step:
            data = copy(data)
            data["step"] = step
            
        super(OrderForm, self).__init__(data=data, initial=initial)
        self._request = request
        self.checkout_errors = []

        # Determine which sets of fields to hide for each checkout step.
        hidden = None
        if CHECKOUT_STEPS_SPLIT:
            if step == CHECKOUT_STEP_FIRST:
                # Hide the cc fields for billing/shipping if steps are split.
                hidden = lambda f: f.startswith("card_")
            elif step == CHECKOUT_STEP_PAYMENT:
                # Hide the non-cc fields for payment if steps are split.
                hidden = lambda f: not f.startswith("card_")
        if CHECKOUT_STEPS_CONFIRMATION and step == CHECKOUT_STEP_LAST:
            # Hide all fields for the confirmation step.
            hidden = lambda f: True
        if hidden is not None:
            for field in self.fields:
                if hidden(field):
                    self.fields[field].widget = forms.HiddenInput()
                    self.fields[field].required = False
            
        # Hide Discount Code field if no codes are active.
        if DiscountCode.objects.active().count() == 0:
            self.fields["discount_code"].widget = forms.HiddenInput()

        # Set the choices for the cc expiry year relative to the current year.
        year = datetime.now().year
        choices = make_choices(range(year, year + 21))
        self.fields["card_expiry_year"].choices = choices
    
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
                self.discount = discount
            except DiscountCode.DoesNotExist:
                error = _("The discount code entered is invalid.")
                raise forms.ValidationError(error)
        return code
        
    def clean(self):
        if self.checkout_errors:
            raise forms.ValidationError(self.checkout_errors)
        return self.cleaned_data

class UserForm(forms.Form):
    """
    Fields for signup & login.
    """
    email = forms.EmailField(label=_("Email Address"))
    password = forms.CharField(label=_("Password"), 
        widget=forms.PasswordInput(render_value=False))

    def authenticate(self):
        """
        Validate email and password as well as setting the user for login.
        """
        self._user = authenticate(username=self.cleaned_data.get("email", ""), 
            password=self.cleaned_data.get("password", ""))
    
    def login(self, request):
        """
        Log the user in.
        """
        login(request, self._user)

class SignupForm(UserForm):
    
    def clean_email(self):
        """
        Ensure the email address is not already registered.
        """
        email = self.cleaned_data["email"]
        try:
            User.objects.get(username=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(_("This email is already registered"))
        
    def save(self):
        """
        Create the new user using their email address as their username.
        """
        User.objects.create_user(self.cleaned_data["email"], 
            self.cleaned_data["email"], self.cleaned_data["password"])
        self.authenticate()

class LoginForm(UserForm):
    
    def clean(self):
        """
        Authenticate the email/password.
        """
        if "email" in self.cleaned_data and "password" in self.cleaned_data:
            self.authenticate()
            if self._user is None:
                raise forms.ValidationError(_("Invalid email/password"))
            elif not self._user.is_active:
                raise forms.ValidationError(_("Your account is inactive"))
        return self.cleaned_data
    
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
            error = _("Only one variation can be checked as the default.")
            raise forms.ValidationError(error)

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

