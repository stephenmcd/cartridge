
from operator import mul
from django.test import TestCase
from django.core.urlresolvers import reverse
from shop.models import Product, Category
from shop.settings import PRODUCT_OPTIONS


total_variations = reduce(mul, [len(opts[1]) for opts in PRODUCT_OPTIONS])


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
		test stock checking methods on product variations
		"""
		pass

	def test_cart(self):
		"""
		test the cart
		"""
		pass

	def test_checkout(self):
		"""
		test the checkout process
		"""
		pass

