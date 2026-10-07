"""Create the append-only audit trail for immediate-service policy changes."""
import frappe


def execute():
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS `tt_immediate_service_policy_event` (
        id varchar(36) PRIMARY KEY,
        service varchar(80) NOT NULL,
        previous_enabled tinyint NOT NULL,
        enabled tinyint NOT NULL,
        reviewer varchar(140) NOT NULL,
        reason varchar(1000) NOT NULL,
        definition_version varchar(80) NOT NULL,
        idempotency_key varchar(100) NOT NULL,
        payload_hash char(64) NOT NULL,
        created datetime(6) NOT NULL,
        UNIQUE KEY service_retry (service,idempotency_key),
        KEY service_created (service,created)
    ) ENGINE=InnoDB''')
