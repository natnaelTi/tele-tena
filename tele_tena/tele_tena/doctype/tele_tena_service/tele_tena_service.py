from tele_tena.localization import localized_throw
import re
import frappe
from frappe.model.document import Document
from tele_tena.backoffice import approver


class TeleTenaService(Document):
    def validate(self):
        approver()
        if not isinstance(self.service_key, str) or not re.fullmatch(r'[a-z0-9-]{1,80}', self.service_key):
            localized_throw('Invalid service identifier')
        if not self.service_label or len(self.service_label.strip()) > 120:
            localized_throw('Invalid service label')
        self.service_label = self.service_label.strip()
        if self.catalog_status not in ('Draft', 'Active', 'Legacy test', 'Retired'):
            localized_throw('Invalid catalog lifecycle status')
        if self.catalog_status == 'Active':
            if self.clinical_review_status != 'Approved' or not self.category:
                localized_throw('Clinical terminology review and a service category are required before activation')
            if self.participant_structure and self.participant_structure not in ('individual','couple') and self.active:
                localized_throw('Family and group services are not bookable in this pilot')
        if self.vetting_required and self.catalog_status == 'Legacy test':
            localized_throw('New vetting-required services cannot use the legacy test catalog state')
        previous = self.get_doc_before_save()
        reviewed_transition = (self.clinical_review_status == 'Approved' and
            (not previous or previous.clinical_review_status != 'Approved'))
        if reviewed_transition and not getattr(frappe.local, 'tele_tena_catalog_review_action', False):
            localized_throw('Clinical approval must use the audited medical-lead review action',
                         frappe.PermissionError)
        if previous and previous.clinical_review_status == 'Approved':
            from tele_tena.api.service_catalog import SERVICE_FIELDS
            mutable = {'active', 'catalog_status', 'immediate_care_enabled'}
            if any(self.get(key) != previous.get(key) for key in SERVICE_FIELDS if key not in mutable):
                localized_throw('Reviewed definitions are versioned; create a new draft instead of changing accepted requirements',
                             frappe.PermissionError)
        immediate_changed = (bool(self.immediate_care_enabled) != bool(
            previous.immediate_care_enabled if previous else 0))
        if immediate_changed and not getattr(frappe.local, 'tele_tena_service_policy_action', False):
            localized_throw('Immediate request policy must be changed through the reviewed policy workflow',
                         frappe.PermissionError)
        if previous and previous.service_key != self.service_key:
            localized_throw('Service identifier is immutable')

    def on_trash(self):
        localized_throw('Deactivate services instead of deleting records', frappe.PermissionError)
