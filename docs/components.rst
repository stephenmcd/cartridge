==========
Components
==========

The following section describes the various components of Cartridge and the Django models used.

Categories
==========

A category is the main approach for displaying products on the website.
Categories in Cartridge are implemented as Mezzanine pages. Consult the
`Mezzanine documentation
<http://mezzanine.jupo.org/docs/content-architecture.html#the-page-model>`_ for a detailed overview of how pages are implemented in Mezzanine.

Products
========

Products are the cornerstone of Cartridge and are made up from three
separate models. First, the model ``Product`` provides the container for
storing the core attributes of a product. The other two models are
``ProductImage`` and ``ProductVariation`` which each contain a
ForeignKeyField to ``Product`` and can be accessed via ``Product.images``
and ``Product.variations`` respectively.

As with the ``Category`` model, the ``Product`` model inherits from the
abstract model ``Displayable``, which provides the model with features such as a URL/slug, and publish dates. It also inherits from the abstract model
``Priced`` which is discussed next. The fields provided by the ``Priced``
model are not editable via the admin. The rationale for this is discussed
later in :ref:`ref-denormalized-fields`.

.. _ref-priced-items:

Priced Items
------------

The ``Priced`` abstract model provides common features for an item that
has a price. It contains fields such as ``Priced.unit_price`` for the base
price and three fields that control whether the given item is on sale:

    * ``Priced.sale_price`` for the sale price
    * ``Priced.sale_from`` DateTimeField for the start of the sale
    * ``Priced.sale_to`` DateTimeField for the end of the sale

The ``Priced`` model also contains several convenience methods:

    * ``Priced.on_sale()`` for checking whether the current price is a sale price
    * ``Priced.has_price()`` for checking whether there is a current price at all
    * ``Priced.price()`` which returns the current price of either ``Priced.unit_price`` or ``Priced.sale_price`` if applicable

The ``Priced`` abstract model is inherited by the ``Product`` model
previously discussed and the ``ProductVariation`` model discussed next.

Product Variations
------------------

The ``ProductVariation`` model represents a unique combination of options
for a product. Consider a shirt that comes in two colours and three sizes:
these combinations would be represented with a single ``Product`` instance for the shirt
and six ``ProductVariation`` instances: one for each colour/size combination.
These options are discussed below in :ref:`ref-product-options`.

The ``ProductVariation`` model is editable via the admin as the inline
``ProductVariationAdmin`` for the ``ProductAdmin`` admin; however, the
attribute ``ProductVariationAdmin.extra`` is set to ``0`` and therefore
``ProductVariation`` instances cannot be added via the admin. Instead, when
editing ``Product`` instances via the admin, a list of check-boxes is
provided with the form, for each type of option available such as colour
and size, with a check-box provided for each individual option.
When the ``Product`` instance is saved, a set of related ``ProductVariation``
instances will be created for each combination of options that are checked.
If no options are selected when creating a new ``Product`` instance, then
a single ``ProductVariation`` instance will be created without any
associated options. This means that a ``Product`` instances will *always*
contains at least one related ``ProductVariation`` instance. All of this
occurs via the ``ProductAdmin.save_formset()`` method and shows that the
process of creating a new ``Product`` instance will always require two
steps: first, creating the ``Product`` instance with its core attributes; and
second, entering values for one or more related ``ProductVariation``
instances that are automatically created for each combination of options.

The ``ProductVariation`` model is dynamically constructed from the abstract
model ``BaseProductVariation`` which defines all of the functionality
discussed in this section, but for convenience is referred to as the
``ProductVariation`` model. The process of dynamically constructing the
``ProductVariation`` model exists in order to create an OptionField for
each of the types of configured options such as colour or size. Like the
``Product`` model, the ``ProductVariation`` model inherits from the
abstract model ``Priced``. However, the fields provided by the ``Priced``
model in this case are editable in the admin via the inline admin
``ProductVariationAdmin``.

The ``ProductVariation`` model also contains an `SKUField
<http://en.wikipedia.org/wiki/Stock-keeping_unit>`_ ``ProductVariation.sku``,
which must be unique, and a ForeignKeyField ``ProductVariation.image``
which allows a ``ProductImage`` instance to optionally be related to the
``ProductVariation`` instance.

The ``ProductVariation`` model also contains a BooleanField
``ProductVariation.default`` which is used to specify which
``ProductVariation`` instance to use when displaying the related
``Product`` instance on the site. Only one ``ProductVariation`` instance
can have this field set to ``True``, and this constraint is managed within
the ``ProductAdmin.save_formset()`` method referred to above.

Product Images
--------------

The ``ProductImage`` model is a simple container for storing an image
file against a related ``Product`` instance. It contains an ImageField
``ProductImage.file`` and a CharField ``ProductImage.description`` which
gives the image a meaningful description. The description provides a means
of identifying the image so that it can be easily selected as the related
image for the ``ProductVariation`` model which contains a nullable
(optional) reference to the ``ProductImage`` model via the ForeignKeyField
``ProductVariation.image``.

.. _ref-denormalized-fields:

Denormalized Fields
-------------------

Certain fields are duplicated for the ``Product`` model in order to avoid
querying the database for ``ProductImage`` and ``ProductVariation``
instances when a large number of products are being iterated through on the
site and the product's image or price need to be displayed. These duplicate fields
are provided by the ``Priced`` abstract model from which both the ``Product``
and ``ProductVariation`` models inherit, as well a CharField
``Product.image`` which stores the location of the image in the related
``ProductImage`` instance that is determined to be the default for display.
The values for these fields are set for the ``Product`` instance when the
``ProductAdmin.save_formset()`` method is run as referred to above. The
``ProductVariation.default`` field is used to determine which
``ProductVariation`` instance's ``Priced`` fields are duplicated. The
``ProductImage`` related to the ``ProductVariation`` instance is used for
the ``Product.image`` field if selected; otherwise, the first
``ProductImage`` instance related to the ``Product`` instance is used.

.. _ref-product-options:

Product Options
---------------

The ``ProductOption`` model provides a simple type and name for a
selectable option for a ``ProductVariation`` instance (for example, Size:
Small or Colour: Red). For performance and simplicity, these options don't
use a model relationship with the ``ProductVariation`` model but simply
store the pool of available options. The configuration of available types
such as colour and size is discussed in the section :ref:`ref-configuration`.

Discounts
=========

The ``Discount`` abstract model provides common features for the reduction
of a price. It contains fields for three types of discounts:

    * ``Discount.discount_deduct`` for reducing by an amount
    * ``Discount.discount_percent`` for reducing by a percent
    * ``Discount.discount_exact`` for reducing to an amount

The ``Discount`` model also contains a DateTimeField ``Discount.valid_from``
and a DateTimeField ``Discount.valid_to``, which together define the start
and end dates of the discount, and a ManyToManyField ``Discount.categories``
and a ManyToManyField ``Discount.products``, which together define the
applicable ``Category`` and ``Product`` instances for which the discount is applicable.

The ``Discount`` abstract model is inherited by the ``DiscountCode`` and
``Sale`` models discussed next.

Discount Codes
--------------

The ``DiscountCode`` model provides a way for managing promotional codes
that a customer can enter during the checkout process to receive a discount
on an order. The ``DiscountCode`` model inherits from the ``Discount``
abstract model as referred to above and also contains fields such as
``DiscountCode.code`` for the promotional code to be entered,
``DiscountCode.min_purchase`` for specifying a minimum order total
required for applying the discount, and a BooleanField
``DiscountCode.free_shipping`` which can be checked to provide free
shipping for the discount code.

.. note::

    Discounts are applied to individual cart items when the discount code
    is assigned to one or more products (individually or by category) in the
    cart. If the discount code is not assigned to any products, the discount will be applied to the entire cart.

Sales
-----

The ``Sale`` model provides a way for managing discounts across
selections of ``Product`` instances. Like the ``DiscountCode`` model, the
``Sale`` model inherits from the abstract model ``Discount``; however, the
``Sale`` model does not provide any extra fields. Instead it acts as a bulk
update tool such that when a ``Sale`` instance is created or updated, it
modifies the ``Product`` and related ``ProductVariation`` instances
according to the selections made for ``Sale.categories`` and
``Sales.products``. When this occurs, the various sale fields discussed in
:ref:`ref-priced-items` such as ``Priced.sale_price``, ``Priced.sale_from``
and  ``Priced.sale_to`` are updated according to the type of discount given
for either ``Sale.discount_deduct``, ``Sale.discount_percent`` or
``Sale.discount_exact``, and the dates given for ``Sale.valid_from`` and
``Sale.valid_to`` respectively. ``Sale.id`` is also stored against
``Product`` and related ``ProductVariation`` instance such that if the
``Sale`` instance is updated or deleted the ``Product`` and related
``ProductVariation`` instances are updated with the relevant fields removed.
This process occurs within the ``Sale._clear()`` method, which is called in
both the ``Sale.save()`` and ``Sale.delete()`` methods.

This goal of this architecture is to decouple the sale information for
each ``Product`` instance from the actual ``Sale`` instance so that no
database querying is required in order to display sale information for a
``Product`` instance.

Carts
=====

The ``Cart`` and related ``CartItem`` models represent a customer's
shopping cart. The ``Cart`` model provides the container for storing each
``CartItem`` instance. This model contains a customer manager ``CartManager`` which
is assigned to ``Cart.objects``. The ``CartManager`` contains the method
``CartManager.from_request()`` which, when given a request object, is
responsible for creating a ``Cart`` instance and maintaining it across the
session.

The ``Cart`` model contains the methods ``Cart.add_item()`` and
``Cart.remove_item()`` for modifying the cart, and also contains several
convenience methods for use in templates that deal with the related
``CartItem`` instances, so as to avoid querying the database multiple times:

    * ``Cart.has_items()`` for checking if the ``Cart`` instance has related ``CartItem`` instances
    * ``Cart.total_quantity()`` for retrieving the total quantity of all the related ``CartItem`` instances
    * ``Cart.total_price()`` for retrieving the total price of all the related ``CartItem`` instances

The ``CartItem`` model represents each unique product in the customer's ``Cart`` instance and inherits from the ``SelectedProduct`` abstract model discussed next.

Selected Products
-----------------

The ``SelectedProduct`` abstract model represents a unique product and set
of selected options that has been selected by a customer. The
``SelectedProduct`` model is inherited by the ``CartItem`` model previously
discussed and the ``OrderItem`` model discussed next.

The ``SelectedProduct`` abstract model acts as a snapshot of a
``ProductVariation`` instance in that it does not contain a direct
reference to the ``ProductVariation`` instance but rather copies information
from it when the ``SelectedProduct`` instance is created. This is to ensure
that any changes made to a ``ProductVariation`` instance do not affect
existing ``SelectedProduct`` instances. The ``SelectedProduct`` model
contains fields such as ``SelectedProduct.sku``,
``SelectedProduct.unit_price`` and ``SelectedProduct.description``, all of
which are copied from the ``ProductVariation`` instance at creation time, with the ``SelectedProduct.description`` being created from the
``ProductVariation`` instances's related ``Product.title`` as well as the
selected options for the ``SelectedProduct`` instance. The
``SelectedProduct`` model also contains the IntegerField
``SelectedProduct.quantity`` for storing the selected quantity.
