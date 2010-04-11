
from django.conf.urls.defaults import *
from shop.settings import CHECKOUT_ACCOUNT_ENABLED

urlpatterns = patterns("shop.views",
    url("^category/(?P<slug>.*)/$", "category", name="shop_category"),
    url("^product/(?P<slug>.*)/$", "product", name="shop_product"),
    url("^search/$", "search", name="shop_search"),
    url("^wishlist/$", "wishlist", name="shop_wishlist"),
    url("^cart/$", "cart", name="shop_cart"),
    url("^checkout/$", "checkout", name="shop_checkout"),
    url("^checkout/complete/$", "complete", name="shop_complete"),
)

if CHECKOUT_ACCOUNT_ENABLED:
    urlpatterns += patterns("shop.views",
        url("^account/$", "account", name="shop_account"),
        url("^logout/$", "logout", name="shop_logout"),
    )

