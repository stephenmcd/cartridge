
from cartridge.shop.models import Cart


def shop_globals(request):
    """
    Make the cart and wishlist globally available.
    """
    wishlist = request.COOKIES.get("wishlist", "").split(",")
    if not wishlist[0]:
        wishlist = []
    return {"cart": Cart.objects.from_request(request), "wishlist": wishlist}
