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

The number of minutes of inactivity for carIf set to ``True``, ts until they're abandoned

CHECKOUT_ACCOUNT_ENABLED
^^^^^^^^^^^^^^^^^^^^^^^^

Default: ``True``

If set to ``True``, links to creating an account and logging in will be available for linking orders to an account and pre-populating the order form with the user's details from their previous order.

CHECKOUT_ACCOUNT_REQUIRED
^^^^^^^^^^^^^^^^^^^^^^^^^

Default: ``False``

If set to ``True``, creating an account and logging in is required to place an order. In this case the ``CHECKOUT_ACCOUNT_ENABLED`` setting is forced to ``True``.

CHECKOUT_STEPS_SPLIT
^^^^^^^^^^^^^^^^^^^^

Default: ``True``

If set to ``True``, the checkout process is split into separate steps. The first step provides a form for entering billing and shipping details, while the second step provides a form for entering payment details. If set to ``False``, a single form for entering all order information is provided.

CHECKOUT_STEPS_CONFIRMATION
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Default: ``True``

If set to ``True``, the final step of the checkout process is a confirmation screen that displays all order information before payment is made.

CHECKOUT_ACCOUNT_ENABLED
^^^^^^^^^^^^^^^^^^^^^^^^

Default: ``True``

CURRENCY_LOCALE
^^^^^^^^^^^^^^^

Default: ``""`` (Empty string)

Controls the formatting of monetary values accord to the POSIX locale specified. Consult the Python docs for the standard ``locale`` module for more information.

FORCE_HOST
^^^^^^^^^^

Default: None

If a host name is given, all URLs will be redirected to this host name if accessed by a different host name. This ensures the correct host name matching your SSL certificate is used.

FORCE_SSL_VIEWS
^^^^^^^^^^^^^^^

Default: ``("shop_checkout", "shop_complete", "shop_account")``

A sequence of view names that when accessed will be redirected to HTTPS for if ``SSL_ENABLED`` is set to ``True``.

ORDER_FROM_EMAIL
^^^^^^^^^^^^^^^^

Default: ``"do_not_reply@%s" % socket.gethostname()``

The email address that order receipts should be emailed from.

ORDER_STATUS_CHOICES
^^^^^^^^^^^^^^^^^^^^

Default: ``((1, _("Unprocessed")), (2, _("Processed")))``

Choices for the ``Order.status`` field. The first status is used as the default.

PER_PAGE_CATEGORY
^^^^^^^^^^^^^^^^^

Default ``10``

The number of products to display per page for a category.

PER_PAGE_SEARCH
^^^^^^^^^^^^^^^

Default ``10``

The number of products to display per page for search results.

MAX_PAGING_LINKS
^^^^^^^^^^^^^^^^^^^^^^^

Default ``15``

The maximum number of paging links to show.

PRODUCT_SORT_OPTIONS
^^^^^^^^^^^^^^^^^^^^

Default ``(_("Relevance"), None), (_("Least expensive"), "unit_price"), (_("Most expensive"), "-unit_price"), (_("Recently added"), "-date_added"))``

A sequence of description and fields with their directions as pairs defining the options available for sorting a list of products when viewing a category or search results.

SSL_ENABLED
^^^^^^^^^^^

Default: ``not settings.DEBUG``

If set to ``True``, HTTPS will be redirected to for the views listed in ``FORCE_SSL_VIEWS``.

Project Settings
----------------

The following settings are provided by Cartridge but are not specific to Cartridge and are applicable to an entire project. Unlike the settings above, these settings do not require the ``SHOP_`` prefix and their exact name can be used in your project's ``settings`` module when overriding them.

ADMIN_REORDER
^^^^^^^^^^^^^

Default: ``(("shop", ("Category", "Product", "ProductOption", "Sale", "DiscountCode", "Order")),)``

A tuple of two-item tuples, each containing an application name and a tuple of model names belonging to the application. The listing of applications and models in the admin will be displayed in the same order as given in this setting. If you override ``ADMIN_REORDER`` in your project's ``settings`` module without specifying the ``shop`` application, the above default will be combined with your custom setting.

Dynamic Settings
----------------

The following settings are dynamically configured and are not meant to be manually specified.

LOGIN_URL
^^^^^^^^^

Default: The URL named ``shop_account`` in ``shop.urls``, ``/shop/account/`` by default.

The login URL that will be used for account integration with Cartridge. Since the Django ``settings`` module has a default ``LOGIN_URL``, this or the value set for it in your project's ``settings`` module is tested to ensure it resolves to a view, otherwise falling back to the login view provided by Cartridge. This allows the project or other installed apps to control the login view.
