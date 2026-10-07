import frappe
from frappe.model.document import Document


class TeleTenaClinicEncounterAccess(Document):
    def validate(self):
        action = getattr(frappe.local, 'tele_tena_clinic_access_action', None)
        if action not in ('grant', 'revoke'):
            frappe.throw('Use the patient clinic-access action.', frappe.PermissionError)
        old = self.get_doc_before_save()
        if old:
            immutable = ('clinic', 'appointment', 'patient', 'clinician', 'purpose',
                         'granted_by', 'granted_at', 'expires_at')
            if any(old.get(field) != self.get(field) for field in immutable):
                frappe.throw('A clinic-access grant cannot be rewritten.', frappe.PermissionError)
            if action != 'revoke' or old.status != 'Active' or self.status != 'Revoked':
                frappe.throw('This clinic-access transition is not allowed.', frappe.PermissionError)
            if self.revoked_by != frappe.session.user or not self.revoked_at:
                frappe.throw('The revocation must record the acting patient.', frappe.PermissionError)
        else:
            if action != 'grant' or self.status != 'Active':
                frappe.throw('Only a patient-approved scheduling grant may be created.', frappe.PermissionError)
            if self.granted_by != self.patient or self.granted_at is None or self.expires_at is None:
                frappe.throw('The patient grant is incomplete.', frappe.PermissionError)
            if self.purpose != 'Scheduling coordination':
                frappe.throw('Unsupported clinic-access purpose.')

    def on_trash(self):
        frappe.throw('Clinic-access history is retained for audit.', frappe.PermissionError)


def get_permission_query_conditions(user=None):
    # Purpose-built APIs apply the exact patient or active membership check.
    # Generic list APIs must never enumerate grants or appointment references.
    return "`tabTele Tena Clinic Encounter Access`.name IS NULL"


def has_document_permission(doc, ptype=None, user=None, debug=False):
    user = user or frappe.session.user
    action = getattr(frappe.local, 'tele_tena_clinic_access_action', None)
    if ptype == 'create':
        return action == 'grant' and doc.patient == user and doc.granted_by == user
    if ptype == 'write':
        return action == 'revoke' and doc.patient == user and doc.revoked_by == user
    return False
