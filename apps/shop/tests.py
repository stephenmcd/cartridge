
from django.test import TestCase
from django.core.urlresolvers import reverse
from shop.models import Product, Category
from shop.settings import PRODUCT_OPTIONS


class ShopTests(TestCase):

	urls = "shop.urls"

	def test_views(self):
		"""
		test the main shop views for errors
		"""
		
		# category
		category = Category.objects.create(active=True)
		response = self.client.get(category.get_absolute_url())
		self.assertEqual(response.status_code, 200)

		# product
		product = Product.objects.create(active=True)
		response = self.client.get(product.get_absolute_url())
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
		pass

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

