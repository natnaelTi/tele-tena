"""Make each immutable vetting decision eligible for one reconsideration."""
import frappe


def execute():
    # The appeal DocType is synced before post-model patches run. A unique
    # decision reference prevents racing duplicate submissions and preserves
    # one clear review history per decision.
    if frappe.db.table_exists('Tele Tena Vetting Appeal'):
        frappe.db.add_unique('Tele Tena Vetting Appeal', ['basis_assessment'],
                             'uniq_vetting_appeal_basis')
