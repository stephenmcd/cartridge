
from cartridge.shop.models import Cart
from cartridge.shop import settings


def shop_globals(request):
    """
    Make the cart, wishlist and some settings globally available.
    """
    shop_globals = {"cart": Cart.objects.from_request(request), "wishlist":
        request.COOKIES.get("wishlist", "").split(",")}
    for k in ("CHECKOUT_ACCOUNT_ENABLED", "CHECKOUT_STEPS_SPLIT", "LOGIN_URL"):
        shop_globals[k] = getattr(settings, k)
    return shop_globals

