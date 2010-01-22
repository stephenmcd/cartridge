
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils import simplejson

from shop.models import Category, Product, ProductVariation, Cart
from shop.forms import get_add_cart_form, OrderForm


def category(request, slug, template="shop/category.html"):
	"""
	display a category
	"""
	category = get_object_or_404(Category.objects.active(), slug=slug)
	return render_to_response(template, {"category": category}, 
		RequestContext(request))
	
def product(request, slug, template="shop/product.html"):
	"""
	display a product - redirect to cart if product added
	"""
	product = get_object_or_404(Product.objects.active().select_related(), 
		slug=slug)
	AddCartForm = get_add_cart_form(product)
	add_cart_form = AddCartForm(initial={"quantity": 1})
	if request.method == "POST":
		add_cart_form = AddCartForm(request.POST)
		if add_cart_form.is_valid():
			Cart.objects.from_request(request).add_item(add_cart_form.variation, 
				add_cart_form.cleaned_data["quantity"])
			return HttpResponseRedirect(reverse("shop_cart"))
	variations = product.variations.all()
	variations_json = simplejson.dumps(list(variations.values("sku", "image",
		*[f.name for f in ProductVariation.option_fields()]))) 
	return render_to_response(template, {"product": product, "variations_json":
		variations_json, "variations": variations, "images": product.images.all(),
		"add_cart_form": add_cart_form}, RequestContext(request))

def cart(request, template="shop/cart.html"):
	"""
	display cart - handle removing items
	"""
	if request.method == "POST":
		Cart.objects.from_request(request).remove_item(request.POST.get("sku", ""))
		return HttpResponseRedirect(reverse("shop_cart"))
	return render_to_response(template, {}, RequestContext(request))

def complete(request, template="shop/complete.html"):
	"""
	order completed
	"""
	return render_to_response(template, {}, RequestContext(request))

