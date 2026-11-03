"""Extend the existing durable outbox for non-appointment lifecycle events."""
import frappe


def execute():
    columns = frappe.db.sql('SHOW COLUMNS FROM tt_booking_notice', as_dict=True)
    if next(c for c in columns if c.Field == 'appointment').Null != 'YES':
        frappe.db.sql_ddl('ALTER TABLE tt_booking_notice MODIFY appointment CHAR(36) NULL')
    existing={c.Field for c in columns}
    for name, definition in (
        ('event_key', 'VARCHAR(180) NULL'),
        ('context_kind', "VARCHAR(24) NOT NULL DEFAULT 'appointment'"),
        ('context_ref', 'VARCHAR(80) NULL'),
    ):
        if name not in existing:
            frappe.db.sql_ddl(f'ALTER TABLE tt_booking_notice ADD COLUMN `{name}` {definition}')
    if not frappe.db.sql("SHOW INDEX FROM tt_booking_notice WHERE Key_name='durable_communication'"):
        frappe.db.sql_ddl('ALTER TABLE tt_booking_notice ADD UNIQUE KEY durable_communication (user,event_key,channel)')

    if not frappe.db.sql("SHOW COLUMNS FROM tt_otp_challenge LIKE 'link_user'"):
        frappe.db.sql_ddl('ALTER TABLE tt_otp_challenge ADD COLUMN link_user VARCHAR(140) NULL')
