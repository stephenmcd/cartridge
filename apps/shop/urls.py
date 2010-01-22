
from django.conf.urls.defaults import *

from shop.forms import checkout_wizard


urlpatterns = patterns("shop.views",
	url("^category/(?P<slug>.*)/$", "category", name="shop_category"),
	url("^product/(?P<slug>.*)/$", "product", name="shop_product"),
	url("^cart/$", "cart", name="shop_cart"),
	url("^checkout/$", checkout_wizard, name="shop_checkout"),
	url("^checkout/complete/$", "complete", name="shop_complete"),
)

