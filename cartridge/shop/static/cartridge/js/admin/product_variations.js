jQuery(function($) {

    var grappelli = $('.admin-title').length == 1;

    // Move the "create variations" fieldset to under current variations.
    var variationsFieldset;
    if (grappelli) {
        variationsFieldset = $('#id_variations-INITIAL_FORMS').parent();
    } else {
        variationsFieldset = $('#id_variations-INITIAL_FORMS').parent().parent();
    }
    $('.create-variations').insertAfter(variationsFieldset);
    // Hide empty option fields.
    $('.create-variations .form-row').each(function(i, row) {
        row = $(row);
        if (row.find('li').length == 0) {
            row.hide();
        }
    });

    // Deselect default variation when another is selected as default.
    var variationDefaults = variationsFieldset.find(' .default input:checkbox');
    variationDefaults.click(function() {
        var clicked = $(this);
        if (clicked.attr('checked')) {
            $.each(variationDefaults, function(i, variation) {
                variation = $(variation);
                if (variation.attr('name') != clicked.attr('name')) {
                    variation.attr('checked', false);
                }
            });
        }
    });

    // Grappelli removes the string value of inline objects, so show these
    // for the product variations.
    if (grappelli) {
        if (variationsFieldset.find('h3').length > 2) {
            $.each(variationsFieldset.find('h3'), function(i, variation) {
                variation = $(variation);
                var titleText = variation.html().split('</b>')[1];
                var titleHtml = '<div class="tiny">' + titleText + '</div>';
                variation.parent().find('.sku input').before(titleHtml);
            });
        }
    }

    $('.variations-help').insertAfter('.create-variations h2').show();

});
