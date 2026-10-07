"""Create private revision storage for per-service vetting evidence."""
import frappe


def execute():
    # Metadata is a native, permission-checked DocType. Binary content stays in
    # an app-owned table with no generic File URL or exposed DocType API.
    frappe.db.sql("""CREATE TABLE IF NOT EXISTS tt_scope_evidence_content (
        evidence VARCHAR(140) PRIMARY KEY,
        content LONGBLOB NOT NULL,
        CONSTRAINT fk_tt_scope_evidence_content FOREIGN KEY (evidence)
          REFERENCES `tabTele Tena Scope Evidence` (name) ON DELETE RESTRICT
    ) ENGINE=InnoDB""")
