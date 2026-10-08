"""Add per-appointment acquisition attribution without inferring history."""
import frappe


def execute():
    if not frappe.db.sql("SHOW COLUMNS FROM tt_appointment LIKE 'acquisition_source'"):
        # Existing bookings receive only the explicit Unknown value. Historical
        # sources are not inferred from referrers, emails or profile state.
        frappe.db.sql_ddl("""ALTER TABLE tt_appointment ADD COLUMN acquisition_source
            varchar(32) NOT NULL DEFAULT 'unknown' AFTER price""")
