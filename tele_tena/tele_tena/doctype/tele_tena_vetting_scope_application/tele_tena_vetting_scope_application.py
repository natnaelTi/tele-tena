import frappe
from frappe.model.document import Document


class TeleTenaVettingScopeApplication(Document):
    def has_permission(self, user=None, ptype=None):
        user = user or frappe.session.user
        if user == 'Administrator' or 'Tele Tena Approver' in frappe.get_roles(user):
            return True
        return ptype in ('read', 'write') and self.clinician == user and bool(
            {'Tele Tena Clinician', 'Tele Tena Applicant'} & set(frappe.get_roles(user)))

    def validate(self):
        user = frappe.session.user
        roles = set(frappe.get_roles(user))
        if 'Tele Tena Approver' in roles or user == 'Administrator':
            if not getattr(frappe.local, 'tele_tena_vetting_decision', False):
                frappe.throw('Use the audited scope-review action to change review state', frappe.PermissionError)
            return
        if self.clinician != user or not roles.intersection({'Tele Tena Clinician', 'Tele Tena Applicant'}):
            frappe.throw('You may edit only your own scope application', frappe.PermissionError)
        previous = self.get_doc_before_save()
        if self.reverification_of and not getattr(frappe.local, 'tele_tena_reverification_action', False):
            frappe.throw('Use the audited credential re-verification action.', frappe.PermissionError)
        if previous and (self.reverification_of != previous.reverification_of or
                         self.reverification_payload_hash != previous.reverification_payload_hash):
            frappe.throw('Credential re-verification references are immutable.', frappe.PermissionError)
        allowed = {'Draft', 'Clarification', 'Submitted', 'Resubmitted'}
        if self.status not in allowed:
            frappe.throw('Applicants cannot set a vetting decision', frappe.PermissionError)
        if previous:
            if previous.status not in ('Draft', 'Clarification'):
                frappe.throw('This application is awaiting reviewer action', frappe.PermissionError)
            if previous.clinician != self.clinician or previous.service != self.service:
                frappe.throw('Application identity cannot change', frappe.PermissionError)
        if self.reviewer or self.decision_reason or self.restrictions or self.decided_by or self.decided_at:
            frappe.throw('Only an authorized reviewer may record decisions', frappe.PermissionError)
        service = frappe.db.get_value('Tele Tena Service', self.service,
                                      ['active', 'catalog_status', 'vetting_required'], as_dict=True)
        if not service or not service.active or service.catalog_status != 'Active' or not service.vetting_required:
            frappe.throw('This service is not open for a structured scope application')
        if self.status in ('Submitted', 'Resubmitted'):
            missing = not (self.professional_category and self.qualification and self.issuing_institution
                           and self.population_adults)
            # The evidence uses private app-owned storage rather than a public File.
            has_resume = bool(frappe.db.sql('SELECT clinician FROM tt_resume_evidence WHERE clinician=%s',
                                           (self.clinician,)))
            if missing or not has_resume:
                frappe.throw('Required profile details and a private CV must be present before submission')

    def on_trash(self):
        frappe.throw('Vetting applications are retained as an audit record', frappe.PermissionError)


def get_permission_query_conditions(user=None):
    user = user or frappe.session.user
    if user == 'Administrator' or 'Tele Tena Approver' in frappe.get_roles(user):
        return ''
    return f"`tabTele Tena Vetting Scope Application`.clinician={frappe.db.escape(user)}"


def has_document_permission(doc, ptype=None, user=None, debug=False):
    user = user or frappe.session.user
    if user == 'Administrator' or 'Tele Tena Approver' in frappe.get_roles(user):
        return True
    return ptype in ('create', 'read', 'write') and doc.clinician == user and bool(
        {'Tele Tena Clinician', 'Tele Tena Applicant'} & set(frappe.get_roles(user)))
