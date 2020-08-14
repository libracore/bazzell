$(document).ready(function(){
    $(".form-control.order_amount").val(0);
    $("#item_selection").val("");
});
function category_selected() {
    var value = $("#category_selection").val().toLowerCase();
    if (value != "empty") {
        $("#product_table tr").filter(function() {
          $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    } else {
        $("#product_table tr").show();
    }
}
function brand_selected() {
    var value = $("#brand_selection").val().toLowerCase();
    if (value != "empty") {
        $("#product_table tr").filter(function() {
          $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    } else {
        $("#product_table tr").show();
    }
}
function item_selected() {
    var value = $("#item_selection").val().toLowerCase();
    if (value != "empty") {
        $("#product_table tr").filter(function() {
          $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    } else {
        $("#product_table tr").show();
    }
}

function table_filter() {
    var category_value = $("#category_selection").val().toLowerCase();
    var brand_value = $("#brand_selection").val().toLowerCase();
    var item_value = $("#item_selection").val().toLowerCase();
    
    if (category_value == "empty" && brand_value == "empty" && item_value == "empty") {
        $("#product_table tr").show();
    } else {
        $("#product_table tr").each(function() {
            if (
                (category_value === "empty" || $(this).text().toLowerCase().indexOf(category_value) > -1) &&
                (brand_value === "empty" || $(this).text().toLowerCase().indexOf(brand_value) > -1) &&
                (item_value === "empty" || $(this).text().toLowerCase().indexOf(item_value) > -1)
            ) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    }
    
}


function calc_total(element) {
    element = $("#" + element)
    var item_code = element.attr('data-itemcode');
    var qty = element.val();
    var rate = element.attr('data-rate');
    var total = parseFloat(qty) * parseFloat(rate);
    $("#" + item_code + "-total").html(total.toFixed(2));
}

function add_to_basket() {
    var all_items = $(".form-control.order_amount");
    var order_items = [];
    var i;
    for (i=0; i <= all_items.length; i++) {
        var item = $(all_items[i]);
        if (item.val() > 0) {
            var list = [];
            list.push(item.attr("data-itemcode"));
            list.push(item.val());
            order_items.push(list);
        }
    }

    frappe.call({
        'method': 'bazzell.www.selection.add_to_basket',
        'args': {
            '_items': order_items
        },
        'callback': function(response) {
            location.href = '/basket';
        }
    });
}
