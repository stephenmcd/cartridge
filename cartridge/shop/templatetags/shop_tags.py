
from decimal import Decimal
import locale

from django import template

from cartridge.shop.utils import set_locale


register = template.Library()


@register.filter
def currency(value):
    """
    Format a value as currency according to locale.
    """
    set_locale()
    if not value:
        value = 0
    if hasattr(locale, "currency"):
        value = locale.currency(value)
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
    Add ``item_total``, ``shipping_total``, ``discount_total`` and
    ``order_total`` to the template context. Use the order object for
    email receipts, or the cart object for checkout.
    """
    if "order" in context:
        for f in ("item_total", "shipping_total", "discount_total"):
            context[f] = getattr(context["order"], f)
    else:
        context["item_total"] = context["request"].cart.total_price()
        if context["item_total"] == 0:
            # Ignore session if cart has no items, as cart may have
            # expired sooner than the session.
            context["discount_total"] = context["shipping_total"] = 0
        else:
            for f in ("shipping_type", "shipping_total", "discount_total"):
                context[f] = context["request"].session.get(f, None)
    context["order_total"] = context.get("item_total", None)
    if context.get("shipping_total", None) is not None:
        context["order_total"] += Decimal(str(context["shipping_total"]))
    if context.get("discount_total", None) is not None:
        context["order_total"] -= context["discount_total"]
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
