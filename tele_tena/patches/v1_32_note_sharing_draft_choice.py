"""Keep a draft's intended sharing choice separate from actual publication."""
import frappe


def execute():
    if not frappe.db.sql("SHOW COLUMNS FROM tt_note_revision LIKE 'note_share_selected'"):
        frappe.db.sql_ddl('''ALTER TABLE tt_note_revision
            ADD COLUMN note_share_selected tinyint NOT NULL DEFAULT 0 AFTER note_published''')
