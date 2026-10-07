import frappe
from frappe.model.document import Document


class TeleTenaScopeAppointmentReview(Document):
    def validate(self):
        if not getattr(frappe.local, 'tele_tena_scope_appointment_review_action', False):
            frappe.throw('Use the authorized scope review workflow.', frappe.PermissionError)
        if not self.is_new():
            frappe.throw('Scope appointment review history is immutable.', frappe.PermissionError)

    def on_trash(self):
        frappe.throw('Scope appointment review records are retained.', frappe.PermissionError)


def get_permission_query_conditions(user=None):
    user = user or frappe.session.user
    if user == 'Administrator' or 'Tele Tena Approver' in frappe.get_roles(user):
        return ''
    return '1=0'


def has_document_permission(doc, ptype=None, user=None, debug=False):
    user = user or frappe.session.user
    if ptype == 'create' and getattr(frappe.local, 'tele_tena_scope_appointment_review_action', False):
        return user == 'Administrator' or 'Tele Tena Approver' in frappe.get_roles(user)
    return ptype == 'read' and (user == 'Administrator' or
        'Tele Tena Approver' in frappe.get_roles(user))
