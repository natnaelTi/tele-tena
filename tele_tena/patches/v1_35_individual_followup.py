"""Recipient-scoped immutable follow-up drafts and published revisions.

No historical content is inferred or copied into this new private table.
"""
import frappe


def execute():
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_note_followup (
        appointment varchar(36) NOT NULL, revision int NOT NULL,
        recipient varchar(36) NOT NULL, content text NOT NULL,
        published tinyint NOT NULL DEFAULT 0,
        PRIMARY KEY(appointment,revision)
    ) ENGINE=InnoDB''')
