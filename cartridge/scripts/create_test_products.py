#!/usr/bin/env python

"""
Stand-alone data generation routine that uses the ecommerce taxonomy found on
Google Base to generate a significant amount of category and product data, as
well as using the Flickr API to retrieve images for the products. The
multiprocessing module is also used for parallelization.

The Django models and environment used here are specific to the Cartridge
project but the approach could easily be reused with any ecommerce database.
"""

import sys
import os
path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(path, "..", ".."))
os.environ["DJANGO_SETTINGS_MODULE"] = "cartridge.project_template.settings"

from multiprocessing import Process, Queue
from os.path import exists, join
from shutil import move
from sys import exit
from urllib import urlopen, urlretrieve

from django.contrib.webdesign.lorem_ipsum import paragraph
from django.db import connection
from django.db.models import F

from mezzanine.conf import settings
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED

from cartridge.shop.models import Category, Product, ProductOption


try:
    import flickr
except ImportError:
    print "flickr.py must be installed from http://code.google.com/p/flickrpy/"
    exit()

WORKERS = 10
image_dir = join(settings.STATIC_ROOT, "product")
queue = Queue()
product_options = {"Size": ("Small", "Medium", "Large"),
    "Colour": ("Red", "Orange", "Yellow", "Green", "Blue", "Indigo", "Violet")}


def create_products(queue):
    """
    Download an image from Flickr for the product on the queue and if
    successful now or previously, create the applicable product records.
    """

    # Close the connection for this process to avoid the issue discussed here:
    # http://groups.google.com/group/django-users/
    # browse_thread/thread/2c7421cdb9b99e48
    connection.close()
    product_options = ProductOption.objects.as_fields()
    while True:

        # Get next set of data from queue.
        data = queue.get()
        if data is None:
            break
        main_category, sub_category, product = data[0], data[1], data[-1]

        # Try and download a product image from Flickr.
        image = join(image_dir, "%s.jpg" % product)
        if exists(image):
            message = "Using already downloaded image for %s" % data
        else:
            try:
                images = flickr.photos_search(tags=[product], per_page=1)
                if not images:
                    raise Exception("No images found")
                url = images[0].getURL(size="Large", urlType="source")
                urlretrieve(url, image)
            except Exception, e:
                message = "Error [%s] for %s" % (e, data)
            else:
                message = "Successfully downloaded image for %s" % data
        remaining = "%s remaining" % queue.qsize()
        print remaining.ljust(20, "."), message

        # Create database records for the product.
        if exists(image):
            product = Category.objects.get(parent__title=main_category,
                title=sub_category).products.create(title=product,
                available=True, status=CONTENT_STATUS_PUBLISHED,
                content="<p>%s</p>" % paragraph())
            image = "product/%s.jpg" % product.title
            product.images.create(file=image)
            product.variations.create_from_options(product_options)
            product.variations.manage_empty()
            product.variations.update(unit_price=F("id") + "10000")
            product.variations.update(unit_price=F("unit_price") / "1000.0")
            product.copy_default_variation()

if __name__ == "__main__":

    # Load the Google Base data.
    category_url = "http://www.google.com/basepages/producttype/taxonomy.txt"
    try:
        category_data = urlopen(category_url).read()
    except Exception, e:
        print "Failed to load category data: %s" % e
        exit()

    # Clear out the database, moving the product images to a temp location and
    # restoring them so that they're not deleted.
    print "Resetting product options"
    ProductOption.objects.all().delete()
    for type, name in settings.SHOP_OPTION_TYPE_CHOICES:
        for name in product_options[unicode(name)]:
            ProductOption.objects.create(type=type, name=name)

    Category.objects.all().delete()
    print "Deleting categories"
    Category.objects.all().delete()
    print "Backing up images"
    move(image_dir, "tmp_products")
    print "Deleting products"
    Product.objects.all().delete()
    print "Restoring images"
    move("tmp_products", image_dir)

    # Parse the category data into triples of main category, sub category and
    # product, create the categories and put the triples onto the queue. The
    # categories must be created here in a single process due to the non-atomic
    # nature of Django's Model.objects.get_or_create()
    print "Creating categories"
    for line in category_data.split("\n"):
        parts = line.split(" > ")
        if len(parts) > 2:
            if len(parts) == 3:
                main_category, created = Category.objects.get_or_create(
                    title=parts[0], status=CONTENT_STATUS_PUBLISHED)
                sub_category, created = Category.objects.get_or_create(
                    title=parts[1], status=CONTENT_STATUS_PUBLISHED,
                    parent=main_category)
                queue.put(parts)

    # Create worker processes and run the main function in them.
    workers = []
    for _ in range(WORKERS):
        queue.put(None)
        workers.append(Process(target=create_products, args=(queue,)))
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
