
DEBUG = False
DEV_SERVER = False
MANAGERS = ADMINS = ()
TIME_ZONE = "Australia/Melbourne"
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
LANGUAGE_CODE = "en"
SITE_ID = 1
USE_I18N = False
SECRET_KEY = "5tve)^cpj9sdfgasdfsdfsdfaddfgfu-e@u=!p2aqwtjiwxzzt%g6p"
INTERNAL_IPS = ("127.0.0.1",)
TEMPLATE_LOADERS = (
	"django.template.loaders.filesystem.load_template_source",
	"django.template.loaders.app_directories.load_template_source",
)


# database
DATABASE_ENGINE = "sqlite3"
DATABASE_NAME = "cartridge.db"
DATABASE_USER = ""
DATABASE_PASSWORD = ""
DATABASE_HOST = ""
DATABASE_PORT = ""


# apps
INSTALLED_APPS = (
	"django.contrib.admin",
	"django.contrib.auth",
	"django.contrib.contenttypes",
	"django.contrib.sessions",
	"django.contrib.sites",
	"shop",
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "shop.context_processors.cart",
)

MIDDLEWARE_CLASSES = (
	"django.contrib.sessions.middleware.SessionMiddleware",
	"django.contrib.auth.middleware.AuthenticationMiddleware",
	"django.middleware.cache.UpdateCacheMiddleware",
	"django.middleware.common.CommonMiddleware",
	"django.middleware.cache.FetchFromCacheMiddleware",
    "shop.middleware.SSLRedirect",
)

try:
	import debug_toolbar
except ImportError:
	pass
else:
	INSTALLED_APPS = list(INSTALLED_APPS) + ["debug_toolbar"]
	MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES) + \
		["debug_toolbar.middleware.DebugToolbarMiddleware"]
DEBUG_TOOLBAR_CONFIG = {"INTERCEPT_REDIRECTS": False }

# caching
CACHE_BACKEND = ""
CACHE_TIMEOUT = CACHE_MIDDLEWARE_SECONDS = 0
try:
	import cmemcache
except ImportError:
	try:
		import memcache
	except ImportError:
		CACHE_BACKEND = "locmem:///"
if not CACHE_BACKEND:
	CACHE_TIMEOUT = CACHE_MIDDLEWARE_SECONDS = 180
	CACHE_BACKEND = "memcached://127.0.0.1:11211/?timeout=%s" % CACHE_MIDDLEWARE_SECONDS
	CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True


# paths
import os
project_path = os.path.dirname(os.path.abspath(__file__))
project_dir = project_path.split(os.sep)[-1]
MEDIA_URL = "/site_media/"
MEDIA_ROOT = os.path.join(project_path, MEDIA_URL.strip("/"))
TEMPLATE_DIRS = (os.path.join(project_path, "templates"),)
ADMIN_MEDIA_PREFIX = "/media/"
ROOT_URLCONF = "%s.urls" % project_dir
if DATABASE_ENGINE == "sqlite3":
	DATABASE_NAME = os.path.join(project_path, DATABASE_NAME)


# host settings
from socket import gethostname
host_settings_module = "%s_%s" % (project_dir, 
	gethostname().replace(".", "_").replace("-", "_").lower())
host_settings_path = os.path.join(project_path, "host_settings", 
	"%s.py" % host_settings_module)
if not os.path.exists(host_settings_path):
	try:
		f = open(host_settings_path, "w")
		f.close()
	except IOError:
		print "couldn't create host_settings module: %s " % host_settings_path
try:
	exec "from host_settings.%s import *" % host_settings_module
except ImportError, e:
	pass
TEMPLATE_DEBUG = DEBUG
