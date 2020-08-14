function calc_total(event) {
    var input = $(event.target);
    var qty = input.val();
    var rate = input.attr('data-rate');
    var total = parseFloat(qty) * parseFloat(rate);
    var item_code = input.attr('data-itemcode');
    $("#" + item_code + "-total").html(total.toFixed(2));
    
    frappe.call({
        'method': 'bazzell.www.basket.change_qtn',
        'args': {
            'item_code': item_code,
            'qty': qty
        },
        'callback': function(response) {
            if (response.message == 'reload') {
                location.reload();
            } else {
                calc_totalsum();
            }
        }
    });
}

function calc_totalsum() {
    var totalTds = $("#product_table td.total-td");
    var sum = 0;
    for (var i = 0; i < totalTds.length; i++) {
        var td = $(totalTds[i]);
        sum += Number.isNaN(td.html()) ? 0 : parseFloat(td.html());
    }
    $("#totalsum").html(sum.toFixed(2));
}
calc_totalsum();
/*
function order_now() {
    var order items = $(".form-control.order_items");
    var ordered_items = [];
    var i;
    for (i=0; i <= order_items.length; i++) {
        var item = $(order_items[i]);
        if (item.val() > 0) {
            var list = [];
            list.push(item.attr("data-itemcode"));
            list.push(item.val());
            ordered_items.push(list);
        }
    }

    frappe.call({
        'method': 'bazzell.www.basket.order_now',
        'args': {
            '_items': ordered_items
        },
        'callback': function(response) {
            location.href = /api/method/frappe.utils.print_format.download_pdf?doctype=Sales Order&name=;     //show pdf
        }
    });
}*/
