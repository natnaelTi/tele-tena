"""Additive direct-transfer claims. Existing sites keep Wallet until explicit operator choice."""
import frappe

def execute():
    tables={
      'payment_config':"id INT PRIMARY KEY,mode VARCHAR(16) NOT NULL,revision INT NOT NULL DEFAULT 1,hold_minutes INT NOT NULL DEFAULT 30,verification_hours INT NOT NULL DEFAULT 24,modified DATETIME(6) NOT NULL",
      'telebirr_payee':"clinician VARCHAR(140) PRIMARY KEY,phone VARCHAR(16) NOT NULL,revision INT NOT NULL,modified DATETIME(6) NOT NULL",
      'direct_payment':"""id CHAR(36) PRIMARY KEY,appointment CHAR(36) NOT NULL,patient VARCHAR(140) NOT NULL,clinician VARCHAR(140) NOT NULL,
        amount BIGINT NOT NULL,currency CHAR(3) NOT NULL DEFAULT 'ETB',payee VARCHAR(16) NOT NULL,payee_revision INT NOT NULL,
        mode_revision INT NOT NULL,reference_type VARCHAR(20) NOT NULL DEFAULT 'Appointment',reference_id CHAR(36),state VARCHAR(30) NOT NULL,hold_until DATETIME(6) NOT NULL,verify_until DATETIME(6) NOT NULL,
        transaction_ref VARCHAR(100),verified_at DATETIME(6),verified_by VARCHAR(140),created DATETIME(6) NOT NULL,
        UNIQUE KEY payable_reference(reference_type,reference_id),KEY owner_payment(patient,created),KEY clinician_payment(clinician,state),KEY expiry(state,hold_until)""",
      'direct_payment_event':"""id CHAR(36) PRIMARY KEY,payment CHAR(36) NOT NULL,actor VARCHAR(140) NOT NULL,event VARCHAR(40) NOT NULL,
        retry_key VARCHAR(100) NOT NULL,payload_hash CHAR(64) NOT NULL,details LONGTEXT,evidence CHAR(36),reason VARCHAR(1000),created DATETIME(6) NOT NULL,
        UNIQUE KEY retry(payment,actor,retry_key),KEY history(payment,created)""",
      'direct_receipt':"id CHAR(36) PRIMARY KEY,payment CHAR(36) NOT NULL,owner VARCHAR(140) NOT NULL,filename VARCHAR(180) NOT NULL,mime VARCHAR(40) NOT NULL,content LONGBLOB NOT NULL,content_sha256 CHAR(64) NOT NULL,created DATETIME(6) NOT NULL",
      'direct_transaction_ref':"payee VARCHAR(16) NOT NULL,transaction_ref VARCHAR(100) NOT NULL,payment CHAR(36) NOT NULL,PRIMARY KEY(payee,transaction_ref)",
    }
    for name,definition in tables.items():frappe.db.sql_ddl(f'CREATE TABLE IF NOT EXISTS tt_{name} ({definition}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4')
    if not frappe.db.sql("SHOW COLUMNS FROM tt_direct_payment LIKE 'reference_type'"):
        frappe.db.sql_ddl("ALTER TABLE tt_direct_payment ADD COLUMN reference_type VARCHAR(20) NOT NULL DEFAULT 'Appointment',ADD COLUMN reference_id CHAR(36) NULL,DROP INDEX appointment_payment,ADD UNIQUE KEY payable_reference(reference_type,reference_id)")
        frappe.db.sql('UPDATE tt_direct_payment SET reference_id=appointment WHERE reference_id IS NULL')
    if not frappe.db.sql("SHOW COLUMNS FROM tt_direct_payment_event LIKE 'details'"):frappe.db.sql_ddl('ALTER TABLE tt_direct_payment_event ADD COLUMN details LONGTEXT NULL')
    if not frappe.db.sql("SHOW COLUMNS FROM tt_booking_notice LIKE 'context_key'"):
        frappe.db.sql_ddl("ALTER TABLE tt_booking_notice ADD COLUMN context_key VARCHAR(80) NOT NULL DEFAULT '',DROP INDEX durable_notice,ADD UNIQUE KEY durable_notice (appointment,user,event,channel,context_key)")
    frappe.db.sql("INSERT IGNORE INTO tt_payment_config (id,mode,modified) VALUES (1,'Wallet',UTC_TIMESTAMP(6))")
    if not frappe.db.sql("SHOW COLUMNS FROM tt_appointment LIKE 'payment_mode'"):
        frappe.db.sql_ddl("ALTER TABLE tt_appointment ADD COLUMN payment_mode VARCHAR(16) NOT NULL DEFAULT 'Wallet'")
    if not frappe.db.exists('Role','Tele Tena Financial Configuration'):
        frappe.get_doc({'doctype':'Role','role_name':'Tele Tena Financial Configuration','desk_access':1}).insert()
