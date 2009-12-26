
class Cart(object):
	"""
	cart object - stores a list of product items persisted via sessions
	"""

	def __init__(self, request):
		"""
		store the request for later writing our items to the session when 
		modified and retrieve our items from the session if they exist
		"""
		self._request = request
		self._items = []
		if "cart" in request.session:
			self._items = request.session["cart"]

	def _save(self):
		"""
		called when items are modified - persist items in session
		"""
		self._request.session["cart"] = self._items

	def __iter__(self):
		"""
		template helper function - iterating through the cart iterates items
		"""
		return iter(self._items)
		
	def has_items(self):
		"""
		template helper function - does the cart have items
		"""
		return len(self._items) > 0 
	
	def total_items(self):
		"""
		template helper function - sum of all item quantities
		"""
		return sum([item["quantity"] for item in self])
		
	def total_value(self):
		"""
		template helper function - sum of all costs of item quantities
		"""
		return sum([item["quantity"] * item["price"] for item in self])
		
	def add_item(self, product, options):
		"""
		add the given product and options to the cart - options is cleaned_data
		dict from shop.forms.AddCartForm
		"""

		quantity = options.pop("quantity")
		new_item = {
			"description": product.title,
			"quantity": quantity,
			"sku": product.sku if product.sku else product.id,
			"url": product.get_absolute_url(),
			"price": product.price(),
			"total_price": quantity * product.price(),
		}
		# if options are selected determine the sku for the variation
		if options:
			variation = product.variations.get(**options)
			new_item["sku"] = variation.sku
			new_item["description"] += " - %s" % variation
		# if the sku exists in the cart, increase the quantity and update item
		for i, item in enumerate(self):
			if item["sku"] == new_item["sku"]:
				new_item["quantity"] += self._items[i]["quantity"]
				new_item["total_price"] = new_item["quantity"] * new_item["price"]
				self._items[i].update(new_item)
				break
		else:
			self._items.insert(0, new_item)
		self._save()
	
	def remove_item(self, sku):
		"""
		remove the given sku from the cart
		"""
		
		for i, item in list(enumerate(self)):
			if str(item["sku"]) == str(sku):
				del self._items[i]
				self._save()
				break

