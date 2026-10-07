"""Ensure retry-safe triage records for each affected eligibility event."""
import frappe


def execute():
    if frappe.db.table_exists('Tele Tena Scope Appointment Review'):
        frappe.db.add_unique('Tele Tena Scope Appointment Review', ['appointment', 'eligibility_event'],
                             'uniq_scope_appointment_review')
