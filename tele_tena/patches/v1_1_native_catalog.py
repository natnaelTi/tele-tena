"""Copy legacy public service configuration once; do not infer service approval."""
import frappe


def execute():
    if 'tt_service' not in frappe.db.get_tables(cached=False):
        return
    for service in frappe.db.sql('SELECT id,label,active FROM tt_service', as_dict=True):
        if not frappe.db.exists('Tele Tena Service', service.id):
            frappe.get_doc(dict(doctype='Tele Tena Service', service_key=service.id,
                                service_label=service.label, active=service.active)).insert()
