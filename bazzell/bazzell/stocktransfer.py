# -*- coding: utf-8 -*-
# Copyright (c) 2020-2025, libracore.com and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnext.stock.doctype.stock_entry.stock_entry import make_stock_in_entry

def repack_to_single_uom(debug=False):
    # get settings
    settings = frappe.get_doc("Bazzell Settings", "Bazzell Settings")
    company = frappe.defaults.get_global_default("company") 
    stock_difference_account = frappe.get_value("Company", company, "stock_adjustment_account")
    if not settings.warehouses:
        frappe.throw("Target warehouse for repack not configured. Please configure this in Bazzell Settings")
    warehouses = settings.warehouses
    for warehouse in warehouses:
        warehouse_for_repacks = warehouse.warehouse_for_repacks

        if debug:
            print("starting stock relocation...")
        # get templates
        query_templates_in_stock = """SELECT `tabItem`.`variant_of`
            FROM `tabItem` 
            JOIN `tabBin` ON `tabBin`.`item_code` = `tabItem`.`item_code` AND `tabBin`.`warehouse` = '{warehouse}'
            WHERE `tabItem`.`variant_of` IS NOT NULL
            GROUP BY `variant_of`;""".format(warehouse=warehouse_for_repacks)
        
        templates_in_stock = frappe.db.sql(query_templates_in_stock, as_dict=True)
        if debug:
            print("templates {0}".format(templates_in_stock))
        
        # loop templates, check for repacking
        for template in templates_in_stock:
            repack_template(template['variant_of'], warehouse_for_repacks, stock_difference_account, debug)
        
    return

def repack_template(template, warehouse_for_repacks, stock_difference_account, debug=False):
    query_variant_stock_levels = """
        SELECT 
            `tabItem`.`item_code`,
            `tabItem`.`safety_stock`,
            IFNULL(`tabBin`.`actual_qty`, 0) AS `actual_qty`,
            `tabUOM`.`value` AS `uom_value`
        FROM `tabItem` 
        LEFT JOIN `tabBin` ON `tabBin`.`item_code` = `tabItem`.`item_code` AND `tabBin`.`warehouse` = '{warehouse}'
        LEFT JOIN `tabUOM` ON `tabUOM`.`name` = `tabItem`.`stock_uom`
        WHERE `tabItem`.`variant_of` = '{variant_of}'
        AND `tabUOM`.`value` > 0
        AND `tabItem`.`disabled` != 1
        ORDER BY `uom_value` ASC;""".format(variant_of=template, warehouse=warehouse_for_repacks)
   
    variants_in_stock = frappe.db.sql(query_variant_stock_levels, as_dict=True)

    if len(variants_in_stock) < 2:
        if debug:
            print("Kein Umlagerungsziel gefunden")
        return
    
    min_uom_item = variants_in_stock[0]
    max_uom_item = variants_in_stock[-1]

    # Prüfung dass beide UOMs > 0 sind
    # if (float(min_uom_item['uom_value']) + float(max_uom_item['uom_value'])) <= 1:
    #     if debug:
    #         print("Verarbeitung wird abgebrochen, mind. eine UOM ist 0")
    #     return

    # Entspricht die uom_max einem Vielfachen von uom_min?
    if max_uom_item['uom_value'] % min_uom_item['uom_value'] != 0:
        if debug:
            print("Abbruch, grössere UOM entspricht nicht einem Vielfachen der kleineren UOM")
        return

    # Umlagerung erforderlich?
    if (min_uom_item['actual_qty'] < min_uom_item['safety_stock']) or (min_uom_item['actual_qty'] < 1):

        # Besitz die grössere UOM Lager?
        if max_uom_item['actual_qty'] < 1:
            if debug:
                print("{1}::{0}: kein grösseres Gebinde gefunden oder dieses hat keinen Lagerbestand".format(min_uom_item['item_code'], template))
            return
        
        # Quelle ausbuchen
        if debug:
            print("{1}::{0} 1x ausbuchen".format(max_uom_item['item_code'], template))

        #create material_issue of item with highest amount in stock
        mi = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Issue",
            "from_warehouse": warehouse_for_repacks,
            "items": [
                {
                    "item_code": max_uom_item['item_code'],
                    "qty": 1,
                    "expense_account": stock_difference_account
                }
            ],
        }).insert()

        if debug:
            print("{0}".format(mi.name))
        else:
            mi.submit()

        target_valuation_rate = (mi.items[0].valuation_rate / max_uom_item['uom_value']) * min_uom_item['uom_value']
        target_qty = int(max_uom_item['uom_value'] / min_uom_item['uom_value'])

        if debug:
            print("{2}::{0} {1}x einbuchen".format(min_uom_item['item_code'], target_qty, template))
            print("Target valuation: {0}".format(target_valuation_rate))
            print("Target QTY: {0}".format(target_qty))
        
        mr = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "to_warehouse": warehouse_for_repacks,
            "items": [
                {
                    "item_code": min_uom_item['item_code'],
                    "qty": target_qty,
                    "basic_rate": target_valuation_rate,
                    "expense_account": stock_difference_account
                }
            ],
        }).insert()

        if debug:
            print("{0}".format(mr.name))
        else:
            mr.submit()
    else:
        if debug:
            print("{1}::{0}: nichts zum umlagern".format(min_uom_item['item_code'], template))
    return

@frappe.whitelist()
def manual_repack_template(template, debug=False):
    # get settings
    settings = frappe.get_doc("Bazzell Settings", "Bazzell Settings")
    company = frappe.defaults.get_global_default("company") 
    stock_difference_account = frappe.get_value("Company", company, "stock_adjustment_account")
    if not settings.warehouses:
        frappe.throw("Target warehouse for repack not configured. Please configure this in Bazzell Settings")
    for warehouse in settings.warehouses:
        warehouse_for_repacks = warehouse.warehouse_for_repacks

        repack_template(template, warehouse_for_repacks, stock_difference_account, debug)
            
    return
