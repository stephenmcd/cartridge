
from django.contrib import admin
from shop.models import Category, Product, ProductVariation, Order, OrderItem
from shop.fields import MoneyField
from shop.forms import MoneyWidget, ProductAdminForm

# lists of field names
option_fields = [field.name for field in ProductVariation.option_fields()]
image_fields = [field.name for field in Product.image_fields()]
billing_fields = Order.billing_field_names()
shipping_fields = Order.shipping_field_names()

		
class CategoryAdmin(admin.ModelAdmin):
	ordering = ("parent","title")
	list_display = ("title","parent","active","admin_link")
	list_editable = ("parent","active")
	list_filter = ("parent",)
	search_fields = ("title","parent__title","product_set__title")	

class ProductVariationAdmin(admin.TabularInline):
	verbose_name_plural = "Current variations"
	model = ProductVariation
	exclude = option_fields
	extra = 0
	
class ProductAdmin(admin.ModelAdmin):

	list_display = ("title","unit_price","active","available","admin_link")
	list_editable = ("unit_price","active","available")
	list_filter = ("categories","active","available")
	filter_horizontal = ("categories",)
	search_fields = ("title","categories__title","variations_sku")
	inlines = (ProductVariationAdmin,)
	form = ProductAdminForm
	formfield_overrides = {MoneyField: {"widget": MoneyWidget}}

	fieldsets = (
		(None, {"fields": 
			("title", "description", ("active", "available"), "categories")}),
		("Pricing", {"fields": 
			("unit_price", ("sale_price", "sale_from", "sale_to"))}),
		("Images", {"fields": image_fields}),
		("Create new variations", {"fields": option_fields}),
	)

	def save_model(self, request, obj, form, change):
		"""
		store the product object for creating variations in save_formset
		"""
		super(ProductAdmin, self).save_model(request, obj, form, change)
		self._product = obj

	def save_formset(self, request, form, formset, change):
		"""
		create variations for selected options if they don't exist, and also
		manage the default empty variation, creating it if no variations exist 
		or removing it if multiple variations exist 
		"""
		super(ProductAdmin, self).save_formset(request, form, formset, change)
		# build a list of field names for options that are selected, and a list 
		# of field values containing the lists of selected options aligned to 
		# the list of field names, and then create all unique variations from
		# the selected options
		option_names = [f for f in option_fields if request.POST.getlist(f)]
		if option_names:
			option_values = [request.POST.getlist(f) for f in option_names] 
			variations = [[]]
			# cartesian product of selected options
			for values_list in option_values:
				variations = [x + [y] for x in variations for y in values_list]
			for v in variations:
				# lookup unselected options as null to ensure a unique filter
				variation = dict(zip(option_names, v))
				lookup = dict(variation)
				lookup.update(dict([("%s__isnull" % field, True) 
					for field in option_fields if field not in variation]))
				try:
					self._product.variations.get(**lookup)
				except ProductVariation.DoesNotExist:
					self._product.variations.create(**variation)
		# create an empty variation (no options) if none exist, otherwise if 
		# multiple variations exist ensure there is no redundant empty variation
		total_variations = self._product.variations.count()
		if total_variations == 0:
			self._product.variations.create()
		elif total_variations > 1:
			no_options = dict([("%s__isnull" % f, True) for f in option_fields])
			self._product.variations.filter(**no_options).delete()

class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0

class OrderAdmin(admin.ModelAdmin):

	ordering = ("status","-id")
	list_display = ("id","billing_name","total","time","status")
	list_editable = ("status",)
	list_filter = ("status","time")
	list_display_links = ("id","billing_name",)
	search_fields = ["id","status"] + billing_fields + shipping_fields
	date_hierarchy = "time"
	radio_fields = {"status": admin.HORIZONTAL}
	inlines = (OrderItemInline,)
	formfield_overrides = {MoneyField: {"widget": MoneyWidget}}
	fieldsets = (
		("Billing details", {"fields": (tuple(billing_fields),)}),
		("Shipping details", {"fields": (tuple(shipping_fields),)}),
		(None, {"fields": ("additional_instructions",
			("shipping_total","shipping_type"),"item_total",("total","status"))}),
	)


admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)

