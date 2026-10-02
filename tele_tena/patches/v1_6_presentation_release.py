"""Add recurring schedules, state metadata, private notes, resume evidence and tours.

All changes are additive. Existing appointments retain their UTC start/end and
state; their schedule timezone remains NULL because it cannot be inferred.
"""
import frappe


APPOINTMENT_COLUMNS = {
    'timezone': 'varchar(80) NULL',
    'schedule_id': 'varchar(36) NULL',
    'confirmation_mode': "varchar(20) NOT NULL DEFAULT 'automatic'",
    'expires_at': 'datetime(6) NULL',
    'confirmed_at': 'datetime(6) NULL',
    'consultation_format': "varchar(16) NOT NULL DEFAULT 'video'",
    'buffer_before': 'int NOT NULL DEFAULT 0',
    'buffer_after': 'int NOT NULL DEFAULT 0',
    'cancelled_by': 'varchar(140) NULL',
    'cancelled_at': 'datetime(6) NULL',
    'cancel_reason': 'varchar(500) NULL',
    'policy_snapshot': 'longtext NULL',
    'created': 'datetime(6) NULL',
}

APPLICATION_COLUMNS = {
    'requested_services': 'longtext NULL',
    'submitted_at': 'datetime(6) NULL',
}

TABLES = {
    'schedule': '''id varchar(36) PRIMARY KEY, clinician varchar(140) NOT NULL,
        offering varchar(36) NOT NULL UNIQUE, schedule_name varchar(120) NOT NULL,
        timezone varchar(80) NOT NULL, consultation_format varchar(16) NOT NULL,
        confirmation_mode varchar(20) NOT NULL, minimum_notice_minutes int NOT NULL,
        horizon_days int NOT NULL, buffer_before int NOT NULL, buffer_after int NOT NULL,
        status varchar(16) NOT NULL, created datetime(6) NOT NULL,
        modified datetime(6) NOT NULL, KEY clinician_status (clinician,status)''',
    'schedule_rule': '''id varchar(36) PRIMARY KEY, schedule_id varchar(36) NOT NULL,
        weekday tinyint NOT NULL, start_local time NOT NULL, end_local time NOT NULL,
        KEY schedule_weekday (schedule_id,weekday)''',
    'schedule_exception': '''id varchar(36) PRIMARY KEY, schedule_id varchar(36) NOT NULL,
        local_date date NOT NULL, kind varchar(16) NOT NULL,
        start_local time NULL, end_local time NULL,
        KEY schedule_date (schedule_id,local_date)''',
    'consultation_note': '''appointment varchar(36) PRIMARY KEY, clinician varchar(140) NOT NULL,
        status varchar(16) NOT NULL, current_revision int NOT NULL DEFAULT 0,
        created datetime(6) NOT NULL, modified datetime(6) NOT NULL,
        KEY clinician_status (clinician,status)''',
    'appointment_event': '''id varchar(36) PRIMARY KEY, appointment varchar(36) NOT NULL,
        event_type varchar(32) NOT NULL, actor varchar(140) NOT NULL,
        reason varchar(500) NULL, created datetime(6) NOT NULL,
        KEY appointment_created (appointment,created)''',
    'note_revision': '''id varchar(36) PRIMARY KEY, appointment varchar(36) NOT NULL,
        clinician varchar(140) NOT NULL, revision int NOT NULL,
        private_note longtext NOT NULL, patient_summary longtext NOT NULL,
        summary_published tinyint NOT NULL, author varchar(140) NOT NULL,
        created datetime(6) NOT NULL, UNIQUE KEY appointment_revision (appointment,revision),
        KEY appointment_published (appointment,summary_published,revision)''',
    'resume_evidence': '''clinician varchar(140) PRIMARY KEY, filename varchar(255) NOT NULL,
        content mediumblob NOT NULL, content_size int NOT NULL, content_sha256 char(64) NOT NULL,
        revision int NOT NULL, uploaded_by varchar(140) NOT NULL,
        uploaded_at datetime(6) NOT NULL''',
    'preferences': '''user varchar(140) PRIMARY KEY, locale varchar(8) NOT NULL DEFAULT 'en',
        timezone varchar(80) NULL, notification_preferences longtext NULL,
        modified datetime(6) NOT NULL''',
    'tour_progress': '''user varchar(140) NOT NULL, role varchar(32) NOT NULL,
        tour_id varchar(64) NOT NULL, version int NOT NULL,
        state varchar(16) NOT NULL, modified datetime(6) NOT NULL,
        PRIMARY KEY (user,role,tour_id,version)''',
}


def execute():
    for column, definition in APPLICATION_COLUMNS.items():
        if not frappe.db.sql(f"SHOW COLUMNS FROM tt_application LIKE '{column}'"):
            frappe.db.sql_ddl(f'ALTER TABLE tt_application ADD COLUMN `{column}` {definition}')
    for column, definition in APPOINTMENT_COLUMNS.items():
        if not frappe.db.sql(f"SHOW COLUMNS FROM tt_appointment LIKE '{column}'"):
            frappe.db.sql_ddl(f'ALTER TABLE tt_appointment ADD COLUMN `{column}` {definition}')
    for table, columns in TABLES.items():
        frappe.db.sql_ddl(f'CREATE TABLE IF NOT EXISTS `tt_{table}` ({columns}) ENGINE=InnoDB')
