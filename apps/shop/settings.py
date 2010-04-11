"""
shop.settings - These are the settings and their default values used internally 
throughout the shop. 

Each can be set via project's settings module with the prefix SHOP_setting_name. 

For example, set PRODUCT_OPTIONS with SHOP_PRODUCT_OPTIONS.
"""

from socket import gethostname

from django.conf import settings
from django.utils.translation import ugettext_lazy as _


# Sequence of available credit card types for payment.
CARD_TYPES = getattr(settings, "SHOP_CARD_TYPES", 
    ("Mastercard", "Visa", "Diners", "Amex")
)

# Number of minutes of inactivity for carts until they're abandoned.
CART_EXPIRY_MINUTES = getattr(settings, "SHOP_CART_EXPIRY_MINUTES", 30) 

# If True, users can *optionally* create a login for the checkout process.
CHECKOUT_ACCOUNT_ENABLED = getattr(settings, 
    "SHOP_CHECKOUT_ACCOUNT_ENABLED", True)

# If True, it is *mandatory* for users to create a login for the checkout 
# process. If True then CHECKOUT_LOGIN_ENABLED is set to True.
CHECKOUT_ACCOUNT_REQUIRED = getattr(settings, 
    "SHOP_CHECKOUT_ACCOUNT_REQUIRED", False)
if CHECKOUT_ACCOUNT_REQUIRED:
    CHECKOUT_ACCOUNT_ENABLED = True

# If True the checkout process is split into two - billing/shipping and payment.
CHECKOUT_STEPS_SPLIT = getattr(settings, "SHOP_CHECKOUT_STEPS_SPLIT", True)

# If True the checkout process has a final confirmation step before completion.
CHECKOUT_STEPS_CONFIRMATION = getattr(settings, 
    "SHOP_CHECKOUT_STEPS_CONFIRMATION", True)

# Controls the display formatting of monetary values accord to the locale 
# module in the python standard library.
CURRENCY_LOCALE = getattr(settings, "SHOP_CURRENCY_LOCALE", "")

# Host name matching the ssl cert that the site should always be accessed via.
FORCE_HOST = getattr(settings, "SHOP_FORCE_HOST", None)

# Sequence of view names forced to run over SSL when SSL_ENABLED is True.
FORCE_SSL_VIEWS = getattr(settings, "SHOP_FORCE_SSL_VIEWS", 
    ("shop_checkout", "shop_complete"))
if CHECKOUT_ACCOUNT_ENABLED:
    FORCE_SSL_VIEWS = list(FORCE_SSL_VIEWS) + ["shop_account"]

# Email address that order receipts should be emailed from.
ORDER_FROM_EMAIL = getattr(settings, "SHOP_ORDER_FROM_EMAIL", 
    "do_not_reply@%s" % gethostname())

# Sequence of value/name pairs for order statuses.
ORDER_STATUSES = getattr(settings, "SHOP_ORDER_STATUSES", (
    (1, _("Unprocessed")),
    (2, _("Processed")),
))

# Default order status for new orders.
ORDER_STATUS_DEFAULT = getattr(settings, "SHOP_ORDER_STATUS_DEFAULT", 
    ORDER_STATUSES[0][0])

# Sequence of name/sequence pairs defining the selectable options for products.
PRODUCT_OPTIONS = getattr(settings, "SHOP_PRODUCT_OPTIONS", (
    ("size", ("Extra Small","Small","Regular","Large","Extra Large")),
    ("colour", ("Red","Orange","Yellow","Green","Blue","Indigo","Violet")),
))

# Bool to enable automatic redirecting to and from https for checkout.
SSL_ENABLED = getattr(settings, "SHOP_SSL_ENABLED", not settings.DEBUG)

# Number of search results to display per page.
SEARCH_RESULTS_PER_PAGE = getattr(settings, "SHOP_SEARCH_RESULTS_PER_PAGE", 10)

# Custom ordering of admin app/model listing.
ADMIN_REORDER = tuple(getattr(settings, "ADMIN_REORDER", ()))
if "shop" not in dict(ADMIN_REORDER):
    ADMIN_REORDER += (("shop", ("Category", "Product", "Sale", "DiscountCode",
        "Order")),)

# Decorator that wraps the given func in the CallableSetting object that calls 
# the func when it is cast to a string.
callable_setting = lambda func: type("", (), {"__str__": lambda self: func()})()

# Fall back to shop's login view if the view for LOGIN_URL hasn't been defined.
@callable_setting
def LOGIN_URL():
    from django.core.urlresolvers import resolve, reverse, Resolver404
    try:
        return resolve(settings.LOGIN_URL)
    except Resolver404:
        return reverse("shop_account")

