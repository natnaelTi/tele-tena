"""Allow a new review episode after a distinct scope re-verification decision."""
import frappe


def execute():
    doctype = 'Tele Tena Scope Appointment Review'
    if not frappe.db.table_exists(doctype):
        return
    table = 'tab' + doctype
    # v1.20 briefly used a single-column unique key in local preview. Remove
    # only such a unique index; preserve all review records and other indexes.
    indexes = frappe.db.sql('''SELECT INDEX_NAME,COUNT(*) AS column_count,
            MAX(COLUMN_NAME='appointment') AS has_appointment,
            MAX(COLUMN_NAME='eligibility_event') AS has_event
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s AND NON_UNIQUE=0
          AND INDEX_NAME<>'PRIMARY'
        GROUP BY INDEX_NAME''', (table,), as_dict=True)
    for index in indexes:
        if index.has_appointment and index.column_count == 1:
            name = str(index.index_name).replace('`', '``')
            frappe.db.sql_ddl(f'ALTER TABLE `{table}` DROP INDEX `{name}`')
    if not any(x.has_appointment and x.has_event and x.column_count == 2 for x in indexes):
        frappe.db.add_unique(doctype, ['appointment', 'eligibility_event'],
                             'uniq_scope_appointment_review')
