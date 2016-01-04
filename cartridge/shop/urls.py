from __future__ import unicode_literals

from django.conf.urls import url
from mezzanine.conf import settings

from cartridge.shop import views


_slash = "/" if settings.APPEND_SLASH else ""

urlpatterns = [
    url("^product/(?P<slug>.*)%s$" % _slash, views.product,
        name="shop_product"),
    url("^wishlist%s$" % _slash, views.wishlist, name="shop_wishlist"),
    url("^cart%s$" % _slash, views.cart, name="shop_cart"),
    url("^checkout%s$" % _slash, views.checkout_steps, name="shop_checkout"),
    url("^checkout/complete%s$" % _slash, views.complete,
        name="shop_complete"),
    url("^invoice/(?P<order_id>\d+)%s$" % _slash, views.invoice,
        name="shop_invoice"),
    url("^invoice/(?P<order_id>\d+)/resend%s$" % _slash,
        views.invoice_resend_email, name="shop_invoice_resend"),
]
