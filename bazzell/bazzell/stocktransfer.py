# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024, libracore.com and Contributors
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
    # per template: repack?
    query_variant_stock_levels = """SELECT 
            `tabItem`.`item_code`,
            `tabItem`.`item_name`,
            `tabItem`.`variant_of`,
            `tabItem`.`stock_uom`,
            `tabItem`.`safety_stock`,
            IFNULL(`tabBin`.`actual_qty`, 0) AS `actual_qty`,
            `tabUOM`.`value` AS `factor`,
            IFNULL(`tabBin`.`actual_qty`, 0) * `tabUOM`.`value` AS `actual_pcs`
        FROM `tabItem` 
        LEFT JOIN `tabBin` ON `tabBin`.`item_code` = `tabItem`.`item_code` AND `tabBin`.`warehouse` = '{warehouse}'
        JOIN `tabUOM` ON `tabUOM`.`name` = `tabItem`.`stock_uom`
        WHERE `tabItem`.`variant_of` = '{variant_of}'
        ORDER BY `factor` ASC;""".format(variant_of=template, warehouse=warehouse_for_repacks)
   
    variants_in_stock = frappe.db.sql(query_variant_stock_levels, as_dict=True)
    frappe.log_error(variants_in_stock, "variants_in_stock")
    #print("variants {0}".format(variants_in_stock))
    single_item_details = variants_in_stock[0]
    # umlagern erforderlich?
    if (single_item_details['actual_qty'] < single_item_details['safety_stock']) or (single_item_details['actual_qty'] < 1):
        # umlagern möglich?
        if (len(variants_in_stock) > 1):
            # has other variants, check if any of them have stock
            source_item_details = {'item_code': None, 'actual_pcs': 0, 'factor': 0}
            for variant in variants_in_stock:
                if variant['item_code'] != single_item_details['item_code']:
                    if variant['actual_pcs'] >= source_item_details['actual_pcs']:
                        source_item_details = {'item_code': variant['item_code'], 'actual_pcs': variant['actual_pcs'], 'factor': variant['factor']}
            if source_item_details['actual_pcs'] > 0:
                # umlagern
                
                # quelle ausbuchen
                if debug:
                    print("{1}::{0} 1x ausbuchen".format(source_item_details['item_code'], template))
                #create material_issue of item with highest amount in stock
                new_mi = frappe.get_doc({
                    "doctype": "Stock Entry",
                    "stock_entry_type": "Material Issue",
                    "from_warehouse": warehouse_for_repacks,
                    "items": [
                        {
                            "item_code": source_item_details['item_code'],
                            "qty": 1,
                            "expense_account": stock_difference_account
                        }
                    ],
                })
                new_record = new_mi.insert()
                if debug:
                    print("{0}".format(new_record.name))
                target_valuation_rate = (new_record.items[0].valuation_rate / source_item_details['factor'])
                if debug:
                    print("Target valuation: {0}".format(target_valuation_rate))
                if not debug:
                    new_mi.submit()
                # create material receipt of single product that needs more stock
                if debug:
                   print("{2}::{0} {1}x einbuchen".format(single_item_details['item_code'], source_item_details['factor'], template))
                new_mr = frappe.get_doc({
                    "doctype": "Stock Entry",
                    "stock_entry_type": "Material Receipt",
                    "to_warehouse": warehouse_for_repacks,
                    "items": [
                        {
                            "item_code": single_item_details['item_code'],
                            "qty": source_item_details['factor'],
                            "basic_rate": target_valuation_rate,
                            "expense_account": stock_difference_account
                        }
                    ],
                })
                new_mr.insert()
                if debug:
                    print("{0}".format(new_mr.name))
                if not debug:
                    new_mr.submit()
            else:
                if debug:
                    print("{1}::{0}: kein grösseres Gebinde gefunden oder dieses hat keinen Lagerbestand".format(single_item_details['item_code'], template))
    else:
        if debug:
            print("{1}::{0}: nichts zum umlagern".format(single_item_details['item_code'], template))
    
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
