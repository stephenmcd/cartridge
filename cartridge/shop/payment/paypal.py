import urllib2
import locale

from django.http import QueryDict

from pyrise import *

from django.utils.http import urlencode

from mezzanine.conf import settings

from cartridge.shop.checkout import CheckoutError

PAYPAL_NVP_API_ENDPOINT_SANDBOX = 'https://api-3t.sandbox.paypal.com/nvp'
PAYPAL_NVP_API_ENDPOINT = 'https://api-3t.paypal.com/nvp'
# Replace this with your paypal username.
PAYPAL_USER = settings.PAYPAL_USER
# Replace this with your Paypal password.
PAYPAL_PASSWORD = settings.PAYPAL_PASSWORD
# Replace this with your paypal signature.
PAYPAL_SIGNATURE = settings.PAYPAL_SIGNATURE


def process(request, order_form, order):
    """
    Paypal direct payment processor.
    PayPal is picky. 
    - https://cms.paypal.com/us/cgi-bin/?cmd=_render-content&content_ID=developer/e_howto_api_nvp_r_DoDirectPayment
    Paypal requires the countrycode, and that it be specified in 2 single-
    byte characters. I create a COUNTRY tuple-of-tuples and subclass OrderForm
    in my app, e.g.:
        class OrderForm(OrderForm):
            def __init__(self,*args,**kwrds):
                super(OrderForm, self).__init__(*args, **kwrds)
                self.fields['billing_detail_country'].widget = forms.Select(choices=COUNTRY),
                self.fields['shipping_detail_country'].widget = forms.Select(choices=COUNTRY),
    Raise cartride.shop.checkout.CheckoutError("error message") if
    payment is unsuccessful.

   """
    trans = {}
    amount = order.total
    trans['amount'] = amount
    locale.setlocale(locale.LC_ALL, settings.SHOP_CURRENCY_LOCALE)
    currency = locale.localeconv()
    try:
        ipaddress = request.META['HTTP_X_FORWARDED_FOR']
    except:
        ipaddress = request.META['REMOTE_ADDR']

    if settings.DEBUG:
        trans['connection'] = PAYPAL_NVP_API_ENDPOINT_SANDBOX
    else:
        trans['connection'] = PAYPAL_NVP_API_ENDPOINT

    trans['configuration'] = {
        'USER' : PAYPAL_USER,
        'PWD' : PAYPAL_PASSWORD,
        'SIGNATURE' : PAYPAL_SIGNATURE,
        'VERSION' : '53.0',
        'METHOD': 'DoDirectPayment',
        'PAYMENTACTION': 'Sale',
        'RETURNFMFDETAILS': 0,
        'CURRENCYCODE': currency['int_curr_symbol'][0:3],
        'IPADDRESS': ipaddress,
    }
    data = order_form.cleaned_data
    trans['custBillData'] = {
        'FIRSTNAME': data['billing_detail_first_name'],
        'LASTNAME': data['billing_detail_last_name'],
        'STREET': data['billing_detail_street'],
        'CITY': data['billing_detail_city'],
        'STATE': data['billing_detail_state'],
        'ZIP': data['billing_detail_postcode'],
        'COUNTRYCODE': data['billing_detail_country'],
        'SHIPTOPHONENUM': data['billing_detail_phone'],
        'EMAIL': data['billing_detail_email'],
    }
    trans['custShipData'] = {
        'SHIPTONAME': (data['shipping_detail_first_name'] + ' ' + 
                data['shipping_detail_last_name']),
        'SHIPTOSTREET': data['shipping_detail_street'],
        'SHIPTOCITY': data['shipping_detail_city'],
        'SHIPTOSTATE': data['shipping_detail_state'],
        'SHIPTOZIP': data['shipping_detail_postcode'],
        'SHIPTOCOUNTRY': data['shipping_detail_country'],
    }
    trans['transactionData'] = {
        'CREDITCARDTYPE': data['card_type'].upper(),
        'ACCT': data['card_number'].replace(' ', ''),
        'EXPDATE': (data['card_expiry_month'] + data['card_expiry_year']),
        'CVV2': data['card_ccv'],
        'AMT': trans['amount'],
        'INVNUM': str(order.id)
    }

    part1 = urlencode(trans['configuration']) + "&"
    part2 = "&" + urlencode(trans['custBillData'])
    part3 = "&" + urlencode(trans['custShipData'])
    trans['postString'] = (part1 + urlencode(trans['transactionData']) +
                           part2 + part3)
    conn = urllib2.Request(url=trans['connection'], data=trans['post_string'])
    try:
        f = urllib2.urlopen(conn)
        all_results = f.read()
    except urllib2.URLError:
        raise CheckoutError("Could not talk to PayPal payment gateway")

    parsed_results = QueryDict(all_results)
    state = parsed_results['ACK']
    if not state in ["Success", "SuccessWithWarning"]:
        raise CheckoutError(parsed_results['L_LONGMESSAGE0'])
    return parsed_results['TRANSACTIONID']
