
from django.test import TestCase
from django.core.urlresolvers import reverse
from shop.models import Product, Category


class ShopTests(TestCase):

	urls = "shop.urls"
	fixtures = ("shop_test.json",)

	def test_views(self):
		"""
		test the main shop views for errors
		"""

		# category / product
		for shop_model in (Category, Product):
			for obj in shop_model.objects.active():
				response = self.client.get(obj.get_absolute_url())
				self.assertEqual(response.status_code, 200)

		# cart
		response = self.client.get(reverse("shop_cart"))
		self.assertEqual(response.status_code, 200)

		# checkout
		response = self.client.get(reverse("shop_checkout"))
		self.assertEqual(response.status_code, 200)

	def test_cart(self):
		"""
		test the cart
		"""
		pass

