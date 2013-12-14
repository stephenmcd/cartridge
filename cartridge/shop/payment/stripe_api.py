from __future__ import unicode_literals
from future.builtins import int
from future.builtins import str
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext as _
from mezzanine.conf import settings

from cartridge.shop.checkout import CheckoutError

# Requires Stripe Library Module -- install from pypi.
try:
    import stripe
except ImportError:
    raise ImproperlyConfigured("stripe package must be installed")

try:
    stripe.api_key = settings.STRIPE_API_KEY
except AttributeError:
    raise ImproperlyConfigured("You need to define STRIPE_API_KEY "
                               "in your settings module to use the "
                               "stripe payment processor.")


def process(request, order_form, order):
    """
    Payment handler for the stripe API.
    """
    data = {
        "amount": int((order.total * 100).to_integral()),
        "currency": getattr(settings, "STRIPE_CURRENCY", "usd"),
        "card": {
            'number': request.POST["card_number"].strip(),
            'exp_month': request.POST["card_expiry_month"].strip(),
            'exp_year': request.POST["card_expiry_year"][2:].strip(),
            'cvc': request.POST["card_ccv"].strip(),
            'address_line1': request.POST['billing_detail_street'],
            'address_city': request.POST['billing_detail_city'],
            'address_state': request.POST['billing_detail_state'],
            'address_zip': request.POST['billing_detail_postcode'],
            'country': request.POST['billing_detail_country'],
        },
    }
    try:
        response = stripe.Charge.create(**data)
    except stripe.CardError:
        raise CheckoutError(_("Transaction declined"))
    except Exception as e:
        raise CheckoutError(_("A general error occured: ") + str(e))
    return response.id
