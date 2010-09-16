
from mezzanine.pages.page_processors import processor_for

from cartridge.shop.models import Category
from cartridge.shop.settings import PER_PAGE_CATEGORY
from cartridge.shop.views import product_list


@processor_for(Category)
def category_processor(request, page):
    """
    Add paging/sorting to the products for the category.
    """
    products = page.category.products.all()
    return {"products": product_list(products, request, PER_PAGE_CATEGORY)}

