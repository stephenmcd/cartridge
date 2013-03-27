from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.contrib.messages import info
from django.core.urlresolvers import get_callable, reverse
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.template.loader import get_template
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache

from mezzanine.conf import settings
from mezzanine.utils.importing import import_dotted_path
from mezzanine.utils.views import render, set_cookie, paginate

from cartridge.shop import checkout
from cartridge.shop.forms import AddProductForm, DiscountForm, CartItemFormSet
from cartridge.shop.models import Product, ProductVariation, Order, OrderItem
from cartridge.shop.models import DiscountCode
from cartridge.shop.utils import recalculate_discount, sign


# Set up checkout handlers.
handler = lambda s: import_dotted_path(s) if s else lambda *args: None
billship_handler = handler(settings.SHOP_HANDLER_BILLING_SHIPPING)
tax_handler = handler(settings.SHOP_HANDLER_TAX)
payment_handler = handler(settings.SHOP_HANDLER_PAYMENT)
order_handler = handler(settings.SHOP_HANDLER_ORDER)


def product(request, slug, template="shop/product.html"):
    """
    Display a product - convert the product variations to JSON as well as
    handling adding the product to either the cart or the wishlist.
    """
    published_products = Product.objects.published(for_user=request.user)
    product = get_object_or_404(published_products, slug=slug)
    fields = [f.name for f in ProductVariation.option_fields()]
    variations = product.variations.all()
    variations_json = simplejson.dumps([dict([(f, getattr(v, f))
                                        for f in fields + ["sku", "image_id"]])
                                        for v in variations])
    to_cart = (request.method == "POST" and
               request.POST.get("add_wishlist") is None)
    initial_data = {}
    if variations:
        initial_data = dict([(f, getattr(variations[0], f)) for f in fields])
    initial_data["quantity"] = 1
    add_product_form = AddProductForm(request.POST or None, product=product,
                                      initial=initial_data, to_cart=to_cart)
    if request.method == "POST":
        if add_product_form.is_valid():
            if to_cart:
                quantity = add_product_form.cleaned_data["quantity"]
                request.cart.add_item(add_product_form.variation, quantity)
                recalculate_discount(request)
                info(request, _("Item added to cart"))
                return redirect("shop_cart")
            else:
                skus = request.wishlist
                sku = add_product_form.variation.sku
                if sku not in skus:
                    skus.append(sku)
                info(request, _("Item added to wishlist"))
                response = redirect("shop_wishlist")
                set_cookie(response, "wishlist", ",".join(skus))
                return response
    context = {
        "product": product,
        "editable_obj": product,
        "images": product.images.all(),
        "variations": variations,
        "variations_json": variations_json,
        "has_available_variations": any([v.has_price() for v in variations]),
        "related_products": product.related_products.published(
                                                      for_user=request.user),
        "add_product_form": add_product_form
    }
    return render(request, template, context)


@never_cache
def wishlist(request, template="shop/wishlist.html"):
    """
    Display the wishlist and handle removing items from the wishlist and
    adding them to the cart.
    """

    skus = request.wishlist
    error = None
    if request.method == "POST":
        to_cart = request.POST.get("add_cart")
        add_product_form = AddProductForm(request.POST or None,
                                          to_cart=to_cart)
        if to_cart:
            if add_product_form.is_valid():
                request.cart.add_item(add_product_form.variation, 1)
                recalculate_discount(request)
                message = _("Item added to cart")
                url = "shop_cart"
            else:
                error = add_product_form.errors.values()[0]
        else:
            message = _("Item removed from wishlist")
            url = "shop_wishlist"
        sku = request.POST.get("sku")
        if sku in skus:
            skus.remove(sku)
        if not error:
            info(request, message)
            response = redirect(url)
            set_cookie(response, "wishlist", ",".join(skus))
            return response

    # Remove skus from the cookie that no longer exist.
    published_products = Product.objects.published(for_user=request.user)
    f = {"product__in": published_products, "sku__in": skus}
    wishlist = ProductVariation.objects.filter(**f).select_related(depth=1)
    wishlist = sorted(wishlist, key=lambda v: skus.index(v.sku))
    context = {"wishlist_items": wishlist, "error": error}
    response = render(request, template, context)
    if len(wishlist) < len(skus):
        skus = [variation.sku for variation in wishlist]
        set_cookie(response, "wishlist", ",".join(skus))
    return response


@never_cache
def cart(request, template="shop/cart.html"):
    """
    Display cart and handle removing items from the cart.
    """
    cart_formset = CartItemFormSet(instance=request.cart)
    discount_form = DiscountForm(request, request.POST or None)
    if request.method == "POST":
        valid = True
        if request.POST.get("update_cart"):
            valid = request.cart.has_items()
            if not valid:
                # Session timed out.
                info(request, _("Your cart has expired"))
            else:
                cart_formset = CartItemFormSet(request.POST,
                                               instance=request.cart)
                valid = cart_formset.is_valid()
                if valid:
                    cart_formset.save()
                    recalculate_discount(request)
                    info(request, _("Cart updated"))
        else:
            valid = discount_form.is_valid()
            if valid:
                discount_form.set_discount()
        if valid:
            return redirect("shop_cart")
    context = {"cart_formset": cart_formset}
    settings.use_editable()
    if (settings.SHOP_DISCOUNT_FIELD_IN_CART and
        DiscountCode.objects.active().count() > 0):
        context["discount_form"] = discount_form
    return render(request, template, context)


@never_cache
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
        return redirect(url)

    # Determine the Form class to use during the checkout process
    form_class = get_callable(settings.SHOP_CHECKOUT_FORM_CLASS)

    initial = checkout.initial_order_data(request, form_class)
    step = int(request.POST.get("step", None)
               or initial.get("step", None)
               or checkout.CHECKOUT_STEP_FIRST)
    form = form_class(request, step, initial=initial)
    data = request.POST
    checkout_errors = []

    if request.POST.get("back") is not None:
        # Back button in the form was pressed - load the order form
        # for the previous step and maintain the field values entered.
        step -= 1
        form = form_class(request, step, initial=initial)
    elif request.method == "POST" and request.cart.has_items():
        form = form_class(request, step, initial=initial, data=data)
        if form.is_valid():
            # Copy the current form fields to the session so that
            # they're maintained if the customer leaves the checkout
            # process, but remove sensitive fields from the session
            # such as the credit card fields so that they're never
            # stored anywhere.
            request.session["order"] = dict(form.cleaned_data)
            sensitive_card_fields = ("card_number", "card_expiry_month",
                                     "card_expiry_year", "card_ccv")
            for field in sensitive_card_fields:
                if field in request.session["order"]:
                    del request.session["order"][field]

            # FIRST CHECKOUT STEP - handle shipping and discount code.
            if step == checkout.CHECKOUT_STEP_FIRST:
                try:
                    billship_handler(request, form)
                    tax_handler(request, form)
                except checkout.CheckoutError, e:
                    checkout_errors.append(e)
                form.set_discount()

            # FINAL CHECKOUT STEP - handle payment and process order.
            if step == checkout.CHECKOUT_STEP_LAST and not checkout_errors:
                # Create and save the initial order object so that
                # the payment handler has access to all of the order
                # fields. If there is a payment error then delete the
                # order, otherwise remove the cart items from stock
                # and send the order receipt email.
                order = form.save(commit=False)
                order.setup(request)
                # Try payment.
                try:
                    transaction_id = payment_handler(request, form, order)
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
                    order.transaction_id = transaction_id
                    order.complete(request)
                    order_handler(request, form, order)
                    checkout.send_order_email(request, order)
                    # Set the cookie for remembering address details
                    # if the "remember" checkbox was checked.
                    response = redirect("shop_complete")
                    if form.cleaned_data.get("remember"):
                        remembered = "%s:%s" % (sign(order.key), order.key)
                        set_cookie(response, "remember", remembered,
                                   secure=request.is_secure())
                    else:
                        response.delete_cookie("remember")
                    return response

            # If any checkout errors, assign them to a new form and
            # re-run is_valid. If valid, then set form to the next step.
            form = form_class(request, step, initial=initial, data=data,
                              errors=checkout_errors)
            if form.is_valid():
                step += 1
                form = form_class(request, step, initial=initial)

    # Update the step so that we don't rely on POST data to take us back to
    # the same point in the checkout process.
    try:
        request.session["order"]["step"] = step
        request.session.modified = True
    except KeyError:
        pass

    step_vars = checkout.CHECKOUT_STEPS[step - 1]
    template = "shop/%s.html" % step_vars["template"]
    CHECKOUT_STEP_FIRST = step == checkout.CHECKOUT_STEP_FIRST
    context = {"form": form, "CHECKOUT_STEP_FIRST": CHECKOUT_STEP_FIRST,
               "step_title": step_vars["title"], "step_url": step_vars["url"],
               "steps": checkout.CHECKOUT_STEPS, "step": step}
    return render(request, template, context)


@never_cache
def complete(request, template="shop/complete.html"):
    """
    Redirected to once an order is complete - pass the order object
    for tracking items via Google Anayltics, and displaying in
    the template if required.
    """
    try:
        order = Order.objects.from_request(request)
    except Order.DoesNotExist:
        raise Http404
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
    context = {"order": order, "items": items,
               "steps": checkout.CHECKOUT_STEPS}
    return render(request, template, context)


def invoice(request, order_id, template="shop/order_invoice.html"):
    """
    Display a plain text invoice for the given order. The order must
    belong to the user which is checked via session or ID if
    authenticated, or if the current user is staff.
    """
    lookup = {"id": order_id}
    if not request.user.is_authenticated():
        lookup["key"] = request.session.session_key
    elif not request.user.is_staff:
        lookup["user_id"] = request.user.id
    order = get_object_or_404(Order, **lookup)
    context = {"order": order}
    context.update(order.details_as_dict())
    context = RequestContext(request, context)
    if request.GET.get("format") == "pdf":
        response = HttpResponse(mimetype="application/pdf")
        name = slugify("%s-invoice-%s" % (settings.SITE_TITLE, order.id))
        response["Content-Disposition"] = "attachment; filename=%s.pdf" % name
        html = get_template(template).render(context)
        import ho.pisa
        ho.pisa.CreatePDF(html, response)
        return response
    return render(request, template, context)


@login_required
def order_history(request, template="shop/order_history.html"):
    """
    Display a list of the currently logged-in user's past orders.
    """
    all_orders = Order.objects.filter(user_id=request.user.id)
    orders = paginate(all_orders.order_by('-time'),
                      request.GET.get("page", 1),
                      settings.SHOP_PER_PAGE_CATEGORY,
                      settings.MAX_PAGING_LINKS)
    # Add the total quantity to each order - this can probably be
    # replaced with fetch_related and Sum when we drop Django 1.3
    order_quantities = defaultdict(int)
    for item in OrderItem.objects.filter(order__user_id=request.user.id):
        order_quantities[item.order_id] += item.quantity
    for order in orders.object_list:
        setattr(order, "quantity_total", order_quantities[order.id])
    context = {"orders": orders}
    return render(request, template, context)
