"""Allow several clinician offerings under one approved service scope."""
import frappe


def execute():
    # The v1.0 table is deliberately frozen. Inspect first so this patch is safe
    # on both fresh installs and sites where it has already run.
    columns = {row[0] for row in frappe.db.sql('SHOW COLUMNS FROM tt_offering')}
    if 'title' not in columns:
        frappe.db.sql_ddl("ALTER TABLE tt_offering ADD COLUMN title varchar(160) NOT NULL DEFAULT '' AFTER service")
    if 'description' not in columns:
        frappe.db.sql_ddl("ALTER TABLE tt_offering ADD COLUMN description varchar(1000) NOT NULL DEFAULT '' AFTER title")
    if 'retry_key' not in columns:
        frappe.db.sql_ddl("ALTER TABLE tt_offering ADD COLUMN retry_key varchar(100) NULL AFTER active")
    if 'payload_hash' not in columns:
        frappe.db.sql_ddl("ALTER TABLE tt_offering ADD COLUMN payload_hash char(64) NULL AFTER retry_key")
    indexes = {row[2] for row in frappe.db.sql('SHOW INDEX FROM tt_offering')}
    if 'clinician_service' in indexes:
        frappe.db.sql_ddl('ALTER TABLE tt_offering DROP INDEX clinician_service')
    indexes = {row[2] for row in frappe.db.sql('SHOW INDEX FROM tt_offering')}
    if 'clinician_retry' not in indexes:
        frappe.db.sql_ddl('ALTER TABLE tt_offering ADD UNIQUE KEY clinician_retry (clinician,retry_key)')
    # Initialize only newly-added presentation metadata; appointment snapshots
    # and every pre-existing operational value remain untouched.
    frappe.db.sql("""UPDATE tt_offering o JOIN `tabTele Tena Service` s ON s.name=o.service
        SET o.title=s.service_label WHERE o.title=''""")
