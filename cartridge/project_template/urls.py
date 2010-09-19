
from django.conf.urls.defaults import *

from mezzanine.project_template.urls import urlpatterns

urlpatterns = patterns("",
    ("^shop/", include("cartridge.shop.urls")),
) + urlpatterns

