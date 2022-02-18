from django.urls import path, re_path
from mezzanine.conf import settings

from cartridge.shop import views

_slash = "/" if settings.APPEND_SLASH else ""

urlpatterns = [
    re_path(r"^product/(?P<slug>.*)%s$" % _slash, views.product, name="shop_product"),
    path("wishlist%s" % _slash, views.wishlist, name="shop_wishlist"),
    path("cart%s" % _slash, views.cart, name="shop_cart"),
    path("checkout%s" % _slash, views.checkout_steps, name="shop_checkout"),
    path("checkout/complete%s" % _slash, views.complete, name="shop_complete"),
    re_path(
        r"^invoice/(?P<order_id>\d+)%s$" % _slash, views.invoice, name="shop_invoice"
    ),
    re_path(
        r"^invoice/(?P<order_id>\d+)/resend%s$" % _slash,
        views.invoice_resend_email,
        name="shop_invoice_resend",
    ),
]
