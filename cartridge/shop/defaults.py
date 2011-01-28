
from socket import gethostname

from django.conf import settings
from django.utils.translation import ugettext as _

from mezzanine.conf import register_setting


register_setting(
    name="SHOP_CARD_TYPES",
    description="Sequence of available credit card types for payment.",
    editable=False,
    default=("Mastercard", "Visa", "Diners", "Amex"),
)

register_setting(
    name="SHOP_CART_EXPIRY_MINUTES",
    description="Number of minutes of inactivity until carts are abandoned.",
    editable=False,
    default=30,
) 

register_setting(
    name="SHOP_CHECKOUT_ACCOUNT_ENABLED",
    description="If True, users can create a login for the checkout process.",
    editable=False,
    default=True,
)

register_setting(
    name="SHOP_CHECKOUT_ACCOUNT_REQUIRED",
    description="If True, users must create a login for the checkout process.",
    editable=False,
    default=False,
)    

register_setting(
    name="SHOP_CHECKOUT_STEPS_SPLIT",
    description="If True, the checkout process is split into separate "
        "billing/shipping and payment steps.",
    editable=False,
    default=True,
)

register_setting(
    name="SHOP_CHECKOUT_STEPS_CONFIRMATION",
    description="If True, the checkout process has a final confirmation "
        "step before completion.",
    editable=False,
    default=True,
)

register_setting(
    name="SHOP_CURRENCY_LOCALE",
    description="Controls the formatting of monetary values accord to "
        "the locale module in the python standard library.",
    editable=False,
    default="",
)

register_setting(
    name="SHOP_FORCE_HOST",
    description="Host name that the site should always be accessed via that "
        "matches the SSL certificate.",
    editable=True,
    default="",
)

register_setting(
    name="SHOP_FORCE_SSL_VIEWS",
    description="Sequence of view names that will be forced to run over SSL "
        "when SSL_ENABLED is True.",
    editable=False,
    default=("shop_checkout", "shop_complete", "shop_account"),
)

register_setting(
    name="SHOP_HANDLER_BILLING_SHIPPING",
    description="Dotted package path and class name of the function that "
        "is called on submit of the billing/shipping checkout step. This "
        "is where shipping calculation can be performed and set using the "
        "function ``cartridge.shop.utils.set_shipping``.",
    editable=True,
    default="cartridge.shop.checkout.dummy_billship_handler",
)

register_setting(
    name="SHOP_HANDLER_PAYMENT",
    description="Dotted package path and class name of the function that "
        "is called on submit of the payment checkout step. This is where "
        "integration with a payment gateway should be implemented.",
    editable=True,
    default="cartridge.shop.checkout.dummy_payment_handler",
)

register_setting(
    name="SHOP_OPTION_TYPE_CHOICES",
    description="Sequence of value/name pairs for types of product options, "
        "eg Size, Colour.",
    editable=False,
    default=(
        (1, _("Size")),
        (2, _("Colour")),
    ),
)

register_setting(
    name="SHOP_ORDER_FROM_EMAIL",
    description="Email address that order receipts should be emailed from.",
    editable=True,
    default="do_not_reply@%s" % gethostname(),
)

register_setting(
    name="SHOP_ORDER_STATUS_CHOICES",
    description="Sequence of value/name pairs for order statuses.",
    editable=False,
    default=(
        (1, _("Unprocessed")),
        (2, _("Processed")),
    ),
)

register_setting(
    name="SHOP_PER_PAGE_CATEGORY",
    description="Number of products to display per category page.",
    editable=True,
    default=10,
)

register_setting(
    name="SHOP_PER_PAGE_SEARCH",
    description="Number of products to display per page for search results.",
    editable=True,
    default=10,
)

register_setting(
    name="SHOP_MAX_PAGING_LINKS",
    description="Maximum number of paging links to show.",
    editable=True,
    default=15,
)

register_setting(
    name="SHOP_PRODUCT_SORT_OPTIONS",
    description="Sequence of description/field+direction pairs defining "
        "the options available for sorting a list of products.",
    editable=False,
    default=(
        (_("Relevance"), None),
        (_("Least expensive"), "unit_price"),
        (_("Most expensive"), "-unit_price"),
        (_("Recently added"), "-date_added"),
    ),
)

register_setting(
    name="SHOP_SSL_ENABLED",
    description="If True, users will be automatically redirect to HTTPS "
        "for the checkout process.",
    editable=True,
    default=not settings.DEBUG,
)

# Decorator that wraps the given func in the CallableSetting object that calls 
# the func when it is cast to a string.
callable_setting = lambda func: type("", (), {
    "__str__": lambda self: func(), "__repr__": lambda self: "[dynamic]"})()

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

register_setting(
    name="SHOP_LOGIN_URL",
    description="Fall back to shop's login view if the view for LOGIN_URL "
        "hasn't been defined.",
    editable=False,
    default=LOGIN_URL,
)

register_setting(
    name="TEMPLATE_ACCESSIBLE_SETTINGS", 
    description=_("Sequence of setting names available within templates."),
    editable=False,
    default=("SHOP_CHECKOUT_ACCOUNT_ENABLED", "SHOP_CHECKOUT_STEPS_SPLIT", 
        "SHOP_LOGIN_URL", "SHOP_MAX_PAGING_LINKS", 
    ),
    append=True,
)
