"""Owner-approved default for newly assigned reviewers; never inferred from client intent."""
import frappe

def set_defaults(doc,method=None):
    roles={r.role for r in doc.roles}
    if 'Tele Tena Approver' not in roles or 'Tele Tena Financial Configuration' in roles:return
    previous=doc.get_doc_before_save()
    if previous and any(r.role=='Tele Tena Approver' for r in previous.roles):return
    # Only an authorized system administrator can create this assignment.
    if frappe.session.user!='Administrator' and 'System Manager' not in frappe.get_roles():return
    doc.append('roles',{'role':'Tele Tena Financial Configuration'})
