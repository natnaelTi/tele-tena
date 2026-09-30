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
        self.reviewed_by = frappe.session.user
        self.reviewed_at = now_datetime()

    def on_update(self):
        from tele_tena.api.journey import audit
        audit(self.clinician, 'ServiceScope', {'service': self.service, 'status': self.status})

    def on_trash(self):
        frappe.throw('Revoke service scopes instead of deleting records', frappe.PermissionError)
