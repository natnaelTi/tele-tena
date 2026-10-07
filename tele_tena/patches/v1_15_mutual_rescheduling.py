"""Add an auditable, participant-consented appointment time-change workflow."""
import frappe


def execute():
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS `tt_reschedule_proposal` (
        id varchar(36) PRIMARY KEY,
        appointment varchar(36) NOT NULL,
        proposer varchar(140) NOT NULL,
        start datetime(6) NOT NULL,
        end datetime(6) NOT NULL,
        timezone varchar(80) NOT NULL,
        retry_key varchar(80) NOT NULL,
        payload_hash char(64) NOT NULL,
        state varchar(20) NOT NULL,
        created_at datetime(6) NOT NULL,
        expires_at datetime(6) NOT NULL,
        responded_by varchar(140) NULL,
        responded_at datetime(6) NULL,
        UNIQUE KEY proposal_retry (appointment,proposer,retry_key),
        KEY appointment_state (appointment,state,expires_at),
        KEY pending_expiry (state,expires_at)
    ) ENGINE=InnoDB''')
