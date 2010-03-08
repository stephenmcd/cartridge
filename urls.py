
from django.conf.urls.defaults import patterns, url, include
from django.contrib import admin
from django.conf import settings
from django.views.generic.simple import direct_to_template


admin.autodiscover()

urlpatterns = patterns("",
    ("^admin/", include(admin.site.urls)),
    ("^shop/", include("shop.urls")),
    ("^$", direct_to_template, {"template": "index.html"}),
)
if settings.DEV_SERVER:
    urlpatterns += patterns("",
        ("^%s/(?P<path>.*)$" % settings.MEDIA_URL.strip("/"), 
            "django.views.static.serve", {"document_root": settings.MEDIA_ROOT}),
        ("^favicon.ico$", "django.views.static.serve", {"document_root": 
            settings.MEDIA_ROOT, "path": "img/favicon.ico"}),
    )

