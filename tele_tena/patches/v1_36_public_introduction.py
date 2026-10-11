"""Optional clinician-authored public introduction; never copy private history."""
import frappe


def execute():
    if not frappe.db.sql("SHOW COLUMNS FROM tt_profile LIKE 'introduction'"):
        frappe.db.sql_ddl("ALTER TABLE tt_profile ADD COLUMN introduction text NULL")
