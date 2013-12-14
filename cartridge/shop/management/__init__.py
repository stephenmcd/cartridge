from __future__ import print_function
from __future__ import unicode_literals
from future.builtins import input

import sys

from django.conf import settings
from django.core.management import call_command
from django.db.models.signals import post_syncdb

from mezzanine.utils.tests import copy_test_to_media

from cartridge.shop.models import Product
from cartridge.shop import models as shop_app


def create_product(app, created_models, verbosity, interactive, **kwargs):
    if Product in created_models:
        call_command("loaddata", "cartridge_required.json")
        if interactive:
            confirm = input("\nWould you like to install an initial "
                                "demo product and sale? (yes/no): ")
            while True:
                if confirm == "yes":
                    break
                elif confirm == "no":
                    return
                confirm = input("Please enter either 'yes' or 'no': ")
        # This is a hack. Ideally to split fixtures between optional
        # and required, we'd use the same approach Mezzanine does,
        # within a ``createdb`` management command. Ideally to do this,
        # we'd subclass Mezzanine's createdb command and shadow it,
        # but to do that, the cartridge.shop app would need to appear
        # *after* mezzanine.core in the INSTALLED_APPS setting, but the
        # reverse is needed for template overriding (and probably other
        # bits) to work correctly.
        # SO........... we just cheat, and check sys.argv here. Namaste.
        elif "--nodata" in sys.argv:
            return
        if verbosity >= 1:
            print()
            print("Creating demo product and sale ...")
            print()
        call_command("loaddata", "cartridge_optional.json")
        copy_test_to_media("cartridge.shop", "product")


if not settings.TESTING:
    post_syncdb.connect(create_product, sender=shop_app)
