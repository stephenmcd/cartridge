
import os
import locale

from django import template
from django.conf import settings

from shop.models import Category
from shop.utils import set_locale


register = template.Library()


def _category_menu(context, parent_category, category_qs):
	"""
	return a list of child categories for the given parent, storing all 
	categories in a dict in the context when first called using parents as keys 
	for retrieval on subsequent recursive calls from the menu template
	"""
	if "menu_cats" not in context:
		categories = {}
		for category in category_qs:
			if category.parent not in categories:
				categories[category.parent] = []
			categories[category.parent].append(category)
		context["menu_cats"] = categories
	context["category_branch"] = context["menu_cats"].get(parent_category, [])
	return context

@register.inclusion_tag("shop/category_menu.html", takes_context=True)
def category_menu(context, parent_category=None):
	"""
	public shop category menu
	"""
	return _category_menu(context, parent_category, Category.objects.active())

@register.inclusion_tag("admin/shop/category/category_menu.html", 
	takes_context=True)
def category_menu_admin(context, parent_category=None):
	"""
	admin category menu
	"""
	return _category_menu(context, parent_category, Category.objects.all())

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

@register.inclusion_tag("shop/order_totals.html", takes_context=True)
def order_totals(context, text_only=False):
	"""
	add item_total, shipping_total and order_total to the include context.
	use the order object for email receipts, or the cart object for checkout
	"""
	context["text_only"] = text_only
	if "order" in context:
		context["item_total"] = context["order"].total
		context["shipping_total"] = context["order"].shipping_total
	elif "cart" in context:
		context["item_total"] = context["cart"].total_price()
		context["shipping_total"] = context["request"].session.get(
			"shipping_total", None)
	context["order_total"] = context.get("item_total", None)
	if context.get("shipping_total", None) is not None:
		context["order_total"] += context["shipping_total"]
	return context

