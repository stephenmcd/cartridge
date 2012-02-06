
from datetime import datetime, timedelta
from decimal import Decimal
from operator import mul

from django.core.urlresolvers import reverse
from django.test import TestCase
from mezzanine.conf import settings
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
from mezzanine.utils.tests import run_pyflakes_for_package
from mezzanine.utils.tests import run_pep8_for_package

from cartridge.shop.models import Product, ProductOption, ProductVariation
from cartridge.shop.models import Category, Cart, Order, DiscountCode
from cartridge.shop.checkout import CHECKOUT_STEPS


TEST_STOCK = 5
TEST_PRICE = Decimal("20")


class ShopTests(TestCase):

    def setUp(self):
        """
        Set up test data - category, product and options.
        """
        self._published = {"status": CONTENT_STATUS_PUBLISHED}
        self._category = Category.objects.create(**self._published)
        self._product = Product.objects.create(**self._published)
        for option_type in settings.SHOP_OPTION_TYPE_CHOICES:
            for i in range(10):
                name = "test%s" % i
                ProductOption.objects.create(type=option_type[0], name=name)
        self._options = ProductOption.objects.as_fields()

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

    def test_variations(self):
        """
        Test creation of variations from options, and management of empty
        variations.
        """
        total = reduce(mul, [len(v) for v in self._options.values()])
        # Clear variations.
        self._product.variations.all().delete()
        self.assertEqual(self._product.variations.count(), 0)
        # Create single empty variation.
        self._product.variations.manage_empty()
        self.assertEqual(self._product.variations.count(), 1)
        # Create variations from all options.
        self._product.variations.create_from_options(self._options)
        # Should do nothing.
        self._product.variations.create_from_options(self._options)
        # All options plus empty.
        self.assertEqual(self._product.variations.count(), total + 1)
        # Remove empty.
        self._product.variations.manage_empty()
        self.assertEqual(self._product.variations.count(), total)

    def test_stock(self):
        """
        Test stock checking on product variations.
        """
        self._product.variations.all().delete()
        self._product.variations.manage_empty()
        variation = self._product.variations.all()[0]
        variation.num_in_stock = TEST_STOCK
        # Check stock field not in use.
        self.assertTrue(variation.has_stock())
        # Check available and unavailable quantities.
        self.assertTrue(variation.has_stock(TEST_STOCK))
        self.assertFalse(variation.has_stock(TEST_STOCK + 1))
        # Check sold out.
        variation = self._product.variations.all()[0]
        variation.num_in_stock = 0
        self.assertFalse(variation.has_stock())

    def assertCategoryFilteredProducts(self, num_products):
        """
        Tests the number of products returned by the category's
        current filters.
        """
        products = Product.objects.filter(self._category.filters())
        self.assertEqual(products.distinct().count(), num_products)

    def test_category_filters(self):
        """
        Test the category filters returns expected results.
        """
        self._product.variations.all().delete()
        self.assertCategoryFilteredProducts(0)

        # Test option filters - add a variation with one option, and
        # assign another option as a category filter. Check that no
        # products match the filters, then add the first option as a
        # category filter and check that the product is matched.
        option_field, options = self._options.items()[0]
        option1, option2 = options[:2]
        # Variation with the first option.
        self._product.variations.create_from_options({option_field: [option1]})
        # Filter with the second option
        option = ProductOption.objects.get(type=option_field[-1], name=option2)
        self.assertCategoryFilteredProducts(0)
        # First option as a filter.
        option = ProductOption.objects.get(type=option_field[-1], name=option1)
        self._category.options.add(option)
        self.assertCategoryFilteredProducts(1)

        # Test price filters - add a price filter that when combined
        # with previously created filters, should match no products.
        # Update the variations to match the filter for a unit price,
        # then with sale prices, checking correct matches based on sale
        # dates.
        self._category.combined = True
        self._category.price_min = TEST_PRICE
        self.assertCategoryFilteredProducts(0)
        self._product.variations.all().update(unit_price=TEST_PRICE)
        self.assertCategoryFilteredProducts(1)
        now, day = datetime.now(), timedelta(days=1)
        tomorrow, yesterday = now + day, now - day
        self._product.variations.all().update(unit_price=0,
                                              sale_price=TEST_PRICE,
                                              sale_from=tomorrow)
        self.assertCategoryFilteredProducts(0)
        self._product.variations.all().update(sale_from=yesterday)
        self.assertCategoryFilteredProducts(1)

        # Clean up previously added filters and check that explicitly
        # assigned products match.
        for option in self._category.options.all():
            self._category.options.remove(option)
        self._category.price_min = None
        self.assertCategoryFilteredProducts(0)
        self._category.products.add(self._product)
        self.assertCategoryFilteredProducts(1)

        # Test the ``combined`` field - create a variation which
        # matches a price filter, and a separate variation which
        # matches an option filter, and check that the filters
        # have no results when ``combined`` is set, and that the
        # product matches when ``combined`` is disabled.
        self._product.variations.all().delete()
        self._product.variations.create_from_options({option_field:
                                                     [option1, option2]})
        # Price variation and filter.
        variation = self._product.variations.get(**{option_field: option1})
        variation.unit_price = TEST_PRICE
        variation.save()
        self._category.price_min = TEST_PRICE
        # Option variation and filter.
        option = ProductOption.objects.get(type=option_field[-1], name=option2)
        self._category.options.add(option)
        # Check ``combined``.
        self._category.combined = True
        self.assertCategoryFilteredProducts(0)
        self._category.combined = False
        self.assertCategoryFilteredProducts(1)

    def _add_to_cart(self, variation, quantity):
        """
        Given a variation, creates the dict for posting to the cart
        form to add the variation, and posts it.
        """
        field_names = [f.name for f in ProductVariation.option_fields()]
        data = dict(zip(field_names, variation.options()))
        data["quantity"] = quantity
        self.client.post(variation.product.get_absolute_url(), data)

    def _empty_cart(self, cart):
        """
        Given a cart, creates the dict for posting to the cart form
        to remove all items from the cart, and posts it.
        """
        data = {"items-INITIAL_FORMS": 0, "items-TOTAL_FORMS": 0,
                "update_cart": 1}
        for i, item in enumerate(cart):
            data["items-INITIAL_FORMS"] += 1
            data["items-TOTAL_FORMS"] += 1
            data["items-%s-id" % i] = item.id
            data["items-%s-DELETE" % i] = "on"
        self.client.post(reverse("shop_cart"), data)

    def _reset_variations(self):
        """
        Recreates variations and sets up the first.
        """
        self._product.variations.all().delete()
        self._product.variations.create_from_options(self._options)
        variation = self._product.variations.all()[0]
        variation.unit_price = TEST_PRICE
        variation.num_in_stock = TEST_STOCK * 2
        variation.save()

    def test_cart(self):
        """
        Test the cart object and cart add/remove forms.
        """

        # Test initial cart.
        cart = Cart.objects.from_request(self.client)
        self.assertFalse(cart.has_items())
        self.assertEqual(cart.total_quantity(), 0)
        self.assertEqual(cart.total_price(), Decimal("0"))

        # Add quantity and check stock levels / cart totals.
        self._reset_variations()
        variation = self._product.variations.all()[0]
        self._add_to_cart(variation, TEST_STOCK)
        cart = Cart.objects.from_request(self.client)
        variation = self._product.variations.all()[0]
        self.assertTrue(variation.has_stock(TEST_STOCK))
        self.assertFalse(variation.has_stock(TEST_STOCK * 2))
        self.assertTrue(cart.has_items())
        self.assertEqual(cart.total_quantity(), TEST_STOCK)
        self.assertEqual(cart.total_price(), TEST_PRICE * TEST_STOCK)

        # Add remaining quantity and check again.
        self._add_to_cart(variation, TEST_STOCK)
        cart = Cart.objects.from_request(self.client)
        variation = self._product.variations.all()[0]
        self.assertFalse(variation.has_stock())
        self.assertTrue(cart.has_items())
        self.assertEqual(cart.total_quantity(), TEST_STOCK * 2)
        self.assertEqual(cart.total_price(), TEST_PRICE * TEST_STOCK * 2)

        # Remove from cart.
        self._empty_cart(cart)
        cart = Cart.objects.from_request(self.client)
        variation = self._product.variations.all()[0]
        self.assertTrue(variation.has_stock(TEST_STOCK * 2))
        self.assertFalse(cart.has_items())
        self.assertEqual(cart.total_quantity(), 0)
        self.assertEqual(cart.total_price(), Decimal("0"))

    def test_discount_codes(self):
        """
        Test that all types of discount codes are applied.
        """

        self._reset_variations()
        variation = self._product.variations.all()[0]
        invalid_product = Product.objects.create(**self._published)
        invalid_product.variations.create_from_options(self._options)
        invalid_variation = invalid_product.variations.all()[0]
        invalid_variation.unit_price = TEST_PRICE
        invalid_variation.num_in_stock = TEST_STOCK * 2
        invalid_variation.save()
        discount_value = TEST_PRICE / 2

        # Set up discounts with and without a specific product, for
        # each type of discount.
        for discount_target in ("cart", "item"):
            for discount_type in ("percent", "deduct"):
                code = "%s_%s" % (discount_target, discount_type)
                kwargs = {
                    "code": code,
                    "discount_%s" % discount_type: discount_value,
                    "active": True,
                }
                cart = Cart.objects.from_request(self.client)
                self._empty_cart(cart)
                self._add_to_cart(variation, 1)
                self._add_to_cart(invalid_variation, 1)
                discount = DiscountCode.objects.create(**kwargs)
                if discount_target == "item":
                    discount.products.add(variation.product)
                post_data = {"discount_code": code}
                self.client.post(reverse("shop_cart"), post_data)
                discount_total = self.client.session["discount_total"]
                if discount_type == "percent":
                    expected = TEST_PRICE / Decimal("100") * discount_value
                    if discount_target == "cart":
                        # Excpected amount applies to entire cart.
                        cart = Cart.objects.from_request(self.client)
                        expected *= cart.items.count()
                elif discount_type == "deduct":
                    expected = discount_value
                self.assertEqual(discount_total, expected)
                if discount_target == "item":
                    # Test discount isn't applied for an invalid product.
                    cart = Cart.objects.from_request(self.client)
                    self._empty_cart(cart)
                    self._add_to_cart(invalid_variation, 1)
                    self.client.post(reverse("shop_cart"), post_data)
                    discount_total = self.client.session.get("discount_total")
                    self.assertEqual(discount_total, None)

    def test_order(self):
        """
        Test that a completed order contains cart items and that
        they're removed from stock.
        """

        # Add to cart.
        self._reset_variations()
        variation = self._product.variations.all()[0]
        self._add_to_cart(variation, TEST_STOCK)
        cart = Cart.objects.from_request(self.client)

        # Post order.
        data = {"step": len(CHECKOUT_STEPS)}
        self.client.post(reverse("shop_checkout"), data)
        try:
            order = Order.objects.from_request(self.client)
        except Order.DoesNotExist:
            self.fail("Couldn't create an order")
        items = order.items.all()
        variation = self._product.variations.all()[0]

        self.assertEqual(cart.total_quantity(), 0)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].sku, variation.sku)
        self.assertEqual(items[0].quantity, TEST_STOCK)
        self.assertEqual(variation.num_in_stock, TEST_STOCK)
        self.assertEqual(order.item_total, TEST_PRICE * TEST_STOCK)

    def test_syntax(self):
        """
        Run pyflakes/pep8 across the code base to check for potential errors.
        """
        extra_ignore = (
                "redefinition of unused 'digest'",
                "redefinition of unused 'OperationalError'",
                "'from mezzanine.project_template.settings import *' used",
        )
        warnings = []
        warnings.extend(run_pyflakes_for_package("cartridge",
                                                 extra_ignore=extra_ignore))
        warnings.extend(run_pep8_for_package("cartridge"))
        if warnings:
            self.fail("Syntax warnings!\n\n%s" % "\n".join(warnings))
