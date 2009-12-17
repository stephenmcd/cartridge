
from django import template
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

def breadcrumb_menu():
	pass
#	categories = sorted(Category.objects.filter(slug__in=slugs), 
#		key=slugs.index)

