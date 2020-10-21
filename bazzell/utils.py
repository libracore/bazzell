# -*- coding: utf-8 -*-
# Copyright (c) 2020, libracore.com and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def set_sync_qty_to_woocommerce():
    frappe.db.sql("""UPDATE `tabItem` SET `sync_qty_with_woocommerce` = 1 WHERE `item_group` = 'WooCommerceItem' AND `has_variants` = 0""")

def set_item_description_equals_to_stock_uom():
    woocommerce_items = frappe.db.sql("""SELECT `item_code`, `stock_uom` FROM `tabItem` WHERE `item_group` = 'WooCommerceItem' AND `has_variants` = 0""", as_dict=True)
    for woocommerce_item in woocommerce_items:
        frappe.db.sql("""UPDATE `tabItem` SET `description` = '{new_description}' WHERE `item_code` = '{item_code}'""".format(new_description=woocommerce_item.stock_uom, item_code=woocommerce_item.item_code), as_list=True)