
from mezzanine.pages.page_processors import processor_for
from mezzanine.settings import load_settings

from cartridge.shop.models import Category
from cartridge.shop.views import product_list


@processor_for(Category)
def category_processor(request, page):
    """
    Add paging/sorting to the products for the category.
    """
    products = page.category.products.all()
    mezz_settings = load_settings("PER_PAGE_CATEGORY")
    return {"products": product_list(products, request, 
        mezz_settings.PER_PAGE_CATEGORY)}
