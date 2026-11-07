"""Private replay admission/chunk indexes only; does not enable collection."""
import frappe
CAPTURE_DEFAULTS={'replay_index_limit':100000,'replay_chunks_per_day':5000,'replay_pending_chunks':500,'replay_chunks_per_record':1000}

def execute():
    tables = {
        'capture': '''id CHAR(64) PRIMARY KEY,owner_actor CHAR(64) NOT NULL,session_scope CHAR(64) NOT NULL,
          provider_id CHAR(36) NOT NULL UNIQUE,window_id CHAR(36) NOT NULL,release_id CHAR(40) NOT NULL,
          role VARCHAR(12) NOT NULL,locale VARCHAR(5) NOT NULL DEFAULT 'en',device VARCHAR(10) NOT NULL DEFAULT 'unknown',payment_mode VARCHAR(10) NOT NULL DEFAULT 'Wallet',environment VARCHAR(12) NOT NULL DEFAULT 'review',synthetic TINYINT NOT NULL DEFAULT 1,captured DATETIME(6) NOT NULL,stop_at DATETIME(6) NOT NULL,
          last_seen DATETIME(6) NOT NULL,state VARCHAR(20) NOT NULL,bytes BIGINT NOT NULL DEFAULT 0,
          style_key CHAR(64) NOT NULL,KEY owner_state(owner_actor,state),KEY lifecycle(state,last_seen)''',
        'chunk': '''id CHAR(64) PRIMARY KEY,capture_id CHAR(64) NOT NULL,digest CHAR(64) NOT NULL,
          object_key CHAR(64),size_bytes BIGINT NOT NULL,state VARCHAR(20) NOT NULL,
          tries INT NOT NULL DEFAULT 0,next_try DATETIME(6),created DATETIME(6) NOT NULL,
          KEY processing(state,next_try),KEY capture(capture_id,state),KEY object_reference(object_key)''',
    }
    for name, fields in tables.items():
        frappe.db.sql_ddl(f'CREATE TABLE IF NOT EXISTS tt_ops_{name} ({fields}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci')

    if not frappe.db.sql("SHOW COLUMNS FROM tt_ops_capture LIKE 'synthetic'"):
        frappe.db.sql_ddl("ALTER TABLE tt_ops_capture ADD COLUMN synthetic TINYINT NOT NULL DEFAULT 1")

    for name, definition in {'locale':"VARCHAR(5) NOT NULL DEFAULT 'en'",'device':"VARCHAR(10) NOT NULL DEFAULT 'unknown'",'payment_mode':"VARCHAR(10) NOT NULL DEFAULT 'Wallet'",'environment':"VARCHAR(12) NOT NULL DEFAULT 'review'"}.items():
        if not frappe.db.sql('SHOW COLUMNS FROM tt_ops_capture LIKE %s',(name,)):
            frappe.db.sql_ddl(f'ALTER TABLE tt_ops_capture ADD COLUMN {name} {definition}')

    if not frappe.db.sql("SHOW INDEX FROM tt_ops_chunk WHERE Key_name='object_reference'"):
        frappe.db.sql_ddl("ALTER TABLE tt_ops_chunk ADD INDEX object_reference(object_key)")

    if not frappe.db.sql("SHOW INDEX FROM tt_ops_archive WHERE Key_name='object_reference'"):
        frappe.db.sql_ddl("ALTER TABLE tt_ops_archive ADD INDEX object_reference(object_key)")
