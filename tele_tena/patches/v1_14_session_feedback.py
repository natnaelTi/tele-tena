"""Add private, encounter-scoped patient session-experience feedback."""
import frappe


def execute():
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS `tt_session_feedback` (
        id varchar(36) PRIMARY KEY,
        appointment varchar(36) NOT NULL UNIQUE,
        patient varchar(140) NOT NULL,
        clinician varchar(140) NOT NULL,
        rating tinyint NOT NULL,
        metric_version varchar(40) NOT NULL,
        created_at datetime(6) NOT NULL,
        KEY clinician_created (clinician,created_at),
        KEY patient_created (patient,created_at),
        CHECK (rating BETWEEN 1 AND 5)
    ) ENGINE=InnoDB''')
