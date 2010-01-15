
from locale import localeconv
from django.db.models import CharField, DecimalField
from shop.utils import set_locale


class OptionField(CharField):
	"""
	a field representing a selectable option for products such as colour or size
	"""
	
	def __init__(self, *args, **kwargs):
		"""
		null must be true and max_length can be derived from choices
		"""
		kwargs["null"] = True
		if "max_length" not in kwargs:
			kwargs["max_length"] = max([len(c[0]) for c in kwargs["choices"]])
		super(OptionField, self).__init__(*args, **kwargs)

class MoneyField(DecimalField):

	def __init__(self, *args, **kwargs):
		set_locale()
		defaults = {"null": True, "blank": True, 
			"max_digits": 10, "decimal_places": localeconv()["frac_digits"]}
		defaults.update(kwargs)
		super(MoneyField, self).__init__(*args, **defaults)

class SKUField(CharField):
	
	def __init__(self, *args, **kwargs):
		if not args:
			args = ("SKU",)
		defaults = {"max_length": 20}
		defaults.update(kwargs)
		super(SKUField, self).__init__(*args, **defaults)

