Introduction
============

Cartridge is a shopping cart application built using the Django framework. Its primary focus is to provide you with a clean and simple base for developing e-commerce websites. It purposely does not include every conceivable feature an e-commerce website could potentially use, instead focusing on providing only the core features that are needed on every e-commerce website. 

This specific focus stems from the idea that every e-commerce website is different, tailoring to the particular business and its products at hand, and should therefore be as easy as possible to customize. Cartridge achieves this goal with a code-base that implements only the core features of an e-commerce site, therefore remaining as simple as possible.

Given the outline above, this document focuses on the technical architecture of Cartridge with the aim of giving you enough of an overall understanding to implement and customize it for your own e-commerce websites.

Components
----------

The following section describes the various components within Cartidge and mostly describes the Django models used.

    * Categories
    * Products
        * Variations
        * Images
        * Denormalized fields
    * Wishlists
    * Discounts
        * Sales
        * Discount Codes
    * Carts
    * Orders

Views & Templates
-----------------

The following section describes the front-end website pages and mostly describes the Django view functions and templates used.

    * Category
    * Product
    * Search
    * Wishlist
    * Cart
    * Checkout
    
Integration
-----------

The following section describes the front-end website views and mostly describes the Django view functions and templates used.

    * Shipping
    * Payment

Utilities
---------

The following section describes various utilities and mostly describes the Django template tags used as well as functions in the shop.utils module.

    * Category Menu
    * Currency Formatting
    * Thumbnails
    * Order Totals
    * Admin Model Re-ordering
    * Remembering Order Details
    * Localization
    * Sending email

Configuration
-------------

The following section lists each of the settings that can be specified for configuring the Cartridge application. All settings are contained in shop.settings with applicable defaults and can mostly be overriden in your project's settings module using the convention SHOP_SETTING_NAME.

    * Application Settings
    * Project Settings

