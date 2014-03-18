import urllib
import urllib2
import random
import string

from django import forms
from django.http import Http404
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ImproperlyConfigured

from mezzanine.conf import settings
from mezzanine.utils.importing import import_dotted_path
from mezzanine.utils.views import render

from cartridge.shop import checkout
from cartridge.shop.models import Order
from cartridge.shop.forms import OrderForm

handler = lambda s: import_dotted_path(s) if s else lambda *args: None
order_handler = handler(settings.SHOP_HANDLER_ORDER)
"""
Special view to fetch the secure token and set up a Paypal advanced
iFrame.  Paypal Payments Advanced
https://developer.paypal.com/docs/classic/products/paypal-payments-advanced/
allows the form where the customer enters their credit card information to
actually be hosted on paypal's website transparantly, meaning that your servers
never actually process the credit card information at all.  You tell Paypal
how much the order is and they give you a secure token.  Then you use that
token to set up an iframe that will allow the customer to pay, and associate
the payment with your paypal account.  Finally, paypal responds with a POST
to the iframe with the status of the order.  We translate that POST, finish
processing the order, and redirect the customer to the order complete page.
"""


def payment_step_view(request, form):
    """
    This sub-view takes the validated checkout form, sends the necessary
    data to paypal, and returns the argument necessary for the Paypal
    iframe.
    """
    template = "shop/paypal_advanced.html"
    try:
        PAYPAL_USER = settings.PAYPAL_USER
        PAYPAL_PASSWORD = settings.PAYPAL_PASSWORD
        PAYPAL_VENDOR = settings.PAYPAL_VENDOR
    except AttributeError:
        raise ImproperlyConfigured("You need to define PAYPAL_USER, "
                                   "PAYPAL_PASSWORD and PAYPAL_VENDOR "
                                   "in your settings module to use the "
                                   "paypal advanced payment processor.")

    if settings.DEBUG:
        pilot_url = "https://pilot-payflowpro.paypal.com"
        iframe_mode = "TEST"
    else:
        pilot_url = "https://payflowpro.paypal.com"
        iframe_mode = "LIVE"
    iframe_url = "https://payflowlink.paypal.com"

    try:
        order = Order.objects.get(id=request.session["order"]["id"])
        order.delete()
    except:
        pass
    order = form.save(commit=False)
    order.setup(request)

    query_args = [
        ("PARTNER", "PayPal"),
        ("VENDOR", PAYPAL_VENDOR),
        ("USER", PAYPAL_USER),
        ("PWD", PAYPAL_PASSWORD),
        ("TRXTYPE", "S"),
        ("AMT", str(order.total)),
        ("CREATESECURETOKEN", "Y"),
        ("SECURETOKENID",
         ''.join(random.choice(string.ascii_uppercase + string.digits)
                 for _ in range(32)))
    ]

    response = send_html(query_args, pilot_url)

    results = {}
    for pair in response.split("&"):
        results[pair.split("=")[0]] = pair.split("=")[1]
    if results["RESULT"] == "0":
        secure_token_id = results["SECURETOKENID"]
        secure_token = results["SECURETOKEN"]
        order.save()
        request.session["order"]["id"] = order.id
        request.session.modified = True

    else:
        order.delete()
        raise checkout.CheckoutError

    paypal_command = (
        '<iframe seamless '
        'src="%s?MODE=%s&'
        'SECURETOKENID=%s&SECURETOKEN=%s" '
        'name="paypal_iframe" scrolling="no" width="570px" '
        'height="540px"></iframe>'
        % (iframe_url, iframe_mode, secure_token_id, secure_token)
    )

    # Hide all the fields since paypal will be displaying this step
    for field in form.fields:
        form.fields[field].widget = forms.HiddenInput()
        form.fields[field].required = False

    return (template, paypal_command)


def send_html(query_args, pilot_url):
    '''
    Send the request to PayPal, and return the response
    '''
    data = urllib.urlencode(query_args)
    paypal_request = urllib2.Request(pilot_url, data)
    return urllib2.urlopen(paypal_request).read()


@csrf_exempt
def payment_redirect_view(request):
    """
    This view receives the response from PayPal, and finishes the order.

    Ensure that your Paypal manager page is set to POST to this URL when
    the order is complete
    """
    order = Order.objects.get(id=request.session["order"]["id"])
    if request.POST.get("RESULT", None) == "0":
        order.transaction_id = request.POST["PNREF"]
        form = OrderForm(request, checkout.CHECKOUT_STEP_LAST)
        order.complete(request)
        order_handler(request, form, order)
        checkout.send_order_email(request, order)
        template = "shop/paypal_redirect.html"
        # redirect from the template so that the complete form loads in the
        # whole window instead of the iframe
        return render(request, template)
    else:
        order.delete()
        raise Http404('Did not communicate properly with PayPal')
