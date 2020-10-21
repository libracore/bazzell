# -*- coding: utf-8 -*-
# Copyright (c) 2020, libracore.com and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def set_sync_qty_to_woocommerce():
    frappe.db.sql("""UPDATE `tabItem` SET `sync_qty_with_woocommerce` = 1 WHERE `item_group` = 'WooCommerceItem' AND `has_variants` = 0""")
