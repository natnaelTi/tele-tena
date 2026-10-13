"""Private, owner-controlled raster photos; no changes to encounter disclosures."""
import frappe


def execute():
    if frappe.db.sql("SHOW TABLES LIKE 'tt_profile_photo'"):
        return
    frappe.db.sql('''CREATE TABLE IF NOT EXISTS tt_profile_photo (
        user VARCHAR(140) PRIMARY KEY, id CHAR(36) NOT NULL UNIQUE,
        content LONGBLOB NOT NULL, published TINYINT NOT NULL DEFAULT 0,
        modified DATETIME(6) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
