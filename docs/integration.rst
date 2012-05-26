.. _ref-integration:

===========
Integration
===========

Cartridge provides integration hooks for various steps in the
checkout process, such as when billing and shipping details are
entered, when payment information is entered, and when an order is
complete. Each of these steps has its own setting which stores
the dotted Python package/module/function name of a handler
function to be called. These settings and their
default values are:

  * ``SHOP_HANDLER_BILLING_SHIPPING = "cartridge.shop.checkout.default_billship_handler"``
  * ``SHOP_HANDLER_PAYMENT = "cartridge.shop.checkout.default_payment_handler"``
  * ``SHOP_HANDLER_ORDER = "cartridge.shop.checkout.default_order_handler"``

By defining your own values for each of these settings, you
can create your own handler functions for each of the corresponding
checkout steps. You can also set their values to ``None`` if you wish
to disable any of the default handlers rather than overriding them.

The handler functions have the signature::

    handler_function(request, form, order=None)

The arguments are:

  * ``request`` - the current Django request object.
  * ``form`` - the :ref:`ref-checkout-form` wizard containing all fields for all checkout steps.
  * ``order`` - the :ref:`ref-order-instance` (not supplied for the billing/shipping handler).

The current cart object can also be retrieved from the request
with the following code::

    from cartridge.shop.models import Cart
    cart = Cart.objects.from_request(request)

With the request object, the user's cart, the order form fields and
order instance all available, you can then implement any custom
integration required, such as validating shipping rules, calculating
the shipping amount, integrating with your preferred payment gateway
and implementing any custom order handling once the order is complete.

Billing / Shipping
==================

The setting ``SHOP_HANDLER_BILLING_SHIPPING`` is used to specify the
handler function that will be called when the billing and shipping
step of the checkout form is submitted. It defaults to the value
``cartridge.shop.checkout.default_billship_handler`` which simply sets
a flat rate shipping value defined by the setting
``SHOP_DEFAULT_SHIPPING_VALUE``. The order instance is not passed
to the billing / shipping handler as it is only available at the
last step of the checkout process.

Specifying Shipping
-------------------

The function ``cartridge.shop.utils.set_shipping`` is used to set
the shipping type and amount, typically from within the
billing / shipping step handler. It has the signature::

    set_shipping(request, shipping_type, shipping_value)

``request`` is the current Django request object, ``shipping_type``
is a string indicating the type of shipping, and ``shipping_value``
is a float or integer for the monetary value of shipping that will
be added to the order.

Under the hood, this simply assigns the given shipping values to
the user's session. Subsequently these values are saved to the user's
order upon successful completion.

Payment
=======

The setting ``SHOP_HANDLER_PAYMENT`` is used to specify the handler
function that will be called when the payment step of the checkout
form is submitted. It defaults to the value
``cartridge.shop.checkout.default_payment_handler``, which does nothing.

.. note::

    The payment handler function can optionally return a transaction ID
    which will be stored against a successful order for display in the
    admin.

Unlike the billing / shipping handler, the payment handler has access
to the order object which contains fields for the order sub total,
shipping, discount and tax amounts. If there is a payment error
(see :ref:`ref-error-handling`) then the order is deleted.

.. note::

    When Cartridge is configured to display a final confirmation step
    after payment info is entered, the handler function defined by
    ``SHOP_HANDLER_PAYMENT`` will not be called until after the
    confirmation step. If there is no confirmation step, then the
    handler function will be called directly upon the customer
    submitting payment info.

Order Processing
================

The setting ``SHOP_HANDLER_ORDER`` is used to specify the handler
function that will be called when the order is complete. It defaults
to the value ``cartridge.shop.checkout.default_order_handler``, which
does nothing. With your order handler function, you can implement
any custom order processing required once an order successfully
completes.

.. _ref-error-handling:

Error Handling
==============

When the billing / shipping and payment handler functions are called,
the exception ``cartridge.shop.checkout.CheckoutError`` is checked
for and, if caught, presented to the customer as an error
message. This can be used to indicate a payment error, or even to
raise potential errors in shipping requirements at the
billing / shipping checkout step.

.. _ref-checkout-form:

Checkout Form
=============

The following list contains the fields for the Django order form
instance that is passed to each of the checkout handler functions.

.. include:: order_form_fields.rst

.. _ref-order-instance:

Order Instance
==============

The following list contains the fields for the Django order model
instance that is passed to the checkout handler functions in the final
step.

.. include:: order_model_fields.rst
