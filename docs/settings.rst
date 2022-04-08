.. THIS DOCUMENT IS AUTO GENERATED VIA conf.py

.. _SHOP_CARD_TYPES:

``SHOP_CARD_TYPES``
-------------------

Sequence of available credit card types for payment.

Default: ``('Mastercard', 'Visa', 'Diners', 'Amex')``

.. _SHOP_CART_EXPIRY_MINUTES:

``SHOP_CART_EXPIRY_MINUTES``
----------------------------

Number of minutes of inactivity until carts are abandoned.

Default: ``30``

.. _SHOP_CATEGORY_USE_FEATURED_IMAGE:

``SHOP_CATEGORY_USE_FEATURED_IMAGE``
------------------------------------

Enable featured images in shop categories

Default: ``False``

.. _SHOP_CHECKOUT_ACCOUNT_REQUIRED:

``SHOP_CHECKOUT_ACCOUNT_REQUIRED``
----------------------------------

If True, users must create a login for the checkout process.

Default: ``False``

.. _SHOP_CHECKOUT_STEPS_CONFIRMATION:

``SHOP_CHECKOUT_STEPS_CONFIRMATION``
------------------------------------

If True, the checkout process has a final confirmation step before completion.

Default: ``True``

.. _SHOP_CHECKOUT_STEPS_SPLIT:

``SHOP_CHECKOUT_STEPS_SPLIT``
-----------------------------

If True, the checkout process is split into separate billing/shipping and payment steps.

Default: ``True``

.. _SHOP_CURRENCY_LOCALE:

``SHOP_CURRENCY_LOCALE``
------------------------

Controls the formatting of monetary values according to the locale module in the python standard library. If an empty string is used, will fall back to the system's locale.

Default: ``''``

.. _SHOP_DEFAULT_SHIPPING_VALUE:

``SHOP_DEFAULT_SHIPPING_VALUE``
-------------------------------

Default cost of shipping when no custom shipping is implemented.

Default: ``10.0``

.. _SHOP_DEFAULT_TAX_RATE:

``SHOP_DEFAULT_TAX_RATE``
-------------------------

Default tax rate in % when no custom tax handling is implemented.

Default: ``0.0``

.. _SHOP_DISCOUNT_FIELD_IN_CART:

``SHOP_DISCOUNT_FIELD_IN_CART``
-------------------------------

Discount codes can be entered on the cart page.

Default: ``True``

.. _SHOP_DISCOUNT_FIELD_IN_CHECKOUT:

``SHOP_DISCOUNT_FIELD_IN_CHECKOUT``
-----------------------------------

Discount codes can be entered on the first checkout step.

Default: ``True``

.. _SHOP_HANDLER_BILLING_SHIPPING:

``SHOP_HANDLER_BILLING_SHIPPING``
---------------------------------

Dotted package path and class name of the function called upon submission of the billing/shipping checkout step. This is where shipping calculations can be performed and set using the function ``cartridge.shop.utils.set_shipping``.

Default: ``'cartridge.shop.checkout.default_billship_handler'``

.. _SHOP_HANDLER_ORDER:

``SHOP_HANDLER_ORDER``
----------------------

Dotted package path and class name of the function that is called once an order is successful and all of the order object's data has been created. This is where any custom order processing should be implemented.

Default: ``'cartridge.shop.checkout.default_order_handler'``

.. _SHOP_HANDLER_PAYMENT:

``SHOP_HANDLER_PAYMENT``
------------------------

Dotted package path and class name of the function that is called upon submission of the payment checkout step. This is where integration with a payment gateway should be implemented.

Default: ``'cartridge.shop.checkout.default_payment_handler'``

.. _SHOP_HANDLER_TAX:

``SHOP_HANDLER_TAX``
--------------------

Dotted package path and class name of the function called upon submission of the billing/shipping checkout step. This is where tax calculations can be performed and set using the function ``cartridge.shop.utils.set_tax``.

Default: ``'cartridge.shop.checkout.default_tax_handler'``

.. _SHOP_OPTION_ADMIN_ORDER:

``SHOP_OPTION_ADMIN_ORDER``
---------------------------

Sequence of indexes from the ``SHOP_OPTION_TYPE_CHOICES`` setting that control how the options should be ordered in the admin, eg given the default for ``SHOP_OPTION_ADMIN_ORDER``, to order by Colour then Size we'd use (2, 1)

Default: ``()``

.. _SHOP_OPTION_TYPE_CHOICES:

``SHOP_OPTION_TYPE_CHOICES``
----------------------------

Sequence of value/name pairs for types of product options (e.g. Size, Colour).

Default: ``((1, 'Size'), (2, 'Colour'))``

.. _SHOP_ORDER_EMAIL_BCC:

``SHOP_ORDER_EMAIL_BCC``
------------------------

All order receipts will be BCCd to this address.

Default: ``''``

.. _SHOP_ORDER_EMAIL_SUBJECT:

``SHOP_ORDER_EMAIL_SUBJECT``
----------------------------

Subject to be used when sending the order receipt email.

Default: ``'Order Receipt'``

.. _SHOP_ORDER_FROM_EMAIL:

``SHOP_ORDER_FROM_EMAIL``
-------------------------

Email address from which order receipts should be emailed.

Default: ``[dynamic]``

.. _SHOP_ORDER_STATUS_CHOICES:

``SHOP_ORDER_STATUS_CHOICES``
-----------------------------

Sequence of value/name pairs for order statuses.

Default: ``((1, 'Unprocessed'), (2, 'Processed'))``

.. _SHOP_PAYMENT_STEP_ENABLED:

``SHOP_PAYMENT_STEP_ENABLED``
-----------------------------

If False, there is no payment step on the checkout process.

Default: ``True``

.. _SHOP_PER_PAGE_CATEGORY:

``SHOP_PER_PAGE_CATEGORY``
--------------------------

Number of products to display per category page.

Default: ``12``

.. _SHOP_PRODUCT_SORT_OPTIONS:

``SHOP_PRODUCT_SORT_OPTIONS``
-----------------------------

Sequence of description/field+direction pairs defining the options available for sorting a list of products.

Default: ``(('Recently added', '-date_added'), ('Highest rated', '-rating_average'), ('Least expensive', 'unit_price'), ('Most expensive', '-unit_price'))``

.. _SHOP_TAX_INCLUDED:

``SHOP_TAX_INCLUDED``
---------------------

If True, tax is already included in a product's price.

Default: ``False``

.. _SHOP_USE_RATINGS:

``SHOP_USE_RATINGS``
--------------------

Show the product rating form, and allow browsing by rating.

Default: ``True``

.. _SHOP_USE_RELATED_PRODUCTS:

``SHOP_USE_RELATED_PRODUCTS``
-----------------------------

Show related products in templates, and allow editing them in the admin.

Default: ``True``

.. _SHOP_USE_UPSELL_PRODUCTS:

``SHOP_USE_UPSELL_PRODUCTS``
----------------------------

Show upsell products in templates, and allow editing them in the admin.

Default: ``True``

.. _SHOP_USE_VARIATIONS:

``SHOP_USE_VARIATIONS``
-----------------------

Use product variations.

Default: ``True``

.. _SHOP_USE_WISHLIST:

``SHOP_USE_WISHLIST``
---------------------

Show the links to the wishlist, and allow adding products to it.

Default: ``True``