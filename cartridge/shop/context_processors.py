from __future__ import unicode_literals

from mezzanine.conf import settings


name = "cartridge.shop.context_processors.shop_globals"
if name in settings.TEMPLATE_CONTEXT_PROCESSORS:
    from warnings import warn
    warn(name + " deprecated; use cartridge.shop.middleware.ShopMiddleware")

    def shop_globals(request):
        return {"cart": request.cart, "wishlist": request.wishlist}
