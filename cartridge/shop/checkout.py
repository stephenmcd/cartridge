"""
Checkout process utilities.
"""
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.template.loader import get_template, TemplateDoesNotExist
from mezzanine.accounts import get_profile_for_user, ProfileNotConfigured

from mezzanine.conf import settings
from mezzanine.utils.email import send_mail_template

from cartridge.shop.models import Order
from cartridge.shop.utils import set_shipping, set_tax, sign


class CheckoutError(Exception):
    """
    Should be raised in billing/shipping and payment handlers for
    cases such as an invalid shipping address or an unsuccessful
    payment.
    """
    pass


def default_billship_handler(request, order_form):
    """
    Default billing/shipping handler - called when the first step in
    the checkout process with billing/shipping address fields is
    submitted. Implement your own and specify the path to import it
    from via the setting ``SHOP_HANDLER_BILLING_SHIPPING``.
    This function will typically contain any shipping calculation
    where the shipping amount can then be set using the function
    ``cartridge.shop.utils.set_shipping``. The Cart object is also
    accessible via ``request.cart``
    """
    if not request.session.get("free_shipping"):
        settings.clear_cache()
        set_shipping(request, _("Flat rate shipping"),
                     settings.SHOP_DEFAULT_SHIPPING_VALUE)


def default_tax_handler(request, order_form):
    """
    Default tax handler - called immediately after the handler defined
    by ``SHOP_HANDLER_BILLING_SHIPPING``. Implement your own and
    specify the path to import it from via the setting
    ``SHOP_HANDLER_TAX``. This function will typically contain any tax
    calculation where the tax amount can then be set using the function
    ``cartridge.shop.utils.set_tax``. The Cart object is also
    accessible via ``request.cart``
    """
    set_tax(request, _("Tax"), 0)


def default_payment_handler(request, order_form, order):
    """
    Default payment handler - called when the final step of the
    checkout process with payment information is submitted. Implement
    your own and specify the path to import it from via the setting
    ``SHOP_HANDLER_PAYMENT``. This function will typically contain
    integration with a payment gateway. Raise
    cartridge.shop.checkout.CheckoutError("error message") if payment
    is unsuccessful.
    """
    pass


def default_order_handler(request, order_form, order):
    """
    Default order handler - called when the order is complete and
    contains its final data. Implement your own and specify the path
    to import it from via the setting ``SHOP_HANDLER_ORDER``.
    """
    pass


def initial_order_data(request, form_class=None):
    """
    Return the initial data for the order form, trying the following in
    order:
    - request.POST which is available when moving backward through the
      checkout steps
    - current order details in the session which are populated via each
      checkout step, to support user leaving the checkout entirely and
      returning
    - last order made by the user, via user ID or cookie
    - matching fields on an authenticated user and profile object
    """
    initial = {}
    if request.method == "POST":
        initial = dict(list(request.POST.items()))
        try:
            initial = form_class.preprocess(initial)
        except (AttributeError, TypeError):
            # form_class has no preprocess method, or isn't callable.
            pass
        # POST on first step won't include the "remember" checkbox if
        # it isn't checked, and it'll then get an actual value of False
        # when it's a hidden field - so we give it an empty value when
        # it's missing from the POST data, to persist it not checked.
        initial.setdefault("remember", "")
    # Look for order in current session.
    if not initial:
        initial = request.session.get("order", {})
    # Look for order in previous session.
    if not initial:
        lookup = {}
        if request.user.is_authenticated():
            lookup["user_id"] = request.user.id
        remembered = request.COOKIES.get("remember", "").split(":")
        if len(remembered) == 2 and remembered[0] == sign(remembered[1]):
            lookup["key"] = remembered[1]
        if lookup:
            previous = list(Order.objects.filter(**lookup).values())[:1]
            if len(previous) > 0:
                initial.update(previous[0])
    if not initial and request.user.is_authenticated():
        # No previous order data - try and get field values from the
        # logged in user. Check the profile model before the user model
        # if it's configured. If the order field name uses one of the
        # billing/shipping prefixes, also check for it without the
        # prefix. Finally if a matching attribute is callable, call it
        # for the field value, to support custom matches on the profile
        # model.
        user_models = [request.user]
        try:
            user_models.insert(0, get_profile_for_user(request.user))
        except ProfileNotConfigured:
            pass
        for order_field in form_class._meta.fields:
            check_fields = [order_field]
            for prefix in ("billing_detail_", "shipping_detail_"):
                if order_field.startswith(prefix):
                    check_fields.append(order_field.replace(prefix, "", 1))
            for user_model in user_models:
                for check_field in check_fields:
                    user_value = getattr(user_model, check_field, None)
                    if user_value:
                        if callable(user_value):
                            try:
                                user_value = user_value()
                            except TypeError:
                                continue
                        if not initial.get(order_field):
                            initial[order_field] = user_value
    # Set initial value for "same billing/shipping" based on
    # whether both sets of address fields are all equal.
    shipping = lambda f: "shipping_%s" % f[len("billing_"):]
    if any([f for f in form_class._meta.fields if f.startswith("billing_") and
        shipping(f) in form_class._meta.fields and
        initial.get(f, "") != initial.get(shipping(f), "")]):
        initial["same_billing_shipping"] = False
    # Never prepopulate discount code.
    try:
        del initial["discount_code"]
    except KeyError:
        pass
    return initial


def send_order_email(request, order):
    """
    Send order receipt email on successful order.
    """
    settings.clear_cache()
    order_context = {"order": order, "request": request,
                     "order_items": order.items.all()}
    order_context.update(order.details_as_dict())
    try:
        get_template("shop/email/order_receipt.html")
    except TemplateDoesNotExist:
        receipt_template = "email/order_receipt"
    else:
        receipt_template = "shop/email/order_receipt"
        from warnings import warn
        warn("Shop email receipt templates have moved from "
             "templates/shop/email/ to templates/email/")
    send_mail_template(settings.SHOP_ORDER_EMAIL_SUBJECT,
                       receipt_template, settings.SHOP_ORDER_FROM_EMAIL,
                       order.billing_detail_email, context=order_context,
                       addr_bcc=settings.SHOP_ORDER_EMAIL_BCC or None)


# Set up some constants for identifying each checkout step.

CHECKOUT_STEPS = [{"template": "billing_shipping", "url": "details",
                   "title": _("Details")}]
CHECKOUT_STEP_FIRST = CHECKOUT_STEP_PAYMENT = CHECKOUT_STEP_LAST = 1
if settings.SHOP_CHECKOUT_STEPS_SPLIT:
    CHECKOUT_STEPS[0].update({"url": "billing-shipping",
                              "title": _("Address")})
    if settings.SHOP_PAYMENT_STEP_ENABLED:
        CHECKOUT_STEPS.append({"template": "payment", "url": "payment",
                                "title": _("Payment")})
        CHECKOUT_STEP_PAYMENT = CHECKOUT_STEP_LAST = 2
if settings.SHOP_CHECKOUT_STEPS_CONFIRMATION:
    CHECKOUT_STEPS.append({"template": "confirmation", "url": "confirmation",
                           "title": _("Confirmation")})
    CHECKOUT_STEP_LAST += 1
