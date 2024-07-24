# Copyright (c) 2020-2024, libracore and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.pdf import get_pdf

@frappe.whitelist()
def get_planzer_label(shipment, label_printer):
    # get raw data
    doc = frappe.get_doc("Shipment", shipment)
    # create pdf
    printer = frappe.get_doc("Label Printer", label_printer)
    
    # create pdf
    html = frappe.render_template(
        frappe.get_value("Print Format", "Planzer Label", "html"),
        {
            'doc': doc.as_dict(),
            'language': doc.get("language") or "de"
        }
    )
    
    # need to load the styles and tags
    html = frappe.render_template(
        'bazzell/templates/pages/print.html',
        {'html': html}
    )
    
    pdf = create_pdf(printer, html)
    # return download
    frappe.local.response.filename = "{name}.pdf".format(name=label_printer.replace(" ", "-").replace("/", "-"))
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "download"

def create_pdf(label_printer, html):
    options = { 
        'page-width': '{0}mm'.format(label_printer.width), 
        'page-height': '{0}mm'.format(label_printer.height), 
        'margin-top': '0mm',
        'margin-bottom': '0mm',
        'margin-left': '0mm',
        'margin-right': '0mm',
        'disable-smart-shrinking': ''
    }
    
    pdf = get_pdf(html, options)
    return pdf

