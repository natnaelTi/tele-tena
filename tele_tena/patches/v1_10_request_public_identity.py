"""Opaque clinician profile references and timezone snapshots for offers."""
import frappe


def execute():
    if not frappe.db.sql("SHOW COLUMNS FROM tt_profile LIKE 'public_id'"):
        frappe.db.sql_ddl('ALTER TABLE tt_profile ADD COLUMN public_id char(36) NULL')
    frappe.db.sql("UPDATE tt_profile SET public_id=UUID() WHERE public_id IS NULL OR public_id=''")
    if not frappe.db.sql("SHOW INDEX FROM tt_profile WHERE Key_name='profile_public_id'"):
        frappe.db.sql_ddl('ALTER TABLE tt_profile ADD UNIQUE KEY profile_public_id (public_id)')
    if not frappe.db.sql("SHOW COLUMNS FROM tt_request_offer LIKE 'timezone'"):
        frappe.db.sql_ddl("ALTER TABLE tt_request_offer ADD COLUMN timezone varchar(80) NOT NULL DEFAULT 'UTC'")
