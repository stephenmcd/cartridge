
import os
import locale
from collections import defaultdict
from urllib import quote

from django import template
from django.conf import settings
from django.template.defaultfilters import slugify
from django.utils.datastructures import SortedDict

from cartridge.shop.models import Category
from cartridge.shop.utils import set_locale
from cartridge.shop.settings import CHECKOUT_STEPS_SPLIT, \
    PRODUCT_SORT_OPTIONS, MAX_PAGING_LINKS


register = template.Library()


@register.filter
def currency(value):
    """
    format a value as currency according to locale
    """
    set_locale()
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

@register.simple_tag
def thumbnail(image_url, width, height):
    """
    given the url to an image, resizes the image using the given width and 
    height on the first time it is requested, and returns the url to the new 
    resized image. if width or height are zero then original ratio is maintained
    """
    
    image_url = unicode(image_url)
    image_path = os.path.join(settings.MEDIA_ROOT, image_url)
    image_dir, image_name = os.path.split(image_path)
    thumb_name = "%s-%sx%s.jpg" % (os.path.splitext(image_name)[0], width, height)
    thumb_path = os.path.join(image_dir, thumb_name)
    thumb_url = "%s/%s" % (os.path.dirname(image_url), thumb_name)

    # abort if thumbnail exists, original image doesn't exist, invalid width or 
    # height are given, or PIL not installed
    if not image_url:
        return ""
    if os.path.exists(thumb_path):
        return thumb_url
    try:
        width = int(width)
        height = int(height)
    except ValueError:
        return image_url
    if not os.path.exists(image_path) or (width == 0 and height == 0):
        return image_url
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return image_url

    # open image, determine ratio if required and resize/crop/save
    image = Image.open(image_path)
    if width == 0:
        width = image.size[0] * height / image.size[1]
    elif height == 0:
        height = image.size[1] * width / image.size[0]
    if image.mode not in ("L", "RGB"):
        image = image.convert("RGB")
    try:
        image = ImageOps.fit(image, (width, height), Image.ANTIALIAS).save(
            thumb_path, "JPEG", quality=100)
    except:
        return image_url
    return thumb_url

def _order_totals(context):
    """
    add item_total, shipping_total, discount and order_total to the include 
    context. use the order object for email receipts, or the cart object for 
    checkout
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
    sort_options = [(o[0], slugify(o[0])) for o in PRODUCT_SORT_OPTIONS]
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
    querystring = ""
    for name in ("query", "sort"):
        value = context["request"].REQUEST.get(name)
        if value is not None:
            querystring += "&%s=%s" % (name, quote(value))
    page_range = products.paginator.page_range
    if len(page_range) > MAX_PAGING_LINKS:
        start = min(products.paginator.num_pages - MAX_PAGING_LINKS, 
            max(0, products.number - (MAX_PAGING_LINKS / 2) - 1))
        page_range = page_range[start:start + MAX_PAGING_LINKS]
    context.update({"products": products, "querystring": querystring, 
        "page_range": page_range})
    return context
