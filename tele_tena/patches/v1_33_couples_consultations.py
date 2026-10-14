"""Add consented adult couples storage without converting old appointments."""
import frappe


def execute():
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_couple_plan (
        id varchar(36) PRIMARY KEY, payer varchar(140) NOT NULL,
        offering varchar(36) NOT NULL, start datetime(6) NOT NULL,
        timezone varchar(80) NOT NULL, price bigint NOT NULL, minutes int NOT NULL,
        retry_key varchar(80) NOT NULL, payload_hash char(64) NOT NULL,
        token_digest char(64) NOT NULL UNIQUE, state varchar(24) NOT NULL,
        appointment varchar(36) UNIQUE, created datetime(6) NOT NULL,
        expires_at datetime(6) NOT NULL, UNIQUE KEY payer_retry(payer,retry_key)
    ) ENGINE=InnoDB''')
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_couple_participant (
        id varchar(36) PRIMARY KEY, plan varchar(36) NOT NULL,
        user varchar(140) NOT NULL, state varchar(24) NOT NULL,
        disclosure longtext NOT NULL, choices text NOT NULL,
        consent_version varchar(50) NOT NULL, consented_at datetime(6) NOT NULL,
        withdrawn_at datetime(6), room_identity varchar(80) NOT NULL UNIQUE,
        UNIQUE KEY plan_user(plan,user), KEY user_state(user,state)
    ) ENGINE=InnoDB''')
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_note_recipient (
        appointment varchar(36) NOT NULL, revision int NOT NULL,
        participant varchar(36) NOT NULL, published_at datetime(6) NOT NULL,
        PRIMARY KEY(appointment,revision,participant)
    ) ENGINE=InnoDB''')
    if not frappe.db.sql("SHOW COLUMNS FROM tt_note_revision LIKE 'recipient_ids'"):
        frappe.db.sql_ddl('ALTER TABLE tt_note_revision ADD COLUMN recipient_ids text')
