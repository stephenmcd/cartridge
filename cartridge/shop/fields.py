"""
Various model fields that mostly provide default field sizes to ensure
these are consistant when used across multiple models.
"""

from __future__ import absolute_import, unicode_literals
from future.builtins import super

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


class PercentageField(DecimalField):
    """
    A field for representing a percentage. Sets restrictions on admin
    form fields to ensure it is between 0-100.
    """
    def formfield(self, *args, **kwargs):
        defaults = {'min_value': 0, 'max_value': 100}
        kwargs.update(**defaults)
        return super(PercentageField, self).formfield(*args, **kwargs)


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
        if not args and "verbose_name" not in kwargs:
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
