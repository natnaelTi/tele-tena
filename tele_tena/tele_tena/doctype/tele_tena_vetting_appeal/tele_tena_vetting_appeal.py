import frappe
from frappe.model.document import Document


class TeleTenaVettingAppeal(Document):
    def validate(self):
        if not getattr(frappe.local, 'tele_tena_vetting_appeal_action', False):
            frappe.throw('Use the audited appeal workflow; appeal records are immutable.',
                         frappe.PermissionError)
        if not self.is_new():
            frappe.throw('Vetting appeal history is immutable.', frappe.PermissionError)

    def on_trash(self):
        frappe.throw('Vetting appeals are retained as an audit trail.', frappe.PermissionError)


def get_permission_query_conditions(user=None):
    user = user or frappe.session.user
    if user == 'Administrator' or 'Tele Tena Approver' in frappe.get_roles(user):
        return ''
    if not ({'Tele Tena Clinician', 'Tele Tena Applicant'} & set(frappe.get_roles(user))):
        return '1=0'
    return f"`tabTele Tena Vetting Appeal`.clinician={frappe.db.escape(user)}"


def has_document_permission(doc, ptype=None, user=None, debug=False):
    user = user or frappe.session.user
    if ptype == 'read':
        if user == 'Administrator' or 'Tele Tena Approver' in frappe.get_roles(user):
            return True
        return doc.clinician == user and bool(
            {'Tele Tena Clinician', 'Tele Tena Applicant'} & set(frappe.get_roles(user)))
    return (ptype in ('read', 'create') and doc.clinician == user and
        bool({'Tele Tena Clinician', 'Tele Tena Applicant'} & set(frappe.get_roles(user))))
