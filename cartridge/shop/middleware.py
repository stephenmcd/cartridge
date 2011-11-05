
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from mezzanine.conf import settings

from cartridge.shop.models import Cart


class ShopMiddleware(object):

    def process_request(self, request):
        """
        Adds cart and wishlist attributes to the current request, and
        handles any redirections required for SSL. If SHOP_FORCE_HOST
        is set and is not the current host, redirect to it if
        SHOP_SSL_ENABLED is True, and ensure checkout views are
        accessed over HTTPS and all other views are accessed over HTTP.
        """
        request.cart = Cart.objects.from_request(request)
        wishlist = request.COOKIES.get("wishlist", "").split(",")
        if not wishlist[0]:
            wishlist = []
        request.wishlist = wishlist
        settings.use_editable()
        force_host = settings.SHOP_FORCE_HOST
        if force_host and request.get_host().split(":")[0] != force_host:
            url = "http://%s%s" % (force_host, request.get_full_path())
            return HttpResponsePermanentRedirect(url)
        if settings.SHOP_SSL_ENABLED and not settings.DEV_SERVER:
            url = "%s%s" % (request.get_host(), request.get_full_path())
            if request.path in map(reverse, settings.SHOP_FORCE_SSL_VIEWS):
                if not request.is_secure():
                    return HttpResponseRedirect("https://%s" % url)
            elif request.is_secure():
                return HttpResponseRedirect("http://%s" % url)

name = "cartridge.shop.middleware.SSLRedirect"
if name in settings.MIDDLEWARE_CLASSES:
    import warnings
    warnings.warn(name + " deprecated; "
                  "use cartridge.shop.middleware.ShopMiddleware",)
    SSLRedirect = ShopMiddleware
