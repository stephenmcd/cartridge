
from django.conf import settings


CART_EXPIRY_AGE = getattr(settings, "SHOP_CART_EXPIRY_AGE", 30) 
CART_EXPIRY_INTERVAL = getattr(settings, "SHOP_CART_EXPIRY_INTERVAL", 5)
SSL_ENABLED = getattr(settings, "SHOP_SSL_ENABLED", not settings.DEBUG)

