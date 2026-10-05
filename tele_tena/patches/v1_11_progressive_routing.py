"""Add auditable wave and inbox-fetch state without rewriting old requests."""
import frappe


def execute():
    if not frappe.db.sql("SHOW COLUMNS FROM tt_open_request LIKE 'current_wave'"):
        frappe.db.sql_ddl("ALTER TABLE tt_open_request ADD COLUMN current_wave tinyint NOT NULL DEFAULT 1")
    if not frappe.db.sql("SHOW COLUMNS FROM tt_open_request LIKE 'last_routed_at'"):
        frappe.db.sql_ddl("ALTER TABLE tt_open_request ADD COLUMN last_routed_at datetime(6) NULL")
    frappe.db.sql('UPDATE tt_open_request SET last_routed_at=COALESCE(first_notice_at,published_at) WHERE last_routed_at IS NULL')
    for column, definition in {
        'wave': 'tinyint NOT NULL DEFAULT 1',
        'enqueued_at': 'datetime(6) NULL',
        'inbox_fetched_at': 'datetime(6) NULL',
    }.items():
        if not frappe.db.sql(f"SHOW COLUMNS FROM tt_request_recipient LIKE '{column}'"):
            frappe.db.sql_ddl(f'ALTER TABLE tt_request_recipient ADD COLUMN `{column}` {definition}')
    frappe.db.sql('UPDATE tt_request_recipient SET enqueued_at=notified_at WHERE enqueued_at IS NULL')
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_request_route_log (
        id varchar(36) PRIMARY KEY, request_id varchar(36) NOT NULL,
        clinician varchar(140) NULL, wave tinyint NOT NULL,
        event varchar(32) NOT NULL, reason_code varchar(48) NULL,
        created_at datetime(6) NOT NULL,
        KEY request_wave (request_id,wave,created_at),
        KEY clinician_created (clinician,created_at)
    ) ENGINE=InnoDB''')
