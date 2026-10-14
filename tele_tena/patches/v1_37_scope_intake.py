"""Add private scope-intake fields; preserve all existing decisions and records."""
import frappe

def execute():
    frappe.reload_doc('tele_tena', 'doctype', 'tele_tena_vetting_scope_application')
