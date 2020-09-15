# -*- coding: utf-8 -*-
# Copyright (c) 2020, libracore.com and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnext.stock.doctype.stock_entry.stock_entry import make_stock_in_entry

def repack_to_single_uom():
    # get settings
    settings = frappe.get_doc("Bazzell Settings", "Bazzell Settings")
    if not settings.warehouse_for_repacks:
        frappe.throw("Target warehouse for repack not configured. Please configure this in Bazzell Settings")

    print("starting stock relocation...")
    # get templates
    query_templates_in_stock = """SELECT `tabItem`.`variant_of`
        FROM `tabItem` 
        JOIN `tabBin` ON `tabBin`.`item_code` = `tabItem`.`item_code` AND `tabBin`.`warehouse` = '{warehouse}'
        WHERE `tabItem`.`variant_of` IS NOT NULL
        GROUP BY `variant_of`;""".format(warehouse=settings.warehouse_for_repacks)
    
    templates_in_stock = frappe.db.sql(query_templates_in_stock, as_dict=True)
    print("templates {0}".format(templates_in_stock))
    
    # loop templates, check for repacking
    for template in templates_in_stock:
        
        # per template: repack?
        query_variant_stock_levels = """SELECT 
                `tabItem`.`item_code`,
                `tabItem`.`item_name`,
                `tabItem`.`variant_of`,
                `tabItem`.`stock_uom`,
                `tabItem`.`safety_stock`,
                `tabBin`.`actual_qty`,
                `tabUOM`.`value` AS `factor`,
                `tabBin`.`actual_qty` * `tabUOM`.`value` AS `actual_pcs`
            FROM `tabItem` 
            JOIN `tabBin` ON `tabBin`.`item_code` = `tabItem`.`item_code` AND `tabBin`.`warehouse` = '{warehouse}'
            JOIN `tabUOM` ON `tabUOM`.`name` = `tabItem`.`stock_uom`
            WHERE `tabItem`.`variant_of` = '{variant_of}'
            ORDER BY `stock_uom` ASC;""".format(variant_of=template['variant_of'], warehouse=settings.warehouse_for_repacks)
       
        variants_in_stock = frappe.db.sql(query_variant_stock_levels, as_dict=True)
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
                    print("{1}::{0} 1x ausbuchen".format(source_item_details['item_code'], template['variant_of']))
                    #create material_issue and then material receipt of 1-er
                    new_mi = frappe.get_doc({
                        "doctype": "Stock Entry",
                        "stock_entry_type": "Material Issue",
                        "from_warehouse": settings.warehouse_for_repacks,
                        "items": [
                            {
                                "item_code": source_item_details['item_code'],
                                "qty": 1
                            }
                        ],
                    })
                    new_mi.insert()
                    #new_mi.submit()
                    # ziel einbuchen
                    print("{2}::{0} {1}x einbuchen".format(single_item_details['item_code'], source_item_details['factor'], template['variant_of']))
                    new_mr = frappe.get_doc({
                        "doctype": "Stock Entry",
                        "stock_entry_type": "Material Receipt",
                        "to_warehouse": settings.warehouse_for_repacks,
                        "items": [
                            {
                                "item_code": single_item_details['item_code'],
                                "qty": source_item_details['factor']
                            }
                        ],
                    })
                    new_mr.insert()
                    #new_mr.submit()
                else:
                    print("{1}::{0}: kein grösseres Gebinde gefunden".format(single_item_details['item_code'], template['variant_of']))
            
        else:
            print("{1}::{0}: nichts zum umlagern".format(single_item_details['item_code'], template['variant_of']))
        # list of stock_uom=1 wieso wollen wir alle item_codes? ich möchte nur uom=1
        target_item_code = single_item_details['item_code']
        #print("target item {0}".format(target_item_code))
        # falls ja: ursprung?
        
        
        #create material_issue and then material receipt of 1-er
        #new_mi = frappe.get_doc({
        #    "doctype": "Stock Entry",
        #    "stock_entry_type": "Material Issue",
        #    "from_warehouse": "Lagerräume - BA",
        #    "items": [
        #    {
        #        "item_code": target_item_code
        #        "qty": 
        #    }
        #],
        #})
        #date?
        #new_mi.insert()
            
            
    return



