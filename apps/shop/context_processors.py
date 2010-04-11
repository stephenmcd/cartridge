
from shop.models import ProductVariation, Cart
from shop import settings


def shop_globals(request):
    """
    Make the cart, wishlist and some settings globally available.
    """
    shop_globals = {"cart": Cart.objects.from_request(request)}
    for k in ("CHECKOUT_ACCOUNT_ENABLED", "CHECKOUT_STEPS_SPLIT", "LOGIN_URL"):
        shop_globals[k] = getattr(settings, k)
    wishlist = []
    skus = request.COOKIES.get("wishlist", "").split(",")
    if skus:
        wishlist = list(ProductVariation.objects.filter(product__active=True,
            sku__in=skus).select_related())
        wishlist.sort(key=lambda v: skus.index(v.sku))
    shop_globals["wishlist"] = wishlist
    return shop_globals

