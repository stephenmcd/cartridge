from __future__ import unicode_literals

from django.conf.urls import patterns, url

urlpatterns = patterns("cartridge.shop.views",
    url("^product/(?P<slug>.*)/$", "product", name="shop_product"),
    url("^wishlist/$", "wishlist", name="shop_wishlist"),
    url("^cart/$", "cart", name="shop_cart"),
    url("^checkout/$", "checkout_steps", name="shop_checkout"),
    url("^checkout/complete/$", "complete", name="shop_complete"),
    url("^invoice/(?P<order_id>\d+)/$", "invoice", name="shop_invoice"),
    url("^invoice/(?P<order_id>\d+)/resend/$", "invoice_resend_email",
            name="shop_invoice_resend"),
)
