============
Introduction
============

Cartridge is a shopping cart application built using the Django framework. Its primary focus is to provide you with a clean and simple base for developing e-commerce websites. It purposely does not include every conceivable feature an e-commerce website could potentially use, instead focusing on providing only the core features that are needed on every e-commerce website. 

This specific focus stems from the idea that every e-commerce website is different, tailoring to the particular business and its products at hand, and should therefore be as easy as possible to customize. Cartridge achieves this goal with a code-base that implements only the core features of an e-commerce site, therefore remaining as simple as possible.

Given the outline above, this document focuses on the technical architecture of Cartridge with the aim of giving you enough of an overall understanding to implement and customize it for your own e-commerce websites.

==========
Components
==========

The following section describes the various components within Cartidge and mostly describes the Django models used.

Categories
----------

The model ``shop.models.Category`` provides the navigational tree structure for organising products throughout the site. This structure is stored using the self referencing ForeignKeyField ``Category.parent`` and rendered on both the site and in the admin recursively via the ``shop.templatetags.category_menu`` and  ``shop.templatetags.category_menu_admin`` template tags respectively. When viewing the list of categories in the admin, the listing template is overriden with a custom ``change_list.html`` that allows the category tree to be managed.

The ``shop.models.Category`` model inherits from the abstract model ``shop.models.Displayable`` which provides common features for a displayable item on the site such as the item's title, automatic generation of slug fields via ``Displayable.save`` and a Boolean field ``Displayable.active`` for controlling whether or not the item is visible on the site.

The ``shop.models.Category`` model also contains a ManyToManyField ``Category.products`` that contains the products assigned to the category,  although this is defined in the product model described below.

Products
--------

Products are made up from three separate models. Firstly the model ``shop.models.Product`` provides the container for storing the core attributes of a product. The other two models are ``shop.models.ProductImage`` and `` shop.models.ProductVariation`` which each contain a ForeignKeyField to the product.

The ``shop.models.Product`` model inherits from the abstract model ``shop.models.Displayable`` like the category model, and also inherits from the abstract model ``shop.models.Priced`` which provides common features for an item that has a price. The fields provided ``shop.models.Priced`` are not editable via the admin for the ``shop.models.Product`` model and are discussed below under :ref:`ref-denormalized-fields`.

Product Images
^^^^^^^^^^^^^^

Product Variations
^^^^^^^^^^^^^^^^^^

.. _ref-denormalized-fields:

Denormalized Fields
^^^^^^^^^^^^^^^^^^^

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

=================
Views & Templates
=================

The following section describes the front-end website pages and mostly describes the Django view functions and templates used.

Category
--------

Product
-------

Search
------

Wishlist
--------

Cart
----

Checkout
--------
    
===========
Integration
===========

The following section describes the front-end website views and mostly describes the Django view functions and templates used.

Shipping
--------

Payment
-------

=========
Utilities
=========

The following section describes various utilities and mostly describes the Django template tags used as well as functions in the shop.utils module.

Category Menu
-------------

Currency Formatting
-------------------

Thumbnails
----------

Order Totals
------------

Admin Model Re-ordering
-----------------------

Remembering Order Details
-------------------------

Localization
------------

Sending email
-------------

=============
Configuration
=============

The following section lists each of the settings that can be specified for configuring the Cartridge application. All settings are contained in shop.settings with applicable defaults and can mostly be overriden in your project's settings module using the convention SHOP_SETTING_NAME.

Application Settings
--------------------

Project Settings
----------------

