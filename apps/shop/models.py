
from copy import copy
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext, ugettext_lazy as _

from shop.fields import OptionField, MoneyField, SKUField
from shop.managers import ShopManager, CartManager, ProductVariationManager
from shop.settings import ORDER_STATUSES, ORDER_STATUS_DEFAULT, PRODUCT_OPTIONS
from shop.utils import clone_model, make_choices


class ShopModel(models.Model):
	"""
	abstract model representing a visible object on the website - Category and 
	Product are derived from this. contains common functionality like auto slug 
	creation and active (toggle visibility) fields
	"""

	class Meta:
		abstract = True

	title = models.CharField(_("Title"), max_length=100)
	slug = models.SlugField(max_length=100, editable=False)
	active = models.BooleanField(_("Visible on the site"), default=False)
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
		return "<a href='%s'>%s</a>" % (self.get_absolute_url(), 
			ugettext("View on site"))
	admin_link.allow_tags = True
	admin_link.short_description = ""
	
	def admin_thumb(self):
		if self.image is None:
			return ""
		from shop.templatetags.shop_tags import thumbnail
		thumb_url = "%s%s" % (settings.MEDIA_URL, thumbnail(self.image, 24, 24))
		return "<img src='%s' />" % thumb_url
	admin_thumb.allow_tags = True
	admin_thumb.short_description = ""

class Category(ShopModel):

	class Meta:
		verbose_name = _("Category")
		verbose_name_plural = _("Categories")

	image = models.ImageField(_("Image"), max_length=100, blank=True, 
		upload_to="category")
	parent = models.ForeignKey("self", blank=True, null=True, 
		related_name="children")

class PricedModel(models.Model):
	"""
	abstract model with unit and sale price fields - for product and variation
	"""

	class Meta:
		abstract = True

	unit_price = MoneyField(_("Unit price"))
	sale_id = models.IntegerField(null=True)
	sale_price = MoneyField(_("Sale price"))
	sale_from = models.DateTimeField(_("Sale start"), blank=True, null=True)
	sale_to = models.DateTimeField(_("Sale end"), blank=True, null=True)

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

class Product(ShopModel, PricedModel):
	"""
	container model for a product
	"""

	class Meta:
		verbose_name = _("Product")
		verbose_name_plural = _("Products")

	description = models.TextField(_("Description"), blank=True)
	available = models.BooleanField(_("Available for purchase"), default=False)
	image = models.CharField(max_length=100, blank=True, null=True)
	categories = models.ManyToManyField(Category, blank=True, 
		related_name="products")
	
	def set_image(self):
		"""
		stores the main image against the image field for direct access
		"""
		image = self._product.variations.get(default=True).image
		if image is None:
			image = self._product.images.all()[:1]
			if len(image) == 1:
				image = image[0]
		if image:
			image = image.file.name
		else:
			image = None
		self.image = image
		self.save()

class ProductImage(models.Model):
	"""
	images related to a product - also given a 1to1 relationship with variations
	"""
	
	class Meta:
		verbose_name = _("Image")
		verbose_name_plural = _("Images")
	
	file = models.ImageField(_("Image"), max_length=100, blank=True, 
		upload_to="product")
	description = models.CharField(_("Description"), max_length=100, unique=True)
	product = models.ForeignKey(Product, related_name="images")
	
	def __unicode__(self):
		return self.description

class BaseProductVariation(PricedModel):
	"""
	abstract model used to create the ProductVariation model below using 
	dynamically created set of option fields from shop.settings.PRODUCT_OPTIONS
	"""
	
	class Meta:
		abstract = True
		ordering = ("default",)
		
	product = models.ForeignKey(Product, related_name="variations")
	sku = SKUField(unique=True)
	quantity = models.IntegerField(_("Number in stock"), blank=True, null=True) 
	default = models.BooleanField(_("Default"))
	image = models.OneToOneField(ProductImage, null=True, blank=True)
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
		if self.default:
			product = self.product
			for field in ("unit_price", "sale_price", "sale_from", "sale_to"):
				setattr(product, field, getattr(self, field))
			product.save()

	@classmethod
	def option_fields(cls):
		return [field for field in cls._meta.fields 
			if isinstance(field, OptionField)]
	
	def options(self):
		return [getattr(self, field.name) for field in self.option_fields()]

	def has_stock(self, quantity=1):
		"""
		check the given quantity is in stock taking carts into account the 
		number in carts, and cache the number
		"""
		if self.quantity is None:
			return True
		if not hasattr(self, "_cached_num_available"):
			num_available = self.quantity
			in_carts = CartItem.objects.filter(sku=self.sku).aggregate(
				quantity_sum=models.Sum("quantity"))["quantity_sum"]
			if in_carts is not None:
				num_available = num_available - in_carts
			self._cached_num_available = num_available
		return self._cached_num_available >= quantity

# build the ProductVariation model from the BaseProductVariation model by
# adding each option in shop.settings.PRODUCT_OPTIONS as an OptionField
ProductVariation = clone_model("ProductVariation", BaseProductVariation, 
	dict([(option[0], OptionField(choices=make_choices(option[1]))) 
	for option in PRODUCT_OPTIONS]))

class Address(models.Model):
	"""
	abstract model used to create new models via Address.make() - new models
	are billing and shipping with the Order model inherits from below 
	"""
	
	class Meta:
		abstract = True

	first_name = models.CharField(_("First name"), max_length=100)
	last_name = models.CharField(_("Last name"), max_length=100)
	street = models.CharField(_("Street"), max_length=100)
	city = models.CharField(_("City/Suburb"), max_length=100)
	state = models.CharField(_("State/Region"), max_length=100)
	postcode = models.CharField(_("Zip/Postcode"), max_length=10)
	country = models.CharField(_("Country"), max_length=100)
	phone = models.CharField(_("Phone"), max_length=20)
	
	@classmethod
	def clone(cls, field_prefix):
		"""
		return a new model with the same fields as Address named using the 
		given PREFIX, as well as a PREFIX_fields and PREFIX_field_names methods 
		for accessing the address fields and field names by prefix
		"""
		def field_names_by_prefix(cls):
			return [f.name for f in cls._meta.fields 
				if f.name.startswith(field_prefix)]
		def fields_by_prefix(instance):
			return [{"name": f.verbose_name, "value": getattr(instance, f.name)} 
				for f in instance._meta.fields if f.name.startswith(field_prefix)]
		fields = dict([("%s_%s" % (field_prefix, f.name), copy(f)) 
			for f in cls._meta.fields if not isinstance(f, models.AutoField)])
		fields.update({"%s_fields" % field_prefix: fields_by_prefix, 
			"%s_field_names" % field_prefix: classmethod(field_names_by_prefix)})
		name = "".join(s.title() for s in field_prefix.split("_"))
		return clone_model(name, models.Model, fields, abstract=True)

class Order(Address.clone("billing_detail"), Address.clone("shipping_detail")):

	class Meta:
		verbose_name = _("Order")
		verbose_name_plural = _("Orders")

	billing_detail_email = models.EmailField(_("Email"))
	additional_instructions = models.TextField(_("Additional instructions"), 
		blank=True)
	time = models.DateTimeField(_("Time"), auto_now_add=True)
	shipping_type = models.CharField(_("Shipping type"), max_length=50, 
		blank=True)
	shipping_total = MoneyField(_("Shipping total"))
	item_total = MoneyField(_("Item total"))
	total = MoneyField(_("Order total"))
	status = models.IntegerField(_("Status"), choices=ORDER_STATUSES, 
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

	last_updated = models.DateTimeField(_("Last updated"), auto_now=True)
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
			item.unit_price = variation.price()
			item.url = variation.product.get_absolute_url()
			image = variation.image
			if image is not None:
				item.image = image.file.name
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
	description = models.CharField(_("Description"), max_length=200)
	quantity = models.IntegerField(_("Quantity"), default=0)
	unit_price = MoneyField(_("Unit price"), default=Decimal("0"))
	total_price = MoneyField(_("Total price"), default=Decimal("0"))
	
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

