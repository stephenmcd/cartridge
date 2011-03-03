
from django.contrib.auth import logout as auth_logout
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.utils import simplejson
from django.utils.translation import ugettext as _

from mezzanine.conf import settings
from mezzanine.utils.importing import import_dotted_path
from mezzanine.utils.views import render_to_response

from cartridge.shop import checkout
from cartridge.shop.forms import OrderForm, LoginForm, SignupForm
from cartridge.shop.forms import get_add_product_form
from cartridge.shop.models import Product, ProductVariation, Cart, Order
from cartridge.shop.utils import set_cookie, set_shipping, sign


# Set up checkout handlers.
handler = lambda s: import_dotted_path(s) if s else lambda *args: None
billship_handler = handler(settings.SHOP_HANDLER_BILLING_SHIPPING)
payment_handler = handler(settings.SHOP_HANDLER_PAYMENT)
order_handler = handler(settings.SHOP_HANDLER_ORDER)

# Fall back to authenticated-only messaging if messages app is unavailable.
try:
    from django.contrib.messages import info 
except ImportError:
    def info(request, message, fail_silently=True):
        if request.user.is_authenticated():
            request.user.message_set.create(message=message)


def product_list(products, request, per_page):
    """
    Handle pagination and sorting for the given products.
    """
    sort_options = settings.SHOP_PRODUCT_SORT_OPTIONS
    sort_options = [(slugify(o[0]), o[1]) for o in sort_options]
    if "query" not in request.REQUEST:
        del sort_options[0]
    sort_name = request.GET.get("sort", sort_options[0][0])
    sort_value = dict(sort_options).get(sort_name)
    if sort_value is not None:
        products = products.order_by(sort_value)
    paginator = Paginator(products, per_page)
    try:
        page_num = int(request.GET.get("page", 1))
    except ValueError:
        page_num = 1
    try:
        products = paginator.page(page_num)
    except (EmptyPage, InvalidPage):
        products = paginator.page(paginator.num_pages)
    products.sort = sort_name
    return products


def product(request, slug, template="shop/product.html"):
    """
    Display a product - convert the product variations to JSON as well as 
    handling adding the product to either the cart or the wishlist.
    """
    published_products = Product.objects.published(for_user=request.user)
    product = get_object_or_404(published_products, slug=slug)
    AddProductForm = get_add_product_form(product)
    add_product_form = AddProductForm(initial={"quantity": 1})
    if request.method == "POST":
        to_cart = request.POST.get("add_wishlist") is None
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
    # Build variations JSON from list of variation dicts.
    fields = [f.name for f in ProductVariation.option_fields()]
    fields.extend(["sku", "image_id"])
    variations = []
    variations_json = []
    has_available_variations = False
    for variation in product.variations.all():
        if not has_available_variations and variation.has_price():
            has_available_variations = True
        variations.append(variation)
        variation_dict = dict([(f, getattr(variation, f)) for f in fields])
        variations_json.append(variation_dict)
    variations_json = simplejson.dumps(variations_json)
    related = product.related_products.published(for_user=request.user)
    context = {"product": product, "images": list(product.images.all()), 
               "variations": variations, "variations_json": variations_json,
               "has_available_variations": has_available_variations,
               "related_products": list(related),
               "add_product_form": add_product_form}
    return render_to_response(template, context, RequestContext(request))


def search(request, template="shop/search_results.html"):
    """
    Display product search results.
    """
    settings.use_editable()
    query = request.REQUEST.get("query", "")
    results = Product.objects.published_for(user=request.user).search(query)
    results = product_list(results, request, settings.SHOP_PER_PAGE_SEARCH)
    context = {"query": query, "results": results}
    return render_to_response(template, context, RequestContext(request))

    
def wishlist(request, template="shop/wishlist.html"):
    """
    Display the wishlist and handle removing items from the wishlist and 
    adding them to the cart.
    """

    skus = request.COOKIES.get("wishlist", "").split(",")
    error = None
    if request.method == "POST":
        sku = request.POST.get("sku")
        to_cart = request.POST.get("add_cart") is not None
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
                    cart = Cart.objects.from_request(request)
                    cart.add_item(variation, quantity)
        if error is None:
            if sku in skus:
                skus.remove(sku)
            if to_cart:
                message = _("Item added to cart")
                response = HttpResponseRedirect(reverse("shop_cart"))
            else:
                message = _("Item removed from wishlist")
                response = HttpResponseRedirect(reverse("shop_wishlist"))
            info(request, message, fail_silently=True)
            set_cookie(response, "wishlist", ",".join(skus))
            return response

    # Remove skus from the cookie that no longer exist.
    published_products = Product.objects.published(for_user=request.user)
    f = {"product__in": published_products, "sku__in": skus}
    wishlist = ProductVariation.objects.filter(**f).select_related(depth=1)
    wishlist = sorted(wishlist, key=lambda v: skus.index(v.sku))
    context = {"wishlist": wishlist, "error": error}
    response = render_to_response(template, context, RequestContext(request))
    if len(wishlist) < len(skus):
        skus = [variation.sku for variation in wishlist]
        set_cookie(response, "wishlist", ",".join(skus))
    return response


def cart(request, template="shop/cart.html"):
    """
    Display cart and handle removing items from the cart.
    """
    if request.method == "POST":
        cart = Cart.objects.from_request(request)
        cart.remove_item(request.POST.get("item_id"))
        info(request, _("Item removed from cart"), fail_silently=True)
        return HttpResponseRedirect(reverse("shop_cart"))
    return render_to_response(template, {}, RequestContext(request))


def account(request, template="shop/account.html"):
    """
    Display and handle both the login and signup forms.
    """
    login_form = LoginForm()
    signup_form = SignupForm()
    if request.method == "POST":
        posted_form = None
        message = ""
        if request.POST.get("login") is not None:
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                posted_form = login_form
                message = _("Successfully logged in")
        else:
            signup_form = SignupForm(request.POST)
            if signup_form.is_valid():
                signup_form.save()
                posted_form = signup_form
                message = _("Successfully signed up")
        if posted_form is not None:
            posted_form.login(request)
            info(request, message, fail_silently=True)
            return HttpResponseRedirect(request.GET.get("next", "/"))
    context = {"login_form": login_form, "signup_form": signup_form}
    return render_to_response(template, context, RequestContext(request))


def logout(request):
    """
    Log the user out.
    """
    auth_logout(request)
    info(request, _("Successfully logged out"), fail_silently=True)
    return HttpResponseRedirect(request.GET.get("next", "/"))


def checkout_steps(request):
    """
    Display the order form and handle processing of each step.
    """
    
    # Do the authentication check here rather than using standard 
    # login_required decorator. This means we can check for a custom 
    # LOGIN_URL and fall back to our own login view.
    authenticated = request.user.is_authenticated()
    if settings.SHOP_CHECKOUT_ACCOUNT_REQUIRED and not authenticated:
        url = "%s?next=%s" % (settings.LOGIN_URL, reverse("shop_checkout"))
        return HttpResponseRedirect(url)
    
    step = int(request.POST.get("step", checkout.CHECKOUT_STEP_FIRST))
    initial = checkout.initial_order_data(request)
    form = OrderForm(request, step, initial=initial)
    data = request.POST
    checkout_errors = []

    if request.POST.get("back") is not None:
        # Back button was pressed - load the order form for the 
        # previous step and maintain the field values entered.
        step -= 1
        form = OrderForm(request, step, initial=initial)
    elif request.method == "POST":
        form = OrderForm(request, step, initial=initial, data=data)
        if form.is_valid():
            # Copy the current form fields to the session so that 
            # they're maintained if the customer leaves the checkout 
            # process, but remove sensitive fields from the session 
            # such as the cart number so that they're never stored 
            # anywhere.
            request.session["order"] = dict(form.cleaned_data)
            sensitive_card_fields = ("card_number", "card_expiry_month", 
                                     "card_expiry_year", "card_ccv")
            for field in sensitive_card_fields:
                del request.session["order"][field]

            # FIRST CHECKOUT STEP - handle shipping and discount code.
            if step == checkout.CHECKOUT_STEP_FIRST:
                try:
                    billship_handler(request, form)
                except checkout.CheckoutError, e:
                    checkout_errors.append(e)
                # The order form gets assigned a discount attribute 
                # when the discount_code field is validated via 
                # clean_discount_code()
                discount = getattr(form, "discount", None)
                if discount is not None:
                    cart = Cart.objects.from_request(request)
                    discount_total = discount.calculate(cart.total_price())
                    if discount.free_shipping:
                        set_shipping(request, _("Free shipping"), 0)
                    request.session["free_shipping"] = discount.free_shipping
                    request.session["discount_total"] = discount_total

            # FINAL CHECKOUT STEP - handle payment and process order.
            if step == checkout.CHECKOUT_STEP_LAST and not checkout_errors:
                # Create and save the inital order object so that 
                # the payment handler has access to all of the order 
                # fields. If there is a payment error then delete the 
                # order, otherwise remove the cart items from stock 
                # and send the order reciept email.
                order = form.save(commit=False)
                order.setup(request)
                # Try payment.
                try:
                    payment_handler(request, form, order)
                except checkout.CheckoutError, e:
                    # Error in payment handler.
                    order.delete()
                    checkout_errors.append(e)
                    if settings.SHOP_CHECKOUT_STEPS_CONFIRMATION:
                        step -= 1
                else:
                    # Finalize order - ``order.complete()`` performs 
                    # final cleanup of session and cart. 
                    # ``order_handler()`` can be defined by the 
                    # developer to implement custom order processing.
                    # Then send the order email to the customer.
                    order.complete(request)
                    order_handler(request, form, order)
                    checkout.send_order_email(request, order)
                    # Set the cookie for remembering address details 
                    # if the "remember" checkbox was checked.
                    response = HttpResponseRedirect(reverse("shop_complete"))
                    if form.cleaned_data.get("remember") is not None:
                        remembered = "%s:%s" % (sign(order.key), order.key)
                        set_cookie(response, "remember", remembered, 
                                   secure=request.is_secure())
                    else:
                        response.delete_cookie("remember")
                    return response

            # If any checkout errors, assign them to a new form and 
            # re-run is_valid. If valid, then set form to the next step.
            form = OrderForm(request, step, initial=initial, data=data, 
                             errors=checkout_errors)
            if form.is_valid():
                step += 1
                form = OrderForm(request, step, initial=initial)
    
    step_vars = checkout.CHECKOUT_STEPS[step - 1]
    template = "shop/%s.html" % step_vars["template"]
    CHECKOUT_STEP_FIRST = step == checkout.CHECKOUT_STEP_FIRST
    context = {"form": form, "CHECKOUT_STEP_FIRST": CHECKOUT_STEP_FIRST, 
               "step_title": step_vars["title"], "step_url": step_vars["url"], 
               "steps": checkout.CHECKOUT_STEPS, "step": step}
    return render_to_response(template, context, RequestContext(request))


def complete(request, template="shop/complete.html"):
    """
    Redirected to once an order is complete - pass the order object 
    for tracking items via Google Anayltics, and displaying in 
    the template if required.
    """
    order = Order.objects.from_request(request)
    items = order.items.all()
    # Assign product names to each of the items since they're not 
    # stored.
    skus = [item.sku for item in items]
    variations = ProductVariation.objects.filter(sku__in=skus)
    names = {}
    for variation in variations.select_related(depth=1):
        names[variation.sku] = variation.product.title
    for i, item in enumerate(items):
        setattr(items[i], "name", names[item.sku])
    context = {"order": order, "items": items}
    return render_to_response(template, context, RequestContext(request))
