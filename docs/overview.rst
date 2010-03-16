Overview
--------

Cartridge is contained entirely within a single reusable Django application named ``shop``. It aims to follow standard Django idioms with models contained in ``shop.models``, views contained in ``shop.views`` and so forth.

Several non-standard modules are provided such as ``shop.utils``, which is discussed in the section :ref:`ref-utilities` and ``shop.checkout``, which is discussed in the section :ref:`ref-integration`. Several admin templates are overriden which can be found under ``shop.templates.admin`` and all template tags are provided under the module ``shop.templatetags.shop_tags``.

