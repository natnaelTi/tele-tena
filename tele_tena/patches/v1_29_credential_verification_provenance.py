"""Add immutable source/date/evidence provenance to new credential reviews."""
import frappe


def execute():
    if not frappe.db.table_exists('Tele Tena Vetting Assessment'):
        return
    if not frappe.db.sql("SHOW COLUMNS FROM `tabTele Tena Vetting Assessment` LIKE 'credential_verification_snapshot'"):
        frappe.db.add_column('Tele Tena Vetting Assessment', 'credential_verification_snapshot', 'Long Text')
