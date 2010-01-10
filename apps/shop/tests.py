
from decimal import Decimal
from operator import mul
from django.test import TestCase
from django.core.urlresolvers import reverse
from shop.models import Product, Category, Cart, CartItem
from shop.settings import PRODUCT_OPTIONS


class ShopTests(TestCase):

	urls = "shop.urls"
	
	def setUp(self):
		self._category = Category.objects.create(active=True)
		self._product = Product.objects.create(active=True)
		
	def _create_variations(self):
		"""
		create all variations from PRODUCT_OPTIONS for the test product
		"""
		self._product.variations.create_from_options(PRODUCT_OPTIONS)

	def _get_default_variation(self):
		"""
		create amd return the default variation
		"""
		self._product.variations.all().delete()
		self._product.variations.manage_empty()
		return self._product.variations.all()[0]

	def test_views(self):
		"""
		test the main shop views for errors
		"""
		# category
		response = self.client.get(self._category.get_absolute_url())
		self.assertEqual(response.status_code, 200)
		# product
		response = self.client.get(self._product.get_absolute_url())
		self.assertEqual(response.status_code, 200)
		# cart
		response = self.client.get(reverse("shop_cart"))
		self.assertEqual(response.status_code, 200)
		# checkout
		response = self.client.get(reverse("shop_checkout"))
		self.assertEqual(response.status_code, 200)

	def test_variations(self):
		"""
		test creation of variations from options and management of empty 
		variations
		"""
		total_variations = reduce(mul, [len(opts[1]) for opts in PRODUCT_OPTIONS])
		# clear variations
		self._product.variations.all().delete()
		self.assertEqual(self._product.variations.count(), 0)
		# create single empty variation
		self._product.variations.manage_empty()
		self.assertEqual(self._product.variations.count(), 1)
		# create variations from all options
		self._create_variations()
		# should do nothing
		self._create_variations()
		# all options plus empty
		self.assertEqual(self._product.variations.count(), total_variations + 1)
		# remove empty
		self._product.variations.manage_empty()
		self.assertEqual(self._product.variations.count(), total_variations)

	def test_stock(self):
		"""
		test stock checking on product variations
		"""
		variation = self._get_default_variation()
		# check stock not in use
		self.assertTrue(variation.has_stock())
		# check available and unavailable quantities
		quantity = 10
		variation.set_quantity(quantity)
		self.assertTrue(variation.has_stock(quantity))
		self.assertFalse(variation.has_stock(quantity + 1))
		# check sold out
		variation.set_quantity(0)
		self.assertFalse(variation.has_stock())

	def test_cart(self):
		"""
		test the cart
		"""
		# set up price and quantity
		price = Decimal("20")
		quantity = 5
		self._product.unit_price = price
		self._product.save()
		variation = self._get_default_variation()
		variation.set_quantity(quantity * 2)
		# test initial cart
		Cart.objects.from_request(self.client).delete()
		cart = Cart.objects.from_request(self.client)
		self.assertFalse(cart.has_items())
		self.assertEqual(cart.total_quantity(), 0)
		self.assertEqual(cart.total_price(), Decimal("0"))
		# add quantity and check stock levels / cart totals
		cart.add_item(variation, quantity)
		self.assertTrue(variation.has_stock(quantity))
		self.assertFalse(variation.has_stock(quantity * 2))
		self.assertTrue(cart.has_items())
		self.assertEqual(cart.total_quantity(), quantity)
		self.assertEqual(cart.total_price(), price * quantity)
		# add remaining quantity and check again
		cart.add_item(variation, quantity)
		variation.set_quantity()
		self.assertFalse(variation.has_stock())
		self.assertTrue(cart.has_items())
		self.assertEqual(cart.total_quantity(), quantity * 2)
		self.assertEqual(cart.total_price(), price * quantity * 2)
		# remove from cart
		cart.remove_item(variation.sku)
		variation.set_quantity()
		self.assertTrue(variation.has_stock(quantity * 2))
		self.assertFalse(cart.has_items())
		self.assertEqual(cart.total_quantity(), 0)
		self.assertEqual(cart.total_price(), Decimal("0"))

	def test_checkout(self):
		"""
		test the checkout process
		"""
		pass

