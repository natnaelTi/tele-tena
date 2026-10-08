"""Store the versioned proposed vetting rubric separately from assessments."""
import frappe


def execute():
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_vetting_rubric_version (
        version varchar(40) PRIMARY KEY,
        status varchar(20) NOT NULL,
        definition_json longtext NOT NULL,
        definition_sha256 char(64) NOT NULL,
        created_by varchar(140) NOT NULL,
        created_at datetime(6) NOT NULL,
        approved_by varchar(140),
        approved_at datetime(6),
        approval_reason text,
        KEY status_created (status,created_at)
    ) ENGINE=InnoDB''')
    from tele_tena.vetting_rubric import canonical_json, digest
    version = 'proposed-1.0'
    frappe.db.sql('''INSERT IGNORE INTO tt_vetting_rubric_version
        (version,status,definition_json,definition_sha256,created_by,created_at)
        VALUES (%s,'Proposed',%s,%s,'System',UTC_TIMESTAMP(6))''',
        (version, canonical_json(version), digest(version)))
    if not frappe.db.exists('Role', 'Tele Tena Medical Lead'):
        frappe.get_doc({'doctype': 'Role', 'role_name': 'Tele Tena Medical Lead',
                        'desk_access': 0}).insert()
