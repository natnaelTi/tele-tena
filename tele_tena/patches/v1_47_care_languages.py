"""Separate interface locales from claimed, reviewed and offering-supported care languages."""
import json
from pathlib import Path
import frappe

def execute():
    tables={
      'care_language':"code VARCHAR(16) PRIMARY KEY,english VARCHAR(160) NOT NULL,amharic VARCHAR(160),afaan_oromo VARCHAR(160),aliases TEXT,source VARCHAR(300) NOT NULL,active TINYINT NOT NULL DEFAULT 1",
      'care_language_claim':"clinician VARCHAR(140) NOT NULL,language VARCHAR(16) NOT NULL,proficiency INT NULL,explanation TEXT,state VARCHAR(30) NOT NULL DEFAULT 'Pending',active TINYINT NOT NULL DEFAULT 1,reviewer VARCHAR(140),reason TEXT,modified DATETIME(6) NOT NULL,PRIMARY KEY(clinician,language)",
      'care_language_event':"id CHAR(36) PRIMARY KEY,clinician VARCHAR(140) NOT NULL,language VARCHAR(16) NOT NULL,actor VARCHAR(140) NOT NULL,event VARCHAR(40) NOT NULL,details LONGTEXT NOT NULL,created DATETIME(6) NOT NULL",
      'language_appointment_review':"appointment CHAR(36) NOT NULL,language VARCHAR(16) NOT NULL,reason VARCHAR(300) NOT NULL,created DATETIME(6) NOT NULL,PRIMARY KEY(appointment,language)",
    }
    for name,definition in tables.items():frappe.db.sql_ddl(f'CREATE TABLE IF NOT EXISTS tt_{name} ({definition}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4')
    bundle=json.loads((Path(__file__).resolve().parents[1]/'reference_data/care-languages-v1.json').read_text())
    for r in bundle['records']:frappe.db.sql('INSERT IGNORE INTO tt_care_language (code,english,amharic,afaan_oromo,aliases,source) VALUES (%s,%s,%s,%s,%s,%s)',(r['code'],r['english'],r['amharic'],r['afaan_oromo'],json.dumps(r['aliases']),bundle['source']))
    for table,column,definition in [('tt_profile','preferred_care_language','VARCHAR(16) NULL'),('tt_offering','care_languages','TEXT NULL')]:
        if not frappe.db.sql('SHOW COLUMNS FROM '+table+' LIKE %s',(column,)):frappe.db.sql_ddl(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
    # Earlier lists are self-declarations, not individual human decisions.
    for p in frappe.db.sql("SELECT user,languages FROM tt_profile WHERE kind='clinician'",as_dict=True):
        try:values=json.loads(p.languages or '[]')
        except (TypeError,ValueError):continue
        for code in values:
            if frappe.db.sql('SELECT code FROM tt_care_language WHERE code=%s',(code,)):
                frappe.db.sql("INSERT IGNORE INTO tt_care_language_claim (clinician,language,state,modified) VALUES (%s,%s,'Pending',UTC_TIMESTAMP(6))",(p.user,code))
