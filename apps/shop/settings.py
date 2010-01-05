
from django.conf import settings


CART_EXPIRY_MINUTES = getattr(settings, "SHOP_CART_EXPIRY_MINUTES", 30) 
SSL_ENABLED = getattr(settings, "SHOP_SSL_ENABLED", not settings.DEBUG)

