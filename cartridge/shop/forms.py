
from copy import copy
from datetime import datetime
from itertools import dropwhile, takewhile
from locale import localeconv
from re import match

from django import forms
from django.forms.models import BaseInlineFormSet, ModelFormMetaclass
from django.forms.models import inlineformset_factory
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from mezzanine.conf import settings
from mezzanine.core.templatetags.mezzanine_tags import thumbnail

from cartridge.shop import checkout
from cartridge.shop.models import Product, ProductOption, ProductVariation
from cartridge.shop.models import Cart, CartItem, Order, DiscountCode
from cartridge.shop.utils import make_choices, set_locale, set_shipping


ADD_PRODUCT_ERRORS = {
    "invalid_options": _("The selected options are currently unavailable."),
    "no_stock": _("The selected options are currently not in stock."),
    "no_stock_quantity": _("The selected quantity is currently unavailable."),
}


class AddProductForm(forms.Form):
    """
    A form for adding the given product to the cart or the
    wishlist.
    """

    quantity = forms.IntegerField(min_value=1)
    sku = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *xargs, **kwargs):
        """
        Handles adding a variation to the cart or wishlist.

        When adding from the product page, the product is provided
        from the view and a set of choice fields for all the
        product options for this product's variations are added to
        the form. When the form is validated, the selected options
        are used to determine the chosen variation.

        A ``to_cart`` boolean keyword arg is also given specifying
        whether the product is being added to a cart or wishlist.
        If a product is being added to the cart, then its stock
        level is also validated.

        When adding to the cart from the wishlist page, a sku is
        given for the variation, so the creation of choice fields
        is skipped.
        """
        self._product = kwargs.pop("product", None)
        self._to_cart = kwargs.pop("to_cart")
        super(AddProductForm, self).__init__(*xargs, **kwargs)
        # Adding from the wishlist with a sku, bail out.
        if xargs[0] is not None and xargs[0].get("sku", None):
            return
        # Adding from the product page, remove the sku field
        # and build the choice fields for the variations.
        del self.fields["sku"]
        option_names, option_labels = zip(*[(f.name, f.verbose_name)
            for f in ProductVariation.option_fields()])
        option_values = zip(*self._product.variations.filter(
            unit_price__isnull=False).values_list(*option_names))
        if option_values:
            for i, name in enumerate(option_names):
                values = filter(None, set(option_values[i]))
                if values:
                    field = forms.ChoiceField(label=option_labels[i],
                                              choices=make_choices(values))
                    self.fields[name] = field

    def clean(self):
        """
        Determine the chosen variation, validate it and assign it as
        an attribute to be used in views.
        """
        if not self.is_valid():
            return
        # Posted data will either be a sku, or product options for
        # a variation.
        data = self.cleaned_data.copy()
        quantity = data.pop("quantity")
        # Ensure the product has a price if adding to cart.
        if self._to_cart:
            data["unit_price__isnull"] = False
        error = None
        if self._product is not None:
            # Chosen options will be passed to the product's
            # variations.
            qs = self._product.variations
        else:
            # A product hasn't been given since we have a direct sku.
            qs = ProductVariation.objects
        try:
            variation = qs.get(**data)
        except ProductVariation.DoesNotExist:
            error = "invalid_options"
        else:
            # Validate stock if adding to cart.
            if self._to_cart:
                if not variation.has_stock():
                    error = "no_stock"
                elif not variation.has_stock(quantity):
                    error = "no_stock_quantity"
        if error is not None:
            raise forms.ValidationError(ADD_PRODUCT_ERRORS[error])
        self.variation = variation
        return self.cleaned_data


class CartItemForm(forms.ModelForm):
    """
    Model form for each item in the cart - used for the
    ``CartItemFormSet`` below which controls editing the entire cart.
    """

    class Meta:
        model = CartItem
        fields = ("quantity",)

    def clean_quantity(self):
        """
        Validate that the given quantity is available.
        """
        variation = ProductVariation.objects.get(sku=self.instance.sku)
        quantity = self.cleaned_data["quantity"]
        if not variation.has_stock(quantity - self.instance.quantity):
            error = ADD_PRODUCT_ERRORS["no_stock_quantity"]
            raise forms.ValidationError(error)
        return quantity

CartItemFormSet = inlineformset_factory(Cart, CartItem, form=CartItemForm,
                                        can_delete=True, extra=0)


class FormsetForm(object):
    """
    Form mixin that provides template methods for iterating through
    sets of fields by prefix, single fields and finally remaning
    fields that haven't been iterated with each fieldset made up from
    a copy of the original form giving access to as_* methods.
    """

    def _fieldset(self, field_names):
        """
        Return a subset of fields by making a copy of the form
        containing only the given field names.
        """
        fieldset = copy(self)
        if not hasattr(self, "_fields_done"):
            self._fields_done = []
        fieldset.non_field_errors = lambda *args: None
        names = filter(lambda f: f not in self._fields_done, field_names)
        fieldset.fields = SortedDict([(f, self.fields[f]) for f in names])
        self._fields_done.extend(names)
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
        Dynamic fieldset caller - matches requested attribute name
        against pattern for creating the list of field names to use
        for the fieldset.
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


class DiscountForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = ("discount_code",)

    def __init__(self, request, data=None, initial=None):
        """
        Store the request so that it can be used to retrieve the cart
        which is required to validate the discount code when entered.
        """
        super(DiscountForm, self).__init__(data=data, initial=initial)
        self._request = request

    def clean_discount_code(self):
        """
        Validate the discount code if given, and attach the discount
        instance to the form.
        """
        code = self.cleaned_data.get("discount_code", "")
        cart = self._request.cart
        if code:
            try:
                discount = DiscountCode.objects.get_valid(code=code, cart=cart)
                self._discount = discount
            except DiscountCode.DoesNotExist:
                error = _("The discount code entered is invalid.")
                raise forms.ValidationError(error)
        return code

    def set_discount(self):
        """
        Assigns the session variables for the discount.
        """
        discount = getattr(self, "_discount", None)
        if discount is not None:
            total = self._request.cart.calculate_discount(discount)
            if discount.free_shipping:
                set_shipping(self._request, _("Free shipping"), 0)
            self._request.session["free_shipping"] = discount.free_shipping
            self._request.session["discount_code"] = discount.code
            self._request.session["discount_total"] = total


class OrderForm(FormsetForm, DiscountForm):
    """
    Main Form for the checkout process - ModelForm for the Order Model
    with extra fields for credit card. Used across each step of the
    checkout process with fields being hidden where applicable.
    """

    step = forms.IntegerField(widget=forms.HiddenInput())
    same_billing_shipping = forms.BooleanField(required=False, initial=True,
        label=_("My delivery details are the same as my billing details"))
    remember = forms.BooleanField(required=False, initial=True,
        label=_("Remember my address for next time"))
    card_name = forms.CharField(label=_("Cardholder name"))
    card_type = forms.ChoiceField(widget=forms.RadioSelect,
        choices=make_choices(settings.SHOP_CARD_TYPES))
    card_number = forms.CharField()
    card_expiry_month = forms.ChoiceField(
        choices=make_choices(["%02d" % i for i in range(1, 13)]))
    card_expiry_year = forms.ChoiceField()
    card_ccv = forms.CharField(label="CCV", help_text=_("A security code, "
        "usually the last 3 digits found on the back of your card."))

    class Meta:
        model = Order
        fields = ([f.name for f in Order._meta.fields if
                   f.name.startswith("billing_detail") or
                   f.name.startswith("shipping_detail")] +
                   ["additional_instructions", "discount_code"])

    def __init__(self, request, step, data=None, initial=None, errors=None):
        """
        Handle setting shipping field values to the same as billing
        field values in case JavaScript is disabled, hiding fields for
        the current step.
        """

        # Copy billing fields to shipping fields if "same" checked.
        first = step == checkout.CHECKOUT_STEP_FIRST
        last = step == checkout.CHECKOUT_STEP_LAST
        if (first and data is not None and "same_billing_shipping" in data):
            data = copy(data)
            # Prevent second copy occuring for forcing step below when
            # moving backwards in steps.
            data["step"] = step
            for field in data:
                billing = field.replace("shipping_detail", "billing_detail")
                if "shipping_detail" in field and billing in data:
                    data[field] = data[billing]

        if initial is not None:
            initial["step"] = step
        # Force the specified step in the posted data - this is
        # required to allow moving backwards in steps.
        if data is not None and int(data["step"]) != step:
            data = copy(data)
            data["step"] = step

        super(OrderForm, self).__init__(request, data=data, initial=initial)
        self._checkout_errors = errors
        settings.use_editable()
        # Hide Discount Code field if no codes are active.
        if (DiscountCode.objects.active().count() == 0 or
            not settings.SHOP_DISCOUNT_FIELD_IN_CHECKOUT):
            self.fields["discount_code"].widget = forms.HiddenInput()

        # Determine which sets of fields to hide for each checkout step.
        hidden = None
        if settings.SHOP_CHECKOUT_STEPS_SPLIT:
            if first:
                # Hide the cc fields for billing/shipping if steps are split.
                hidden = lambda f: f.startswith("card_")
            elif step == checkout.CHECKOUT_STEP_PAYMENT:
                # Hide the non-cc fields for payment if steps are split.
                hidden = lambda f: not f.startswith("card_")
        elif not settings.SHOP_PAYMENT_STEP_ENABLED:
            # Hide all the cc fields if payment step is not enabled.
            hidden = lambda f: f.startswith("card_")
        if settings.SHOP_CHECKOUT_STEPS_CONFIRMATION and last:
            # Hide all fields for the confirmation step.
            hidden = lambda f: True
        if hidden is not None:
            for field in self.fields:
                if hidden(field):
                    self.fields[field].widget = forms.HiddenInput()
                    self.fields[field].required = False

        # Set the choices for the cc expiry year relative to the current year.
        year = datetime.now().year
        choices = make_choices(range(year, year + 21))
        self.fields["card_expiry_year"].choices = choices

    def clean_card_expiry_year(self):
        """
        Ensure the card expiry doesn't occur in the past.
        """
        try:
            month = int(self.cleaned_data["card_expiry_month"])
            year = int(self.cleaned_data["card_expiry_year"])
        except ValueError:
            # Haven't reached payment step yet.
            return
        now = datetime.now()
        if year == now.year and month < now.month:
            raise forms.ValidationError(_("A valid expiry date is required."))
        return str(year)

    def clean(self):
        """
        Raise ``ValidationError`` if any errors have been assigned
        externally, via one of the custom checkout step handlers.
        """
        if self._checkout_errors:
            raise forms.ValidationError(self._checkout_errors)
        return self.cleaned_data


#######################
#    ADMIN WIDGETS    #
#######################

class ImageWidget(forms.FileInput):
    """
    Render a visible thumbnail for image fields.
    """
    def render(self, name, value, attrs):
        rendered = super(ImageWidget, self).render(name, value, attrs)
        if value:
            orig_url = "%s%s" % (settings.MEDIA_URL, value)
            thumb_url = "%s%s" % (settings.MEDIA_URL, thumbnail(value, 48, 48))
            rendered = ("<a target='_blank' href='%s'>"
                        "<img style='margin-right:6px;' src='%s'>"
                        "</a>%s" % (orig_url, thumb_url, rendered))
        return mark_safe(rendered)


class MoneyWidget(forms.TextInput):
    """
    Render missing decimal places for money fields.
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


class ProductAdminFormMetaclass(ModelFormMetaclass):
    """
    Metaclass for the Product Admin form that dynamically assigns each
    of the types of product options as sets of checkboxes for selecting
    which options to use when creating new product variations.
    """
    def __new__(cls, name, bases, attrs):
        for option in settings.SHOP_OPTION_TYPE_CHOICES:
            field = forms.MultipleChoiceField(label=option[1],
                required=False, widget=forms.CheckboxSelectMultiple)
            attrs["option%s" % option[0]] = field
        args = (cls, name, bases, attrs)
        return super(ProductAdminFormMetaclass, cls).__new__(*args)


class ProductAdminForm(forms.ModelForm):
    """
    Admin form for the Product model.
    """
    __metaclass__ = ProductAdminFormMetaclass

    class Meta:
        model = Product

    def __init__(self, *args, **kwargs):
        """
        Set the choices for each of the fields for product options.
        Also remove the current instance from choices for related and
        upsell products.
        """
        super(ProductAdminForm, self).__init__(*args, **kwargs)
        for field, options in ProductOption.objects.as_fields().items():
            self.fields[field].choices = make_choices(options)
        instance = kwargs.get("instance")
        if instance:
            queryset = Product.objects.exclude(id=instance.id)
            self.fields["related_products"].queryset = queryset
            self.fields["upsell_products"].queryset = queryset


class ProductVariationAdminForm(forms.ModelForm):
    """
    Ensure the list of images for the variation are specific to the
    variation's product.
    """
    def __init__(self, *args, **kwargs):
        super(ProductVariationAdminForm, self).__init__(*args, **kwargs)
        if "instance" in kwargs:
            product = kwargs["instance"].product
            qs = self.fields["image"].queryset.filter(product=product)
            self.fields["image"].queryset = qs


class ProductVariationAdminFormset(BaseInlineFormSet):
    """
    Ensure no more than one variation is checked as default.
    """
    def clean(self):
        if len([f for f in self.forms if hasattr(f, "cleaned_data") and
            f.cleaned_data["default"]]) > 1:
            error = _("Only one variation can be checked as the default.")
            raise forms.ValidationError(error)


class DiscountAdminForm(forms.ModelForm):
    """
    Ensure only one discount field is given a value and if not, assign
    the error to the first discount field so that it displays correctly.
    """
    def clean(self):
        fields = [f for f in self.fields if f.startswith("discount_")]
        reductions = filter(None, [self.cleaned_data.get(f) for f in fields])
        if len(reductions) > 1:
            error = _("Please enter a value for only one type of reduction.")
            self._errors[fields[0]] = self.error_class([error])
        return self.cleaned_data
