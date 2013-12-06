;(function($){
    $(function() {
    
        var selections = $('#add-cart select');
    
        var showImage = function(id) {
            var image = $(id);
            if (image.length == 1) {
                $('#product-images-large li').hide();
                image.show();
            }
        };
    
        // on selection of an option, reduce the list of variations to the one
        // matching all the selected options - if there is one, show it and hide
        // the others
        selections.change(function() {
            var variation = $.grep(variations, function(v) {
                var valid = true;
                $.each(selections, function() {
                    valid = valid && v[this.name] == this[this.selectedIndex].value;
                });
                return valid;
            });
            if (variation.length == 1) {
                $('#variations li').hide();
                $('#variation-' + variation[0].sku).show();
                showImage('#image-' + variation[0].image_id + '-large');
            }
        });
        selections.change();
    
        // show enlarged image on thumbnail click
        $('#product-images-thumb a').click(function() {
            showImage('#' + $(this).attr('id') + '-large');
            return false;
        });
    
    });
})(jQuery);
