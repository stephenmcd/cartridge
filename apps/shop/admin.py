
from django.contrib import admin
from django.db.models import ImageField
from django.utils.translation import ugettext_lazy as _

from shop.fields import MoneyField
from shop.forms import ProductAdminForm, ProductVariationAdminForm, \
	ProductVariationAdminFormset, DiscountAdminForm, ImageWidget, MoneyWidget
from shop.models import Category, Product, ProductImage, ProductVariation, \
	Order, OrderItem, Sale, DiscountCode


# lists of field names
option_fields = [field.name for field in ProductVariation.option_fields()]
billing_fields = Order.billing_detail_field_names()
shipping_fields = Order.shipping_detail_field_names()

		
class CategoryAdmin(admin.ModelAdmin):
	formfield_overrides = {ImageField: {"widget": ImageWidget}}

class ProductVariationAdmin(admin.TabularInline):
	verbose_name_plural = _("Current variations")
	model = ProductVariation
	fields = ("sku", "default", "num_in_stock", "unit_price", "sale_price", 
		"sale_from", "sale_to", "image")
	extra = 0
	formfield_overrides = {MoneyField: {"widget": MoneyWidget}}
	form = ProductVariationAdminForm
	formset = ProductVariationAdminFormset

class ProductImageAdmin(admin.TabularInline):
	model = ProductImage
	extra = 20 
	formfield_overrides = {ImageField: {"widget": ImageWidget}}
	
class ProductAdmin(admin.ModelAdmin):

	list_display = ("admin_thumb", "title", "active", "available", "admin_link")
	list_display_links = ("admin_thumb", "title")
	list_editable = ("active", "available")
	list_filter = ("active", "available", "categories")
	filter_horizontal = ("categories",)
	search_fields = ("title", "categories__title", "variations__sku")
	inlines = (ProductImageAdmin, ProductVariationAdmin)
	form = ProductAdminForm
	fieldsets = (
		(None, {"fields": ("title", "description", ("active", "available"), 
			"keywords", "categories")}),
		(_("Create new variations"), {"classes": ("create-variations",), 
			"fields": option_fields}),
	)

	def save_model(self, request, obj, form, change):
		"""
		store the product object for creating variations in save_formset
		"""
		super(ProductAdmin, self).save_model(request, obj, form, change)
		self._product = obj

	def save_formset(self, request, form, formset, change):
		"""
		create variations for selected options if they don't exist, manage the 
		default empty variation creating it if no variations exist or removing 
		it if multiple variations exist, and copy the pricing and image fields
		from the default variation to the product
		"""
		super(ProductAdmin, self).save_formset(request, form, formset, change)
		if isinstance(formset, ProductVariationAdminFormset):
			options = dict([(f, request.POST.getlist(f)) for f in option_fields 
				if request.POST.getlist(f)])
			self._product.variations.create_from_options(options)
			self._product.variations.manage_empty()
			self._product.copy_default_variation()

class OrderItemInline(admin.TabularInline):
	verbose_name_plural = _("Items")
	model = OrderItem
	extra = 0
	formfield_overrides = {MoneyField: {"widget": MoneyWidget}}

class OrderAdmin(admin.ModelAdmin):
	ordering = ("status", "-id")
	list_display = ("id", "billing_name", "total", "time", "status")
	list_editable = ("status",)
	list_filter = ("status", "time")
	list_display_links = ("id", "billing_name",)
	search_fields = ["id", "status"] + billing_fields + shipping_fields
	date_hierarchy = "time"
	radio_fields = {"status": admin.HORIZONTAL}
	inlines = (OrderItemInline,)
	formfield_overrides = {MoneyField: {"widget": MoneyWidget}}
	fieldsets = (
		(_("Billing details"), {"fields": (tuple(billing_fields),)}),
		(_("Shipping details"), {"fields": (tuple(shipping_fields),)}),
		(None, {"fields": ("additional_instructions", ("shipping_total", 
			"shipping_type"), ("discount_total", "discount_code"), 
			"item_total",("total", "status"))}),
	)

class SaleAdmin(admin.ModelAdmin):
	list_display = ("title", "active", "discount_deduct", "discount_percent", 
		"discount_exact", "valid_from", "valid_to")
	list_editable = ("active", "discount_deduct", "discount_percent", 
		"discount_exact", "valid_from", "valid_to")
	filter_horizontal = ("categories", "products")
	formfield_overrides = {MoneyField: {"widget": MoneyWidget}}
	form = DiscountAdminForm
	fieldsets = (
		(None, {"fields": ("title", "active")}),
		(_("Apply to product and/or products in categories"), 
			{"fields": ("products", "categories")}),
		(_("Reduce unit price by"), 
			{"fields": (("discount_deduct", "discount_percent", 
			"discount_exact"),)}),
		(_("Sale period"), {"fields": (("valid_from", "valid_to"),)}),
	)

class DiscountCodeAdmin(admin.ModelAdmin):
	list_display = ("title", "active", "code", "discount_deduct", 
		"discount_percent", "min_purchase", "free_shipping", "valid_from", 
		"valid_to")
	list_editable = ("active", "code", "discount_deduct", "discount_percent", 
		"min_purchase", "free_shipping", "valid_from", "valid_to")
	filter_horizontal = ("categories", "products")
	formfield_overrides = {MoneyField: {"widget": MoneyWidget}}
	form = DiscountAdminForm
	fieldsets = (
		(None, {"fields": ("title", "active", "code")}),
		(_("Apply to product and/or products in categories"), 
			{"fields": ("products", "categories")}),
		(_("Reduce unit price by"), 
			{"fields": (("discount_deduct", "discount_percent"),)}),
		(None, {"fields": (("min_purchase", "free_shipping"),)}),
		(_("Valid for"), {"fields": (("valid_from", "valid_to"),)}),
	)

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(DiscountCode, DiscountCodeAdmin)

