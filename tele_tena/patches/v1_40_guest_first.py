"""Additive,empty consent/grant/outbox structures. Never rewrite prior choices."""
import frappe

def execute():
    if not frappe.db.sql("SHOW COLUMNS FROM tt_profile LIKE 'care_alias'"):
        frappe.db.sql('ALTER TABLE tt_profile ADD COLUMN care_alias VARCHAR(120) NULL')
    for statement in [
    '''CREATE TABLE IF NOT EXISTS tt_policy_acceptance (
      id CHAR(36) PRIMARY KEY,user VARCHAR(140) NOT NULL,terms_version VARCHAR(80) NOT NULL,
      privacy_version VARCHAR(80) NOT NULL,terms_accepted TINYINT NOT NULL,privacy_acknowledged TINYINT NOT NULL,
      care_consent TINYINT NOT NULL,marketing TINYINT NOT NULL DEFAULT 0,review_only TINYINT NOT NULL DEFAULT 1,
      created DATETIME(6) NOT NULL,UNIQUE KEY user_policy (user,terms_version,privacy_version)) ENGINE=InnoDB''',
    '''CREATE TABLE IF NOT EXISTS tt_history_grant (
      id CHAR(36) PRIMARY KEY,document_id CHAR(36) NOT NULL,appointment CHAR(36) NOT NULL,
      patient VARCHAR(140) NOT NULL,recipient VARCHAR(140) NOT NULL,version VARCHAR(80) NOT NULL,
      filename VARCHAR(180) NOT NULL,mime VARCHAR(40) NOT NULL,content LONGBLOB NOT NULL,
      content_sha256 CHAR(64) NOT NULL,created DATETIME(6) NOT NULL,revoked_at DATETIME(6),
      UNIQUE KEY encounter_file (appointment,document_id,recipient),KEY owner_grants (patient,created)) ENGINE=InnoDB''',
    '''CREATE TABLE IF NOT EXISTS tt_history_grant_event (
      id CHAR(36) PRIMARY KEY,grant_id CHAR(36) NOT NULL,actor VARCHAR(140) NOT NULL,
      event VARCHAR(30) NOT NULL,created DATETIME(6) NOT NULL) ENGINE=InnoDB''',
    '''CREATE TABLE IF NOT EXISTS tt_notice_preference (
      user VARCHAR(140) PRIMARY KEY,email_enabled TINYINT NOT NULL DEFAULT 0,sms_enabled TINYINT NOT NULL DEFAULT 0) ENGINE=InnoDB''',
    '''CREATE TABLE IF NOT EXISTS tt_booking_notice (
      id CHAR(36) PRIMARY KEY,appointment CHAR(36) NOT NULL,user VARCHAR(140) NOT NULL,event VARCHAR(30) NOT NULL,
      channel VARCHAR(12) NOT NULL,state VARCHAR(30) NOT NULL,attempts INT NOT NULL DEFAULT 0,
      created DATETIME(6) NOT NULL,modified DATETIME(6) NOT NULL,read_at DATETIME(6),
      UNIQUE KEY durable_notice (appointment,user,event,channel),KEY dispatch (state,created)) ENGINE=InnoDB'''
    ]:frappe.db.sql(statement)
