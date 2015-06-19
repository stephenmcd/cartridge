from __future__ import absolute_import, unicode_literals
from future.builtins import bytes, zip, str as _str

import hmac
from locale import setlocale, LC_MONETARY, Error as LocaleError

try:
    from hashlib import sha512 as digest
except ImportError:
    from md5 import new as digest

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext as _

from mezzanine.conf import settings
from mezzanine.utils.importing import import_dotted_path


def make_choices(choices):
    """
    Zips a list with itself for field choices.
    """
    return list(zip(choices, choices))


def clear_session(request, *names):
    """
    Removes values for the given session variables names
    if they exist.
    """
    for name in names:
        try:
            del request.session[name]
        except KeyError:
            pass


def recalculate_cart(request):
    """
    Updates an existing discount code, shipping, and tax when the
    cart is modified.
    """
    from cartridge.shop import checkout
    from cartridge.shop.forms import DiscountForm
    from cartridge.shop.models import Cart

    # Rebind the cart to request since it's been modified.
    if request.session.get('cart') != request.cart.pk:
        request.session['cart'] = request.cart.pk
    request.cart = Cart.objects.from_request(request)

    discount_code = request.session.get("discount_code", "")
    if discount_code:
        # Clear out any previously defined discount code
        # session vars.
        names = ("free_shipping", "discount_code", "discount_total")
        clear_session(request, *names)
        discount_form = DiscountForm(request, {"discount_code": discount_code})
        if discount_form.is_valid():
            discount_form.set_discount()

    handler = lambda s: import_dotted_path(s) if s else lambda *args: None
    billship_handler = handler(settings.SHOP_HANDLER_BILLING_SHIPPING)
    tax_handler = handler(settings.SHOP_HANDLER_TAX)
    try:
        if request.session["order"]["step"] >= checkout.CHECKOUT_STEP_FIRST:
            billship_handler(request, None)
            tax_handler(request, None)
    except (checkout.CheckoutError, ValueError, KeyError):
        pass


def set_shipping(request, shipping_type, shipping_total):
    """
    Stores the shipping type and total in the session.
    """
    request.session["shipping_type"] = _str(shipping_type)
    request.session["shipping_total"] = _str(shipping_total)


def set_tax(request, tax_type, tax_total):
    """
    Stores the tax type and total in the session.
    """
    request.session["tax_type"] = _str(tax_type)
    request.session["tax_total"] = _str(tax_total)


def sign(value):
    """
    Returns the hash of the given value, used for signing order key stored in
    cookie for remembering address fields.
    """
    key = bytes(settings.SECRET_KEY, encoding="utf8")
    value = bytes(value, encoding="utf8")
    return hmac.new(key, value, digest).hexdigest()


def set_locale():
    """
    Sets the locale for currency formatting.
    """
    currency_locale = str(settings.SHOP_CURRENCY_LOCALE)
    try:
        if setlocale(LC_MONETARY, currency_locale) == "C":
            # C locale doesn't contain a suitable value for "frac_digits".
            raise LocaleError
    except LocaleError:
        msg = _("Invalid currency locale specified for SHOP_CURRENCY_LOCALE: "
                "'%s'. You'll need to set the locale for your system, or "
                "configure the SHOP_CURRENCY_LOCALE setting in your settings "
                "module.")
        raise ImproperlyConfigured(msg % currency_locale)
