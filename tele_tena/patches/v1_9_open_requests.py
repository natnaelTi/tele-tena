"""Private open requests, scoped delivery, offers and clinician readiness."""
import frappe

TABLES = {
    'clinician_request_presence': '''clinician varchar(140) PRIMARY KEY, ready tinyint NOT NULL DEFAULT 0,
        heartbeat_at datetime(6) NOT NULL, expires_at datetime(6) NOT NULL''',
    'open_request': '''id varchar(36) PRIMARY KEY, patient varchar(140) NOT NULL,
        state varchar(16) NOT NULL, urgency varchar(16) NOT NULL, service varchar(80) NOT NULL,
        language varchar(12) NOT NULL, consultation_format varchar(8) NOT NULL,
        request_text text NOT NULL, disclosure_snapshot longtext NOT NULL,
        max_price_minor bigint NULL, earliest_start datetime(6) NULL, latest_start datetime(6) NOT NULL,
        timezone varchar(80) NOT NULL, retry_key varchar(80) NOT NULL,
        payload_hash char(64) NOT NULL, sharing_choices varchar(200) NOT NULL,
        appointment varchar(36) NULL, published_at datetime(6) NOT NULL,
        first_notice_at datetime(6) NULL, first_offer_at datetime(6) NULL,
        matched_at datetime(6) NULL, expires_at datetime(6) NOT NULL,
        UNIQUE KEY patient_retry (patient,retry_key), KEY state_expiry (state,expires_at),
        KEY patient_created (patient,published_at)''',
    'request_recipient': '''request_id varchar(36) NOT NULL, clinician varchar(140) NOT NULL,
        notified_at datetime(6) NOT NULL, delivered_round tinyint NOT NULL DEFAULT 1,
        PRIMARY KEY (request_id,clinician), KEY clinician_notice (clinician,notified_at)''',
    'request_offer': '''id varchar(36) PRIMARY KEY, request_id varchar(36) NOT NULL,
        clinician varchar(140) NOT NULL, offering varchar(36) NOT NULL,
        start datetime(6) NOT NULL, duration_minutes int NOT NULL, consultation_format varchar(8) NOT NULL,
        price_minor bigint NOT NULL, price_source varchar(16) NOT NULL,
        state varchar(16) NOT NULL, valid_until datetime(6) NOT NULL, appointment varchar(36) NULL,
        created_at datetime(6) NOT NULL, KEY request_state (request_id,state,valid_until),
        KEY clinician_offer (clinician,state,created_at)''',
    'request_metric': '''id varchar(36) PRIMARY KEY, request_id varchar(36) NOT NULL,
        event varchar(32) NOT NULL, occurred_at datetime(6) NOT NULL,
        eligible_supply int NULL, external_event_id varchar(128) NULL UNIQUE,
        KEY request_event (request_id,event,occurred_at)''',
}


def execute():
    for name, columns in TABLES.items():
        frappe.db.sql_ddl(f'CREATE TABLE IF NOT EXISTS `tt_{name}` ({columns}) ENGINE=InnoDB')
    if not frappe.db.sql("SHOW COLUMNS FROM tt_profile LIKE 'languages'"):
        frappe.db.sql_ddl("ALTER TABLE tt_profile ADD COLUMN languages varchar(400) NOT NULL DEFAULT '[]'")
