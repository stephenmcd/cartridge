
from shop.models import ProductVariation, Cart

def shop_globals(request):
    """
    make the cart object and wishlist items globally available 
    """
    wishlist = []
    skus = request.COOKIES.get("wishlist", "").split(",")
    if skus:
        wishlist = list(ProductVariation.objects.filter(product__active=True,
            sku__in=skus).select_related())
        wishlist.sort(key=lambda v: skus.index(v.sku))
    return {"wishlist": wishlist, "cart": Cart.objects.from_request(request)}

