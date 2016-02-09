
from __future__ import unicode_literals
from future.builtins import str

from decimal import Decimal
import locale
import platform

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
    value = locale.currency(Decimal(value), grouping=True)
    if platform.system() == 'Windows':
        try:
            value = str(value, encoding=locale.getpreferredencoding())
        except TypeError:
            pass
    return value


def _order_totals(context):
    """
    Add shipping/tax/discount/order types and totals to the template
    context. Use the context's completed order object for email
    receipts, or the cart object for checkout.
    """
    fields = ["shipping_type", "shipping_total", "discount_total",
              "tax_type", "tax_total"]
    template_vars = {}

    if "order" in context:
        for field in fields + ["item_total"]:
            template_vars[field] = getattr(context["order"], field)
    else:
        template_vars["item_total"] = context["request"].cart.total_price()
        if template_vars["item_total"] == 0:
            # Ignore session if cart has no items, as cart may have
            # expired sooner than the session.
            template_vars["tax_total"] = 0
            template_vars["discount_total"] = 0
            template_vars["shipping_total"] = 0
        else:
            for field in fields:
                template_vars[field] = context["request"].session.get(
                    field, None)
    template_vars["order_total"] = template_vars.get("item_total", None)
    if template_vars.get("shipping_total", None) is not None:
        template_vars["order_total"] += Decimal(
            str(template_vars["shipping_total"]))
    if template_vars.get("discount_total", None) is not None:
        template_vars["order_total"] -= Decimal(
            str(template_vars["discount_total"]))
    if template_vars.get("tax_total", None) is not None:
        template_vars["order_total"] += Decimal(
            str(template_vars["tax_total"]))
    return template_vars


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
