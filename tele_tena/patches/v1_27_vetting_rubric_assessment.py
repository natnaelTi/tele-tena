"""Add an immutable snapshot of structured rubric dimensions to assessments."""
import frappe


def execute():
    if not frappe.db.table_exists('Tele Tena Vetting Assessment'):
        return
    if not frappe.db.sql("SHOW COLUMNS FROM `tabTele Tena Vetting Assessment` LIKE 'scored_criteria_snapshot'"):
        frappe.db.add_column('Tele Tena Vetting Assessment', 'scored_criteria_snapshot', 'Long Text')
