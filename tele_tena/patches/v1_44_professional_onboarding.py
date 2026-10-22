"""Additive structured applications and private evidence. No inferred legacy names/roles."""
import re
import frappe


def execute():
    definitions={
        'reference':'''id VARCHAR(100) PRIMARY KEY,kind VARCHAR(20) NOT NULL,label VARCHAR(240) NOT NULL,
            aliases TEXT NOT NULL,country VARCHAR(2) NOT NULL DEFAULT '',region VARCHAR(140) NOT NULL DEFAULT '',
            entity_type VARCHAR(80) NOT NULL DEFAULT '',source_id VARCHAR(180),source_url VARCHAR(500),
            accessed DATE,permitted_use VARCHAR(180),status VARCHAR(20) NOT NULL DEFAULT 'Listed',
            submitted_by VARCHAR(140),merged_into VARCHAR(100),clinic VARCHAR(140),
            KEY reference_search(kind,status,country,label),KEY source_identity(kind,source_id)''',
        'professional_draft':'''user VARCHAR(140) PRIMARY KEY,payload LONGTEXT NOT NULL,
            revision INT NOT NULL DEFAULT 1,modified DATETIME(6) NOT NULL,legacy_name VARCHAR(120) NULL''',
        'professional_submission':'''id CHAR(36) PRIMARY KEY,user VARCHAR(140) NOT NULL,
            payload LONGTEXT NOT NULL,digest CHAR(64) NOT NULL,created DATETIME(6) NOT NULL,
            declaration_version VARCHAR(60) NOT NULL,KEY owner_submissions(user,created),UNIQUE KEY same_submission(user,digest)''',
        'professional_evidence':'''id CHAR(36) PRIMARY KEY,user VARCHAR(140) NOT NULL,
            purpose VARCHAR(30) NOT NULL,filename VARCHAR(180) NOT NULL,mime VARCHAR(40) NOT NULL,
            content LONGBLOB NOT NULL,content_sha256 CHAR(64) NOT NULL,content_size INT NOT NULL,
            created DATETIME(6) NOT NULL,UNIQUE KEY owner_file(user,purpose,content_sha256),KEY owner_evidence(user,created)''',
        'identity_reviewer':'''clinician VARCHAR(140) NOT NULL,reviewer VARCHAR(140) NOT NULL,
            assigned_by VARCHAR(140) NOT NULL,reason VARCHAR(500) NOT NULL,created DATETIME(6) NOT NULL,
            PRIMARY KEY(clinician,reviewer)''',
    }
    for key,definition in definitions.items():
        frappe.db.sql_ddl(f'CREATE TABLE IF NOT EXISTS tt_{key} ({definition}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4')
    if not frappe.db.sql("SHOW COLUMNS FROM tt_professional_draft LIKE 'legacy_name'"):
        frappe.db.sql_ddl('ALTER TABLE tt_professional_draft ADD COLUMN legacy_name VARCHAR(120) NULL')
    if not frappe.db.sql("SHOW COLUMNS FROM tt_professional_submission LIKE 'reference_snapshot'"):
        frappe.db.sql_ddl('ALTER TABLE tt_professional_submission ADD COLUMN reference_snapshot LONGTEXT NULL')
    if frappe.db.table_exists('Tele Tena Vetting Scope Application') and not frappe.db.sql("SHOW COLUMNS FROM `tabTele Tena Vetting Scope Application` LIKE 'professional_submission'"):
        frappe.db.sql_ddl('ALTER TABLE `tabTele Tena Vetting Scope Application` ADD COLUMN professional_submission CHAR(36) NULL')
    if frappe.db.table_exists('Tele Tena Vetting Scope Application'):
        for column in ('qualification','issuing_institution','issuing_authority'):
            found=frappe.db.sql('SHOW COLUMNS FROM `tabTele Tena Vetting Scope Application` LIKE %s',(column,))
            width=re.fullmatch(r'varchar\((\d+)\)',str(found[0][1]).lower()) if found else None
            if width and int(width[1]) < 240:
                frappe.db.sql_ddl(f'ALTER TABLE `tabTele Tena Vetting Scope Application` MODIFY `{column}` VARCHAR(240) NULL')
    from tele_tena.professional_reference import import_bundled
    import_bundled()
