from tele_tena.localization import localized_throw
import frappe
from frappe.model.document import Document

class TeleTenaVettingAssessment(Document):
    def validate(self):
        if frappe.session.user != 'Administrator' and 'Tele Tena Approver' not in frappe.get_roles():
            localized_throw('Approver required', frappe.PermissionError)
        if not self.is_new():
            localized_throw('Vetting assessment history is immutable', frappe.PermissionError)

    def on_update_after_submit(self):
        localized_throw('Vetting assessment history is immutable', frappe.PermissionError)

    def on_trash(self):
        localized_throw('Vetting assessment history is retained', frappe.PermissionError)
import frappe
from frappe.model.document import Document


class TeleTenaVettingAssessment(Document):
    def validate(self):
        if not getattr(frappe.local, 'tele_tena_vetting_assessment_action', False):
            localized_throw('Assessments are append-only; use the audited vetting decision action.',
                         frappe.PermissionError)
        if not self.is_new():
            localized_throw('Vetting assessments cannot be edited.', frappe.PermissionError)
        if 'Tele Tena Approver' not in frappe.get_roles(frappe.session.user):
            localized_throw('Reviewer access required.', frappe.PermissionError)

    def on_trash(self):
        localized_throw('Vetting assessments are retained as an audit trail.', frappe.PermissionError)
