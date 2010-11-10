
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from mezzanine.conf import settings


class SSLRedirect(object):

    def process_request(self, request):
        """
        If SHOP_FORCE_HOST is set and is not the current host, redirect to it
        if SHOP_SSL_ENABLED is True, ensure checkout views are accessed over 
        HTTPS and all other views are accessed over HTTP.
        """
        settings.use_editable()
        if settings.SHOP_FORCE_HOST and \
            request.get_host().split(":")[0] != FORCE_HOST:
            return http.HttpResponsePermanentRedirect("http://%s%s" % 
                (settings.SHOP_FORCE_HOST, request.get_full_path()))            
        if settings.SHOP_SSL_ENABLED and not \
            getattr(settings, "DEV_SERVER", False):
            url = "%s%s" % (request.get_host(), request.get_full_path())
            if request.path in map(reverse, settings.SHOP_FORCE_SSL_VIEWS):
                if not request.is_secure():
                    return HttpResponseRedirect("https://%s" % url)
            elif request.is_secure():
                return HttpResponseRedirect("http://%s" % url)
