# -*- coding: utf-8 -*-
# Copyright (c) 2020, libracore.com and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import json

no_cache = True

def get_context(context):
    if frappe.session.user == 'Guest':
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)
    
    #get customer
    customer = get_customer(frappe.session.user)
    
    price_list = 'WooCommerce Listpreise'
    context["price_list"] = price_list
    
    # pre check for price rule
    price_rules = frappe.db.sql("""SELECT `name` FROM `tabPricing Rule` WHERE `applicable_for` = 'Customer Group' AND `customer_group` = '{customer_group}' AND `selling` = 1 AND `apply_on` = 'Brand' AND `for_price_list` = 'WooCommerce Listpreise'""".format(customer_group=customer.customer_group), as_list=True)
    if len(price_rules) < 1:
        price_rules = False
    
    
    #filter
    context["product_categories"] = frappe.db.sql("""SELECT DISTINCT `category` FROM `tabItem Product Category`""", as_dict=True)
    context["product_brands"] = frappe.db.sql("""SELECT DISTINCT `attribute_value` FROM `tabItem Variant Attribute` WHERE `attribute` LIKE '%Marke%' ORDER BY `attribute_value` ASC""", as_dict=True)
    
    context["item_table"] = []
    items_without_categories = frappe.db.sql("""SELECT `item_code`,
                                                    `item_name`,
                                                    `stock_uom`,
                                                    `brand`
                                            FROM `tabItem`
                                            WHERE `disabled` = 0
                                            AND `has_variants` = 0
                                            AND `item_group` IN (
                                            SELECT `name` FROM `tabItem Group` WHERE `show_in_b2b_shop` = 1)""", as_dict=True)
    
    #table                                        
    for item in items_without_categories:
        #category
        try:
            product_categories = []
            _product_categories = frappe.db.sql("""SELECT `category` FROM `tabItem Product Category` WHERE `parent` = '{item_code}'""".format(item_code=item.item_code), as_list=True)
            for pc in _product_categories:
                product_categories.append(pc[0])
        except:
            product_categories = []
        item["categories"] = product_categories
        
        brand_for_pricing_rule = item["brand"]
        
        #brand
        try:
            brand = frappe.db.sql("""SELECT `attribute_value` FROM `tabItem Variant Attribute` WHERE `attribute` LIKE '%Marke%' AND `parent` = '{item_code}'""".format(item_code=item.item_code), as_list=True)[0][0]
        except:
            brand = ''
        item["brand"] = brand
        
        #rate
        try:
            rate_and_currency = frappe.db.sql("""SELECT `price_list_rate` AS `rate`, `currency` FROM `tabItem Price` WHERE `price_list` = '{price_list}' AND `item_code` = '{item_code}'""".format(price_list=price_list, item_code=item.item_code), as_dict=True)[0]
            item["currency"] = rate_and_currency.currency
            item["rate"] = rate_and_currency.rate
            item["default_rate"] = 0.00
            
            #check for price rule
            if price_rules:
                affected_rules = frappe.db.sql("""SELECT DISTINCT `parent`
                                                    FROM `tabPricing Rule Brand`
                                                    WHERE `brand` = '{item_brand}'
                                                    AND `parent` IN
                                                    (SELECT `name`
                                                        FROM `tabPricing Rule`
                                                        WHERE `applicable_for` = 'Customer Group'
                                                        AND `customer_group` = '{customer_group}'
                                                        AND `selling` = 1
                                                        AND `apply_on` = 'Brand')
                                                    ORDER BY `modified_by` ASC""".format(item_brand=brand_for_pricing_rule, customer_group=customer.customer_group), as_list=True)
                if len(affected_rules) == 1:
                    item["default_rate"] = item["rate"]
                    pricing_rule = frappe.get_doc("Pricing Rule", affected_rules[0][0])
                    if pricing_rule.rate_or_discount == 'Rate':
                        item["rate"] = pricing_rule.rate
                    elif pricing_rule.rate_or_discount == 'Discount Percentage':
                        item["rate"] = (item["rate"] / 100) * (100 - pricing_rule.discount_percentage)
                    elif pricing_rule.rate_or_discount == 'Discount Amount':
                        item["rate"] = item["rate"] - pricing_rule.discount_amount
                
        except:
            item["currency"] = 'CHF'
            item["rate"] = 'N/A'
            
        #stock
        try:
            qty = 0
            stocks = get_stocks(item.item_code)
            qty += stocks[0]["actual_qty"]
            qty -= stocks[0]["reserved_qty"]
            item["stock_qty"] = int(qty)
        except:
            item["stock_qty"] = 0
            
        #stock uom
        item["stock_uom"] = item.stock_uom
        
        #conversion rate
        try:
            conversion_detail = frappe.db.sql("""SELECT `conversion_factor`, `uom` FROM `tabUOM Conversion Detail` WHERE `parent` = '{item_code}' AND `parentfield` = 'uoms' AND `uom` != 'Stk' LIMIT 1""".format(item_code=item.item_code), as_list=True)
            item["conversion_factor"] = int(conversion_detail[0][0])
            item["uom"] = conversion_detail[0][1]
        except:
            item["conversion_factor"] = 1
            item["uom"] = 'Stk'
        context["item_table"].append(item)
        
    return context
    
def get_customer(user):
    _customer = frappe.db.sql("""SELECT
                                    `link_name`
                                FROM `tabDynamic Link`
                                WHERE
                                    `parenttype` = 'Contact'
                                    AND `link_doctype` = 'Customer'
                                    AND `parent` IN (SELECT `name` FROM `tabContact` WHERE `user` = '{user}')""".format(user=user), as_list=True)
    customer = frappe.get_doc("Customer", _customer[0][0])
    return customer

@frappe.whitelist()
def add_to_basket(_items):
    customer = get_customer(frappe.session.user).name
    quotation = frappe.db.sql("""SELECT `name` FROM `tabQuotation` WHERE `party_name` = '{customer}' AND `docstatus` = 0 LIMIT 1""".format(customer=customer), as_dict=True)
    _items = json.loads(_items)
    
    if len(quotation) == 1:
        quotation = frappe.get_doc("Quotation", quotation[0].name)
        new_item_found = []
        for item in _items:
            # check if item already exist in QTN
            old_item = frappe.db.sql("""SELECT `qty`, `name`, `item_code`, `rate` FROM `tabQuotation Item` WHERE `parent` = '{quotation}' AND `item_code` = '{item_code}'""".format(quotation=quotation.name, item_code=item[0]), as_dict=True)
            if len(old_item) == 1:
                # update qty
                new_qty = old_item[0].qty + float(item[1])
                new_amount = new_qty * old_item[0].rate
                update = frappe.db.sql("""UPDATE `tabQuotation Item` SET `qty` = '{new_qty}', `amount` = '{new_amount}' WHERE `name` = '{name}'""".format(new_qty=new_qty, new_amount=new_amount, name=old_item[0].name), as_list=True)
            else:
                # add item to quotation
                new_item_found.append({'item_code': item[0], 'qty': item[1]})
        frappe.db.commit()
        if len(new_item_found) > 0:
            for item in new_item_found:
                quotation = frappe.get_doc("Quotation", quotation.name)
                row = quotation.append('items', {})
                row.item_code = item["item_code"]
                row.qty = item["qty"]
                quotation.save()
                frappe.db.commit()
        
    else:    
        items = []
        for item in _items:
            item_dict = {
                'item_code': item[0],
                'qty': item[1]
            }
            items.append(item_dict)
        
        quotation = frappe.get_doc({
            "doctype": "Quotation",
            "party_name": customer,
            "items": items,
            "order_type": "Shopping Cart"
            })
        quotation.insert()
    
    return quotation.name
    
def get_stocks(item_code):
    stocks = frappe.db.get_all('Bin', fields=['reserved_qty', 'actual_qty'],
        filters={'item_code': item_code},
        or_filters={
            'reserved_qty': ['!=', 0],
            'actual_qty': ['!=', 0],
        })
    return stocks
