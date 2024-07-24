# Copyright (c) 2020-2024, libracore and contributors
# For license information, please see license.txt

import frappe
from erpnextswiss.erpnextswiss.doctype.label_printer.label_printer import create_pdf

@frappe.whitelist()
def get_planzer_label(shipment, label_printer):
    # get raw data
    doc = frappe.get_doc("Shipment", shipment)
    template = frappe.get_value("Print Format", "Planzer Label").html
    # prepare content
    content = frappe.render_template(template, {'doc': doc})
    # create pdf
    printer = frappe.get_doc("Label Printer", label_printer)
    pdf = create_pdf(printer, content)
    # return download
    frappe.local.response.filename = "{name}.pdf".format(name=label_printer.replace(" ", "-").replace("/", "-"))
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "download"

