
from __future__ import unicode_literals
from future.builtins import str, chr

from decimal import Decimal
import locale
import platform

from django import template

from cartridge.shop.utils import set_locale

from mezzanine.conf import settings

register = template.Library()


@register.filter
def currency(value):
    """
    Format a value as currency according to locale.
    """
    try:
        set_locale()
    except:
        pass
    if not value:
        value = 0
    # if SHOP_CURRENCY_SYMBOL and SHOP_CURRENCY_FRAC_DIGITS are defined,
    # they take precedence.
    # SHOP_CURRENCY_SYMBOL can be an ASCII string like
    # SHOP_CURRENCY_SYMBOL = "$",
    # or it can be a number that represents a currency, like
    # SHOP_CURRENCY_SYMBOL = 163
    # where 163 is the ASCII code for the British Pound currency symbol.
    if hasattr(settings, "SHOP_CURRENCY_SYMBOL") and \
        hasattr(settings, "SHOP_CURRENCY_FRAC_DIGITS"):
        frac_digits = settings.SHOP_CURRENCY_FRAC_DIGITS
        try:
            currency_symbol = chr(settings.SHOP_CURRENCY_SYMBOL)
        except:
            currency_symbol = settings.SHOP_CURRENCY_SYMBOL
        if hasattr(settings, "SHOP_CURRENCY_SEP_BY_SPACE"):
            p_sep_by_space = settings.SHOP_CURRENCY_SEP_BY_SPACE
        else:
            p_sep_by_space = False
        if hasattr(settings, "SHOP_CURRENCY_MON_DECIMAL_POINT"):
            mon_decimal_point = settings.SHOP_CURRENCY_MON_DECIMAL_POINT
        else:
            mon_decimal_point = "."
        if hasattr(settings, "SHOP_CURRENCY_P_CS_PRECEDES"):
            p_cs_precedes = settings.SHOP_CURRENCY_P_CS_PRECEDES
        else:
            p_cs_precedes = True

        value = [currency_symbol, p_sep_by_space and " " or "",
            (("%%.%sf" % frac_digits) % value).replace(".", mon_decimal_point)]
        if not p_cs_precedes:
            value.reverse()
        value = "".join(value)
    elif hasattr(locale, "currency"):
        value = locale.currency(Decimal(value), grouping=True)
        if platform.system() == 'Windows':
            try:
                value = str(value, encoding=locale.getpreferredencoding())
            except TypeError:
                pass
    else:
        # based on locale.currency() in python >= 2.5
        conv = locale.localeconv()
        value = [conv["currency_symbol"], conv["p_sep_by_space"] and " " or "",
            (("%%.%sf" % conv["frac_digits"]) % value).replace(".",
            conv["mon_decimal_point"])]
        if not conv["p_cs_precedes"]:
            value.reverse()
        value = "".join(value)
    return value


def _order_totals(context):
    """
    Add shipping/tax/discount/order types and totals to the template
    context. Use the context's completed order object for email
    receipts, or the cart object for checkout.
    """
    fields = ["shipping_type", "shipping_total", "discount_total",
              "tax_type", "tax_total"]
    if "order" in context:
        for field in fields + ["item_total"]:
            context[field] = getattr(context["order"], field)
    else:
        context["item_total"] = context["request"].cart.total_price()
        if context["item_total"] == 0:
            # Ignore session if cart has no items, as cart may have
            # expired sooner than the session.
            context["tax_total"] = 0
            context["discount_total"] = 0
            context["shipping_total"] = 0
        else:
            for field in fields:
                context[field] = context["request"].session.get(field, None)
    context["order_total"] = context.get("item_total", None)
    if context.get("shipping_total", None) is not None:
        context["order_total"] += Decimal(str(context["shipping_total"]))
    if context.get("discount_total", None) is not None:
        context["order_total"] -= Decimal(str(context["discount_total"]))
    if context.get("tax_total", None) is not None:
        context["order_total"] += Decimal(str(context["tax_total"]))
    return context


@register.inclusion_tag("shop/includes/order_totals.html", takes_context=True)
def order_totals(context):
    """
    HTML version of order_totals.
    """
    return _order_totals(context)


@register.inclusion_tag("shop/includes/order_totals.txt", takes_context=True)
def order_totals_text(context):
    """
    Text version of order_totals.
    """
    return _order_totals(context)
