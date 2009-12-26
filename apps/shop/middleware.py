
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

class SSLRedirect(object):
	
	def process_request(self, request):
		if getattr(settings, "SSL_ENABLED", False):
			url = "%s%s" % (request.get_host(), request.get_full_path())
			if request.path in map(reverse, ("shop_checkout", "shop_complete")):
				if not request.is_secure():
					return HttpResponseRedirect("https://%s" % url)
			elif request.is_secure():
				return HttpResponseRedirect("http://%s" % url)

