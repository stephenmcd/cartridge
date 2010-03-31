.. _ref-configuration:

Configuration
=============

The following section lists each of the settings that can be configured within Cartridge. All settings are contained in the ``shop.settings`` module.

Application Settings
--------------------

The following settings are specific to Cartridge and can mostly be overriden in your project's ``settings`` module using the convention ``SHOP_SETTING_NAME``, for example the following convention is generally used within ``shop.settings``::

    from django.conf import settings
    
    CART_EXPIRY_MINUTES = getattr(settings, "SHOP_CART_EXPIRY_MINUTES", 30) 

CARD_TYPES
^^^^^^^^^^

Default: ``("Mastercard", "Visa", "Diners", "Amex")``

A sequence of available credit card types for payment.

CART_EXPIRY_MINUTES
^^^^^^^^^^^^^^^^^^^

Default: ``30``

The number of minutes of inactivity for carts until they're abandoned

CURRENCY_LOCALE
^^^^^^^^^^^^^^^

Default: ``""`` (Empty string)

Controls the formatting of monetary values accord to the POSIX locale specified. Consult the Python docs for the standard ``locale`` module for more information.

FORCE_HOST
^^^^^^^^^^

Default: None

If a host name is given, all URLs will be redirected to this host name if accessed by a different host name. This ensures the correct host name matching your SSL certificate is used.

ORDER_FROM_EMAIL
^^^^^^^^^^^^^^^^

Default: ``"do_not_reply@%s" % socket.gethostname()``

The email address that order receipts should be emailed from.

ORDER_STATUSES
^^^^^^^^^^^^^^

Default: ``((1, _("Unprocessed")), (2, _("Processed")))``

Choices for the ``Order.status`` field.

ORDER_STATUS_DEFAULT
^^^^^^^^^^^^^^^^^^^^

Default: ``1``

Default value for the ``Order.status`` field when new orders are created.

# sequence of name/sequence pairs defining the selectable options for products
# PRODUCT_OPTIONS = getattr(settings, "SHOP_PRODUCT_OPTIONS", (
#     ("size", ("Extra Small","Small","Regular","Large","Extra Large")),
#     ("colour", ("Red","Orange","Yellow","Green","Blue","Indigo","Violet")),
# ))

SEARCH_RESULTS_PER_PAGE
^^^^^^^^^^^^^^^^^^^^^^^

Default ``10``

The number of search results to display per page.

SSL_ENABLED
^^^^^^^^^^^

Default: ``not settings.DEBUG``

If set to True, HTTPS will be redirect to for the checkout process.

Project Settings
----------------

The following settings are provided by Cartridge but are not specific to Cartridge and are applicable to an entire project. Unlike the settings above, these settings do not require the ``SHOP_`` prefix and their exact name can be used in your project's ``settings`` module when overriding them.

ADMIN_REORDER
^^^^^^^^^^^^^

Default: ``(("shop", ("Category", "Product", "Sale", "DiscountCode", "Order")),)``

A tuple of two-item tuples, each containing an application name and a tuple of model names belonging to the application. The listing of applications and models in the admin will be displayed in the same order as given in this setting. If you override ``ADMIN_REORDER`` in your project's ``settings`` module without specifying the ``shop`` application, the above default will be combined with your custom setting.



