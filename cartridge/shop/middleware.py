
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect

from mezzanine.conf import settings


class SSLRedirect(object):

    def process_request(self, request):
        """
        If SHOP_FORCE_HOST is set and is not the current host, redirect to it
        if SHOP_SSL_ENABLED is True, ensure checkout views are accessed over 
        HTTPS and all other views are accessed over HTTP.
        """
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
