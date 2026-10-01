"""Add verified contact identities and resumable drafts; preserve existing records."""
import frappe


def execute():
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_contact_identity (
        channel varchar(8) NOT NULL, contact varchar(254) NOT NULL,
        user varchar(140) NOT NULL, verified_at datetime(6) NOT NULL,
        PRIMARY KEY (channel,contact), KEY user_identity (user)
    ) ENGINE=InnoDB''')
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_onboarding (
        user varchar(140) PRIMARY KEY, kind varchar(12) NOT NULL DEFAULT 'patient',
        step int NOT NULL DEFAULT 0, answers longtext NOT NULL,
        completed datetime(6), modified datetime(6) NOT NULL
    ) ENGINE=InnoDB''')
