
from django.conf.urls.defaults import *


urlpatterns = patterns("shop.views",
    url("^category/(?P<slug>.*)/$", "category", name="shop_category"),
    url("^product/(?P<slug>.*)/$", "product", name="shop_product"),
    url("^search/$", "search", name="shop_search"),
    url("^wishlist/$", "wishlist", name="shop_wishlist"),
    url("^cart/$", "cart", name="shop_cart"),
    url("^checkout/$", "checkout", name="shop_checkout"),
    url("^checkout/complete/$", "complete", name="shop_complete"),
)

