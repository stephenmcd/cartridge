from __future__ import unicode_literals
from future.builtins import str

try:
    from urllib.request import Request, urlopen
    from urllib.error import URLError
except ImportError:
    from urllib2 import Request, urlopen, URLError

from django.core.exceptions import ImproperlyConfigured
from django.utils.http import urlencode
from mezzanine.conf import settings

from cartridge.shop.checkout import CheckoutError


AUTH_NET_LIVE = 'https://secure.authorize.net/gateway/transact.dll'
AUTH_NET_TEST = 'https://test.authorize.net/gateway/transact.dll'

try:
    AUTH_NET_LOGIN = settings.AUTH_NET_LOGIN
    AUTH_NET_TRANS_KEY = settings.AUTH_NET_TRANS_KEY
except AttributeError:
    raise ImproperlyConfigured("You need to define AUTH_NET_LOGIN and "
                               "AUTH_NET_TRANS_KEY in your settings module "
                               "to use the authorizenet payment processor.")


def process(request, order_form, order):
    """
    Raise cartridge.shop.checkout.CheckoutError("error message") if
    payment is unsuccessful.
    """

    trans = {}
    amount = order.total
    trans['amount'] = amount
    if settings.DEBUG:
        trans['connection'] = AUTH_NET_TEST
    else:
        trans['connection'] = AUTH_NET_LIVE
    trans['authorize_only'] = False
    trans['configuration'] = {
        'x_login': AUTH_NET_LOGIN,
        'x_tran_key': AUTH_NET_TRANS_KEY,
        'x_version': '3.1',
        'x_relay_response': 'FALSE',
        'x_test_request': 'FALSE',
        'x_delim_data': 'TRUE',
        'x_delim_char': '|',
        # could be set to AUTH_ONLY to only authorize but not capture payment
        'x_type': 'AUTH_CAPTURE',
        'x_method': 'CC',
    }
    data = order_form.cleaned_data
    trans['custBillData'] = {
        'x_first_name': data['billing_detail_first_name'],
        'x_last_name': data['billing_detail_last_name'],
        'x_address': data['billing_detail_street'],
        'x_city': data['billing_detail_city'],
        'x_state': data['billing_detail_state'],
        'x_zip': data['billing_detail_postcode'],
        'x_country': data['billing_detail_country'],
        'x_phone': data['billing_detail_phone'],
        'x_email': data['billing_detail_email'],
    }

    trans['custShipData'] = {
        'x_ship_to_first_name': data['shipping_detail_first_name'],
        'x_ship_to_last_name': data['shipping_detail_last_name'],
        'x_ship_to_address': data['shipping_detail_street'],
        'x_ship_to_city': data['shipping_detail_city'],
        'x_ship_to_state': data['shipping_detail_state'],
        'x_ship_to_zip': data['shipping_detail_postcode'],
        'x_ship_to_country': data['shipping_detail_country'],
    }
    trans['transactionData'] = {
        'x_amount': amount,
        'x_card_num': data['card_number'],
        'x_exp_date': '{month}/{year}'.format(month=data['card_expiry_month'],
                                              year=data['card_expiry_year']),
        'x_card_code': data['card_ccv'],
        'x_invoice_num': str(order.id)
    }

    part1 = urlencode(trans['configuration']) + "&"
    part2 = "&" + urlencode(trans['custBillData'])
    part3 = "&" + urlencode(trans['custShipData'])
    trans['postString'] = (part1 + urlencode(trans['transactionData']) +
                           part2 + part3)

    request_args = {"url": trans['connection'],
                    "data": trans['postString'].encode('utf-8')}
    try:
        all_results = urlopen(Request(**request_args)).read()
    except URLError:
        raise CheckoutError("Could not talk to authorize.net payment gateway")

    parsed_results = all_results.decode('utf-8').split(
        trans['configuration']['x_delim_char'])
    # response and response_reason_codes with their meaning here:
    # http://www.authorize.net/support/merchant/Transaction_Response/
    # Response_Reason_Codes_and_Response_Reason_Text.htm
    # not exactly sure what the reason code is
    response_code = parsed_results[0]
    # reason_code = parsed_results[1]
    # response_reason_code = parsed_results[2]
    # response_text = parsed_results[3]
    # transaction_id = parsed_results[6]
    success = response_code == '1'
    if not success:
        raise CheckoutError("Transaction declined: " + parsed_results[2])
    return parsed_results[6]
