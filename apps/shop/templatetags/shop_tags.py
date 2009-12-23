
import os
from django import template
from django.conf import settings
from shop.models import Category


register = template.Library()


@register.inclusion_tag("shop/category_menu.html", takes_context=True)
def category_menu(context, parent_category=None):
	"""
	return a list of child categories for the given parent, storing all 
	categories in the context when first called for retrieval on subsequent 
	recursive calls when building a category tree at the template level
	"""
	if "category_menu_categories" not in context:
		context["category_menu_categories"] = Category.objects.active(
			).select_related(depth=1)
	category_branch = []
	for category in context["category_menu_categories"]:
		if category.parent == parent_category:
			category_branch.append(category)
	return {"category_branch": category_branch}

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
def thumbnail(image_url, width=0, height=0):
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
		image = ImageOps.fit(image, (width, height)).save(thumb_path, "JPEG")
	except:
		return image_url
	return thumb_url

def breadcrumb_menu():
	pass
#	categories = sorted(Category.objects.filter(slug__in=slugs), 
#		key=slugs.index)

