"""Owner-requested photo preference default; never modifies encounter consent/history."""
import frappe

def execute():
    if not frappe.db.sql("SHOW TABLES LIKE 'tt_patient_photo_preference'"):
        frappe.db.sql('''CREATE TABLE IF NOT EXISTS tt_patient_photo_preference (
        user VARCHAR(140) PRIMARY KEY, share_photo TINYINT NOT NULL DEFAULT 1,
        modified DATETIME(6) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
    # INSERT IGNORE preserves every explicit opt-out. No earlier photo-sharing
    # preference existed; name/history flags are distinct and must not be reused.
    frappe.db.sql('''INSERT IGNORE INTO tt_patient_photo_preference (user,share_photo,modified)
        SELECT user,1,UTC_TIMESTAMP(6) FROM tt_profile WHERE kind='patient' ''')
