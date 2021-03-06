function calc_total(event) {
    var input = $(event.target);
    var qty = input.val();
    var rate = input.attr('data-rate');
    var total = parseFloat(qty) * parseFloat(rate);
    var item_code = input.attr('data-itemcode');
    $("#" + item_code + "-total").html(total.toFixed(2));
	show_please_wait();
    frappe.call({
        'method': 'bazzell.www.basket.change_qtn',
        'args': {
            'item_code': item_code,
            'qty': qty
        },
        'callback': function(response) {
            if (response.message == 'reload') {
                location.reload();
            } else if (response.message == 'qtn deleted') {
				window.open("/selection", "_self");
            } else {
                calc_totalsum();
				hide_please_wait();
            }
        }
    });
}

function calc_totalsum() {
    /* var totalTds = $("#product_table td.total-td");
    var sum = 0;
    for (var i = 0; i < totalTds.length; i++) {
        var td = $(totalTds[i]);
        sum += Number.isNaN(td.html()) ? 0 : parseFloat(td.html());
    }
    $("#totalsum").html(sum.toFixed(2)); */
	
	frappe.call({
        'method': 'bazzell.www.basket.get_totals',
        'callback': function(response) {
            var totals = response.message;
			if (totals) {
                $("#totel_excl_mwst").html(totals.total.toFixed(2));
				$("#total_mwst").html(totals.tax.toFixed(2));
				$("#totalsum").html(totals.grand_total.toFixed(2));
            }
        }
    });
}
calc_totalsum();

function order_now() {
    show_order_complete();
    frappe.call({
        'method': 'bazzell.www.basket.order_now',
        'callback': function(response) {
            if (response.message) {
                window.open("/selection", "_self");
            }
        }
    });
}

function show_please_wait() {
    $("#main_content").css("display", "none");
    $("#info_overlay").css("display", "block");
}

function hide_please_wait() {
    $("#info_overlay").css("display", "none");
    $("#main_content").css("display", "block");
}

function show_order_complete() {
    $("#info_overlay_ordered").css("display", "block");
    $("#main_content").css("display", "none");
}
