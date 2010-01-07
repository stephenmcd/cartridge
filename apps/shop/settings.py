
from django.conf import settings


CART_EXPIRY_MINUTES = getattr(settings, "SHOP_CART_EXPIRY_MINUTES", 30) 

CARD_TYPES = getattr(settings, "SHOP_CARD_TYPES", 
	("Mastercard", "Visa", "Diners", "Amex")
)

ORDER_STATUSES = getattr(settings, "SHOP_ORDER_STATUSES", (
	(1, "Unprocessed"),
	(2, "Processed"),
))

ORDER_STATUS_DEFAULT = getattr(settings, "SHOP_ORDER_STATUS_DEFAULT", 1)

PRODUCT_OPTIONS = getattr(settings, "SHOP_PRODUCT_OPTIONS", (
	("Size", ("Extra Small","Small","Regular","Large","Extra Large")),
	("Colour", ("Red","Orange","Yellow","Green","Blue","Indigo","Violet")),
))

SSL_ENABLED = getattr(settings, "SHOP_SSL_ENABLED", not settings.DEBUG)


