
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

from mezzanine.core.views import direct_to_template


admin.autodiscover()

# Add the urlpatterns for any custom Django applications here.
# You can also change the ``home`` view to add your own functionality to
# the project's homepage.
urlpatterns = patterns("",
    ("^admin/", include(admin.site.urls)),
    ("^shop/", include("cartridge.shop.urls")),
    url("^$", direct_to_template, {"template": "index.html"}, name="home"),
    ("^", include("mezzanine.urls")),
)
