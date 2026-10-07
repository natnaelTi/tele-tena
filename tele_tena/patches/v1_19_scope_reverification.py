"""Prevent duplicate credential-renewal applications for one approved record."""
import frappe


def execute():
    if frappe.db.table_exists('Tele Tena Vetting Scope Application'):
        frappe.db.add_unique(
            'Tele Tena Vetting Scope Application',
            ['reverification_of'],
            'uniq_scope_reverification_parent',
        )
