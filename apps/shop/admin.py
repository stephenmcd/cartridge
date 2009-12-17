
from django.contrib import admin
from shop.models import Category, Product, Order, OrderItem, _Address

class CategoryAdmin(admin.ModelAdmin):

	ordering = ("parent","title")
	list_display = ("title","parent","active")
	list_editable = ("parent","active")
	list_filter = ("parent",)
	search_fields = ("title","parent__title","product_set__title")	

class ProductAdmin(admin.ModelAdmin):

	list_display = ("title","regular_price","active")
	list_editable = ("regular_price","active")
	list_filter = ("categories",)
	filter_horizontal = ("categories",)
	search_fields = ("title","categories__title",)

	fieldsets = (
		(None, {"fields": ("title", "description", ("active", "available"),
			"categories")}),
		("Images", {"fields": (Product.image_fields(),)}),
		("Pricing", {"fields": ("regular_price", 
			("sale_price","sale_from","sale_to"))}),
		("Options", {"fields": (Product.option_fields(),)}),
	)

class OrderItemInline(admin.TabularInline):

	model = OrderItem
	extra = 0

_fields = {}
for fieldset in ("billing", "shipping"):
	_fields[fieldset] = [order_field.name for order_field in Order._meta.fields 
		if order_field.name.startswith(fieldset) and order_field.name in 
		["%s_%s" % (fieldset, address_field.name) for address_field in 
		_Address._meta.fields]]

class OrderAdmin(admin.ModelAdmin):

	ordering = ("status","-id")
	list_display = ("id","billing_name","total","time","status")
	list_editable = ("status",)
	list_filter = ("status","time")
	list_display_links = ("id","billing_name",)
	search_fields = ["id","status"] + _fields["shipping"] + _fields["billing"]
	date_hierarchy = "time"
	radio_fields = {"status": admin.HORIZONTAL}

	fieldsets = (
		("Shipping details", {"fields": (tuple(_fields["shipping"]),)}),
		("Billing details", {"fields": (tuple(_fields["billing"]),)}),
		(None, {"fields": ("additional_instructions",
			("shipping","shipping_type"),("total","status"))}),
	)
	inlines = (OrderItemInline,)

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)

