"""Explicit per-revision note publication; historical notes remain private."""
import frappe


def execute():
    if not frappe.db.sql("SHOW COLUMNS FROM tt_note_revision LIKE 'note_published'"):
        frappe.db.sql_ddl('''ALTER TABLE tt_note_revision
            ADD COLUMN note_published tinyint NOT NULL DEFAULT 0 AFTER summary_published''')
