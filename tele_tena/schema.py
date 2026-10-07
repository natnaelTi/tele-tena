"""App-owned command storage; deliberately unavailable to generic DocType APIs."""
import frappe

# Frozen v1_0 baseline. Future structural changes belong in new numbered patches.
TABLES = {
    'gate': 'id int PRIMARY KEY',
    'audit': '''id varchar(36) PRIMARY KEY, actor varchar(140) NOT NULL, subject varchar(140) NOT NULL, action varchar(40) NOT NULL, evidence longtext NOT NULL, created datetime(6) NOT NULL''',
    'profile': '''user varchar(140) PRIMARY KEY, kind varchar(20) NOT NULL,
        display_name varchar(120) NOT NULL, history text NOT NULL,
        share_name tinyint NOT NULL DEFAULT 0, share_history tinyint NOT NULL DEFAULT 0''',
    'application': '''user varchar(140) PRIMARY KEY, statement text NOT NULL,
        status varchar(20) NOT NULL, reviewed_by varchar(140), reviewed_at datetime(6)''',
    'service': '''id varchar(80) PRIMARY KEY, label varchar(120) NOT NULL, active tinyint NOT NULL''',
    'offering': '''id varchar(36) PRIMARY KEY, clinician varchar(140) NOT NULL,
        service varchar(80) NOT NULL, price bigint NOT NULL, minutes int NOT NULL,
        active tinyint NOT NULL, UNIQUE KEY clinician_service (clinician, service)''',
    'availability': '''id varchar(36) PRIMARY KEY, clinician varchar(140) NOT NULL,
        start datetime(6) NOT NULL, end datetime(6) NOT NULL, KEY clinician_start (clinician, start)''',
    'wallet': '''patient varchar(140) PRIMARY KEY, available bigint NOT NULL DEFAULT 0,
        reserved bigint NOT NULL DEFAULT 0, CHECK (available >= 0), CHECK (reserved >= 0)''',
    'appointment': '''id varchar(36) PRIMARY KEY, patient varchar(140) NOT NULL,
        clinician varchar(140) NOT NULL, offering varchar(36) NOT NULL,
        start datetime(6) NOT NULL, end datetime(6) NOT NULL, state varchar(20) NOT NULL,
        price bigint NOT NULL, minutes int NOT NULL, service_label varchar(120) NOT NULL,
        disclosure longtext NOT NULL, choices text NOT NULL, retry_key varchar(80) NOT NULL,
        payload_hash varchar(64) NOT NULL, UNIQUE KEY patient_retry (patient, retry_key),
        KEY clinician_start (clinician, start)''',
    # Legacy physical name: simulation events only, not a double-entry ledger.
    'ledger': '''id varchar(36) PRIMARY KEY, patient varchar(140) NOT NULL,
        kind varchar(20) NOT NULL, amount bigint NOT NULL, reference varchar(180) NOT NULL UNIQUE,
        created datetime(6) NOT NULL, CHECK (amount > 0)''',
}

# Added in numbered patch v1_3; never mutate the frozen v1_0 baseline.
PHONE_AUTH_TABLES = {
    'phone_identity': '''user varchar(140) PRIMARY KEY, phone varchar(20) NOT NULL UNIQUE,
        verified_at datetime(6) NOT NULL, created datetime(6) NOT NULL''',
    'otp_challenge': '''id varchar(36) PRIMARY KEY, phone_digest char(64) NOT NULL,
        purpose varchar(32) NOT NULL, otp_digest char(64) NOT NULL,
        request_digest char(64) NOT NULL, created datetime(6) NOT NULL,
        expires datetime(6) NOT NULL, attempts int NOT NULL DEFAULT 0,
        consumed datetime(6), dispatch_state varchar(20) NOT NULL,
        dispatch_code varchar(40), UNIQUE KEY request_once (phone_digest,purpose,request_digest),
        KEY phone_created (phone_digest,created), KEY challenge_expiry (expires)''',
    'otp_rate_limit': '''bucket_key char(64) PRIMARY KEY, window_start datetime(6) NOT NULL,
        attempts int NOT NULL''',
    'otp_gate': 'id int PRIMARY KEY',
}


def create_tables():
    # Called by bench migrate/install; no web-accessible schema mutation.
    for name, columns in TABLES.items():
        frappe.db.sql_ddl(f'CREATE TABLE IF NOT EXISTS `tt_{name}` ({columns}) ENGINE=InnoDB')
    frappe.db.sql('INSERT IGNORE INTO tt_gate (id) VALUES (1)')
    for role in ('Tele Tena Patient', 'Tele Tena Clinician', 'Tele Tena Approver'):
        if not frappe.db.exists('Role', role):
            frappe.get_doc(dict(doctype='Role', role_name=role, desk_access=0)).insert()


def install():
    # Fresh installs mark patches complete before after_install. Bootstrap the
    # exact versioned routines; subsequent upgrades run through Frappe Patch Log.
    from tele_tena.patches.v1_0_command_storage import execute as baseline
    from tele_tena.patches.v1_1_native_catalog import execute as catalog
    from tele_tena.patches.v1_3_consultations import execute as consultations
    from tele_tena.patches.v1_4_consultation_close_state import execute as consultation_close_state
    from tele_tena.patches.v1_3_phone_auth import execute as phone_auth
    baseline()
    catalog()
    consultations()
    consultation_close_state()
    phone_auth()
    from tele_tena.patches.v1_5_contact_onboarding import execute as contact_onboarding
    contact_onboarding()
    from tele_tena.patches.v1_6_presentation_release import execute as presentation_release
    presentation_release()
    from tele_tena.patches.v1_7_demo_subledger import execute as demo_subledger
    demo_subledger()
    from tele_tena.patches.v1_8_legacy_event_reconciliation import execute as legacy_event_reconciliation
    legacy_event_reconciliation()
    from tele_tena.patches.v1_9_open_requests import execute as open_requests
    open_requests()
    from tele_tena.patches.v1_10_request_public_identity import execute as request_public_identity
    request_public_identity()
    from tele_tena.patches.v1_11_progressive_routing import execute as progressive_routing
    progressive_routing()
    from tele_tena.patches.v1_12_catalog_vetting import execute as catalog_vetting
    catalog_vetting()
    # Fresh installs mark post-model-sync patches complete before after_install.
    # Bootstrap the v1.13 audit table explicitly so fresh and upgraded sites
    # expose the same fail-closed financial reconciliation boundary.
    from tele_tena.patches.v1_13_financial_reconciliation_audit import execute as financial_reconciliation
    financial_reconciliation()
    from tele_tena.patches.v1_14_session_feedback import execute as session_feedback
    session_feedback()
    from tele_tena.patches.v1_15_mutual_rescheduling import execute as mutual_rescheduling
    mutual_rescheduling()
    from tele_tena.patches.v1_16_scope_evidence_storage import execute as scope_evidence_storage
    scope_evidence_storage()
    from tele_tena.patches.v1_17_consultation_extensions import execute as consultation_extensions
    consultation_extensions()
    from tele_tena.patches.v1_18_vetting_appeals import execute as vetting_appeals
    vetting_appeals()
    from tele_tena.patches.v1_19_scope_reverification import execute as scope_reverification
    scope_reverification()
    from tele_tena.patches.v1_20_scope_appointment_review import execute as scope_appointment_review
    scope_appointment_review()
    from tele_tena.patches.v1_21_scope_review_history import execute as scope_review_history
    scope_review_history()
    from tele_tena.patches.v1_22_immediate_service_policy import execute as immediate_service_policy
    immediate_service_policy()
