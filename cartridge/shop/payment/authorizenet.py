import urllib2

from django.utils.http import urlencode
from mezzanine.conf import settings

from cartridge.shop.checkout import CheckoutError


AUTH_NET_LIVE = 'https://secure.authorize.net/gateway/transact.dll'
AUTH_NET_TEST = 'https://test.authorize.net/gateway/transact.dll'
# replace this with your authroize.net login
AUTH_NET_LOGIN = '29qC5gYDw'
# replace with your transaction key
AUTH_NET_TRANS_KEY = '425974X5vnpfGA3J'


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
    trans['custBillData'] = {
        'x_first_name' : order_form.cleaned_data['billing_detail_first_name'],
        'x_last_name' : order_form.cleaned_data['billing_detail_last_name'],
        'x_address': order_form.cleaned_data['billing_detail_street'],
        'x_city': order_form.cleaned_data['billing_detail_city'],
        'x_state' : order_form.cleaned_data['billing_detail_state'],
        'x_zip' : order_form.cleaned_data['billing_detail_postcode'],
        'x_country': order_form.cleaned_data['billing_detail_country'],
        'x_phone' : order_form.cleaned_data['billing_detail_phone'],
        'x_email' : order_form.cleaned_data['billing_detail_email'],
    }

    trans['custShipData'] = {
        'x_ship_to_first_name' : order_form.cleaned_data['shipping_detail_first_name'],
        'x_ship_to_last_name' : order_form.cleaned_data['shipping_detail_last_name'],
        'x_ship_to_address' : order_form.cleaned_data['shipping_detail_street'],
        'x_ship_to_city' : order_form.cleaned_data['shipping_detail_city'],
        'x_ship_to_state' : order_form.cleaned_data['shipping_detail_state'],
        'x_ship_to_zip' : order_form.cleaned_data['shipping_detail_postcode'],
        'x_ship_to_country' : order_form.cleaned_data['shipping_detail_country'],
    }
    trans['transactionData'] = {
        'x_amount': amount,
        'x_card_num': order_form.cleaned_data['card_number'],
        'x_exp_date': order_form.cleaned_data['card_expiry_month'] + "/" + order_form.cleaned_data['card_expiry_year'],
        'x_card_code': order_form.cleaned_data['card_ccv'],
        'x_invoice_num': str(order.id)
    }
    
    part1 = urlencode(trans['configuration']) + "&"
    part2 = "&" + urlencode(trans['custBillData'])
    part3 = "&" + urlencode(trans['custShipData'])
    trans['postString'] = part1 + urlencode(trans['transactionData']) + part2 + part3
    
    
    conn = urllib2.Request(url=trans['connection'], data=trans['postString'])
    # useful for debugging transactions
    #print trans['postString']
    try:
        f = urllib2.urlopen(conn)
        all_results = f.read()
    except urllib2.URLError:
        raise CheckoutError("Could not talk to authorize.net payment gateway")
    
    parsed_results = all_results.split(trans['configuration']['x_delim_char'])
    # print all_results
    # response and response_reason_codes with their meaning here:
    # http://www.authorize.net/support/merchant/Transaction_Response/Response_Reason_Codes_and_Response_Reason_Text.htm
    # not exactly sure what the reason code is
    response_code = parsed_results[0]
    #reason_code = parsed_results[1]
    #response_reason_code = parsed_results[2]
    #response_text = parsed_results[3]
    #print "response: " + response_code + " response_reason_code: " + response_reason_code + " " + response_text
    #transaction_id = parsed_results[6]
    success = response_code == '1'  
    if not success:
        raise CheckoutError("Transaction denied")
