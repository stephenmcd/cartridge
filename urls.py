
from django.conf.urls.defaults import patterns, url, include
from django.views.generic.simple import direct_to_template
from django.contrib import admin
from django.conf import settings

admin.autodiscover()
urlpatterns = []

if settings.DEV_SERVER:
	import os.path
	media_url = settings.MEDIA_URL.strip("/")
	urlpatterns += patterns("",
		(r"^%s/(?P<path>.*)$" % media_url, "django.views.static.serve",
			{"document_root": 
			os.path.join(os.path.dirname(__file__), media_url)}),)


urlpatterns += patterns("",
	(r"^admin/(.*)", admin.site.root),
	(r"^shop/", include("shop.urls")),
)
