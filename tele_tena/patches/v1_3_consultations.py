"""Versioned storage for appointment-bound LiveKit consultations."""
import frappe


def execute():
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_consultation (
        appointment varchar(36) PRIMARY KEY,
        id varchar(36) NOT NULL UNIQUE,
        room_name varchar(80) NOT NULL UNIQUE,
        patient_identity varchar(80) NOT NULL,
        clinician_identity varchar(80) NOT NULL,
        state varchar(20) NOT NULL,
        created datetime(6) NOT NULL,
        ended_by varchar(140),
        ended datetime(6)
    ) ENGINE=InnoDB''')
