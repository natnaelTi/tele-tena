import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class TeleTenaClinic(Document):
    def validate(self):
        user = frappe.session.user
        roles = set(frappe.get_roles(user))
        reviewer = user == 'Administrator' or 'Tele Tena Approver' in roles
        if reviewer:
            if not getattr(frappe.local, 'tele_tena_clinic_review', False):
                frappe.throw('Use the audited clinic review action.', frappe.PermissionError)
            return
        if self.submitted_by != user or not roles.intersection({'Tele Tena Clinician', 'Tele Tena Applicant'}):
            frappe.throw('You may submit only your own clinic application.', frappe.PermissionError)
        old = self.get_doc_before_save()
        if old and old.submitted_by != user:
            frappe.throw('Clinic application owner cannot change.', frappe.PermissionError)
        if old and old.status != 'Draft':
            frappe.throw('Submitted clinic details are locked pending reviewer action.', frappe.PermissionError)
        if self.status not in ('Draft', 'Submitted'):
            frappe.throw('Only a reviewer may decide clinic verification.', frappe.PermissionError)
        if self.reviewed_by or self.reviewed_at or self.decision_reason:
            frappe.throw('Reviewer decision fields are protected.', frappe.PermissionError)
        if self.status == 'Submitted':
            if not all((self.clinic_name, self.legal_name, self.registration_reference, self.jurisdiction)):
                frappe.throw('Complete the clinic identity, registration reference and jurisdiction before submission.')
            # Serialize all create paths, including generic DocType API calls,
            # and prevent bypassing the command API's duplicate checks.
            frappe.db.sql('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
            existing = frappe.db.sql('''SELECT name,submitted_by,status FROM `tabTele Tena Clinic`
                WHERE registration_reference=%s AND jurisdiction=%s AND name!=%s FOR UPDATE''',
                (self.registration_reference, self.jurisdiction, self.name or ''), as_dict=True)
            for prior in existing:
                if prior.status in ('Submitted', 'Verified', 'Suspended'):
                    frappe.throw('A clinic application already uses this registration reference in this jurisdiction.')
                if prior.status == 'Rejected' and prior.submitted_by != user:
                    frappe.throw('Only the original applicant may resubmit a rejected registration.')
            if any(prior.status == 'Rejected' for prior in existing) and not self.previous_application:
                frappe.throw('A rejected registration must be resubmitted with its application history link.')
            if self.previous_application:
                prior = frappe.db.get_value('Tele Tena Clinic', self.previous_application,
                    ['submitted_by', 'status', 'registration_reference', 'jurisdiction'], as_dict=True)
                if (not prior or prior.submitted_by != user or prior.status != 'Rejected'
                        or prior.registration_reference != self.registration_reference
                        or prior.jurisdiction != self.jurisdiction):
                    frappe.throw('The previous application link must refer to your rejected registration.')
            self.submitted_at = self.submitted_at or now_datetime()

    def on_trash(self):
        frappe.throw('Clinic applications are retained as an audit record.', frappe.PermissionError)


def get_permission_query_conditions(user=None):
    user = user or frappe.session.user
    if user == 'Administrator' or 'Tele Tena Approver' in frappe.get_roles(user):
        return ''
    if set(frappe.get_roles(user)).intersection({'Tele Tena Clinician', 'Tele Tena Applicant'}):
        return f"`tabTele Tena Clinic`.submitted_by={frappe.db.escape(user)}"
    return '1=0'


def has_document_permission(doc, ptype=None, user=None, debug=False):
    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))
    return bool(user == 'Administrator' or 'Tele Tena Approver' in roles
                or (ptype in ('read', 'create', 'write') and doc.submitted_by == user
                    and roles.intersection({'Tele Tena Clinician', 'Tele Tena Applicant'})))
