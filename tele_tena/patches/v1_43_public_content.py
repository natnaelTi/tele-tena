"""Additive immutable review-content registry. Never changes historical acceptances."""
import json
import frappe
from tele_tena.public_content_defaults import DOCUMENTS,CONTACT

def execute():
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_public_content_revision (
      id VARCHAR(80) PRIMARY KEY,content_key VARCHAR(60) NOT NULL,payload LONGTEXT NOT NULL,
      actor VARCHAR(140) NOT NULL,created DATETIME(6) NOT NULL,
      KEY content_history(content_key,created)) ENGINE=InnoDB''')
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_public_content_head (
      content_key VARCHAR(60) PRIMARY KEY,draft_id VARCHAR(80) NOT NULL,published_id VARCHAR(80),
      revision INT NOT NULL DEFAULT 1,updated DATETIME(6) NOT NULL) ENGINE=InnoDB''')
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_public_content_event (
      id CHAR(36) PRIMARY KEY,content_key VARCHAR(60) NOT NULL,version VARCHAR(80) NOT NULL,
      action VARCHAR(20) NOT NULL,actor VARCHAR(140) NOT NULL,created DATETIME(6) NOT NULL,
      KEY content_events(content_key,created)) ENGINE=InnoDB''')
    defaults={'contact':CONTACT,**{key:{'title':title,'body':body,'audience':audience,'review_only':True} for key,(title,audience,body) in DOCUMENTS.items()}}
    for key,payload in defaults.items():
        # Stable IDs and INSERT IGNORE preserve all subsequent reviewer decisions.
        version=key+'-draft-2026-10-20-v1'
        frappe.db.sql('INSERT IGNORE INTO tt_public_content_revision VALUES (%s,%s,%s,%s,UTC_TIMESTAMP(6))',(version,key,json.dumps(payload,ensure_ascii=False),'System: review boilerplate'))
        frappe.db.sql('INSERT IGNORE INTO tt_public_content_head VALUES (%s,%s,%s,1,UTC_TIMESTAMP(6))',(key,version,version))
