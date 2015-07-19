;(function($){

$(function() {

    var sameShipping = $('#id_same_billing_shipping');

    // show/hide shipping fields on change of "same as" checkbox and call on load
    sameShipping.change(function() {
        $('#shipping_fields')[sameShipping.prop('checked') ? 'hide' : 'show']();
    }).change();

});

})(jQuery);
