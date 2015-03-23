from __future__ import unicode_literals

try:
    from urllib.request import Request, urlopen
    from urllib.error import URLError
except ImportError:
    from urllib2 import Request, urlopen, URLError

import locale

from django.core.exceptions import ImproperlyConfigured
from django.http import QueryDict
from django.utils.http import urlencode
from mezzanine.conf import settings

from cartridge.shop.checkout import CheckoutError


PAYPAL_NVP_API_ENDPOINT_SANDBOX = 'https://api-3t.sandbox.paypal.com/nvp'
PAYPAL_NVP_API_ENDPOINT = 'https://api-3t.paypal.com/nvp'

try:
    PAYPAL_USER = settings.PAYPAL_USER
    PAYPAL_PASSWORD = settings.PAYPAL_PASSWORD
    PAYPAL_SIGNATURE = settings.PAYPAL_SIGNATURE
except AttributeError:
    raise ImproperlyConfigured("You need to define PAYPAL_USER, "
                               "PAYPAL_PASSWORD and PAYPAL_SIGNATURE "
                               "in your settings module to use the "
                               "paypal payment processor.")


def process(request, order_form, order):
    """
    Paypal direct payment processor.
    PayPal is picky.
    - https://cms.paypal.com/us/cgi-bin/?cmd=_render-content
      &content_ID=developer/e_howto_api_nvp_r_DoDirectPayment
    - https://cms.paypal.com/us/cgi-bin/?cmd=_render-content
      &content_ID=developer/e_howto_api_nvp_errorcodes
    Paypal requires the countrycode, and that it be specified in 2 single-
    byte characters. Import the COUNTRIES tuple-of-tuples, included below,
    and subclass OrderForm in my app, e.g.:

    from cartridge.shop.payment.paypal import COUNTRIES

    class MyOrderForm(OrderForm):
        def __init__(self, *args, **kwargs):
            super(OrderForm, self).__init__(*args, **kwrds)
            billing_country = forms.Select(choices=COUNTRIES)
            shipping_country = forms.Select(choices=COUNTRIES)
            self.fields['billing_detail_country'].widget = billing_country
            self.fields['shipping_detail_country'].widget = shipping_country

    Raise cartride.shop.checkout.CheckoutError("error message") if
    payment is unsuccessful.

    """
    trans = {}
    amount = order.total
    trans['amount'] = amount
    locale.setlocale(locale.LC_ALL, str(settings.SHOP_CURRENCY_LOCALE))
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
        'USER': PAYPAL_USER,
        'PWD': PAYPAL_PASSWORD,
        'SIGNATURE': PAYPAL_SIGNATURE,
        'VERSION': '53.0',
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
        # optional below
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
        'EXPDATE': str(data['card_expiry_month'] + data['card_expiry_year']),
        'CVV2': data['card_ccv'],
        'AMT': trans['amount'],
        'INVNUM': str(order.id)
    }

    part1 = urlencode(trans['configuration']) + "&"
    part2 = "&" + urlencode(trans['custBillData'])
    part3 = "&" + urlencode(trans['custShipData'])
    trans['postString'] = (part1 + urlencode(trans['transactionData']) +
                           part2 + part3)
    trans['postString'] = trans['postString'].encode('utf-8')
    request_args = {"url": trans['connection'], "data": trans['postString']}
    # useful for debugging transactions
    # print trans['postString']
    try:
        all_results = urlopen(Request(**request_args)).read()
    except URLError:
        raise CheckoutError("Could not talk to PayPal payment gateway")
    parsed_results = QueryDict(all_results)
    state = parsed_results['ACK']
    if state not in ["Success", "SuccessWithWarning"]:
        raise CheckoutError(parsed_results['L_LONGMESSAGE0'])
    return parsed_results['TRANSACTIONID']


COUNTRIES = (
    ("US", "UNITED STATES"),
    ("CA", "CANADA"),
    ("GB", "UNITED KINGDOM"),
    ("AF", "AFGHANISTAN"),
    ("AX", "ALAND ISLANDS"),
    ("AL", "ALBANIA"),
    ("DZ", "ALGERIA"),
    ("AS", "AMERICAN SAMOA"),
    ("AD", "ANDORRA"),
    ("AO", "ANGOLA"),
    ("AI", "ANGUILLA"),
    ("AQ", "ANTARCTICA"),
    ("AG", "ANTIGUA AND BARBUDA"),
    ("AR", "ARGENTINA"),
    ("AM", "ARMENIA"),
    ("AW", "ARUBA"),
    ("AU", "AUSTRALIA"),
    ("AT", "AUSTRIA"),
    ("AZ", "AZERBAIJAN"),
    ("BS", "BAHAMAS"),
    ("BH", "BAHRAIN"),
    ("BD", "BANGLADESH"),
    ("BB", "BARBADOS"),
    ("BY", "BELARUS"),
    ("BE", "BELGIUM"),
    ("BZ", "BELIZE"),
    ("BJ", "BENIN"),
    ("BM", "BERMUDA"),
    ("BT", "BHUTAN"),
    ("BO", "BOLIVIA, PLURINATIONAL STATE OF"),
    ("BA", "BOSNIA AND HERZEGOVINA"),
    ("BW", "BOTSWANA"),
    ("BV", "BOUVET ISLAND"),
    ("BR", "BRAZIL"),
    ("IO", "BRITISH INDIAN OCEAN TERRITORY"),
    ("BN", "BRUNEI DARUSSALAM"),
    ("BG", "BULGARIA"),
    ("BF", "BURKINA FASO"),
    ("BI", "BURUNDI"),
    ("KH", "CAMBODIA"),
    ("CM", "CAMEROON"),
    ("CV", "CAPE VERDE"),
    ("KY", "CAYMAN ISLANDS"),
    ("CF", "CENTRAL AFRICAN REPUBLIC"),
    ("TD", "CHAD"),
    ("CL", "CHILE"),
    ("CN", "CHINA"),
    ("CX", "CHRISTMAS ISLAND"),
    ("CC", "COCOS (KEELING) ISLANDS"),
    ("CO", "COLOMBIA"),
    ("KM", "COMOROS"),
    ("CG", "CONGO"),
    ("CD", "CONGO, THE DEMOCRATIC REPUBLIC OF THE"),
    ("CK", "COOK ISLANDS"),
    ("CR", "COSTA RICA"),
    ("CI", "COTE D'IVOIRE"),
    ("HR", "CROATIA"),
    ("CU", "CUBA"),
    ("CY", "CYPRUS"),
    ("CZ", "CZECH REPUBLIC"),
    ("DK", "DENMARK"),
    ("DJ", "DJIBOUTI"),
    ("DM", "DOMINICA"),
    ("DO", "DOMINICAN REPUBLIC"),
    ("EC", "ECUADOR"),
    ("EG", "EGYPT"),
    ("SV", "EL SALVADOR"),
    ("GQ", "EQUATORIAL GUINEA"),
    ("ER", "ERITREA"),
    ("EE", "ESTONIA"),
    ("ET", "ETHIOPIA"),
    ("FK", "FALKLAND ISLANDS (MALVINAS)"),
    ("FO", "FAROE ISLANDS"),
    ("FJ", "FIJI"),
    ("FI", "FINLAND"),
    ("FR", "FRANCE"),
    ("GF", "FRENCH GUIANA"),
    ("PF", "FRENCH POLYNESIA"),
    ("TF", "FRENCH SOUTHERN TERRITORIES"),
    ("GA", "GABON"),
    ("GM", "GAMBIA"),
    ("GE", "GEORGIA"),
    ("DE", "GERMANY"),
    ("GH", "GHANA"),
    ("GI", "GIBRALTAR"),
    ("GR", "GREECE"),
    ("GL", "GREENLAND"),
    ("GD", "GRENADA"),
    ("GP", "GUADELOUPE"),
    ("GU", "GUAM"),
    ("GT", "GUATEMALA"),
    ("GG", "GUERNSEY"),
    ("GN", "GUINEA"),
    ("GW", "GUINEA-BISSAU"),
    ("GY", "GUYANA"),
    ("HT", "HAITI"),
    ("HM", "HEARD ISLAND AND MCDONALD ISLANDS"),
    ("VA", "HOLY SEE (VATICAN CITY STATE)"),
    ("HN", "HONDURAS"),
    ("HK", "HONG KONG"),
    ("HU", "HUNGARY"),
    ("IS", "ICELAND"),
    ("IN", "INDIA"),
    ("ID", "INDONESIA"),
    ("IR", "IRAN, ISLAMIC REPUBLIC OF"),
    ("IQ", "IRAQ"),
    ("IE", "IRELAND"),
    ("IM", "ISLE OF MAN"),
    ("IL", "ISRAEL"),
    ("IT", "ITALY"),
    ("JM", "JAMAICA"),
    ("JP", "JAPAN"),
    ("JE", "JERSEY"),
    ("JO", "JORDAN"),
    ("KZ", "KAZAKHSTAN"),
    ("KE", "KENYA"),
    ("KI", "KIRIBATI"),
    ("KP", "KOREA, DEMOCRATIC PEOPLE'S REPUBLIC OF"),
    ("KR", "KOREA, REPUBLIC OF"),
    ("KW", "KUWAIT"),
    ("KG", "KYRGYZSTAN"),
    ("LA", "LAO PEOPLE'S DEMOCRATIC REPUBLIC"),
    ("LV", "LATVIA"),
    ("LB", "LEBANON"),
    ("LS", "LESOTHO"),
    ("LR", "LIBERIA"),
    ("LY", "LIBYAN ARAB JAMAHIRIYA"),
    ("LI", "LIECHTENSTEIN"),
    ("LT", "LITHUANIA"),
    ("LU", "LUXEMBOURG"),
    ("MO", "MACAO"),
    ("MK", "MACEDONIA, THE FORMER YUGOSLAV REPUBLIC OF"),
    ("MG", "MADAGASCAR"),
    ("MW", "MALAWI"),
    ("MY", "MALAYSIA"),
    ("MV", "MALDIVES"),
    ("ML", "MALI"),
    ("MT", "MALTA"),
    ("MH", "MARSHALL ISLANDS"),
    ("MQ", "MARTINIQUE"),
    ("MR", "MAURITANIA"),
    ("MU", "MAURITIUS"),
    ("YT", "MAYOTTE"),
    ("MX", "MEXICO"),
    ("FM", "MICRONESIA, FEDERATED STATES OF"),
    ("MD", "MOLDOVA, REPUBLIC OF"),
    ("MC", "MONACO"),
    ("MN", "MONGOLIA"),
    ("ME", "MONTENEGRO"),
    ("MS", "MONTSERRAT"),
    ("MA", "MOROCCO"),
    ("MZ", "MOZAMBIQUE"),
    ("MM", "MYANMAR"),
    ("NA", "NAMIBIA"),
    ("NR", "NAURU"),
    ("NP", "NEPAL"),
    ("NL", "NETHERLANDS"),
    ("AN", "NETHERLANDS ANTILLES"),
    ("NC", "NEW CALEDONIA"),
    ("NZ", "NEW ZEALAND"),
    ("NI", "NICARAGUA"),
    ("NE", "NIGER"),
    ("NG", "NIGERIA"),
    ("NU", "NIUE"),
    ("NF", "NORFOLK ISLAND"),
    ("MP", "NORTHERN MARIANA ISLANDS"),
    ("NO", "NORWAY"),
    ("OM", "OMAN"),
    ("PK", "PAKISTAN"),
    ("PW", "PALAU"),
    ("PS", "PALESTINIAN TERRITORY, OCCUPIED"),
    ("PA", "PANAMA"),
    ("PG", "PAPUA NEW GUINEA"),
    ("PY", "PARAGUAY"),
    ("PE", "PERU"),
    ("PH", "PHILIPPINES"),
    ("PN", "PITCAIRN"),
    ("PL", "POLAND"),
    ("PT", "PORTUGAL"),
    ("PR", "PUERTO RICO"),
    ("QA", "QATAR"),
    ("RE", "REUNION"),
    ("RO", "ROMANIA"),
    ("RU", "RUSSIAN FEDERATION"),
    ("RW", "RWANDA"),
    ("BL", "SAINT BARTHELEMY"),
    ("SH", "SAINT HELENA, ASCENSION AND TRISTAN DA CUNHA"),
    ("KN", "SAINT KITTS AND NEVIS"),
    ("LC", "SAINT LUCIA"),
    ("MF", "SAINT MARTIN"),
    ("PM", "SAINT PIERRE AND MIQUELON"),
    ("VC", "SAINT VINCENT AND THE GRENADINES"),
    ("WS", "SAMOA"),
    ("SM", "SAN MARINO"),
    ("ST", "SAO TOME AND PRINCIPE"),
    ("SA", "SAUDI ARABIA"),
    ("SN", "SENEGAL"),
    ("RS", "SERBIA"),
    ("SC", "SEYCHELLES"),
    ("SL", "SIERRA LEONE"),
    ("SG", "SINGAPORE"),
    ("SK", "SLOVAKIA"),
    ("SI", "SLOVENIA"),
    ("SB", "SOLOMON ISLANDS"),
    ("SO", "SOMALIA"),
    ("ZA", "SOUTH AFRICA"),
    ("GS", "SOUTH GEORGIA AND THE SOUTH SANDWICH ISLANDS"),
    ("ES", "SPAIN"),
    ("LK", "SRI LANKA"),
    ("SD", "SUDAN"),
    ("SR", "SURINAME"),
    ("SJ", "SVALBARD AND JAN MAYEN"),
    ("SZ", "SWAZILAND"),
    ("SE", "SWEDEN"),
    ("CH", "SWITZERLAND"),
    ("SY", "SYRIAN ARAB REPUBLIC"),
    ("TW", "TAIWAN, PROVINCE OF CHINA"),
    ("TJ", "TAJIKISTAN"),
    ("TZ", "TANZANIA, UNITED REPUBLIC OF"),
    ("TH", "THAILAND"),
    ("TL", "TIMOR-LESTE"),
    ("TG", "TOGO"),
    ("TK", "TOKELAU"),
    ("TO", "TONGA"),
    ("TT", "TRINIDAD AND TOBAGO"),
    ("TN", "TUNISIA"),
    ("TR", "TURKEY"),
    ("TM", "TURKMENISTAN"),
    ("TC", "TURKS AND CAICOS ISLANDS"),
    ("TV", "TUVALU"),
    ("UG", "UGANDA"),
    ("UA", "UKRAINE"),
    ("AE", "UNITED ARAB EMIRATES"),
    ("UM", "UNITED STATES MINOR OUTLYING ISLANDS"),
    ("UY", "URUGUAY"),
    ("UZ", "UZBEKISTAN"),
    ("VU", "VANUATU"),
    ("VE", "VENEZUELA, BOLIVARIAN REPUBLIC OF"),
    ("VN", "VIET NAM"),
    ("VG", "VIRGIN ISLANDS, BRITISH"),
    ("VI", "VIRGIN ISLANDS, U.S."),
    ("WF", "WALLIS AND FUTUNA"),
    ("EH", "WESTERN SAHARA"),
    ("YE", "YEMEN"),
    ("ZM", "ZAMBIA"),
    ("ZW ", "ZIMBABWE")
)
