import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class TeleTenaClinicAffiliation(Document):
    def validate(self):
        user = frappe.session.user
        reviewer = user == 'Administrator' or 'Tele Tena Approver' in frappe.get_roles(user)
        if reviewer:
            if not getattr(frappe.local, 'tele_tena_affiliation_review', False):
                frappe.throw('Use the audited affiliation review action.', frappe.PermissionError)
            return
        if self.clinician != user or not set(frappe.get_roles(user)).intersection({'Tele Tena Clinician', 'Tele Tena Applicant'}):
            frappe.throw('You may submit only your own clinician affiliation.', frappe.PermissionError)
        old = self.get_doc_before_save()
        if old:
            if old.clinician != self.clinician or old.clinic != self.clinic:
                frappe.throw('Affiliation identity cannot change.', frappe.PermissionError)
            if old.status not in ('Draft', 'Clarification'):
                frappe.throw('This affiliation is awaiting reviewer action.', frappe.PermissionError)
        if self.status not in ('Draft', 'Submitted'):
            frappe.throw('Only a reviewer may decide affiliation verification.', frappe.PermissionError)
        if self.reviewed_by or self.reviewed_at or self.decision_reason:
            frappe.throw('Reviewer decision fields are protected.', frappe.PermissionError)
        if self.status == 'Submitted':
            if frappe.db.get_value('Tele Tena Clinic', self.clinic, 'status') != 'Verified':
                frappe.throw('The clinic must be verified before affiliation review can begin.')
            if not (self.professional_role and self.evidence_summary):
                frappe.throw('Add your role and supporting information before submission.')
            self.submitted_at = self.submitted_at or now_datetime()

    def on_trash(self):
        frappe.throw('Affiliation decisions are retained as an audit record.', frappe.PermissionError)


def get_permission_query_conditions(user=None):
    user = user or frappe.session.user
    if user == 'Administrator' or 'Tele Tena Approver' in frappe.get_roles(user):
        return ''
    if set(frappe.get_roles(user)).intersection({'Tele Tena Clinician', 'Tele Tena Applicant'}):
        return f"`tabTele Tena Clinic Affiliation`.clinician={frappe.db.escape(user)}"
    return '1=0'


def has_document_permission(doc, ptype=None, user=None, debug=False):
    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))
    return bool(user == 'Administrator' or 'Tele Tena Approver' in roles
                or (ptype in ('read', 'create', 'write') and doc.clinician == user
                    and roles.intersection({'Tele Tena Clinician', 'Tele Tena Applicant'})))
