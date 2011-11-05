
from django.utils.translation import ugettext_lazy as _
# Allow the development version of Mezzanine to be picked up.
import os
import sys
sys.path.insert(0, os.path.join("..", "..", "..", "mezzanine"))
from mezzanine.project_template.settings import *


######################
# CARTRIDGE SETTINGS #
######################

# The following Cartridge settings are already defined in
# cartridge.shop.defaults, but can be uncommented below in
# order to override their defaults.

# If True, users will be automatically redirect to HTTPS for the
# checkout process.
# SHOP_SSL_ENABLED = False

# Sequence of available credit card types for payment.
# SHOP_CARD_TYPES = ("Mastercard", "Visa", "Diners", "Amex")

# If True, users can create a login for the checkout process.
# SHOP_CHECKOUT_ACCOUNT_ENABLED = True

# If True, users must create a login for the checkout process.
# SHOP_CHECKOUT_ACCOUNT_REQUIRED = False

# If True, the checkout process is split into separate
# billing/shipping and payment steps.
# SHOP_CHECKOUT_STEPS_SPLIT = True

# If True, the checkout process has a final confirmation step before
# completion.
# SHOP_CHECKOUT_STEPS_CONFIRMATION = True

# Controls the formatting of monetary values accord to the locale
# module in the python standard library. If an empty string is
# used, will fall back to the system's locale.
# SHOP_CURRENCY_LOCALE = ""

# Default cost of shipping when no custom shipping is implemented.
# SHOP_DEFAULT_SHIPPING_VALUE = 10

# Host name that the site should always be accessed via that matches
# the SSL certificate.
# SHOP_FORCE_HOST = ""

# Sequence of view names that will be forced to run over SSL when
# SSL_ENABLED is True.
# SHOP_FORCE_SSL_VIEWS = ("shop_checkout", "shop_complete", "shop_account")

# Dotted package path and class name of the function that
# is called on submit of the billing/shipping checkout step. This
# is where shipping calculation can be performed and set using the
# function ``cartridge.shop.utils.set_shipping``.
# SHOP_HANDLER_BILLING_SHIPPING = \
#                           "cartridge.shop.checkout.default_billship_handler"

# Dotted package path and class name of the function that
# is called once an order is successful and all of the order
# object's data has been created. This is where any custom order
# processing should be implemented.
# SHOP_HANDLER_ORDER = "cartridge.shop.checkout.default_order_handler"

# Dotted package path and class name of the function that
# is called on submit of the payment checkout step. This is where
# integration with a payment gateway should be implemented.
# SHOP_HANDLER_PAYMENT = "cartridge.shop.checkout.default_payment_handler"

# Sequence of value/name pairs for order statuses.
# SHOP_ORDER_STATUS_CHOICES = (
#     (1, _("Unprocessed")),
#     (2, _("Processed")),
# )

# Sequence of value/name pairs for types of product options,
# eg Size, Colour.
# SHOP_OPTION_TYPE_CHOICES = (
#     (1, _("Size")),
#     (2, _("Colour")),
# )


######################
# MEZZANINE SETTINGS #
######################

# The following Mezzanine settings are already defined in
# mezzanine.conf.defaults, but can be uncommented below in
# order to override their defaults.

# Controls the ordering and grouping of the admin menu.
ADMIN_MENU_ORDER = (
     (_("Content"), ("pages.Page", "blog.BlogPost",
        "generic.ThreadedComment", (_("Media Library"), "fb_browse"),)),
    (_("Shop"), ("shop.Product", "shop.ProductOption", "shop.DiscountCode",
        "shop.Sale", "shop.Order")),
    (_("Site"), ("sites.Site", "redirects.Redirect", "conf.Setting")),
    (_("Users"), ("auth.User", "auth.Group",)),
)

# A three item sequence, each containing a sequence of template tags
# used to render the admin dashboard.
#
# DASHBOARD_TAGS = (
#     ("blog_tags.quick_blog", "mezzanine_tags.app_list"),
#     ("comment_tags.recent_comments",),
#     ("mezzanine_tags.recent_actions",),
# )

# A sequence of fields that will be injected into Mezzanine's (or any
# library's) models. Each item in the sequence is a four item sequence.
# The first two items are the dotted path to the model and its field
# name to be added, and the dotted path to the field class to use for
# the field. The third and fourth items are a sequence of positional
# args and a dictionary of keyword args, to use when creating the
# field instance. When specifying the field class, the path
# ``django.models.db.`` can be omitted for regular Django model fields.
#
# from django.utils.translation import ugettext as _
# EXTRA_MODEL_FIELDS = (
#     (
#         # Dotted path to field.
#         "mezzanine.blog.models.BlogPost.image",
#         # Dotted path to field class.
#         "somelib.fields.ImageField",
#         # Positional args for field class.
#         (_("Image"),),
#         # Keyword args for field class.
#         {"blank": True, "upload_to: "blog"},
#     ),
#     # Example of adding a field to *all* of Mezzanine's content types:
#     (
#         "mezzanine.pages.models.Page.another_field",
#         "IntegerField", # 'django.db.models.' is implied if path is omitted.
#         (_("Another name"),),
#         {"blank": True, "default": 1},
#     ),
# )

# Name of the current theme to host during theme development.
#
# THEME = ""

# If True, the south application will be automatically added to the
# INSTALLED_APPS setting. This setting is not defined in
# mezzanine.conf.defaults as is the case with the above settings.
USE_SOUTH = True


########################
# MAIN DJANGO SETTINGS #
########################

# People who get code error notifications.
# In the format (('Full Name', 'email@example.com'),
#                ('Full Name', 'anotheremail@example.com'))
ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = ""

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en"

# A boolean that turns on/off debug mode. When set to ``True``, stack traces
# are displayed for error pages. Should always be set to ``False`` in
# production. Best set to ``True`` in local_settings.py
DEBUG = False

# Whether a user's session cookie expires when the Web browser is closed.
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Make this unique, and don't share it with anybody.
SECRET_KEY = "%(SECRET_KEY)s"

# Tuple of IP addresses, as strings, that:
#   * See debug comments, when DEBUG is true
#   * Receive x-headers
INTERNAL_IPS = ("127.0.0.1",)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
)


#############
# DATABASES #
#############

DATABASES = {
    "default": {
        # "postgresql_psycopg2", "postgresql", "mysql", "sqlite3" or "oracle".
        "ENGINE": "",
        # DB name or path to database file if using sqlite3.
        "NAME": "",
        # Not used with sqlite3.
        "USER": "",
        # Not used with sqlite3.
        "PASSWORD": "",
        # Set to empty string for localhost. Not used with sqlite3.
        "HOST": "",
         # Set to empty string for default. Not used with sqlite3.
        "PORT": "",
    }
}


#########
# PATHS #
#########

import os

# Full filesystem path to the project.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Name of the directory for the project.
PROJECT_DIRNAME = PROJECT_ROOT.split(os.sep)[-1]

# Every cache key will get prefixed with this value - here we set it to
# the name of the directory the project is in to try and use something
# project specific.
CACHE_MIDDLEWARE_KEY_PREFIX = PROJECT_DIRNAME

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = "/media/"

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = "/site_media/"

# Absolute path to the directory that holds media.
MEDIA_ROOT = os.path.join(PROJECT_ROOT, MEDIA_URL.strip("/"))

# Package/module name to import the root urlpatterns from for the project.
ROOT_URLCONF = "%s.urls" % PROJECT_DIRNAME

# Put strings here, like "/home/html/django_templates"
# or "C:/www/django/templates".
# Always use forward slashes, even on Windows.
# Don't forget to use absolute paths, not relative paths.
TEMPLATE_DIRS = (os.path.join(PROJECT_ROOT, "templates"),)

LOGIN_URL = "/shop/account/"


################
# APPLICATIONS #
################

# django.contrib.sites should be before cartridge.shop to avoid a
# foreign key error when installing the test fixtures with Postgres,
# and cartridge.shop should be before mezzanine.core so that the
# shop's base template is loaded over mezzanine's.

INSTALLED_APPS = list(INSTALLED_APPS)
INSTALLED_APPS.remove("django.contrib.sites")
INSTALLED_APPS = tuple(INSTALLED_APPS)
INSTALLED_APPS = ("django.contrib.sites", "cartridge.shop") + INSTALLED_APPS

# List of processors used by RequestContext to populate the context.
# Each one should be a callable that takes the request object as its
# only parameter and returns a dictionary to add to the context.

# Just use those imported from Mezzanine
# TEMPLATE_CONTEXT_PROCESSORS = tuple(TEMPLATE_CONTEXT_PROCESSORS) + (
# )

# List of middleware classes to use. Order is important; in the request phase,
# this middleware classes will be applied in the order given, and in the
# response phase the middleware will be applied in reverse order.

MIDDLEWARE_CLASSES = tuple(MIDDLEWARE_CLASSES) + (
    "cartridge.shop.middleware.ShopMiddleware",
)

##################
# LOCAL SETTINGS #
##################

# Allow any settings to be defined in local_settings.py which should be
# ignored in your version control system allowing for settings to be
# defined per machine.
try:
    from local_settings import *
except ImportError:
    pass


####################
# DYNAMIC SETTINGS #
####################

# set_dynamic_settings() will rewrite globals based on what has been
# defined so far, in order to provide some better defaults where
# applicable.
from mezzanine.utils.conf import set_dynamic_settings
set_dynamic_settings(globals())
