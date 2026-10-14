"""Patient-owned medical history; no automatic encounter disclosure."""
import frappe


def execute():
    frappe.db.sql('''CREATE TABLE IF NOT EXISTS tt_history_document (
        id CHAR(36) PRIMARY KEY, patient VARCHAR(140) NOT NULL,
        filename VARCHAR(180) NOT NULL, mime VARCHAR(40) NOT NULL,
        content LONGBLOB NOT NULL, content_size INT NOT NULL,
        content_sha256 CHAR(64) NOT NULL, created DATETIME(6) NOT NULL,
        UNIQUE KEY patient_content (patient,content_sha256,filename),
        INDEX patient_created (patient,created)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
