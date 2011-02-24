import csv
import sys
import os
import shutil

# images get copied from thie directory
LOCAL_IMAGE_DIR = "/tmp/orig"
# images get copied to this directory under MEDIA_ROOT
IMAGE_SUFFIXES = [".jpg", ".JPG", ".jpeg", ".JPEG", ".tif"]
EMPTY_IMAGE_ENTRIES = ["Please add", "N/A", ""]

# setup sys.path
# assumes script is in subdirectory. e.g. scripts/Import.py
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_DIR)
sys.path.insert(0, os.path.join(PROJECT_DIR, 'apps'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from cartridge.shop.models import Product
from cartridge.shop.models import ProductOption
from cartridge.shop.models import ProductImage
from cartridge.shop.models import ProductVariation
from cartridge.shop.models import Category
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
from django.conf import settings

SITE_MEDIA_IMAGE_DIR = "product"
PRODUCT_IMAGE_DIR = os.path.join(settings.MEDIA_ROOT, SITE_MEDIA_IMAGE_DIR)
# Here we define what column headings are used in the csv.
TITLE = "Title"
DESCRIPTION = "Description"
SKU = "SKU"
IMAGE = "Image"
CATEGORY = "Category"
SUB_CATEGORY = "Sub-Category"
SIZE = "Size"


def _product_from_row(row):
    product, created = Product.objects.get_or_create(title=row[TITLE])
    product.content = row[DESCRIPTION]
    # TODO: set the 2 below from spreadsheet.
    product.status = CONTENT_STATUS_PUBLISHED
    product.available = True
    # TODO: allow arbitrary level/number of categories.
    base_cat, created = Category.objects.get_or_create(title=row[CATEGORY])
    sub_cat, created = Category.objects.get_or_create(
        title=row[SUB_CATEGORY],
        parent=base_cat)
    shop_cat, created = Category.objects.get_or_create(title="Shop")
    product.categories.add(shop_cat)
    product.categories.add(sub_cat)
    return product


def _add_image(image_str, product):
    if image_str in EMPTY_IMAGE_ENTRIES:
        return None
    elif image_str.endswith(".pdf"):
        return None
    # try adding various image suffixes, if none given in original filename.
    elif not "." in image_str:
        found = False
        for suffix in IMAGE_SUFFIXES:
            myfile = os.path.join(LOCAL_IMAGE_DIR, image_str + suffix)
            print "trying: %s" % myfile
            if os.path.exists(myfile):
                image_str += suffix
                found = True
                break
        if not found:
            print "gNO FILE %s" % image_str
            sys.exit(1)
    image_path = os.path.join(LOCAL_IMAGE_DIR, image_str)
    if not os.path.exists(image_path):
        print "NO FILE %s" % image_path
        sys.exit(1)
    shutil.copy(image_path, PRODUCT_IMAGE_DIR)
    #shutil.copy(image_path, os.path.join(PRODUCT_IMAGE_DIR, "orig"))
    image, created = ProductImage.objects.get_or_create(
        file="%s" % (os.path.join(SITE_MEDIA_IMAGE_DIR, image_str)),
        description=image_str,  # TODO: handle column for this.
        product=product)
    return image

if __name__ == '__main__':
    try:
        infile = sys.argv[1]
    except IndexError:
        print "Please provide csv file to import"
        sys.exit(1)
    # More appropriate for testing.
    #Product.objects.all().delete()
    reader = csv.DictReader(open(infile), delimiter=',')
    for row in reader:
        print row
        product = _product_from_row(row)
        variation = ProductVariation.objects.create(
            # strip whitespace
            sku=row[SKU].replace(" ", ""),
            product=product,
        )
        variation.option1 = row[SIZE]
        variation.save()
        option, created = ProductOption.objects.get_or_create(
            type=1,  # TODO: set dynamically
            name=row[SIZE])
        image = _add_image(row[IMAGE], product)
        if image:
            variation.image = image
        product.variations.manage_empty()
        product.copy_default_variation()
        product.save()

    print "Variations: %s" % ProductVariation.objects.all().count()
    print "Products: %s" % Product.objects.all().count()
