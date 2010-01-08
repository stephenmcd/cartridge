"""
shop.settings - these are the settings and their default values used internally 
throughout the shop. each should set in your project's settings module using the 
prefix SHOP_setting_name eg: SHOP_PRODUCT_OPTIONS
"""

from django.conf import settings

# number of minutes of inactivity for carts until they're abandoned
CART_EXPIRY_MINUTES = getattr(settings, "SHOP_CART_EXPIRY_MINUTES", 30) 

# sequence of available credit card types for payment
CARD_TYPES = getattr(settings, "SHOP_CARD_TYPES", 
	("Mastercard", "Visa", "Diners", "Amex")
)

# sequence of pairs for order statuses
ORDER_STATUSES = getattr(settings, "SHOP_ORDER_STATUSES", (
	(1, "Unprocessed"),
	(2, "Processed"),
))

# default order status for new orders
ORDER_STATUS_DEFAULT = getattr(settings, "SHOP_ORDER_STATUS_DEFAULT", 1)

# sequence of name/sequence pairs defining the selectable options for products
PRODUCT_OPTIONS = getattr(settings, "SHOP_PRODUCT_OPTIONS", (
	("Size", ("Extra Small","Small","Regular","Large","Extra Large")),
	("Colour", ("Red","Orange","Yellow","Green","Blue","Indigo","Violet")),
))

# email address that order receipts should be emailed from
ORDER_FROM_EMAIL = getattr(settings, "SHOP_ORDER_FROM_EMAIL", None)

# bool to enable automatic redirecting to and from https for checkout
SSL_ENABLED = getattr(settings, "SHOP_SSL_ENABLED", not settings.DEBUG)

# host name matching the ssl cert that the site should always be accessed via
FORCE_HOST = getattr(settings, "SHOP_FORCE_HOST", None)
