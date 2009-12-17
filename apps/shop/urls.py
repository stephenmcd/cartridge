
from django.conf.urls.defaults import patterns, url
from shop.forms import checkout_wizard

urlpatterns = patterns("shop.views",
	url(r"^category/(?P<slugs>.*)/$", "category", name="shop_category"),
	url(r"^product/(?P<slugs>.*)/$", "product", name="shop_product"),
	url(r"^cart/$", "cart", name="shop_cart"),
	url(r"^checkout/$", checkout_wizard, name="shop_checkout"),
	url(r"^checkout/complete/$", "complete", name="shop_complete"),
)

