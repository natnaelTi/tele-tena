"""Add the app-owned consultation extension lifecycle; preserve all prior rows."""
import frappe


def execute():
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_consultation_extension (
        id varchar(36) PRIMARY KEY,
        appointment varchar(36) NOT NULL,
        patient varchar(140) NOT NULL,
        clinician varchar(140) NOT NULL,
        retry_key varchar(80) NOT NULL,
        state varchar(24) NOT NULL,
        duration_minutes int NOT NULL,
        amount_minor bigint NOT NULL,
        price_snapshot longtext NOT NULL,
        policy_snapshot longtext NOT NULL,
        start_after datetime(6) NOT NULL,
        expires_at datetime(6) NOT NULL,
        proposed_at datetime(6) NOT NULL,
        accepted_at datetime(6) NULL,
        started_at datetime(6) NULL,
        closed_at datetime(6) NULL,
        UNIQUE KEY appointment_retry (appointment,retry_key),
        KEY appointment_state (appointment,state),
        KEY clinician_state (clinician,state)
    ) ENGINE=InnoDB''')
