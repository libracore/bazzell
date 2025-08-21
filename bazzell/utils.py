# -*- coding: utf-8 -*-
# Copyright (c) 2020-2025, libracore.com and Contributors
# AGPL License. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def set_sync_qty_to_woocommerce():
    frappe.db.sql("""
        UPDATE `tabItem` 
        SET `sync_qty_with_woocommerce` = 1 
        WHERE 
            `item_group` = 'WooCommerceItem' 
            AND `has_variants` = 0
            AND `woocommerce_product_id` IS NOT NULL
            AND `woocommerce_product_id` != "";
    """)

def set_item_description_equals_to_stock_uom():
    woocommerce_items = frappe.db.sql("""SELECT `item_code`, `stock_uom` FROM `tabItem` WHERE `item_group` = 'WooCommerceItem' AND `has_variants` = 0""", as_dict=True)
    for woocommerce_item in woocommerce_items:
        frappe.db.sql("""UPDATE `tabItem` SET `description` = '{new_description}' WHERE `item_code` = '{item_code}'""".format(
            new_description=woocommerce_item.stock_uom, item_code=woocommerce_item.item_code), as_list=True)

@frappe.whitelist()
def get_stock_items(warehouse):
    sql_query = """SELECT `tabBin`.`item_code`, `tabBin`.`actual_qty`, `tabItem`.`item_name`, `tabItem`.`stock_uom`
        FROM `tabBin`
        LEFT JOIN `tabItem` ON `tabBin`.`item_code` = `tabItem`.`item_code`
        WHERE `tabBin`.`warehouse` = "{warehouse}"
        ORDER BY `tabItem`.`item_name` ASC;""".format(warehouse=warehouse)
    data = frappe.db.sql(sql_query, as_dict=True)
    return data
