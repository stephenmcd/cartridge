
from decimal import Decimal
from operator import mul

from django.core.urlresolvers import reverse
from django.test import TestCase

from mezzanine.conf import settings
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
from mezzanine.utils.tests import run_pyflakes_for_package

from cartridge.shop.models import Product, ProductOption, ProductVariation
from cartridge.shop.models import Category, Cart


class ShopTests(TestCase):

    def setUp(self):
        published = {"status": CONTENT_STATUS_PUBLISHED}
        self._category = Category.objects.create(**published)
        self._product = Product.objects.create(**published)
        for option_type in settings.SHOP_OPTION_TYPE_CHOICES:
            for i in range(10):
                name = "test%s" % i
                ProductOption.objects.create(type=option_type[0], name=name)

    def test_views(self):
        """
        Test the main shop views for errors.
        """
        # Category.
        response = self.client.get(self._category.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        # Product.
        response = self.client.get(self._product.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        # Cart.
        response = self.client.get(reverse("shop_cart"))
        self.assertEqual(response.status_code, 200)
        # Checkout.
        response = self.client.get(reverse("shop_checkout"))
        self.assertEqual(response.status_code, 200 if not 
            settings.SHOP_CHECKOUT_ACCOUNT_REQUIRED else 302)
        # Login.
        if settings.SHOP_CHECKOUT_ACCOUNT_ENABLED:
            response = self.client.get(reverse("shop_account"))
            self.assertEqual(response.status_code, 200)

    def test_variations(self):
        """
        Test creation of variations from options, and management of empty 
        variations.
        """
        product_options = ProductOption.objects.as_fields()
        total_variations = reduce(mul, [len(values) 
            for values in product_options.values()])
        # Clear variations.
        self._product.variations.all().delete()
        self.assertEqual(self._product.variations.count(), 0)
        # Create single empty variation.
        self._product.variations.manage_empty()
        self.assertEqual(self._product.variations.count(), 1)
        # Create variations from all options.
        self._product.variations.create_from_options(product_options)
        # Should do nothing.
        self._product.variations.create_from_options(product_options)
        # All options plus empty.
        self.assertEqual(self._product.variations.count(), total_variations + 1)
        # Remove empty.
        self._product.variations.manage_empty()
        self.assertEqual(self._product.variations.count(), total_variations)

    def test_stock(self):
        """
        Test stock checking on product variations.
        """
        self._product.variations.all().delete()
        self._product.variations.manage_empty()
        num_in_stock = 10
        variation = self._product.variations.all()[0]
        variation.num_in_stock = num_in_stock
        # Check stock field not in use.
        self.assertTrue(variation.has_stock())
        # Check available and unavailable quantities.
        self.assertTrue(variation.has_stock(num_in_stock))
        self.assertFalse(variation.has_stock(num_in_stock + 1))
        # Check sold out.
        variation = self._product.variations.all()[0]
        variation.num_in_stock = 0
        self.assertFalse(variation.has_stock())

    def test_cart(self):
        """
        Test the cart object and cart add/remove forms.
        """
        product_options = ProductOption.objects.as_fields()
        self._product.variations.all().delete()
        self._product.variations.create_from_options(product_options)
        price = Decimal("20")
        num_in_stock = 5
        variation = self._product.variations.all()[0]
        variation.unit_price = price
        variation.num_in_stock = num_in_stock * 2
        variation.save()

        # Test initial cart.
        cart = Cart.objects.from_request(self.client)
        self.assertFalse(cart.has_items())
        self.assertEqual(cart.total_quantity(), 0)
        self.assertEqual(cart.total_price(), Decimal("0"))

        # Add quantity and check stock levels / cart totals.
        data = dict(zip([field.name for field in 
            ProductVariation.option_fields()], variation.options()))
        data["quantity"] = num_in_stock
        self.client.post(self._product.get_absolute_url(), data)
        cart = Cart.objects.from_request(self.client)
        variation = self._product.variations.all()[0]
        self.assertTrue(variation.has_stock(num_in_stock))
        self.assertFalse(variation.has_stock(num_in_stock * 2))
        self.assertTrue(cart.has_items())
        self.assertEqual(cart.total_quantity(), num_in_stock)
        self.assertEqual(cart.total_price(), price * num_in_stock)

        # Add remaining quantity and check again.
        self.client.post(self._product.get_absolute_url(), data)
        cart = Cart.objects.from_request(self.client)
        variation = self._product.variations.all()[0]
        self.assertFalse(variation.has_stock())
        self.assertTrue(cart.has_items())
        self.assertEqual(cart.total_quantity(), num_in_stock * 2)
        self.assertEqual(cart.total_price(), price * num_in_stock * 2)

        # Remove from cart.
        for item in cart:
            self.client.post(reverse("shop_cart"), {"item_id": item.id})
        cart = Cart.objects.from_request(self.client)
        variation = self._product.variations.all()[0]
        self.assertTrue(variation.has_stock(num_in_stock * 2))
        self.assertFalse(cart.has_items())
        self.assertEqual(cart.total_quantity(), 0)
        self.assertEqual(cart.total_price(), Decimal("0"))

    def test_with_pyflakes(self):
        """
        Run pyflakes across the code base to check for potential errors.
        """
        ignore = ("redefinition of unused 'digest'", 
                  "redefinition of unused 'info'")
        warnings = run_pyflakes_for_package("cartridge", extra_ignore=ignore)
        if warnings:
            warnings.insert(0, "pyflakes warnings:")
            self.fail("\n".join(warnings))
