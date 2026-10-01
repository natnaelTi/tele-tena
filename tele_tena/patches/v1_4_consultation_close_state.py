"""Track confirmed provider room closure, retaining retryable end state."""
import frappe


def execute():
    if not frappe.db.sql("SHOW COLUMNS FROM tt_consultation LIKE 'room_closed'"):
        frappe.db.sql_ddl('ALTER TABLE tt_consultation ADD COLUMN room_closed tinyint NOT NULL DEFAULT 0')
