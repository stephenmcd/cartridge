
class Cart(object):

	def __init__(self, request):
		self._request = request
		self._items = []
		self._item_index = 0
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
		description = product.title
		quantity = options.pop("quantity")
		options = ", ".join(["%s: %s" % option for option in 
			sorted(options.items())])
		if options:
			description = "%s - %s" % (description, options)
		for i, item in enumerate(self):
			if item["description"] == description:
				self._items[i]["quantity"] += quantity
				break
		else:
			self._item_index += 1
			self._items.insert(0, {
				"index": self._item_index,
				"description": description, 
				"url": product.get_absolute_url(),
				"quantity": quantity, 
				"product_id": product.id,
				"unit_price": product.actual_price(),
				"total_price": quantity * product.actual_price(),
			})
		self._modified()
	
	def remove_item(self, index):
		for i, item in list(enumerate(self)):
			if str(item["index"]) == index:
				del self._items[i]
				self._modified()
				break

