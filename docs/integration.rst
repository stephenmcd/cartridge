.. _ref-integration:

===========
Integration
===========

Cartridge provides integration hooks for the two input steps in the 
checkout process, namely billing/shipping details and payment 
information. When each of these steps occur, a custom handler function 
which you implement will be called. Cartridge provides settings which 
allow you to specify the dotted Python package/module/function name as 
a string for each of the handler functions. The handler functions 
have the signature::

    handler_function(request, form)

``request`` is the current Django request object and ``form`` is 
Cartridge's checkout form wizard containing each of the fields in the 
checkout process. It's worth noting that the current cart object 
can be retrieved from the request with the following code::

    from cartridge.shop.models import Cart
    cart = Cart.objects.from_request(request)

With the request object, the user's cart, and the form fields all 
available, you can then implement any custom integration required 
such as validating shipping rules, calculating the shipping amount 
and integrating with your preferred payment gateway.

Billing / Shipping
==================

The setting ``SHOP_HANDLER_BILLING_SHIPPING`` is used to specify the 
handler function that will be called when the billing and shipping 
step of the checkout form is submitted. It defaults to the value 
``cartridge.shop.checkout.default_billship_handler`` which simply sets 
a flat rate shipping value defined by the setting 
``SHOP_DEFAULT_SHIPPING_VALUE``.

Setting Shipping
================

The function ``cartridge.shop.utils.set_shipping`` is used to set 
the shipping type and amount, typically from within the 
billing/shipping step handler. It has the signature::

    set_shipping(request, shipping_type, shipping_value)
    
``request`` is the current Django request object, ``shipping_type`` 
is a string indicating the type of shipping, and ``shipping_value``
is a float or integer for the monetary value of shipping that will 
be added to the order.

Under the hood this simply assigns the given shipping values to 
the user's session and these values are then saved to the user's 
order on successful completion.

Payment
=======

The setting ``SHOP_HANDLER_PAYMENT`` is used to specify the handler 
function that will be called when the payment step of the checkout 
form is submitted. It defaults to the value 
``cartridge.shop.checkout.dummy_payment_handler`` which does nothing.

.. note:: 

    When Cartridge is configured to display a final confirmation step 
    after payment info is entered, the handler function defined by 
    ``SHOP_HANDLER_PAYMENT`` won't be called until after the 
    confirmation step. If there is no confirmation step, then the 
    handler function will be called directly upon the customer 
    submitting payment info.

Error Handling
==============

When a checkout handler function is called, the exception 
``cartridge.shop.checkout.CheckoutError`` is checked for and if caught 
will be presented to the customer as an error message. This can be 
used to indicate a payment error, or even to raise any potential 
errors around shipping requirements at the billing / shipping checkout 
step.

Checkout Fields
===============

The following list contains the fields for the Django form object that 
is passed to each of the checkout handler functions.

.. include:: fields.rst
