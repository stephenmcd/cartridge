
from datetime import datetime
from decimal import Decimal
from django.db import models
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse

ORDER_STATUS_CHOICES = (
	(1, "Unprocessed"),
	(2, "Processed"),
)
ORDER_STATUS_DEFAULT = 1

OPTION_COLOURS = ("Red","Orange","Yellow","Green","Blue","Indigo","Violet")
OPTION_COLOURS = zip(OPTION_COLOURS, OPTION_COLOURS)
OPTION_SIZES = ("Extra Small","Small","Regular","Large","Extra Large")
OPTION_SIZES = zip(OPTION_SIZES, OPTION_SIZES)

class ShopManager(models.Manager):
	def active(self, **kwargs):
		return self.filter(active=True, **kwargs)

class ShopModel(models.Model):

	class Meta:
		abstract = True

	title = models.CharField(max_length=100)
	slug = models.SlugField(max_length=100, editable=False)
	active = models.BooleanField(default=False, 
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

	def get_absolute_url(self, slugs=None):
		if slugs is None:
			slugs = []
		slugs.append(self.slug)
		return reverse("shop_%s" % self.__class__.__name__.lower(), 
			kwargs={"slugs": "/".join(slugs)})
	
	def admin_link(self):
		return "<a href='%s'>View on site</a>" % self.get_absolute_url()
	admin_link.allow_tags = True
	admin_link.short_description = " "

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
	unit_price = models.DecimalField(blank=True, null=True, 
		max_digits=6, decimal_places=2)
	sale_price = models.DecimalField(blank=True, null=True,
		max_digits=6, decimal_places=2)
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
	
	def actual_price(self):
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
	def images(cls):
		return [field for field in cls._meta.fields 
			if isinstance(field, models.ImageField)]

class OptionField(models.CharField):
	pass
 
class ProductVariation(models.Model):
		
	sku = models.CharField("SKU", max_length=20, unique=True)
	product = models.ForeignKey(Product, related_name="variations")
	
	colour = OptionField(max_length=20, choices=OPTION_COLOURS)
	size = OptionField(max_length=20, choices=OPTION_SIZES)
	
	def __unicode__(self):
		return ", ".join(["%s: %s" % (field.name.title(), 
			getattr(self, field.name)) for field in self.options()])
	
	def save(self, *args, **kwargs):
		super(ProductVariation, self).save(*args, **kwargs)
		if not self.sku:
			self.sku = self.id
			self.save()

	@classmethod
	def options(cls):
		return [field for field in cls._meta.fields 
			if isinstance(field, OptionField)]

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
	def shipping_fields(cls):
		return [field.name for field in cls._meta.fields 
			if field.name.startswith("shipping_detail_")]
		
	@classmethod
	def billing_fields(cls):
		return [field.name for field in cls._meta.fields 
			if field.name.startswith("billing_detail_")]

class OrderItem(models.Model):

	order = models.ForeignKey(Order, related_name="items")
	sku = models.CharField("SKU", max_length=20)
	description = models.TextField(blank=True)
	price = models.DecimalField(blank=True, null=True, 
		max_digits=6, decimal_places=2)
	quantity = models.IntegerField()

