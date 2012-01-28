
from django.conf import settings
from django.core.management import call_command
from django.db.models.signals import post_syncdb

from mezzanine.utils.tests import copy_test_to_media

from cartridge.shop.models import Product
from cartridge.shop import models as shop_app


def create_initial_product(app, created_models, verbosity, **kwargs):
    if settings.DEBUG and Product in created_models:
        if kwargs.get("interactive"):
            confirm = raw_input("\nWould you like to install an initial "
                                "Category and Product? (yes/no): ")
            while True:
                if confirm == "yes":
                    break
                elif confirm == "no":
                    return
                confirm = raw_input("Please enter either 'yes' or 'no': ")
        if verbosity >= 1:
            print
            print "Creating initial Category and Product ..."
            print
        call_command("loaddata", "cartridge.json")
        copy_test_to_media("cartridge.shop", "product")


post_syncdb.connect(create_initial_product, sender=shop_app)
