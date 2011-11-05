"""
Various model fields that mostly provide default field sizes to ensure
these are consistant when used across multiple models.
"""

from locale import localeconv

from django.db.models import CharField, DecimalField
from django.utils.translation import ugettext_lazy as _

from cartridge.shop.utils import set_locale


class OptionField(CharField):
    """
    A field for a selectable option of a product such as colour or
    size. Ensure ``null`` is ``True`` and provide a default field size.
    """
    def __init__(self, *args, **kwargs):
        kwargs["null"] = True
        defaults = {"max_length": 50}
        defaults.update(kwargs)
        super(OptionField, self).__init__(*args, **defaults)


class MoneyField(DecimalField):
    """
    A field for a monetary amount. Provide the default size and
    precision.
    """
    def __init__(self, *args, **kwargs):
        set_locale()
        defaults = {"null": True, "blank": True, "max_digits": 10,
                    "decimal_places": localeconv()["frac_digits"]}
        defaults.update(kwargs)
        super(MoneyField, self).__init__(*args, **defaults)


class SKUField(CharField):
    """
    A field for a product SKU. Provide the name and default field size.
    """
    def __init__(self, *args, **kwargs):
        if not args:
            args = (_("SKU"),)
        defaults = {"max_length": 20}
        defaults.update(kwargs)
        super(SKUField, self).__init__(*args, **defaults)


class DiscountCodeField(CharField):
    """
    A field for Discount Codes. Provide the default field size.
    """
    def __init__(self, *args, **kwargs):
        defaults = {"max_length": 20}
        defaults.update(kwargs)
        super(DiscountCodeField, self).__init__(*args, **defaults)

# South requires custom fields to be given "rules".
# See http://south.aeracode.org/docs/customfields.html
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules(rules=[((OptionField, MoneyField, SKUField,
        DiscountCodeField), [], {})], patterns=["cartridge\.shop\.fields\."])
except ImportError:
    pass
