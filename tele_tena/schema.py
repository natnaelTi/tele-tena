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
    baseline()
    catalog()
    consultations()
    consultation_close_state()
