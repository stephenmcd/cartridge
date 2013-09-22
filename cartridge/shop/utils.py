import hmac
from locale import setlocale, LC_MONETARY
try:
    from hashlib import sha512 as digest
except ImportError:
    from md5 import new as digest

from django.core.exceptions import ImproperlyConfigured
from django.utils.timezone import now
from django.utils.translation import ugettext as _

from mezzanine.conf import settings
from mezzanine.utils.importing import import_dotted_path

class EmptyCart(object):
    """
    A dummy cart object used before any items have been added.
    Used to avoid querying the database for cart and items on each
    request.
    """

    id = None
    pk = None
    has_items = lambda *a, **k: False
    skus = lambda *a, **k: []
    upsell_products = lambda *a, **k: []
    total_quantity = lambda *a, **k: 0
    total_price = lambda *a, **k: 0
    calculate_discount = lambda *a, **k: 0
    __int__ = lambda *a, **k: 0
    __iter__ = lambda *a, **k: iter([])

    def __init__(self, request):
        """
        Store the request so we can add the real cart ID to the
        session if any items get added.
        """
        self._request = request

    def add_item(self, *args, **kwargs):
        """
        Create a real cart object, add the items to it and store
        the cart ID in the session.
        """
        from cartridge.shop.models import Cart
        cart = Cart.objects.create(last_updated=now())
        cart.add_item(*args, **kwargs)
        self._request.session["cart"] = cart.id


def make_choices(choices):
    """
    Zips a list with itself for field choices.
    """
    return zip(choices, choices)


def recalculate_discount(request):
    """
    Updates an existing discount code when the cart is modified.
    """
    from cartridge.shop.forms import DiscountForm
    from cartridge.shop.models import Cart
    # Rebind the cart to request since it's been modified.
    request.cart = Cart.objects.from_request(request)
    discount_code = request.session.get("discount_code", "")
    discount_form = DiscountForm(request, {"discount_code": discount_code})
    if discount_form.is_valid():
        discount_form.set_discount()
    else:
        try:
            del request.session["discount_total"]
        except KeyError:
            pass


def recalculate_billship_tax(request):
    """
    Updates billship and tax information when the cart is modified.
    """
    from cartridge.shop import checkout
    handler = lambda s: import_dotted_path(s) if s else lambda *args: None
    billship_handler = handler(settings.SHOP_HANDLER_BILLING_SHIPPING)
    tax_handler = handler(settings.SHOP_HANDLER_TAX)
    # call billship and tax handlers if
    # past the first step and address is known.
    try:
        if request.session["order"]["step"] >= checkout.CHECKOUT_STEP_FIRST:
            billship_handler(request, None)
            tax_handler(request, None)
    except checkout.CheckoutError:
        pass
    except ValueError:
        pass
    except KeyError:
        pass


def set_shipping(request, shipping_type, shipping_total):
    """
    Stores the shipping type and total in the session.
    """
    request.session["shipping_type"] = shipping_type
    request.session["shipping_total"] = shipping_total


def set_tax(request, tax_type, tax_total):
    """
    Stores the tax type and total in the session.
    """
    request.session["tax_type"] = tax_type
    request.session["tax_total"] = tax_total


def sign(value):
    """
    Returns the hash of the given value, used for signing order key stored in
    cookie for remembering address fields.
    """
    return hmac.new(settings.SECRET_KEY, value, digest).hexdigest()


def set_locale():
    """
    Sets the locale for currency formatting.
    """
    currency_locale = settings.SHOP_CURRENCY_LOCALE
    try:
        if setlocale(LC_MONETARY, currency_locale) == "C":
            # C locale doesn't contain a suitable value for "frac_digits".
            raise
    except:
        msg = _("Invalid currency locale specified for SHOP_CURRENCY_LOCALE: "
                "'%s'. You'll need to set the locale for your system, or "
                "configure the SHOP_CURRENCY_LOCALE setting in your settings "
                "module.")
        raise ImproperlyConfigured(msg % currency_locale)
