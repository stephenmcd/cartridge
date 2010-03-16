Components
==========

The following section describes the various components within Cartidge and mostly describes the Django models used. All of the models referred to in this section are contained in the module ``shop.models`` and all of the admin classes referred to are contained in the module ``shop.admin``.

Categories
----------

The ``Category`` model provides the navigational tree structure for organising products throughout the site. This structure is stored using the self referencing ForeignKeyField ``Category.parent`` and rendered on both the site and in the admin via the ``category_menu`` and  ``category_menu_admin`` template tags respectively. When viewing the list of categories in the admin, the listing template is overriden with a custom ``change_list.html`` template that allows the category tree to be managed.

**Inheritance:** The ``Category`` model inherits from the abstract model ``Displayable`` which provides common features for a displayable item on the site such as the item's title, automatic generation of slug fields via ``Displayable.save`` and a Boolean field ``Displayable.active`` for controlling whether or not the item is visible on the site.

The ``Category`` model also contains a ManyToManyField ``Category.products`` that contains the products assigned to the category, although this is defined in the ``Product`` model described below.

Products
--------

Products are the cornerstone of Cartridge and are made up from three separate models. Firstly the model ``Product`` provides the container for storing the core attributes of a product. The other two models are ``ProductImage`` and ``ProductVariation`` which each contain a ForeignKeyField to ``Product`` and can be accessed via ``Product.images`` and ``Product.variations`` respectively.

**Inheritance:** Like the ``Category`` model, the ``Product`` model inherits from the abstract model ``Displayable``. It also inherits from the abstract model ``Priced`` which provides common features for an item that has a price. The fields provided by the ``Priced`` model are not editable via the admin - the rationale for this is discussed below under :ref:`ref-denormalized-fields`. The ``Priced`` model itself is discussed below under :ref:`ref-product-variations`.

Product Images
^^^^^^^^^^^^^^

The ``ProductImage`` model is a simple container for storing an image file against a product. It contains an ImageField ``ProductImage.file`` and a CharField ``ProductImage.description`` which gives the image a meaningful description. The description provides a means of identifying the image so that it can be easily selected as the related image for the ``ProductVariation`` model which contains a nullable (optional) reference to the ``ProductImage`` model via the ForeignKeyField ``ProductVariation.image``, which is described next in :ref:`ref-product-variations`.

.. _ref-product-variations:

Product Variations
^^^^^^^^^^^^^^^^^^

The ``ProductVariation`` model represents a unique combination of options for a product. Consider a shirt that comes in two colours and three sizes: this would be represented with a single ``Product`` instance for the shirt, and six ``ProductVariation`` instances, one for each colour/size combination. The configuration of available options such as colours and sizes is discussed in the section :ref:`ref-configuration`.

The ``ProductVariation`` model is editable via the admin as the inline ``ProductVariationAdmin`` for the ``ProductAdmin`` admin, however the attribute ``ProductVariationAdmin.extra`` is set to ``0`` and therefore ``ProductVariation`` instances cannot be added via the admin. Instead when editing ``Product`` instances via the admin, a list of checkboxes is provided with the form for each type of option available such as colour and size, with a checkbox provided for each of the individual options. When the ``Product`` instance is saved, a set of related ``ProductVariation`` instances will be created for each combination of options that are checked. If no options are selected when creating a new ``Product`` instance, then a single ``ProductVariation`` instance will be created without any associated options. This means that a ``Product`` instances will *always* contains at least one related ``ProductVariation`` instance. All of this occurs via the ``ProductAdmin.save_formset`` method and shows that the process of creating a new ``Product`` instance will always require two steps: firstly, creating the ``Product`` instance with its core attributes and secondly, entering values for one or more related ``ProductVariation`` instances that are automatically created for each combination of options.

**Inheritance:** The ``ProductVariation`` model is dynamically constructed from the abstract model ``BaseProductVariation`` which defines all of the functionality described in this section, and for convenience is referred to as the ``ProductVariation`` model. The process of dynamically constructing the ``ProductVariation`` model exists in order to create an OptionField for each of the types of configured options such as colour or size. Like the ``Product`` model, the ``ProductVariation`` model inherits from the abstract model ``Priced``, however the fields provided by the ``Priced`` model in this case are editable in the admin via the inline admin ``ProductVariationAdmin``. These fields are ``Priced.unit_price`` for the base price, ``Priced.sale_price`` and both the  DateTimeField ``Priced.sale_from`` and the DateTimeField ``Priced.sale_to`` which together define a sale price with a date range specifying when the sale price is applicable. The ``Priced`` model contains convenience methods such as ``Priced.on_sale`` for checking whether the current price is a sale price, ``Priced.has_price`` for checking whether there is a current price at all, and ``Priced.price`` which returns the current price being either ``Priced.unit_price`` or ``Priced.sale_price`` if applicable.

The ``ProductVariation`` model also contains an `SKUField <http://en.wikipedia.org/wiki/Stock-keeping_unit>`_ ``ProductVariation.sku`` which must be unique and a ForeignKeyField ``ProductVariation.image`` which allows a ``ProductImage`` instance to optionally be related to the ``ProductVariation`` instance.

The ``ProductVariation`` model also contains a BooleanField ``ProductVariation.default`` which is used to specify which ``ProductVariation`` instance to use when displaying the related ``Product`` instance on the site. Only one ``ProductVariation`` instance can have this field set to ``True`` and this constraint is managed within the ``ProductAdmin.save_formset`` method referred to above.

.. _ref-denormalized-fields:

Denormalized Fields
^^^^^^^^^^^^^^^^^^^

Certain fields are duplicated for the ``Product`` model in order to avoid querying the database for ``ProductImage`` and ``ProductVariation`` instances when a large number of products are being interated through on the site and the product's image or price need to be displayed. These fields are those provided by the ``Priced`` abstract model which both the ``Product`` and ``ProductVariation`` models inherit from, as well a CharField ``Product.image`` which stores the location of the image in the related ``ProductImage`` instance that is determined to be the default for display. The values for these fields are set for the ``Product`` instance when the  ``ProductAdmin.save_formset`` method is run as referred to above. The  ``ProductVariation.default`` field is used to determine which ``ProductVariation`` instance's ``Priced`` fields are duplicated. The ``ProductImage`` related to the ``ProductVariation`` instance is used for the ``Product.image`` field if selected, otherwise the first ``ProductImage`` instance related to the ``Product`` instance is used.

Wishlists
---------

Discounts
---------

Sales
^^^^^

Discount Codes
^^^^^^^^^^^^^^

Carts
-----

Orders
------
