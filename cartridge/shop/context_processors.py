
from cartridge.shop.models import Cart


def shop_globals(request):
    """
    Make the cart and wishlist globally available.
    """
    return {
        "cart": Cart.objects.from_request(request), 
        "wishlist": request.COOKIES.get("wishlist", "").split(","),
    }
