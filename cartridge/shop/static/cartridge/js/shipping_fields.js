$(function() {

    var sameShipping = $('#id_same_billing_shipping');

    // prepopulate shipping fields with billing values if "same as" checkbox
    // checked by iterating the billing fields, mapping each billing field name
    // to the shipping field name and setting its value
    $('#checkout-form').submit(function() {
        if (sameShipping.attr('checked')) {
            $('input[name^=billing_]').each(function() {
                var shippingName = this.name.replace('billing_', 'shipping_');
                $('input[name=' + shippingName + ']').attr('value', this.value);
            });
            $('select[name^=billing_]').each(function() {
                var shippingSelected = $(this).children('option[selected]').val();
                var shippingSelName = this.name.replace('billing_', 'shipping_');
                $('select[name=' + shippingSelName + '] option[value=' + shippingSelected +']').attr('selected', 'selected');
            });
        }
    });

    // show/hide shipping fields on change of "same as" checkbox and call on load
    sameShipping.change(function() {
        $('#shipping_fields')[sameShipping.attr('checked') ? 'hide' : 'show']();
    }).change();

});
