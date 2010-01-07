
import os
from copy import copy
from django import template
from django.conf import settings
from shop.models import Category


register = template.Library()


@register.inclusion_tag("shop/category_menu.html", takes_context=True)
def category_menu(context, parent_category=None):
	"""
	return a list of child categories for the given parent, storing all 
	categories in the context when first called for retrieval on subsequent 
	recursive calls from the menu template
	"""

	if "menu_cats" not in context:
		context["menu_cats"] = list(Category.objects.active())
	context["category_branch"] = [category for category in context["menu_cats"] 
		if category.parent == parent_category]
	return context

@register.filter
def money(value):
	"""
	format a value as money with dollar sign and two decimal places
	"""

	try:
		value = float(value)
	except:
		value = 0.
	return "$%.2f" % value

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
		image = ImageOps.fit(image, (width, height), 
			Image.ANTIALIAS).save(thumb_path, "JPEG", quality=100)
	except:
		return image_url
	return thumb_url

@register.inclusion_tag("shop/order_totals.html", takes_context=True)
def order_totals(context):
	"""
	add the cart and order totals to the context - if a shipping total has been 
	put into the session then add it to the context and the order total
	"""
	context["cart_total"] = context["order_total"] = context["cart"].total_price()
	if "shipping_total" in context["request"].session:
		context["shipping_total"] = context["request"].session["shipping_total"]
		context["order_total"] += context["shipping_total"]
	return context

