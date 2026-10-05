import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime
from tele_tena.backoffice import approver, scope_name


class TeleTenaServiceScope(Document):
    def autoname(self):
        self.name = scope_name(self.clinician, self.service)

    def validate(self):
        approver()
        if self.clinician == frappe.session.user:
            frappe.throw('Self approval is prohibited', frappe.PermissionError)
        previous = self.get_doc_before_save()
        if previous and (previous.clinician != self.clinician or previous.service != self.service):
            frappe.throw('Scope identity is immutable')
        if self.name != scope_name(self.clinician, self.service):
            frappe.throw('Invalid scope identity')
        if self.status not in ('Approved', 'Revoked'):
            frappe.throw('Invalid scope status')
        # Same lock order as offering publication and new booking. Generic writes
        # cannot race past approval revocation or approve an ineligible clinician.
        from tele_tena.api.journey import one, approved
        one('SELECT user FROM tt_profile WHERE user=%s AND kind=%s FOR UPDATE', (self.clinician, 'clinician'))
        if self.status == 'Approved':
            approved(self.clinician, True)
            if not frappe.db.get_value('Tele Tena Service', self.service, 'active'):
                frappe.throw('Service is inactive')
            definition = frappe.db.get_value('Tele Tena Service', self.service,
                ['vetting_required', 'catalog_status', 'clinical_review_status'], as_dict=True)
            if definition.vetting_required:
                if not getattr(frappe.local, 'tele_tena_vetting_decision', False):
                    frappe.throw('This scope must be approved through its structured assessment', frappe.PermissionError)
                vetted = frappe.db.sql("""SELECT a.name FROM `tabTele Tena Vetting Scope Application` a
                    JOIN `tabTele Tena Vetting Assessment` v ON v.scope_application=a.name
                    WHERE a.clinician=%s AND a.service=%s AND a.status='Approved' AND v.decision='Approved'
                    ORDER BY v.creation DESC LIMIT 1""", (self.clinician, self.service))
                if definition.catalog_status != 'Active' or definition.clinical_review_status != 'Approved' or not vetted:
                    frappe.throw('Required clinical catalog and individual scope review is incomplete')
        self.reviewed_by = frappe.session.user
        self.reviewed_at = now_datetime()

    def on_update(self):
        from tele_tena.api.journey import audit
        audit(self.clinician, 'ServiceScope', {'service': self.service, 'status': self.status})

    def on_trash(self):
        frappe.throw('Revoke service scopes instead of deleting records', frappe.PermissionError)
