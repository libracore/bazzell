# -*- coding: utf-8 -*-
# Copyright (c) 2020, libracore.com and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import json
from bazzell.www.selection import get_customer, get_stocks
from erpnext.selling.doctype.quotation.quotation import make_sales_order

no_cache = True

def get_context(context):
    if frappe.session.user == 'Guest':
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)
    
    #get customer
    customer = get_customer(frappe.session.user)
    
    context["items"] = get_items(customer.name)
    context["currency"] = get_currency(customer.name)
    
    return context
    
def get_items(customer):
    quotation = frappe.db.sql("""SELECT `name` FROM `tabQuotation` WHERE `party_name` = '{customer}' AND `docstatus` = 0 LIMIT 1""".format(customer=customer), as_dict=True)
    items = frappe.db.sql("""SELECT `qty`, `item_code`, `item_name`, `rate`, `uom`, `stock_uom`, `conversion_factor` FROM `tabQuotation Item` WHERE `parent` = '{quotation}'""".format(quotation=quotation[0].name), as_dict=True)
    for item in items:
        item["stock"] = get_stocks(item.item_code)
    return items
    
def get_currency(customer):
    quotation = frappe.db.sql("""SELECT `currency` FROM `tabQuotation` WHERE `party_name` = '{customer}' AND `docstatus` = 0 LIMIT 1""".format(customer=customer), as_dict=True)
    return quotation[0].currency

@frappe.whitelist()
def order_now():
    customer = get_customer(frappe.session.user)
    _quotation = frappe.db.sql("""SELECT `name` FROM `tabQuotation` WHERE `party_name` = '{customer}' AND `docstatus` = 0 LIMIT 1""".format(customer=customer.name), as_dict=True)[0].name
    quotation = frappe.get_doc("Quotation", _quotation).submit()
    sales_order = frappe.get_doc(make_sales_order(_quotation))
    sales_order.insert(ignore_permissions=True)
    return sales_order

@frappe.whitelist()
def change_qtn(item_code, qty):
    #get customer
    customer = get_customer(frappe.session.user)
    quotation = frappe.db.sql("""SELECT `name` FROM `tabQuotation` WHERE `party_name` = '{customer}' AND `docstatus` = 0 LIMIT 1""".format(customer=customer.name), as_dict=True)
    items = frappe.db.sql("""SELECT `item_code`, `rate`, `name` FROM `tabQuotation Item` WHERE `parent` = '{quotation}'""".format(quotation=quotation[0].name), as_dict=True)
    if int(qty) > 0:
        for item in items:
            if item.item_code == item_code:
                new_amount = item.rate * int(qty)
                frappe.db.sql("""UPDATE `tabQuotation Item` SET `qty` = '{qty}', `amount` = '{new_amount}' WHERE `name` = '{name}' AND `parent` = '{qtn}'""".format(qty=qty, name=item.name, new_amount=new_amount, qtn=quotation[0].name), as_list=True)
        quotation = frappe.get_doc("Quotation", quotation[0].name).save(ignore_permissions=True)
        return 'changed'
    else:
        for item in items:
            if item.item_code == item_code:
                frappe.db.sql("""DELETE FROM `tabQuotation Item` WHERE `name` = '{name}'""".format(name=item.name), as_list=True)
        check_qtn_qty = frappe.db.sql("""SELECT COUNT(`name`) FROM `tabQuotation Item` WHERE `parent` = '{qtn}'""".format(qtn=quotation[0].name), as_list=True)[0][0]
        if check_qtn_qty > 0:
            quotation = frappe.get_doc("Quotation", quotation[0].name).save(ignore_permissions=True)
        else:
            quotation = frappe.get_doc("Quotation", quotation[0].name).delete()
            return 'qtn deleted'
        return 'reload'
