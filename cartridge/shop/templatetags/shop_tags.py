
import locale
from urllib import quote

from django import template
from django.template.defaultfilters import slugify

from mezzanine.conf import settings

from cartridge.shop.utils import set_locale


register = template.Library()


@register.filter
def currency(value):
    """
    Format a value as currency according to locale.
    """
    set_locale()
    if len(str(value)) == 0:
        value = 0
    if hasattr(locale, "currency"):
        value = locale.currency(value)
    else:
        # based on locale.currency() in python >= 2.5
        conv = locale.localeconv()
        value = [conv["currency_symbol"], conv["p_sep_by_space"] and " "  or "", 
            (("%%.%sf" % conv["frac_digits"]) % value).replace(".", 
            conv["mon_decimal_point"])]
        if not conv["p_cs_precedes"]:
            value.reverse()
        value = "".join(value)
    return value


def _order_totals(context):
    """
    Add ``item_total``, ``shipping_total``, ``discount_total`` and 
    ``order_total`` to the include context. use the order object for email 
    receipts, or the cart object for checkout.
    """
    if "order" in context:
        context["item_total"] = context["order"].total
        context["shipping_total"] = context["order"].shipping_total
        context["discount_total"] = context["order"].discount_total
    elif "cart" in context:
        context["item_total"] = context["cart"].total_price()
        if context["item_total"] == 0:
            # ignore session if cart has no items as cart may have expired
            # sooner than session
            context["discount_total"] = context["shipping_total"] = 0
        else:
            context["shipping_total"] = context["request"].session.get(
                "shipping_total", None)
            context["discount_total"] = context["request"].session.get(
                "discount_total", None)
    context["order_total"] = context.get("item_total", None)
    if context.get("shipping_total", None) is not None:
        context["order_total"] += context["shipping_total"]
    if context.get("discount_total", None) is not None:
        context["order_total"] -= context["discount_total"]
    return context


@register.inclusion_tag("shop/order_totals.html", takes_context=True)
def order_totals(context):
    """
    HTML version of order_totals.
    """
    return _order_totals(context)

    
@register.inclusion_tag("shop/order_totals.txt", takes_context=True)
def order_totals_text(context):
    """
    Text version of order_totals.
    """
    return _order_totals(context)


@register.inclusion_tag("shop/product_sorting.html", takes_context=True)
def product_sorting(context, products):
    """
    Renders the links for each product sort option.
    """
    sort_options = [(option[0], slugify(option[0])) for option in 
                                        settings.SHOP_PRODUCT_SORT_OPTIONS]
    querystring = context["request"].REQUEST.get("query", "")
    if querystring:
        querystring = "&query=" + quote(querystring)
    else:
        del sort_options[0]
    context.update({"selected_option": getattr(products, "sort"), 
                    "sort_options": sort_options, "querystring": querystring})
    return context


@register.inclusion_tag("shop/product_paging.html", takes_context=True)
def product_paging(context, products):
    """
    Renders the links for each page number in a paginated list of products.
    """
    settings = context["settings"]
    querystring = ""
    for name in ("query", "sort"):
        value = context["request"].REQUEST.get(name)
        if value is not None:
            querystring += "&%s=%s" % (name, quote(value))
    page_range = products.paginator.page_range
    page_links = settings.SHOP_MAX_PAGING_LINKS
    if len(page_range) > page_links:
        start = min(products.paginator.num_pages - page_links, 
            max(0, products.number - (page_links / 2) - 1))
        page_range = page_range[start:start + page_links]
    context.update({"products": products, "querystring": querystring, 
                    "page_range": page_range})
    return context
