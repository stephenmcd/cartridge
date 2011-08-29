
from mezzanine.conf import settings


if "cartridge.shop.context_processors.shop_globals" in settings.TEMPLATE_CONTEXT_PROCESSORS:
    from warnings import warn
    warn("shop_globals deprecated; use cartridge.shop.middleware.ShopMiddleware")
    def shop_globals(request):
        return {"cart": request.cart, "wishlist": request.wishlist}
