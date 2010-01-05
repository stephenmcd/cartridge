
from datetime import datetime
from decimal import Decimal
from django.db import models
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from shop.managers import ShopManager, CartManager
from shop.fields import OptionField, MoneyField, SKUField


ORDER_STATUS_CHOICES = (
	(1, "Unprocessed"),
	(2, "Processed"),
)
ORDER_STATUS_DEFAULT = 1

OPTION_COLOURS = ("Red","Orange","Yellow","Green","Blue","Indigo","Violet")
OPTION_COLOURS = zip(OPTION_COLOURS, OPTION_COLOURS)
OPTION_SIZES = ("Extra Small","Small","Regular","Large","Extra Large")
OPTION_SIZES = zip(OPTION_SIZES, OPTION_SIZES)


class ShopModel(models.Model):

	class Meta:
		abstract = True

	title = models.CharField(max_length=100)
	slug = models.SlugField(max_length=100, editable=False)
	active = models.BooleanField(default=True, 
		help_text="Check this to make this item visible on the site")

	objects = ShopManager()

	def __unicode__(self):
		return self.title
		
	def save(self, *args, **kwargs):
		if self.id is None:
			i = 0
			while True:
				self.slug = slugify(self.title)
				if i > 0:
					self.slug = "%s-%s" % (self.slug, i)
				if not self.__class__.objects.filter(slug=self.slug):
					break
				i += 1
		super(ShopModel, self).save(*args, **kwargs)
		
	def get_absolute_url(self):
		return reverse("shop_%s" % self.__class__.__name__.lower(), 
			kwargs={"slug": self.slug})
	
	def admin_link(self):
		return "<a href='%s'>View on site</a>" % self.get_absolute_url()
	admin_link.allow_tags = True
	admin_link.short_description = ""

class Category(ShopModel):

	class Meta:
		verbose_name_plural = "Categories"

	image = models.ImageField(max_length=100, blank=True, upload_to="category")
	parent = models.ForeignKey("self", blank=True, null=True, 
		related_name="children")

class Product(ShopModel):

	description = models.TextField(blank=True)
	available = models.BooleanField(default=True, 
		help_text="Check this to make this item available for purchase when it is visible on the site")
	categories = models.ManyToManyField(Category, blank=True, 
		related_name="products")
	unit_price = MoneyField()
	sale_price = MoneyField()
	sale_from = models.DateTimeField("Start", blank=True, null=True)
	sale_to = models.DateTimeField("Finish", blank=True, null=True)

	image_1 = models.ImageField(max_length=100, blank=True, upload_to="product")
	image_2 = models.ImageField(max_length=100, blank=True, upload_to="product")
	image_3 = models.ImageField(max_length=100, blank=True, upload_to="product")
	image_4 = models.ImageField(max_length=100, blank=True, upload_to="product")
	
	def on_sale(self):
		return self.sale_price and self.sale_to > datetime.now() > self.sale_from

	def has_price(self):
		return self.on_sale() or self.unit_price is not None
	
	def price(self):
		if self.on_sale():
			return self.sale_price
		elif self.has_price():
			return self.unit_price
		return Decimal("0")
	
	def save(self, *args, **kwargs):
		if not self.has_price():
			self.available = False
		super(Product, self).save(*args, **kwargs)
		
	@classmethod
	def image_fields(cls):
		return [field for field in cls._meta.fields 
			if isinstance(field, models.ImageField)]
	
	def images(self):
		return [getattr(self, field.name) for field in self.image_fields()
			if getattr(self, field.name)]
 
class ProductVariation(models.Model):
		
	product = models.ForeignKey(Product, related_name="variations")
	sku = SKUField(unique=True)
	quantity = models.IntegerField("Number in stock", blank=True, null=True) 

	colour = OptionField(choices=OPTION_COLOURS)
	size = OptionField(choices=OPTION_SIZES)
	
	def __unicode__(self):
		return "%s %s" % (self.product, ", ".join(["%s: %s" % 
			(field.name.title(), getattr(self, field.name)) for field in 
			self.option_fields() if getattr(self, field.name) is not None]))
	
	def save(self, *args, **kwargs):
		super(ProductVariation, self).save(*args, **kwargs)
		if not self.sku:
			self.sku = self.id
			self.save()

	@classmethod
	def option_fields(cls):
		return [field for field in cls._meta.fields 
			if isinstance(field, OptionField)]
	
	def options(self):
		return [getattr(self, field.name) for field in self.option_fields()]

	def has_stock(self, quantity=1):
		if self.quantity is None:
			return True
		if not hasattr(self, "_num_available"):
			self._num_available = (self.quantity + 
				CartItem.objects.filter(sku=self.sku).count())
		return self._num_available >= quantity

class Order(models.Model):

	billing_detail_first_name = models.CharField("First name", max_length=100)
	billing_detail_last_name = models.CharField("Last name", max_length=100)
	billing_detail_street = models.CharField("Street", max_length=100)
	billing_detail_city = models.CharField("City/Suburb", max_length=100)
	billing_detail_state = models.CharField("State/Region", max_length=100)
	billing_detail_postcode = models.CharField("Zip/Postcode", max_length=10)
	billing_detail_country = models.CharField("Country", max_length=100)
	billing_detail_phone = models.CharField("Phone", max_length=20)
	billing_detail_email = models.EmailField("Email")

	shipping_detail_first_name = models.CharField("First name", max_length=100)
	shipping_detail_last_name = models.CharField("Last name", max_length=100)
	shipping_detail_street = models.CharField("Street", max_length=100)
	shipping_detail_city = models.CharField("City/Suburb", max_length=100)
	shipping_detail_state = models.CharField("State/Region", max_length=100)
	shipping_detail_postcode = models.CharField("Zip/Postcode", max_length=10)
	shipping_detail_country = models.CharField("Country", max_length=100)
	shipping_detail_phone = models.CharField("Phone", max_length=20)

	additional_instructions = models.TextField(blank=True)
	time = models.DateTimeField(auto_now_add=True)
	shipping_type = models.CharField(max_length=50, blank=True)
	shipping_total = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	total = models.DecimalField(max_digits=6, decimal_places=2)
	status = models.IntegerField(choices=ORDER_STATUS_CHOICES, 
		default=ORDER_STATUS_DEFAULT)

	def billing_name(self):
		return "%s %s" % (self.billing_detail_first_name, 
			self.billing_detail_last_name)

	def __unicode__(self):
		return "#%s %s %s" % (self.id, self.billing_name(), self.time)
		
	@classmethod
	def shipping_field_names(cls):
		return [field.name for field in cls._meta.fields 
			if field.name.startswith("shipping_detail_")]
		
	@classmethod
	def billing_field_names(cls):
		return [field.name for field in cls._meta.fields 
			if field.name.startswith("billing_detail_")]

class Cart(models.Model):

	timestamp = models.DateTimeField(auto_now=True)
	objects = CartManager()

	def __iter__(self):
		"""
		allow the cart to be iterated giving access to the cart's items, 
		ensuring the items are only retrieved once and cached
		"""
		if not hasattr(self, "_cached_items"):
			self._cached_items = self.items.all()
		return iter(self._cached_items)
		
	def add_item(self, variation, quantity):
		"""
		increase quantity of existing item if sku matches, otherwise create new
		"""
		item, created = self.items.get_or_create(sku=variation.sku)
		if created:
			product = variation.product
			images = product.images()
			item.description = str(variation)
			item.price = product.price()
			item.url = product.get_absolute_url()
			if images:
				item.image = str(images[0])
		item.quantity += quantity
		item.save()
				
	def remove_item(self, sku):
		"""
		remove item by sku
		"""
		self.items.filter(sku=sku).delete()
		
	def has_items(self):
		"""
		template helper function - does the cart have items
		"""
		return len(list(self)) > 0 
	
	def total_items(self):
		"""
		template helper function - sum of all item quantities
		"""
		return sum([item.quantity for item in self])
		
	def total_value(self):
		"""
		template helper function - sum of all costs of item quantities
		"""
		return sum([item.quantity * item.price for item in self])
	
class SelectedProduct(models.Model):
	"""
	a product and selected variation in a cart or order
	"""

	class Meta:
		abstract = True
		
	sku = SKUField()
	description = models.CharField(max_length=200)
	price = MoneyField()
	quantity = models.IntegerField(default=0)
	
	def total_price(self):
		return self.price * self.quantity

class CartItem(SelectedProduct):
	cart = models.ForeignKey(Cart, related_name="items")
	url = models.CharField(max_length=200)
	image = models.CharField(max_length=200)

class OrderItem(SelectedProduct):
	order = models.ForeignKey(Order, related_name="items")

