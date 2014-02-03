from __future__ import unicode_literals

from django.conf.urls import patterns, url

from mezzanine.conf import settings


_slash = "/" if settings.APPEND_SLASH else ""

urlpatterns = patterns("cartridge.shop.views",
    url("^product/(?P<slug>.*)%s$" % _slash, "product", name="shop_product"),
    url("^wishlist%s$" % _slash, "wishlist", name="shop_wishlist"),
    url("^cart%s$" % _slash, "cart", name="shop_cart"),
    url("^checkout%s$" % _slash, "checkout_steps", name="shop_checkout"),
    url("^checkout/complete%s$" % _slash, "complete", name="shop_complete"),
    url("^invoice/(?P<order_id>\d+)%s$" % _slash, "invoice",
        name="shop_invoice"),
    url("^invoice/(?P<order_id>\d+)/resend%s$" % _slash,
        "invoice_resend_email", name="shop_invoice_resend"),
)
