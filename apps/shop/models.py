
from copy import copy
from datetime import datetime
from decimal import Decimal
from django.db import models
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse

class _ShopManager(models.Manager):
	
	def active(self, **kwargs):
		return self.filter(active=True, **kwargs)
		
class _ShopModel(models.Model):

	class Meta:
		abstract = True

	title = models.CharField(max_length=100)
	slug = models.SlugField(max_length=100, editable=False)
	active = models.BooleanField(default=True, 
		help_text="Check this to make this item visible on the site")
	objects = _ShopManager()

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
		super(_ShopModel, self).save(*args, **kwargs)

	def get_absolute_url(self, slugs=None):
		if slugs is None:
			slugs = []
		slugs.append(self.slug)
		return reverse(self.url_pattern, kwargs={"slugs": "/".join(slugs)})

class Category(_ShopModel):

	class Meta:
		verbose_name_plural = "Categories"

	parent = models.ForeignKey("self", blank=True, null=True,
		related_name="children")

	url_pattern = "shop_category"

class _OptionModel(models.Model):
	
	class Meta:
		abstract = True
		
	name = models.CharField(max_length=50)

class _ProductOption(models.CharField):
	pass

class Product(_ShopModel):

	description = models.TextField(blank=True)
	available = models.BooleanField(default=True, 
		help_text="Check this to make this item available for purchase when it is visible on the site")
	categories = models.ManyToManyField(Category, blank=True, 
		related_name="products")
	regular_price = models.DecimalField(blank=True, null=True, 
		max_digits=6, decimal_places=2)
	sale_price = models.DecimalField(blank=True, null=True,
		max_digits=6, decimal_places=2)
	sale_from = models.DateTimeField("Start", blank=True, null=True)
	sale_to = models.DateTimeField("Finish", blank=True, null=True)

	sizes = _ProductOption(max_length=200, blank=True)
	colours = _ProductOption(max_length=200, blank=True)
	image1 = models.ImageField("First Image", max_length=100, blank=True, upload_to="product")
	image2 = models.ImageField("Second Image", max_length=100, blank=True, upload_to="product")
	image3 = models.ImageField("Third Image", max_length=100, blank=True, upload_to="product")
	image4 = models.ImageField("Fourth Image", max_length=100, blank=True, upload_to="product")
	image5 = models.ImageField("Fifth Image", max_length=100, blank=True, upload_to="product")

	url_pattern = "shop_product"
	
	def on_sale(self):
		return self.sale_price and self.sale_to > datetime.now() > self.sale_from

	def has_price(self):
		return self.on_sale() or self.regular_price is not None
	
	def actual_price(self):
		if self.on_sale():
			return self.sale_price
		elif self.has_price():
			return self.regular_price
		return Decimal("0")
	
	@classmethod
	def option_fields(cls):
		return tuple([field.name for field in cls._meta.fields 
			if isinstance(field, _ProductOption)])

	def options(self):
		choices = lambda field: map(str.strip, 
			str(getattr(self, field)).split(","))
		return [{"name": field[:-1], "choices": choices(field)} for field in 
			Product.option_fields()]
	
	@classmethod
	def image_fields(cls):
		return tuple([field.name for field in cls._meta.fields 
			if isinstance(field, models.ImageField)])
			
	def images(self):
		return [getattr(self, field) for field in Product.image_fields()
			if getattr(self, field)]
	
	def save(self, *args, **kwargs):
		if not self.has_price():
			self.available = False
		super(Product, self).save(*args, **kwargs)
					
class _Address(models.Model):
	
	class Meta:
		abstract = True

	first_name = models.CharField(max_length=100)
	last_name = models.CharField(max_length=100)
	street = models.CharField(max_length=100)
	city = models.CharField(max_length=100)
	state = models.CharField(max_length=100)
	postcode = models.CharField(max_length=10)
	country = models.CharField(max_length=100)
	email = models.EmailField()
	phone = models.CharField(max_length=20)

def _address(prefix):
	def clone_model(prefix, model):
		class Meta:
			abstract = model._meta.abstract
		attrs = {"__module__": model.__module__}
		for field in model._meta.fields:
			if not isinstance(field, models.AutoField):
				attrs["%s_%s" % (prefix.lower(), field.name)] = copy(field)
		return type("%s%s" % (prefix, model.__name__), (models.Model,), attrs)
	return clone_model(prefix, _Address)

class Order(_address("Billing"), _address("Shipping")):

	ORDER_STATUS_CHOICES = (
		(1, "Unprocessed"),
		(2, "Processed"),
	)

	additional_instructions = models.TextField()
	time = models.DateTimeField(auto_now_add=True)
	shipping_type = models.CharField(max_length=50, blank=True)
	shipping = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	total = models.DecimalField(max_digits=6, decimal_places=2)
	status = models.IntegerField(choices=ORDER_STATUS_CHOICES, default=1)

	def billing_name(self):
		return "%s %s" % (self.billing_first_name, self.billing_last_name)

	def __unicode__(self):
		return "#%s %s %s" % (self.id, self.billing_name(), self.time)

class OrderItem(models.Model):

	order = models.ForeignKey(Order, related_name="items")
	product_id = models.IntegerField(editable=False)
	description = models.TextField(blank=True)
	unit_price = models.DecimalField(blank=True, null=True, 
		max_digits=6, decimal_places=2)
	quantity = models.IntegerField()

