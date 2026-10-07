import frappe
from frappe.model.document import Document


class TeleTenaScopeEvidence(Document):
    def validate(self):
        if not getattr(frappe.local, 'tele_tena_scope_evidence_action', False):
            frappe.throw('Use the private service-evidence upload action.', frappe.PermissionError)
        if not self.is_new():
            frappe.throw('Scope evidence revisions are immutable.', frappe.PermissionError)
        user = frappe.session.user
        if self.clinician != user or not {'Tele Tena Applicant', 'Tele Tena Clinician'} & set(frappe.get_roles(user)):
            frappe.throw('You may upload evidence only to your own application.', frappe.PermissionError)
        applications = frappe.db.sql('''SELECT status FROM `tabTele Tena Vetting Scope Application`
            WHERE name=%s AND clinician=%s''', (self.scope_application, user), as_dict=True)
        if not applications or applications[0].status not in ('Draft', 'Clarification'):
            frappe.throw('Evidence can be added only to your draft or clarification application.', frappe.PermissionError)

    def on_update_after_submit(self):
        frappe.throw('Scope evidence revisions are immutable.', frappe.PermissionError)

    def on_trash(self):
        frappe.throw('Scope evidence is retained as a review-history record.', frappe.PermissionError)


def get_permission_query_conditions(user=None):
    user = user or frappe.session.user
    if user == 'Administrator' or 'Tele Tena Approver' in frappe.get_roles(user):
        return ''
    if not {'Tele Tena Applicant', 'Tele Tena Clinician'} & set(frappe.get_roles(user)):
        return '1=0'
    return f"`tabTele Tena Scope Evidence`.clinician={frappe.db.escape(user)}"


def has_document_permission(doc, ptype=None, user=None, debug=False):
    user = user or frappe.session.user
    if user == 'Administrator' or 'Tele Tena Approver' in frappe.get_roles(user):
        return ptype == 'read'
    return (ptype in ('read', 'create') and doc.clinician == user and
            bool({'Tele Tena Applicant', 'Tele Tena Clinician'} & set(frappe.get_roles(user))))
