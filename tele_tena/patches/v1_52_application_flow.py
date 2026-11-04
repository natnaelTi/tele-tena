"""Additive typed information requests and recorded assisted-entry provenance."""
import frappe

def execute():
 definitions={
 'scope_information_request':'''id CHAR(36) PRIMARY KEY,application VARCHAR(140) NOT NULL,assessment VARCHAR(140),reviewer VARCHAR(140) NOT NULL,reason TEXT NOT NULL,items LONGTEXT NOT NULL,state VARCHAR(20) NOT NULL,created DATETIME(6) NOT NULL,KEY app_state(application,state,created)''',
 'scope_information_response':'''id CHAR(36) PRIMARY KEY,request_id CHAR(36) NOT NULL UNIQUE,application VARCHAR(140) NOT NULL,actor VARCHAR(140) NOT NULL,payload LONGTEXT NOT NULL,digest CHAR(64) NOT NULL,created DATETIME(6) NOT NULL''',
 'assistance_case':'''id CHAR(36) PRIMARY KEY,clinician VARCHAR(140) NOT NULL,services LONGTEXT NOT NULL,state VARCHAR(20) NOT NULL,requested DATETIME(6) NOT NULL,modified DATETIME(6) NOT NULL,KEY clinician_state(clinician,state)''',
 'assisted_submission':'''id CHAR(36) PRIMARY KEY,case_id CHAR(36) NOT NULL UNIQUE,clinician VARCHAR(140) NOT NULL,reviewer VARCHAR(140) NOT NULL,authorization_file CHAR(36) NOT NULL,source_reference VARCHAR(240) NOT NULL,received_on DATE NOT NULL,terms_version VARCHAR(120) NOT NULL,privacy_version VARCHAR(120) NOT NULL,attestations LONGTEXT NOT NULL,payload_sha256 CHAR(64) NOT NULL,created DATETIME(6) NOT NULL''',
 }
 for name,fields in definitions.items():frappe.db.sql_ddl(f'CREATE TABLE IF NOT EXISTS tt_{name} ({fields}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4')

 if not frappe.db.sql("SHOW COLUMNS FROM tt_scope_information_request LIKE 'origin'"):
  frappe.db.sql_ddl("ALTER TABLE tt_scope_information_request ADD COLUMN origin VARCHAR(40) NOT NULL DEFAULT 'Reviewer'")
