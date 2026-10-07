import re
import frappe
from frappe.model.document import Document
from tele_tena.backoffice import approver


class TeleTenaService(Document):
    def validate(self):
        approver()
        if not isinstance(self.service_key, str) or not re.fullmatch(r'[a-z0-9-]{1,80}', self.service_key):
            frappe.throw('Invalid service identifier')
        if not self.service_label or len(self.service_label.strip()) > 120:
            frappe.throw('Invalid service label')
        self.service_label = self.service_label.strip()
        if self.catalog_status not in ('Draft', 'Active', 'Legacy test', 'Retired'):
            frappe.throw('Invalid catalog lifecycle status')
        if self.catalog_status == 'Active':
            if self.clinical_review_status != 'Approved' or not self.category:
                frappe.throw('Clinical terminology review and a service category are required before activation')
            if self.participant_structure and self.participant_structure != 'individual' and self.active:
                frappe.throw('Couple, family and group services are not bookable in this pilot')
        if self.vetting_required and self.catalog_status == 'Legacy test':
            frappe.throw('New vetting-required services cannot use the legacy test catalog state')
        previous = self.get_doc_before_save()
        immediate_changed = (bool(self.immediate_care_enabled) != bool(
            previous.immediate_care_enabled if previous else 0))
        if immediate_changed and not getattr(frappe.local, 'tele_tena_service_policy_action', False):
            frappe.throw('Immediate request policy must be changed through the reviewed policy workflow',
                         frappe.PermissionError)
        if previous and previous.service_key != self.service_key:
            frappe.throw('Service identifier is immutable')

    def on_trash(self):
        frappe.throw('Deactivate services instead of deleting records', frappe.PermissionError)
