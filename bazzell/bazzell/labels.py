# Copyright (c) 2020-2024, libracore and contributors
# For license information, please see license.txt

import frappe
#from erpnextswiss.erpnextswiss.doctype.label_printer.label_printer import create_pdf
#from frappe.utils.pdf import get_pdf
import pdfkit, os, frappe

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
    
    options = {
        'disable-smart-shrinking': ''
    }
    
    #pdf = get_pdf(html, options)
            
    pdf = create_pdf(printer, html)
    # return download
    frappe.local.response.filename = "{name}.pdf".format(name=label_printer.replace(" ", "-").replace("/", "-"))
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "download"

def create_pdf(label_printer, content):
    # create temporary file
    fname = os.path.join("/tmp", "frappe-pdf-{0}.pdf".format(frappe.generate_hash()))
    
    options = { 
        'page-width': '{0}mm'.format(label_printer.width), 
        'page-height': '{0}mm'.format(label_printer.height), 
        'margin-top': '0mm',
        'margin-bottom': '0mm',
        'margin-left': '0mm',
        'margin-right': '0mm',
        'disable-smart-shrinking': ''
    }
    
    pdfkit.from_string(html_content, fname, options=options or {})
    
    with open(fname, "rb") as fileobj:
        filedata = fileobj.read()
    
    cleanup(fname)
    
    return filedata

def cleanup(fname):
    if os.path.exists(fname):
        os.remove(fname)
    return
