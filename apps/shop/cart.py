
class Cart(object):

	def __init__(self, request):
		self._request = request
		self._items = []
		self.total_items = 0
		self.total_value = 0
		if "cart" in request.session:
			self.__dict__.update(request.session["cart"])

	def _modified(self):
		self.total_items = 0
		self.total_value = 0
		for item in self:
			self.total_items += item["quantity"]
			self.total_value += item["quantity"] * item["unit_price"]
		request = self.__dict__.pop("_request")
		request.session["cart"] = self.__dict__

	def __iter__(self):
		return iter(self._items)
		
	def has_items(self):
		return len(self._items) > 0 
		
	def add_item(self, product, options):
		quantity = options.pop("quantity")
		new_item = {
			"description": product.title,
			"quantity": quantity,
			"sku": product.id,
			"url": product.get_absolute_url(),
			"unit_price": product.actual_price(),
			"total_price": quantity * product.actual_price(),
		}
		if options:
			new_item["sku"] = product.variations.get(**options).sku
			options = ", ".join(["%s: %s" % option for option in 
				sorted(options.items())])
			new_item["description"] += " - %s" % options
		for i, item in enumerate(self):
			if item["sku"] == new_item["sku"]:
				self._items[i]["quantity"] += new_item["quantity"]
				break
		else:
			self._items.insert(0, new_item)
		self._modified()
	
	def remove_item(self, sku):
		for i, item in list(enumerate(self)):
			if str(item["sku"]) == sku:
				del self._items[i]
				self._modified()
				break

