"""Immutable individual consent for proposed shared-session time/price changes."""
import frappe


def execute():
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_shared_change_consent (
        kind varchar(20) NOT NULL, change_id varchar(36) NOT NULL,
        participant varchar(140) NOT NULL, decision varchar(10) NOT NULL,
        created datetime(6) NOT NULL,
        PRIMARY KEY(kind,change_id,participant)
    ) ENGINE=InnoDB''')
