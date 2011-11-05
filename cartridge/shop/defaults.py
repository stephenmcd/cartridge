
from socket import gethostname

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
    default=10,
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
    name="SHOP_FORCE_HOST",
    label=_("Force Host"),
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
    label=_("Billing & Shipping Handler"),
    description="Dotted package path and class name of the function that "
        "is called on submit of the billing/shipping checkout step. This "
        "is where shipping calculation can be performed and set using the "
        "function ``cartridge.shop.utils.set_shipping``.",
    editable=True,
    default="cartridge.shop.checkout.default_billship_handler",
)

register_setting(
    name="SHOP_HANDLER_ORDER",
    label=_("Order Handler"),
    description="Dotted package path and class name of the function that "
        "is called once an order is successful and all of the order "
        "object's data has been created. This is where any custom order "
        "processing should be implemented.",
    editable=True,
    default="cartridge.shop.checkout.default_order_handler",
)

register_setting(
    name="SHOP_HANDLER_PAYMENT",
    label=_("Payment Handler"),
    description="Dotted package path and class name of the function that "
        "is called on submit of the payment checkout step. This is where "
        "integration with a payment gateway should be implemented.",
    editable=True,
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
    default=10,
)

register_setting(
    name="SHOP_PER_PAGE_SEARCH",
    label=_("Search Products Per Page"),
    description="Number of products to display per page for search results.",
    editable=True,
    default=10,
)

register_setting(
    name="SHOP_MAX_PAGING_LINKS",
    label=_("Number of Paging Links"),
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
        (_("Highest rated"), "-rating_average"),
    ),
)

register_setting(
    name="SHOP_SSL_ENABLED",
    label=_("Enable SSL"),
    description="If True, users will be automatically redirect to HTTPS "
        "for the checkout process.",
    editable=True,
    default=False,
)

register_setting(
    name="TEMPLATE_ACCESSIBLE_SETTINGS",
    description=_("Sequence of setting names available within templates."),
    editable=False,
    default=("LOGIN_URL", "SHOP_CHECKOUT_ACCOUNT_ENABLED", "SHOP_CARD_TYPES",
             "SHOP_CHECKOUT_STEPS_SPLIT", "SHOP_MAX_PAGING_LINKS",
    ),
    append=True,
)
