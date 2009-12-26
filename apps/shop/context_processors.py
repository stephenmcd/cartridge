
from django.core.cache import cache
from django.conf import settings
from cart import Cart
from shop.models import Category


def shop_globals(request):
	category_cache_key = "%sshop_categories" % settings.CACHE_MIDDLEWARE_KEY_PREFIX
	categories = cache.get(category_cache_key)
	if categories is None:
		categories = Category.objects.active().select_related(depth=1)
		cache.set(category_cache_key, categories)
	return {"cart": Cart(request), "shop_categories": categories}


