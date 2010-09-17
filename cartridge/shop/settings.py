"""
cartridge.shop.settings - These are the settings and their default values 
used internally throughout the shop. 

Each can be set via project's settings module with the prefix 
SHOP_setting_name. 

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

# Sequence of value/name pairs for types of product options, eg Size, Colour.
OPTION_TYPE_CHOICES = getattr(settings, "SHOP_OPTION_TYPE_CHOICES", (
    (1, _("Size")),
    (2, _("Colour")),
))

# Email address that order receipts should be emailed from.
ORDER_FROM_EMAIL = getattr(settings, "SHOP_ORDER_FROM_EMAIL", 
    "do_not_reply@%s" % gethostname())

# Sequence of value/name pairs for order statuses.
ORDER_STATUS_CHOICES = getattr(settings, "SHOP_ORDER_STATUS_CHOICES", (
    (1, _("Unprocessed")),
    (2, _("Processed")),
))

# Number of products to display per page for a category.
PER_PAGE_CATEGORY = getattr(settings, "SHOP_PER_PAGE_CATEGORY", 10)

# Number of products to display per page for search results.
PER_PAGE_SEARCH = getattr(settings, "SHOP_PER_PAGE_SEARCH", 10)

# Maximum number of paging links to show.
MAX_PAGING_LINKS = getattr(settings, "SHOP_MAX_PAGING_LINKS", 15)

# Sequence of description/field+direction pairs defining the options available 
# for sorting a list of products.
PRODUCT_SORT_OPTIONS = getattr(settings, "SHOP_PRODUCT_SORT_OPTIONS", (
    (_("Relevance"), None),
    (_("Least expensive"), "unit_price"),
    (_("Most expensive"), "-unit_price"),
    (_("Recently added"), "-date_added"),
))

# Bool to enable automatic redirecting to and from https for checkout.
SSL_ENABLED = getattr(settings, "SHOP_SSL_ENABLED", not settings.DEBUG)

# Decorator that wraps the given func in the CallableSetting object that calls 
# the func when it is cast to a string.
callable_setting = lambda func: type("", (), {"__str__": lambda self: func()})()

# Fall back to shop's login view if the view for LOGIN_URL hasn't been defined.
@callable_setting
def LOGIN_URL():
    from django.core.urlresolvers import resolve, reverse, Resolver404
    from mezzanine.pages.views import page
    try:
        if resolve(settings.LOGIN_URL)[0] is page:
            raise Resolver404
        return settings.LOGIN_URL
    except Resolver404:
        return reverse("shop_account")

