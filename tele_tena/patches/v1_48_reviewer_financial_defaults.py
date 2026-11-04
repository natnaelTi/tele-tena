"""Explicit28October owner decision: existing/new reviewers get financial configuration by default."""
import frappe

def execute():
    from tele_tena.api.journey import audit
    for row in frappe.db.sql("SELECT DISTINCT parent FROM `tabHas Role` WHERE role='Tele Tena Approver' ORDER BY parent",as_dict=True):
        doc=frappe.get_doc('User',row.parent)
        if any(r.role=='Tele Tena Financial Configuration' for r in doc.roles):continue
        doc.add_roles('Tele Tena Financial Configuration')
        audit(row.parent,'ReviewerFinancialDefaultGranted',{'role':'Tele Tena Financial Configuration','policy':'reviewer-default-2026-10-28','source':'v1.48 owner-approved default'})
