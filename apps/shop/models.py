
from copy import copy
from datetime import datetime
from decimal import Decimal
from django.db import models
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from shop.managers import ShopManager, CartManager, ProductVariationManager
from shop.fields import OptionField, MoneyField, SKUField
from shop.settings import ORDER_STATUSES, ORDER_STATUS_DEFAULT, PRODUCT_OPTIONS


class ShopModel(models.Model):
	"""
	abstract model representing a visible object on the website - Category and 
	Product are derived from this. contains common functionality like auto slug 
	creation and active (toggle visibility) fields
	"""

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
	available = models.BooleanField(default=True, help_text="Check this to " \
		"make this item available for purchase when it is visible on the site")
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
 
class BaseProductVariation(models.Model):
	"""
	abstract model used to create the ProductVariation model below using 
	dynamically created set of option fields from shop.settings.PRODUCT_OPTIONS
	"""
	
	class Meta:
		abstract = True
		
	product = models.ForeignKey(Product, related_name="variations")
	sku = SKUField(unique=True)
	quantity = models.IntegerField("Number in stock", blank=True, null=True) 
	objects = ProductVariationManager()
	
	def __unicode__(self):
		return "%s %s" % (self.product, ", ".join(["%s: %s" % 
			(field.name.title(), getattr(self, field.name)) for field in 
			self.option_fields() if getattr(self, field.name) is not None]))
	
	def save(self, *args, **kwargs):
		super(BaseProductVariation, self).save(*args, **kwargs)
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
		"""
		check the given quantity is in stock taking carts into account and 
		caching the number in carts
		"""
		if self.quantity is None:
			return True
		if not hasattr(self, "_cached_num_available"):
			num_available = self.quantity
			in_carts = CartItem.objects.filter(sku=self.sku).aggregate(
				total_quantity=models.Sum("quantity"))["total_quantity"]
			if in_carts is not None:
				num_available = num_available - in_carts
			self._cached_num_available = num_available
		return self._cached_num_available >= quantity

	def set_quantity(self, quantity=None):
		"""
		update the available quantity ensuring the cached num available is 
		removed - only used in testing
		"""
		if quantity is not None:
			self.quantity = quantity
			self.save()
		if hasattr(self, "_cached_num_available"):
			delattr(self, "_cached_num_available")

# build the ProductVariation model from the BaseProductVariation model by
# adding each option in shop.settings.PRODUCT_OPTIONS as an OptionField
_options = {"Meta": object, "__module__": BaseProductVariation.__module__}
for _name, _choices in PRODUCT_OPTIONS:
	_options[_name] = OptionField(choices=zip(_choices, _choices))
ProductVariation = type("ProductVariation", (BaseProductVariation,), _options)

class Address(models.Model):
	"""
	abstract model used to create new models via Address.make() - new models
	are billing and shipping with the Order model inherits from below 
	"""
	
	class Meta:
		abstract = True

	first_name = models.CharField("First name", max_length=100)
	last_name = models.CharField("Last name", max_length=100)
	street = models.CharField("Street", max_length=100)
	city = models.CharField("City/Suburb", max_length=100)
	state = models.CharField("State/Region", max_length=100)
	postcode = models.CharField("Zip/Postcode", max_length=10)
	country = models.CharField("Country", max_length=100)
	phone = models.CharField("Phone", max_length=20)
	
	@classmethod
	def make(cls, field_prefix):
		"""
		return a new model with the same fields as Address as well as a 
		PREFIX_fields and PREFIX_field_names methods for accessing the address 
		fields and field names by prefix
		"""
		class Meta:
			abstract = True
		def field_names_by_prefix(cls):
			return [f.name for f in cls._meta.fields 
				if f.name.startswith(field_prefix)]
		def fields_by_prefix(instance):
			return [{"name": f.verbose_name, "value": getattr(instance, f.name)} 
				for f in instance._meta.fields if f.name.startswith(field_prefix)]
		fields = {"Meta": Meta, "__module__": cls.__module__, 
			"%s_field_names" % field_prefix: classmethod(field_names_by_prefix),
			"%s_fields" % field_prefix: fields_by_prefix}
		for field in cls._meta.fields:
			if not isinstance(field, models.AutoField):
				fields["%s_%s" % (field_prefix, field.name)] = copy(field)
		cls_name = "".join(s.title() for s in field_prefix.split("_"))
		return type(cls_name, (models.Model,), fields)

class Order(Address.make("billing_detail"), Address.make("shipping_detail")):

	billing_detail_email = models.EmailField("Email")
	additional_instructions = models.TextField(blank=True)
	time = models.DateTimeField(auto_now_add=True)
	shipping_type = models.CharField(max_length=50, blank=True)
	shipping_total = MoneyField()
	item_total = MoneyField()
	total = MoneyField()
	status = models.IntegerField(choices=ORDER_STATUSES, 
		default=ORDER_STATUS_DEFAULT)

	def billing_name(self):
		return "%s %s" % (self.billing_detail_first_name, 
			self.billing_detail_last_name)

	def __unicode__(self):
		return "#%s %s %s" % (self.id, self.billing_name(), self.time)

	def save(self, *args, **kwargs):
		self.total = self.item_total
		if self.shipping_total is not None:
			self.total += self.shipping_total
		super(Order, self).save(*args, **kwargs)

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
			item.description = str(variation)
			item.unit_price = variation.product.price()
			item.url = variation.product.get_absolute_url()
			images = variation.product.images()
			if images:
				item.image = str(images[0])
		item.quantity += quantity
		item.save()
		if hasattr(self, "_cached_items"):
			delattr(self, "_cached_items")
			
	def remove_item(self, sku):
		"""
		remove item by sku
		"""
		self.items.filter(sku=sku).delete()
		if hasattr(self, "_cached_items"):
			delattr(self, "_cached_items")
		
	def has_items(self):
		"""
		template helper function - does the cart have items
		"""
		return len(list(self)) > 0 
	
	def total_quantity(self):
		"""
		template helper function - sum of all item quantities
		"""
		return sum([item.quantity for item in self])
		
	def total_price(self):
		"""
		template helper function - sum of all costs of item quantities
		"""
		return sum([item.total_price for item in self])
	
class SelectedProduct(models.Model):
	"""
	abstract model representing a "selected" product in a cart or order
	"""

	class Meta:
		abstract = True
		
	sku = SKUField()
	description = models.CharField(max_length=200)
	quantity = models.IntegerField(default=0)
	unit_price = MoneyField(default=Decimal("0"))
	total_price = MoneyField(default=Decimal("0"))
	
	def __unicode__(self):
		return ""
	
	def save(self, *args, **kwargs):
		self.total_price = self.unit_price * self.quantity
		super(SelectedProduct, self).save(*args, **kwargs)

class CartItem(SelectedProduct):
	cart = models.ForeignKey(Cart, related_name="items")
	url = models.CharField(max_length=200)
	image = models.CharField(max_length=200)

class OrderItem(SelectedProduct):
	order = models.ForeignKey(Order, related_name="items")

