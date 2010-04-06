
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.forms import Form
from django.http import HttpResponseRedirect
from django.utils import simplejson
from django.utils.translation import ugettext as _

from shop.forms import OrderForm, get_add_product_form
from shop.checkout import billing_shipping, payment, initial_order_data, \
    send_order_email, CheckoutError, CHECKOUT_STEP_FIRST, CHECKOUT_STEP_LAST, \
    CHECKOUT_TEMPLATES
from shop.exceptions import PaymentError
from shop.models import Category, Product, ProductVariation, Cart
from shop.utils import set_cookie, send_mail_template, sign
from shop.settings import SEARCH_RESULTS_PER_PAGE, CHECKOUT_STEPS_SPLIT, CHECKOUT_STEPS_CONFIRMATION


# Fall back to authenticated-only messaging if messages app is unavailable.
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
        to_cart = len(request.POST.get("add_wishlist", "")) == 0
        add_product_form = AddProductForm(request.POST, to_cart=to_cart)
        if add_product_form.is_valid():
            if to_cart:
                Cart.objects.from_request(request).add_item(
                    add_product_form.variation, 
                    add_product_form.cleaned_data["quantity"])
                info(request, _("Item added to cart"), fail_silently=True)
                return HttpResponseRedirect(reverse("shop_cart"))
            else:
                skus = request.COOKIES.get("wishlist", "").split(",")
                sku = add_product_form.variation.sku
                if sku not in skus:
                    skus.append(sku)
                info(request, _("Item added to wishlist"), fail_silently=True)
                response = HttpResponseRedirect(reverse("shop_wishlist"))
                set_cookie(response, "wishlist", ",".join(skus))
                return response
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
    results = paginate(Product.objects.active().search(query), 
        request.GET.get("page", 1), SEARCH_RESULTS_PER_PAGE)
    return render_to_response(template, {"query": query, "results": results},
        RequestContext(request))
    
def wishlist(request, template="shop/wishlist.html"):
    """
    display wishlist - handle removing items and adding to cart
    """
    skus = request.COOKIES.get("wishlist", "").split(",")
    error = None
    if request.method == "POST":
        sku = request.POST.get("sku", None)
        to_cart = len(request.POST.get("add_cart", "")) > 0
        if to_cart:
            quantity = 1
            try:
                variation = ProductVariation.objects.get(sku=sku)
            except ProductVariation:
                error = _("This item is no longer available")
            else:
                if not variation.has_stock(quantity):
                    error = _("This item is currently out of stock")
                else:
                    Cart.objects.from_request(request).add_item(variation, quantity)
        if error is None:
            if sku in skus:
                skus.remove(sku)
            if to_cart:
                info(request, _("Item add to cart"), fail_silently=True)
                response = HttpResponseRedirect(reverse("shop_cart"))
            else:
                info(request, _("Item removed from wishlist"), fail_silently=True)
                response = HttpResponseRedirect(reverse("shop_wishlist"))
            set_cookie(response, "wishlist", ",".join(skus))
            return response
    return render_to_response(template, {"error": error}, RequestContext(request))

def cart(request, template="shop/cart.html"):
    """
    display cart - handle removing items
    """
    if request.method == "POST":
        Cart.objects.from_request(request).remove_item(
            request.POST.get("item_id", ""))
        info(request, _("Item removed from cart"), fail_silently=True)
        return HttpResponseRedirect(reverse("shop_cart"))
    return render_to_response(template, {}, RequestContext(request))

def checkout(request):
    """
    Display the order form and handle processing of each step.
    """
    step = int(request.POST.get("step", CHECKOUT_STEP_FIRST))
    initial = initial_order_data(request)
    form = OrderForm(request, step, initial=initial)
    data = request.POST

    if request.POST.get("back", ""):
        step -= 1
        form = OrderForm(request, step, initial=initial)
    elif request.method == "POST":
        form = OrderForm(request, step, initial=initial, data=data)
        if form.is_valid():
            checkout_errors = []
            request.session["order"] = dict(form.cleaned_data)
            for field in ("card_number", "card_expiry_month", 
                "card_expiry_year", "card_ccv"):
                del request.session["order"][field]

            # Handle shipping and discount code on first step.
            if step == CHECKOUT_STEP_FIRST:
                try:
                    billing_shipping(request, form)
                except CheckoutError, e:
                    checkout_errors.append(e)
                if hasattr(form, "discount"):
                    cart = Cart.objects.from_request(request)
                    discount_total = discount.calculate(cart.total_price())
                    request.session["free_shipping"] = discount.free_shipping
                    request.session["discount_total"] = discount_total

            # Process order on final step.
            if step == CHECKOUT_STEP_LAST and not checkout_errors:
                try:
                    payment(request, form)
                except CheckoutError, e:
                    checkout_errors.append(e)
                    if CHECKOUT_STEPS_CONFIRMATION:
                        step -= 1
                else:    
                    order = form.save(commit=False)
                    order.process(request)
                    send_order_email(request, order)
                    response = HttpResponseRedirect(reverse("shop_complete"))
                    if form.cleaned_data.get("remember", False):
                        remembered = "%s:%s" % (sign(order.key), order.key)
                        set_cookie(response, "remember", remembered, 
                            secure=request.is_secure())
                    else:
                        response.delete_cookie("remember")
                    return response

            # Assign checkout errors to new form if any and re-run is_valid 
            # if valid set form to next step.
            form = OrderForm(request, step, initial=initial, data=data)
            form.checkout_errors = checkout_errors
            if form.is_valid():
                step += 1
                form = OrderForm(request, step, initial=initial)
            
    template = "shop/%s.html" % CHECKOUT_TEMPLATES[step - 1]
    return render_to_response(template, {"form": form, 
        "CHECKOUT_STEPS_SPLIT": CHECKOUT_STEPS_SPLIT, 
        "CHECKOUT_STEP_FIRST": step == CHECKOUT_STEP_FIRST}, 
        RequestContext(request))

def complete(request, template="shop/complete.html"):
    """
    order completed
    """
    return render_to_response(template, {}, RequestContext(request))

