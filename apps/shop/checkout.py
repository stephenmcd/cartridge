"""

Checkout process utilities. The following are particularly for customization
and if fail should raise checkout.CheckoutError:

billing_shipping() - Hook for setting shipping via shop.utils.set_shipping.

payment() - Hook for payment gateway integration.

"""

from django.utils.translation import ugettext as _

from shop.models import Order
from shop.settings import CHECKOUT_STEPS_SPLIT, CHECKOUT_STEPS_CONFIRMATION, \
    ORDER_FROM_EMAIL
from shop.utils import set_shipping, send_mail_template, sign


def billing_shipping(request, order_form):
    """
    Implement shipping handling here.
    """
    # Cart is also accessible via shop.Cart.objects.from_request(request)
    set_shipping(request, "Shipping Test", 10)
    
def payment(request, order_form):
    """
    Implement payment gateway integration here.
    """
    # Eg, for declined credit card: raise CheckoutError("Credit card declined")
    pass
    
def initial_order_data(request):
    """
    Return the initial data for the order form - favor request.POST, then 
    session, then previous order cookie set with "remember my details".
    """
    if request.method == "POST":
        return dict(request.POST.items())
    if "order" in request.session:
        return request.session["order"]
    initial = {}
    remembered = request.COOKIES.get("remember", "").split(":")
    if len(remembered) == 2 and remembered[0] == sign(remembered[1]):
        previous_orders = Order.objects.filter(key=remembered[1]).values()[:1]
        if len(previous_orders) > 0:
            initial.update(previous_orders[0])
            # Set initial value for "same billing/shipping" based on 
            # whether both sets of address fields are all equal.
            ship_field = lambda f: "shipping_%s" % f[len("billing_"):]
            if any([f for f in initial.keys() 
                if f.startswith("billing_") and ship_field(f) in 
                    initial and initial[f] != initial[ship_field(f)]]):
                    initial["same_billing_shipping"] = False
    return initial
    
def send_order_email(request, order):
    """
    Send order receipt email on successful order.
    """
    order_context = {"order": order, "request": request, 
        "order_items": order.items.all()}
    for fieldset in ("billing_detail", "shipping_detail"):
        fields = [(f.verbose_name, getattr(order, f.name)) for f in
            order._meta.fields if f.name.startswith(fieldset)]
        order_context["order_%s_fields" % fieldset] = fields
    send_mail_template(_("Order Receipt"), "shop/email/order_receipt", 
        ORDER_FROM_EMAIL, order.billing_detail_email, context=order_context)

class CheckoutError(Exception):
    """
    Raised if an error occurs when processing payment above in 
    shop.checkout.payment() and caught in shop.views.checkout()
    """
    pass

# set up some constants for identifying each checkout step.
CHECKOUT_TEMPLATES = ["billing_shipping"]
CHECKOUT_STEP_FIRST = CHECKOUT_STEP_PAYMENT = CHECKOUT_STEP_LAST = 1
if CHECKOUT_STEPS_SPLIT:
    CHECKOUT_TEMPLATES.append("payment")
    CHECKOUT_STEP_PAYMENT = CHECKOUT_STEP_LAST = 2
if CHECKOUT_STEPS_CONFIRMATION:
    CHECKOUT_TEMPLATES.append("confirmation")
    CHECKOUT_STEP_LAST += 1

