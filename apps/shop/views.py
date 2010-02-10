
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import HttpResponseRedirect
from django.utils import simplejson
from django.utils.translation import ugettext as _

from shop.models import Category, Product, ProductVariation, Cart
from shop.forms import get_add_product_form, OrderForm
from shop.settings import SEARCH_RESULTS_PER_PAGE


try:
	from django.contrib.messages import info 
except ImportError:
	def info(request, message, fail_silently=True):
		if request.user.is_authenticated():
			request.user.message_set.create(message=message)

def paginate(objects, page_num, per_page):
	"""
	pagination 
	"""
	paginator = Paginator(objects, per_page)
	try:
		page_num = int(page_num)
	except ValueError:
		page_num = 1
	try:
		objects = paginator.page(page_num)
	except (EmptyPage, InvalidPage):
		objects = paginator.page(paginator.num_pages)
	return objects


def category(request, slug, template="shop/category.html"):
	"""
	display a category
	"""
	category = get_object_or_404(Category.objects.active(), slug=slug)
	return render_to_response(template, {"category": category}, 
		RequestContext(request))

def product(request, slug, template="shop/product.html"):
	"""
	display a product - redirect to wishlist or cart if product added to either
	"""
	product = get_object_or_404(Product.objects.active(slug=slug))
	AddProductForm = get_add_product_form(product)
	add_product_form = AddProductForm(initial={"quantity": 1})
	if request.method == "POST":
		add_product_form = AddProductForm(request.POST)
		if add_product_form.is_valid():
			Cart.objects.from_request(request).add_item(add_product_form.variation, 
				add_product_form.cleaned_data["quantity"])
			info(request, _("Item added to cart"), fail_silently=True)
			return HttpResponseRedirect(reverse("shop_cart"))
	variations = product.variations.all()
	variations_json = simplejson.dumps([dict([(f, getattr(v, f)) for f in 
		["sku", "image_id"] + [f.name for f in ProductVariation.option_fields()]]) 
		for v in variations])
	return render_to_response(template, {"product": product, "variations_json":
		variations_json, "variations": variations, "images": product.images.all(),
		"add_product_form": add_product_form}, RequestContext(request))

def search(request, template="shop/search_results.html"):
	"""
	display product search results
	"""
	query = request.REQUEST.get("query", "")
	results = paginate(Product.objects.search(query), request.GET.get("page", 1), 
		SEARCH_RESULTS_PER_PAGE)
	return render_to_response(template, {"query": query, "results": results},
		RequestContext(request))
	
def wishlist(request, template="shop/wishlist.html"):
	"""
	display wishlist - handle removing items
	"""
	skus = request.COOKIES.get("wishlist", "").split(",")
	if request.method == "POST":
		sku = request.POST.get("sku", "")
		if sku in skus:
			skus.remove(sku)
		info(request, _("Item removed from wishlist"), fail_silently=True)
		response = HttpResponseRedirect(reverse("shop_wishlist"))
		return set_wishlist(response, skus)
	variations = []
	if "wishlist" in request.COOKIES:
		variations = ProductVariations.objects.filter(product__active=True,
			sku__in=skus).select_related()
		variations.sort(key=lambda v: skus.index(v.sku))
	return render_to_response(template, {"wishlist": variations}, 
		RequestContext(request))

def cart(request, template="shop/cart.html"):
	"""
	display cart - handle removing items
	"""
	if request.method == "POST":
		Cart.objects.from_request(request).remove_item(request.POST.get("sku", ""))
		info(request, _("Item removed from cart"), fail_silently=True)
		return HttpResponseRedirect(reverse("shop_cart"))
	return render_to_response(template, {}, RequestContext(request))

def complete(request, template="shop/complete.html"):
	"""
	order completed
	"""
	return render_to_response(template, {}, RequestContext(request))

