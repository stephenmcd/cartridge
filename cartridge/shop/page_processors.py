
from mezzanine.pages.page_processors import processor_for
from mezzanine.conf import settings

from cartridge.shop.models import Category, Product
from cartridge.shop.views import product_list


@processor_for(Category)
def category_processor(request, page):
    """
    Add paging/sorting to the products for the category.
    """
    settings.use_editable()
    per_page = settings.SHOP_PER_PAGE_CATEGORY
    published_products = Product.objects.published(for_user=request.user)
    filters = page.category.filters()
    products = published_products.filter(filters).distinct()
    return {"products": product_list(products, request, per_page)}
