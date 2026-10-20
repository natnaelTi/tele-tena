"""Empty private notification and manual-response observations; no historical backfill."""
import frappe

def execute():
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_user_notification (
      id CHAR(36) PRIMARY KEY,user VARCHAR(140) NOT NULL,event_key VARCHAR(180) NOT NULL,
      kind VARCHAR(40) NOT NULL,appointment CHAR(36),created DATETIME(6) NOT NULL,read_at DATETIME(6),
      UNIQUE KEY user_event (user,event_key),KEY user_created (user,created)) ENGINE=InnoDB''')
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_confirmation_observation (
      appointment CHAR(36) PRIMARY KEY,clinician VARCHAR(140) NOT NULL,requested_at DATETIME(6) NOT NULL,
      first_presented_at DATETIME(6),responded_at DATETIME(6),response VARCHAR(20),reminded_at DATETIME(6),
      expired_at DATETIME(6),KEY clinician_requested (clinician,requested_at)) ENGINE=InnoDB''')
