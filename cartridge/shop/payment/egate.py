
from urllib import urlencode, urlopen

from django.http import QueryDict
from django.utils.translation import ugettext as _

from mezzanine.conf import settings

from cartridge.shop.checkout import CheckoutError


GATEWAY_COMMAND = getattr(settings, "EGATE_GATEWAY_COMMAND", "pay")
GATEWAY_VERSION = getattr(settings, "EGATE_GATEWAY_VERSION", "1")
GATEWAY_URL = getattr(settings, "EGATE_GATEWAY_URL",
                      "https://migs.mastercard.com.au/vpcdps")


def process(request, order_form, order):
    """
    Payment handler for the eGate payment gateway.
    """

    # Set up the data to post to the gateway.
    post_data = {
        "vpc_Version": GATEWAY_VERSION,
        "vpc_Command": GATEWAY_COMMAND,
        "vpc_AccessCode": settings.EGATE_ACCESS_CODE,
        "vpc_Merchant": settings.EGATE_MERCHANT_ID,
        "vpc_Amount": unicode((order.total * 100).to_integral()),
        "vpc_CardNum": request.POST["card_number"].strip(),
        "vpc_CardExp": (request.POST["card_expiry_year"][2:].strip() +
                        request.POST["card_expiry_month"].strip()),
        "vpc_CardSecurityCode": request.POST["card_ccv"].strip(),
        "vpc_OrderInfo": u"Order: %s " % order.id,
        "vpc_MerchTxnRef": u"Order: %s " % order.id,
    }

    # Post the data and retrieve the response code. If any exception is
    # raised, or the error code doesn't indicate success (0) then raise
    # a CheckoutError.
    try:
        response = QueryDict(urlopen(GATEWAY_URL, urlencode(post_data)).read())
    except Exception, e:
        raise CheckoutError(_("A general error occured: ") + e)
    else:
        if response["vpc_TxnResponseCode"] != "0":
            raise CheckoutError(_("Transaction declined: ") +
                                response["vpc_Message"])
        else:
            return response["vpc_TransactionNo"]
