
from mezzanine.settings import load_settings

from cartridge.shop.models import Cart


def shop_globals(request):
    """
    Make the cart, wishlist and some settings globally available.
    """
    names = ("CHECKOUT_ACCOUNT_ENABLED", "CHECKOUT_STEPS_SPLIT", "LOGIN_URL")
    mezz_settings = load_settings(*names)
    shop_globals = {"cart": Cart.objects.from_request(request), "wishlist":
        request.COOKIES.get("wishlist", "").split(",")}
    for k in names:
        shop_globals[k] = getattr(mezz_settings, k)
    return shop_globals
