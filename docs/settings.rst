.. THIS DOCUMENT IS AUTO GENERATED VIA conf.py

``SHOP_CARD_TYPES``
-------------------

Sequence of available credit card types for payment.

Default: ``('Mastercard', 'Visa', 'Diners', 'Amex')``

``SHOP_CART_EXPIRY_MINUTES``
----------------------------

Number of minutes of inactivity until carts are abandoned.

Default: ``30``

``SHOP_CHECKOUT_ACCOUNT_ENABLED``
---------------------------------

If True, users can create a login for the checkout process.

Default: ``True``

``SHOP_CHECKOUT_ACCOUNT_REQUIRED``
----------------------------------

If True, users must create a login for the checkout process.

Default: ``False``

``SHOP_CHECKOUT_STEPS_CONFIRMATION``
------------------------------------

If True, the checkout process has a final confirmation step before completion.

Default: ``True``

``SHOP_CHECKOUT_STEPS_SPLIT``
-----------------------------

If True, the checkout process is split into separate billing/shipping and payment steps.

Default: ``True``

``SHOP_CURRENCY_LOCALE``
------------------------

Controls the formatting of monetary values accord to the locale module in the python standard library.

Default: ``''``

``SHOP_FORCE_HOST``
-------------------

Host name that the site should always be accessed via that matches the SSL certificate.

Default: ``''``

``SHOP_FORCE_SSL_VIEWS``
------------------------

Sequence of view names that will be forced to run over SSL when SSL_ENABLED is True.

Default: ``('shop_checkout', 'shop_complete', 'shop_account')``

``SHOP_LOGIN_URL``
------------------

Fall back to shop's login view if the view for LOGIN_URL hasn't been defined.

Default: ``[dynamic]``

``SHOP_MAX_PAGING_LINKS``
-------------------------

Maximum number of paging links to show.

Default: ``15``

``SHOP_OPTION_TYPE_CHOICES``
----------------------------

Sequence of value/name pairs for types of product options, eg Size, Colour.

Default: ``((1, u'Size'), (2, u'Colour'))``

``SHOP_ORDER_FROM_EMAIL``
-------------------------

Email address that order receipts should be emailed from.

Default: ``[dynamic]``

``SHOP_ORDER_STATUS_CHOICES``
-----------------------------

Sequence of value/name pairs for order statuses.

Default: ``((1, u'Unprocessed'), (2, u'Processed'))``

``SHOP_PER_PAGE_CATEGORY``
--------------------------

Number of products to display per category page.

Default: ``10``

``SHOP_PER_PAGE_SEARCH``
------------------------

Number of products to display per page for search results.

Default: ``10``

``SHOP_PRODUCT_SORT_OPTIONS``
-----------------------------

Sequence of description/field+direction pairs defining the options available for sorting a list of products.

Default: ``((u'Relevance', None), (u'Least expensive', 'unit_price'), (u'Most expensive', '-unit_price'), (u'Recently added', '-date_added'))``

``SHOP_SSL_ENABLED``
--------------------

If True, users will be automatically redirect to HTTPS for the checkout process.

Default: ``True``