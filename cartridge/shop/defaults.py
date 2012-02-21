
from socket import gethostname

from django.utils.translation import ugettext as _

from mezzanine.conf import register_setting


##################################################
#  These first set of settings already exist in  #
#  mezzanine.conf.defaults, and are overridden   #
#  or appended to here, with Cartridge values.   #
##################################################

# Default to False in Mezzanine, change to True so checkout can have
# an account option.
register_setting(
    name="ACCOUNTS_ENABLED",
    description="If True, users can create an account.",
    editable=False,
    default=True,
)

# Add shop admin modules to the admin menu.
register_setting(
    name="ADMIN_MENU_ORDER",
    description=_("Controls the ordering and grouping of the admin menu."),
    editable=False,
    default=(
        (_("Content"), ("pages.Page", "blog.BlogPost",
            "generic.ThreadedComment", (_("Media Library"), "fb_browse"),)),
        (_("Shop"), ("shop.Product", "shop.ProductOption", "shop.DiscountCode",
            "shop.Sale", "shop.Order")),
        (_("Site"), ("sites.Site", "redirects.Redirect", "conf.Setting")),
        (_("Users"), ("auth.User", "auth.Group",)),
    ),
)

# Add the checkout URLs prefix to those forced to run over SSL.
# Only relevant if SSL_ENABLED (defined in Mezzanine) is True.
register_setting(
    name="SSL_FORCE_URL_PREFIXES",
    description="Sequence of URL prefixes that will be forced to run over "
                "SSL when ``SSL_ENABLED`` is ``True``. i.e. "
                "('/admin', '/example') would force all URLs beginning with "
                "/admin or /example to run over SSL.",
    editable=False,
    default=("/shop/checkout",),
    append=True,
)

# Append the Cartridge settings used in templates to the list of settings
# accessible in templates.
register_setting(
    name="TEMPLATE_ACCESSIBLE_SETTINGS",
    description=_("Sequence of setting names available within templates."),
    editable=False,
    default=("SHOP_CARD_TYPES", "SHOP_CHECKOUT_STEPS_SPLIT",
             "SHOP_PRODUCT_SORT_OPTIONS",),
    append=True,
)


##########################################
#  Remaning settings are all defined by  #
#  Cartridge, prefixed with "SHOP_".     #
##########################################

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
    name="SHOP_CHECKOUT_ACCOUNT_REQUIRED",
    description="If True, users must create a login for the checkout process.",
    editable=False,
    default=False,
)

register_setting(
    name="SHOP_CHECKOUT_FORM_CLASS",
    description="Dotted path to the Form class to be used at checkout.",
    editable=False,
    default="cartridge.shop.forms.OrderForm",
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
    name="SHOP_PAYMENT_STEP_ENABLED",
    label=_("Payment Enabled"),
    description="If False, there is no payment step on the checkout process.",
    editable=True,
    default=True,
)

register_setting(
    name="SHOP_CURRENCY_LOCALE",
    label=_("Currency Locale"),
    description="Controls the formatting of monetary values accord to "
        "the locale module in the python standard library. If an empty "
        "string is used, will fall back to the system's locale.",
    editable=False,
    default="",
)

register_setting(
    name="SHOP_DEFAULT_SHIPPING_VALUE",
    label=_("Default Shipping Cost"),
    description="Default cost of shipping when no custom shipping is "
        "implemented.",
    editable=True,
    default=10.0,
)

register_setting(
    name="SHOP_DISCOUNT_FIELD_IN_CART",
    label=_("Discount in Cart"),
    description="Can discount codes be entered on the cart page.",
    editable=True,
    default=True,
)

register_setting(
    name="SHOP_DISCOUNT_FIELD_IN_CHECKOUT",
    label=_("Discount in Checkout"),
    description="Can discount codes be entered on the first checkpout step.",
    editable=True,
    default=True,
)

register_setting(
    name="SHOP_HANDLER_BILLING_SHIPPING",
    label=_("Billing & Shipping Handler"),
    description="Dotted package path and class name of the function that "
        "is called on submit of the billing/shipping checkout step. This "
        "is where shipping calculation can be performed and set using the "
        "function ``cartridge.shop.utils.set_shipping``.",
    editable=False,
    default="cartridge.shop.checkout.default_billship_handler",
)

register_setting(
    name="SHOP_HANDLER_ORDER",
    label=_("Order Handler"),
    description="Dotted package path and class name of the function that "
        "is called once an order is successful and all of the order "
        "object's data has been created. This is where any custom order "
        "processing should be implemented.",
    editable=False,
    default="cartridge.shop.checkout.default_order_handler",
)

register_setting(
    name="SHOP_HANDLER_PAYMENT",
    label=_("Payment Handler"),
    description="Dotted package path and class name of the function that "
        "is called on submit of the payment checkout step. This is where "
        "integration with a payment gateway should be implemented.",
    editable=False,
    default="cartridge.shop.checkout.default_payment_handler",
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
    name="SHOP_ORDER_EMAIL_SUBJECT",
    label=_("Order Email Subject"),
    description="Subject to be used when sending the order receipt email.",
    editable=True,
    default=_("Order Receipt"),
)

register_setting(
    name="SHOP_ORDER_FROM_EMAIL",
    label=_("From Email"),
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
    label=_("Products Per Category Page"),
    description="Number of products to display per category page.",
    editable=True,
    default=12,
)

register_setting(
    name="SHOP_PRODUCT_SORT_OPTIONS",
    description="Sequence of description/field+direction pairs defining "
        "the options available for sorting a list of products.",
    editable=False,
    default=(
        (_("Recently added"), "-date_added"),
        (_("Highest rated"), "-rating_average"),
        (_("Least expensive"), "unit_price"),
        (_("Most expensive"), "-unit_price"),
    ),
)
