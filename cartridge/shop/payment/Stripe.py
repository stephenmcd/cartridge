
from urllib import urlencode, urlopen

from django.http import QueryDict
from django.utils.translation import ugettext as _

from mezzanine.conf import settings

from cartridge.shop.checkout import CheckoutError

#Requires Stripe Library Module -- install from pypi

import stripe
stripe.api_key = settings.STRIPE_API_KEY


def process(request, order_form, order):
    """
    Payment handler for the eGate payment gateway.
    """

    # Post the data and retrieve the response code. If any exception is
    # raised, or the error code doesn't indicate success (0) then raise
    # a CheckoutError.
    try:
        # Set up the data to post to the gateway.
        response = stripe.Charge.create(
            amount=unicode(order.total.to_integral() * 100), # amount in cents, again
            currency="usd",
            card={
                'number':        request.POST["card_number"].strip(),
                'exp_month':     request.POST["card_expiry_month"].strip(),
                'exp_year':      request.POST["card_expiry_year"][2:].strip(),
                'address_line1': request.POST['billing_detail_street'],
                'address_city':  request.POST['billing_detail_city'], 
                'address_state': request.POST['billing_detail_state'],
                'address_zip':   request.POST['billing_detail_postcode'],
                'country':       request.POST['billing_detail_country']
             }
        )
        return response.id
    except stripe.CardError:
        raise CheckoutError(_("Transaction declined: ") + _("There was a card error"))
    except Exception, e:
        raise CheckoutError(_("A general error occured: ") + e)
