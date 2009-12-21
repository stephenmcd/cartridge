
import os
from django import template
from django.conf import settings
from shop.models import Category


register = template.Library()


@register.inclusion_tag("shop/category_menu.html", takes_context=True)
def category_menu(context, parent_category=None):
	if "category_menu_categories" not in context:
		context["category_menu_categories"] = Category.objects.active().select_related(depth=1)
	category_branch = []
	for category in context["category_menu_categories"]:
		if category.parent == parent_category:
			category_branch.append(category)
	return {"category_branch": category_branch}

@register.filter
def money(value):
	try:
		value = float(value)
	except:
		value = 0.
	return "$%.2f" % value

@register.simple_tag
def thumbnail(image_url, width=0, height=0):
	
	image_path = os.path.join(settings.MEDIA_ROOT, unicode(image_url))
	try:
		width = int(width)
		height = int(height)
	except ValueError:
		return image_url
	if not os.path.exists(image_path) or (height == 0 and width == 0):
		return image_url
	try:
		from PIL import Image
	except ImportError:
		return image_url

	image = Image.open(image_path)
	crop = False
	if width == 0:
		width = image.size[0] * height / image.size[1]
	elif height == 0:
		height = image.size[1] * width / image.size[0]
	else:
		crop = True
	if image.mode not in ("L", "RGB"):
		image = image.convert("RGB")
	image_dir, image_name = os.path.split(image_path)
	thumb_name = "%s-%sx%s.jpg" % (os.path.splitext(image_name)[0], width, height)
	try:
		image = image.resize((width, height), Image.ANTIALIAS)
		#if crop:
		#	image = image.crop((x1, y1, x2, y2))
		image.save(os.path.join(image_dir, thumb_name), "JPEG")
	except:
		return image_url
	return "%s/%s" % (os.path.dirname(unicode(image_url)), thumb_name)

def breadcrumb_menu():
	pass
#	categories = sorted(Category.objects.filter(slug__in=slugs), 
#		key=slugs.index)

