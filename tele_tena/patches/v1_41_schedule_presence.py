"""Opt-in connected schedule presence; existing preferences and appointments untouched."""
import frappe

def execute():
    for table, column, definition in (
        ('tt_schedule', 'auto_requests', 'TINYINT NOT NULL DEFAULT 0'),
        ('tt_clinician_request_presence', 'control_mode', "VARCHAR(12) NOT NULL DEFAULT 'manual'"),
    ):
        if not frappe.db.sql(f"SHOW COLUMNS FROM {table} LIKE %s", (column,)):
            frappe.db.sql_ddl(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
