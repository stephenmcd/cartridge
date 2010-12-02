
import locale
import hmac
from datetime import datetime, timedelta
try:
    from hashlib import sha512 as digest
except ImportError:
    from md5 import new as digest

from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMultiAlternatives
from django.template import loader, Context
from django.utils.translation import ugettext as _

from mezzanine.conf import settings


def make_choices(choices):
    """
    Zips a list with itself for field choices.
    """
    return zip(choices, choices)


def set_shipping(request, shipping_type, shipping_total):
    """
    Stores the shipping type and total in the session.
    """
    if request.session.get("free_shipping", False):
        shipping_type = _("Free shipping")
        shipping_total = 0
    request.session["shipping_type"] = shipping_type
    request.session["shipping_total"] = shipping_total


def set_cookie(response, name, value, secure=False):
    """
    Sets a cookie that expires in a year.
    """
    expires = datetime.strftime(datetime.utcnow() + 
        timedelta(seconds=365*24*60*60), "%a, %d-%b-%Y %H:%M:%S GMT")
    response.set_cookie(name, value, expires=expires, secure=secure)


def sign(value):
    """
    Returns the hash of the given value, used for signing order key stored in 
    cookie for remembering address fields.
    """
    return hmac.new(settings.SECRET_KEY, value, digest).hexdigest()


def send_mail_template(subject, template, addr_from, addr_to, context=None,
    attachments=None, fail_silently=False):
    """
    Send email rendering text and html versions for the specified template name
    using the context dictionary passed in.
    """
    if context is None:
        context = {}
    if attachments is None:
        attachments = []
    # Allow for a single address to be passed in.
    if not hasattr(addr_to, "__iter__"):
        addr_to = [addr_to]
    # Loads a template passing in vars as context.
    render = lambda type: loader.get_template("%s.%s" % 
        (template, type)).render(Context(context))
    # Create and send email.
    msg = EmailMultiAlternatives(subject, render("txt"), addr_from, addr_to)
    msg.attach_alternative(render("html"), "text/html")
    for attachment in attachments:
        msg.attach(attachment)
    msg.send(fail_silently=fail_silently)


def set_locale():
    """
    Sets the locale for currency formatting.
    """
    try:
        locale.setlocale(locale.LC_MONETARY, settings.SHOP_CURRENCY_LOCALE)
    except:
        raise ImproperlyConfigured(_("Invalid currency locale specified: %s") % 
            settings.SHOP_CURRENCY_LOCALE)
