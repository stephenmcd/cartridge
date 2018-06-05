from __future__ import unicode_literals

from mezzanine.utils.deprecation import MiddlewareMixin

from cartridge.shop.models import Cart


class ShopMiddleware(MiddlewareMixin):
    """
    Adds cart and wishlist attributes to the current request.
    """
    def process_request(self, request):
        request.cart = Cart.objects.from_request(request)
        wishlist = request.COOKIES.get("wishlist", "").split(",")
        if not wishlist[0]:
            wishlist = []
        request.wishlist = wishlist
