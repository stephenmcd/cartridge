
from __future__ import division, unicode_literals
from future.builtins import range, zip

from datetime import timedelta
from decimal import Decimal
from operator import mul
from functools import reduce

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory
from django.utils.timezone import now
from django.utils.unittest import skipUnless
from mezzanine.conf import settings
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
from mezzanine.utils.importing import import_dotted_path
from mezzanine.utils.tests import run_pyflakes_for_package
from mezzanine.utils.tests import run_pep8_for_package

from cartridge.shop.models import Product, ProductOption, ProductVariation
from cartridge.shop.models import Category, Cart, Order, DiscountCode
from cartridge.shop.models import Sale
from cartridge.shop.forms import OrderForm
from cartridge.shop.checkout import CHECKOUT_STEPS
from cartridge.shop.utils import set_tax


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
        total = reduce(mul, [len(v) for v in list(self._options.values())])
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
        option_field, options = list(self._options.items())[0]
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
        n, d = now(), timedelta(days=1)
        tomorrow, yesterday = n + d, n - d
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
        data = dict(list(zip(field_names, variation.options())))
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
                discount_total = Decimal(self.client.session["discount_total"])
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
                    r = self.client.post(reverse("shop_cart"), post_data)
                    self.assertFormError(r, "discount_form", "discount_code",
                                     "The discount code entered is invalid.")

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
        data = {
            "step": len(CHECKOUT_STEPS),
            "billing_detail_email": "example@example.com",
            "discount_code": "",
        }
        for field_name, field in list(OrderForm(None, None).fields.items()):
            value = field.choices[-1][1] if hasattr(field, "choices") else "1"
            data.setdefault(field_name, value)
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


class SaleTests(TestCase):

    def setUp(self):
        product1 = Product(unit_price="1.27")
        product1.save()

        ProductVariation(unit_price="1.27", product_id=product1.id).save()
        ProductVariation(unit_price="1.27", product_id=product1.id).save()

        product2 = Product(unit_price="1.27")
        product2.save()

        ProductVariation(unit_price="1.27", product_id=product2.id).save()
        ProductVariation(unit_price="1.27", product_id=product2.id).save()

        sale = Sale(
            title="30% OFF - Ken Bruce has gone mad!",
            discount_percent="30"
            )
        sale.save()

        sale.products.add(product1)
        sale.products.add(product2)
        sale.save()

    def test_sale_save(self):
        """
        Regression test for GitHub issue #24. Incorrect exception handle meant
        that in some cases (usually percentage discount) sale_prices were not
        being applied to all products and their varitations.

        Note: This issues was only relevant using MySQL and with exceptions
        turned on (which is the default when DEBUG=True).
        """
        # Initially no sale prices will be set.
        for product in Product.objects.all():
            self.assertFalse(product.sale_price)
        for variation in ProductVariation.objects.all():
            self.assertFalse(variation.sale_price)

        # Activate the sale and verify the prices.
        sale = Sale.objects.all()[0]
        sale.active = True
        sale.save()

        # Afterward ensure that all the sale prices have been updated.
        for product in Product.objects.all():
            self.assertTrue(product.sale_price)
        for variation in ProductVariation.objects.all():
            self.assertTrue(variation.sale_price)


try:
    __import__("stripe")
    import mock
except ImportError:
    stripe_used = False
else:
    stripe_handler = "cartridge.shop.payment.stripe_api.process"
    stripe_used = settings.SHOP_HANDLER_PAYMENT == stripe_handler
    if stripe_used:
        settings.STRIPE_API_KEY = "dummy"
        from cartridge.shop.payment import stripe_api


class StripeTests(TestCase):
    """
    Test the Stripe payment backend.
    """

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()

    def test_charge(self, mock_charge):

        # Create a fake request object with the test data
        request = self.factory.post("/shop/checkout/")
        request.POST["card_number"] = "4242424242424242"
        request.POST["card_expiry_month"] = "06"
        request.POST["card_expiry_year"] = "2014"
        request.POST["billing_detail_street"] = "123 Evergreen Terrace"
        request.POST["billing_detail_city"] = "Springfield"
        request.POST["billing_detail_state"] = "WA"
        request.POST["billing_detail_postcode"] = "01234"
        request.POST["billing_detail_country"] = "USA"

        # Order form isn't used by stripe backend
        order_form = None

        # Create an order
        order = Order.objects.create(total=Decimal("22.37"))

        # Code under test
        stripe_api.process(request, order_form, order)

        # Assertion
        mock_charge.create.assert_called_with(
            amount=2237,
            currency="usd",
            card={'number': "4242424242424242",
                  'exp_month': "06",
                  'exp_year': "14",
                  'address_line1': "123 Evergreen Terrace",
                  'address_city': "Springfield",
                  'address_state': "WA",
                  'address_zip': "01234",
                  'country': "USA"})


StripeTests = skipUnless(stripe_used, "Stripe not used")(StripeTests)
if stripe_used:
    charge = "stripe.Charge"
    StripeTests.test_charge = mock.patch(charge)(StripeTests.test_charge)


class TaxationTests(TestCase):

    def test_default_handler_exists(self):
        """
        Ensure that the handler specified in default settings exists as well as
        the default setting itself.
        """
        settings.use_editable()
        handler = lambda s: import_dotted_path(s) if s else lambda *args: None
        self.assertTrue(handler(settings.SHOP_HANDLER_TAX) is not None)

    def test_set_tax(self):
        """
        Regression test to ensure that set_tax still sets the appropriate
        session variables.
        """

        tax_type = 'Tax for Testing'
        tax_total = 56.65

        class request:
            session = {}

        set_tax(request, tax_type, tax_total)
        self.assertEqual(request.session.get("tax_type"), str(tax_type))
        self.assertEqual(request.session.get("tax_total"), str(tax_total))
