from __future__ import print_function

import csv
import os
import shutil
import datetime

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.utils.translation import ugettext as _
from django.db.utils import IntegrityError
from mezzanine.conf import settings

from cartridge.shop.models import Product
from cartridge.shop.models import ProductOption
from cartridge.shop.models import ProductImage
from cartridge.shop.models import ProductVariation
from cartridge.shop.models import Category
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED


# images get copied from thie directory
LOCAL_IMAGE_DIR = "/tmp/orig"
# images get copied to this directory under STATIC_ROOT
IMAGE_SUFFIXES = [".jpg", ".JPG", ".jpeg", ".JPEG", ".tif", ".gif", ".GIF",
                  ".png", ".PNG"]
EMPTY_IMAGE_ENTRIES = ["Please add", "N/A", ""]
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"

# Here we define what column headings are used in the csv.
TITLE = _("Title")
CONTENT = _("Content")
DESCRIPTION = _("Description")
SKU = _("SKU")
IMAGE = _("Image")
CATEGORY = _("Category")
SUB_CATEGORY = _("Sub-Category")
# SIZE = _("Size")
NUM_IN_STOCK = _("Number in Stock")
UNIT_PRICE = _("Unit Price")
SALE_PRICE = _("Sale Price")
SALE_START_DATE = _("Sale Start Date")
SALE_START_TIME = _("Sale Start Time")
SALE_END_DATE = _("Sale End Date")
SALE_END_TIME = _("Sale End Time")

DATETIME_FORMAT = "%s %s" % (DATE_FORMAT, TIME_FORMAT)
SITE_MEDIA_IMAGE_DIR = _("product")
PRODUCT_IMAGE_DIR = os.path.join(settings.STATIC_ROOT, SITE_MEDIA_IMAGE_DIR)
TYPE_CHOICES = dict()
for id, choice in settings.SHOP_OPTION_TYPE_CHOICES:
    TYPE_CHOICES[choice] = id

fieldnames = [TITLE, CONTENT, DESCRIPTION, CATEGORY, SUB_CATEGORY,
    SKU, IMAGE, NUM_IN_STOCK, UNIT_PRICE,
    SALE_PRICE, SALE_START_DATE, SALE_START_TIME, SALE_END_DATE, SALE_END_TIME]
# TODO: Make sure no options conflict with other fieldnames.
fieldnames += list(TYPE_CHOICES.keys())


class Command(BaseCommand):
    help = _('Import/Export products from a csv file.')

    def add_arguments(self, parser):
        parser.add_argument("csv_file")
        parser.add_argument(
            '--import',
            action='store_true',
            dest='import',
            default=False,
            help=_('Import products from csv file.')
        )

        parser.add_argument(
            '--export',
            action='store_true',
            dest='export',
            default=False,
            help=_('Export products from csv file.')
        )

    def handle(self, *args, **options):
        csv_file = options.get('csv_file')
        if options["import"] and options["export"]:
            raise CommandError("can't both import and export")
        if not options["import"] and not options["export"]:
            raise CommandError(_("need to import or export"))
        if options['import']:
            import_products(csv_file)
        elif options['export']:
            export_products(csv_file)


def _product_from_row(row):
    product, created = Product.objects.get_or_create(title=row[TITLE])
    product.content = row[CONTENT]
    product.description = row[DESCRIPTION]
    # TODO: set the 2 below from spreadsheet.
    product.status = CONTENT_STATUS_PUBLISHED
    product.available = True
    # TODO: allow arbitrary level/number of categories.
    base_cat, created = Category.objects.get_or_create(title=row[CATEGORY])
    sub_cat, created = Category.objects.get_or_create(
        title=row[SUB_CATEGORY],
        parent=base_cat)
    product.categories.add(sub_cat)
    shop_cat, created = Category.objects.get_or_create(title="Shop")
    product.categories.add(shop_cat)
    return product


def _make_image(image_str, product):
    if image_str in EMPTY_IMAGE_ENTRIES:
        return None
    # try adding various image suffixes, if none given in original filename.
    root, suffix = os.path.splitext(image_str)
    if suffix not in IMAGE_SUFFIXES:
        raise CommandError("INCORRECT SUFFIX: %s" % image_str)
    image_path = os.path.join(LOCAL_IMAGE_DIR, image_str)
    if not os.path.exists(image_path):
        raise CommandError("NO FILE %s" % image_path)
    shutil.copy(image_path, PRODUCT_IMAGE_DIR)
    # shutil.copy(image_path, os.path.join(PRODUCT_IMAGE_DIR, "orig"))
    image, created = ProductImage.objects.get_or_create(
        file="%s" % (os.path.join(SITE_MEDIA_IMAGE_DIR, image_str)),
        description=image_str,  # TODO: handle column for this.
        product=product)
    return image


def _make_date(date_str, time_str):
    date_string = '%s %s' % (date_str, time_str)
    date = datetime.datetime.strptime(date_string, DATETIME_FORMAT)
    return date


def import_products(csv_file):
    print(_("Importing .."))
    # More appropriate for testing.
    # Product.objects.all().delete()
    reader = csv.DictReader(open(csv_file), delimiter=',')
    for row in reader:
        print(row)
        product = _product_from_row(row)
        try:
            variation = ProductVariation.objects.create(
                # strip whitespace
                sku=row[SKU].replace(" ", ""),
                product=product,
            )
        except IntegrityError:
            raise CommandError("Product with SKU exists! sku: %s" % row[SKU])
        if row[NUM_IN_STOCK]:
            variation.num_in_stock = row[NUM_IN_STOCK]
        if row[UNIT_PRICE]:
            variation.unit_price = row[UNIT_PRICE]
        if row[SALE_PRICE]:
            variation.sale_price = row[SALE_PRICE]
        if row[SALE_START_DATE] and row[SALE_START_TIME]:
            variation.sale_from = _make_date(row[SALE_START_DATE],
                                                row[SALE_START_TIME])
        if row[SALE_END_DATE] and row[SALE_END_TIME]:
            variation.sale_to = _make_date(row[SALE_END_DATE],
                                                row[SALE_END_TIME])
        for option in TYPE_CHOICES:
            if row[option]:
                name = "option%s" % TYPE_CHOICES[option]
                setattr(variation, name, row[option])
                new_option, created = ProductOption.objects.get_or_create(
                    type=TYPE_CHOICES[option],  # TODO: set dynamically
                    name=row[option])
        variation.save()
        image = _make_image(row[IMAGE], product)
        if image:
            variation.image = image
        product.variations.manage_empty()
        product.variations.set_default_images([])
        product.copy_default_variation()
        product.save()

    print("Variations: %s" % ProductVariation.objects.all().count())
    print("Products: %s" % Product.objects.all().count())


def export_products(csv_file):
    print(_("Exporting .."))
    filehandle = open(csv_file, 'w')
    writer = csv.DictWriter(filehandle, delimiter=',', fieldnames=fieldnames)
    headers = dict()
    for field in fieldnames:
        headers[field] = field
    writer.writerow(headers)
    for pv in ProductVariation.objects.all():
        row = dict()
        row[TITLE] = pv.product.title
        row[CONTENT] = pv.product.content
        row[DESCRIPTION] = pv.product.description
        row[SKU] = pv.sku
        row[IMAGE] = pv.image
        # TODO: handle multiple categories, and multiple levels of categories
        cat = pv.product.categories.all()[0]
        if cat.parent:
            row[SUB_CATEGORY] = cat.title
            row[CATEGORY] = cat.parent.title
        else:
            row[CATEGORY] = cat.title
            row[SUB_CATEGORY] = ""

        for option in TYPE_CHOICES:
            row[option] = getattr(pv, "option%s" % TYPE_CHOICES[option])

        row[NUM_IN_STOCK] = pv.num_in_stock
        row[UNIT_PRICE] = pv.unit_price
        row[SALE_PRICE] = pv.sale_price
        try:
            row[SALE_START_DATE] = pv.sale_from.strftime(DATE_FORMAT)
            row[SALE_START_TIME] = pv.sale_from.strftime(TIME_FORMAT)
        except AttributeError:
            pass
        try:
            row[SALE_END_DATE] = pv.sale_to.strftime(DATE_FORMAT)
            row[SALE_END_TIME] = pv.sale_to.strftime(TIME_FORMAT)
        except AttributeError:
            pass
        writer.writerow(row)
    filehandle.close()
