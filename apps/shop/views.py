
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from shop.models import Category, Product, Order
from shop.forms import get_add_cart_form, OrderForm
from shop.cart import Cart


def category(request, slugs, template="shop/category.html"):

	category = get_object_or_404(Category.objects.active(), 
		slug=slugs.split("/")[-1])
	return render_to_response(template, {"category": category}, 
		RequestContext(request))
	
def product(request, slugs, template="shop/product.html"):

	product = get_object_or_404(Product.objects.active(), 
		slug=slugs.split("/")[-1])
	AddCartForm = get_add_cart_form(product)
	add_cart_form = AddCartForm(initial={"quantity": 1})
	if request.method == "POST":
		add_cart_form = AddCartForm(request.POST)
		if add_cart_form.is_valid():
			Cart(request).add_item(product, add_cart_form.cleaned_data)
			return HttpResponseRedirect(reverse("shop_cart"))
	return render_to_response(template, {"product": product, 
		"add_cart_form": add_cart_form}, RequestContext(request))

def cart(request, template="shop/cart.html"):

	if request.method == "POST":
		Cart(request).remove_item(request.POST.get("sku", ""))
		return HttpResponseRedirect(reverse("shop_cart"))
	return render_to_response(template, {}, RequestContext(request))

def complete(request, template="shop/complete.html"):

	return render_to_response(template, {}, RequestContext(request))

