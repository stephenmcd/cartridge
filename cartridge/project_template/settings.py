
import os, sys; sys.path.insert(0, os.path.join("..", "..", "..", "mezzanine"))
from mezzanine.project_template.settings import *

# Cartridge settings.
SHOP_SSL_ENABLED = False

# Mezzanine settings.
from django.utils.translation import ugettext_lazy as _
ADMIN_MENU_ORDER = (
    (_("Content"), ("pages.Page", "blog.BlogPost", "blog.Comment",
        (_("Media Library"), "fb_browse"),)),
    (_("Shop"), ("shop.Product", "shop.ProductOption", "shop.DiscountCode", 
        "shop.Sale", "shop.Order")),
    (_("Site"), ("sites.Site", "redirects.Redirect", "conf.Setting")),
    (_("Users"), ("auth.User", "auth.Group",)),
)

THEME = ""

# Main Django settings.
DEBUG = False
DEV_SERVER = False
MANAGERS = ADMINS = ()
TIME_ZONE = ""
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
LANGUAGE_CODE = "en"
SITE_ID = 1
USE_I18N = False
SECRET_KEY = "%(SECRET_KEY)s"
INTERNAL_IPS = ("127.0.0.1",)

# Databases.
DATABASES = {
    "default": {
        "ENGINE": "",
        "HOST": "",
        "NAME": "",
        "PASSWORD": "",
        "PORT": "",
        "USER": "",
    }
}

# Paths.
import os
_project_path = os.path.dirname(os.path.abspath(__file__))
_project_dir = _project_path.split(os.sep)[-1]
ADMIN_MEDIA_PREFIX = "/media/"
CACHE_MIDDLEWARE_KEY_PREFIX = _project_dir
MEDIA_URL = "/site_media/"
MEDIA_ROOT = os.path.join(_project_path, MEDIA_URL.strip("/"))
ROOT_URLCONF = "%s.urls" % _project_dir
TEMPLATE_DIRS = (os.path.join(_project_path, "templates"),)

# Apps.
INSTALLED_APPS = ("cartridge.shop",) + tuple(INSTALLED_APPS)

TEMPLATE_CONTEXT_PROCESSORS = tuple(TEMPLATE_CONTEXT_PROCESSORS) + (
    "cartridge.shop.context_processors.shop_globals",
)

MIDDLEWARE_CLASSES = tuple(MIDDLEWARE_CLASSES) + (
    "cartridge.shop.middleware.SSLRedirect",
)

# Local settings.
try:
    from local_settings import *
except ImportError:
    pass

# Dynamic settings.
from mezzanine.utils.conf import set_dynamic_settings
set_dynamic_settings(globals())
