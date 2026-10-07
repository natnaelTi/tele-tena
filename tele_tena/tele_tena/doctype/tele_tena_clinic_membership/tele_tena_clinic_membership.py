import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class TeleTenaClinicMembership(Document):
    def validate(self):
        if not getattr(frappe.local, 'tele_tena_clinic_membership_action', False):
            frappe.throw('Use the clinic membership action.', frappe.PermissionError)

        old = self.get_doc_before_save()
        user = frappe.session.user
        if old:
            immutable = ('clinic', 'invite_email', 'membership_role', 'invited_by', 'invited_at')
            if any(old.get(field) != self.get(field) for field in immutable):
                frappe.throw('Clinic membership identity cannot be changed.', frappe.PermissionError)
            transition = (old.status, self.status)
            allowed = {
                ('Invited', 'Active'), ('Invited', 'Declined'),
                ('Invited', 'Revoked'), ('Active', 'Revoked'),
            }
            if transition not in allowed:
                frappe.throw('This clinic membership transition is not valid.', frappe.PermissionError)
            if self.status == 'Active':
                if not self.member_user or self.member_user != user or not self.accepted_at:
                    frappe.throw('The intended account must accept its own invitation.', frappe.PermissionError)
            elif self.status == 'Declined':
                if self.member_user or not getattr(frappe.local, 'tele_tena_clinic_membership_invitee', False):
                    frappe.throw('Only the invited contact may decline this invitation.', frappe.PermissionError)
            elif self.status == 'Revoked':
                if not getattr(frappe.local, 'tele_tena_clinic_membership_admin', False):
                    frappe.throw('A clinic manager must revoke this membership.', frappe.PermissionError)
        else:
            if self.status != 'Invited' or self.member_user or not self.invited_by or self.invited_by != user:
                frappe.throw('Clinic membership invitations must be created by the acting manager.', frappe.PermissionError)
            if self.membership_role not in ('Clinic Manager', 'Scheduling', 'Billing'):
                frappe.throw('Choose a supported clinic role.')
            if not self.invite_email:
                frappe.throw('An invitation email is required.')
            self.invited_at = self.invited_at or now_datetime()

    def on_trash(self):
        frappe.throw('Clinic membership history is retained for audit.', frappe.PermissionError)


def get_permission_query_conditions(user=None):
    user = user or frappe.session.user
    if user == 'Administrator':
        return ''
    escaped = frappe.db.escape(user)
    return f'''(
      `tabTele Tena Clinic Membership`.member_user={escaped}
      OR EXISTS (
        SELECT 1 FROM `tabTele Tena Clinic` clinic
        WHERE clinic.name=`tabTele Tena Clinic Membership`.clinic
          AND clinic.submitted_by={escaped}
      )
      OR EXISTS (
        SELECT 1 FROM `tabTele Tena Clinic Membership` manager
        WHERE manager.clinic=`tabTele Tena Clinic Membership`.clinic
          AND manager.member_user={escaped}
          AND manager.membership_role='Clinic Manager'
          AND manager.status='Active'
      )
    )'''


def has_document_permission(doc, ptype=None, user=None, debug=False):
    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))
    if user == 'Administrator':
        return ptype in ('read', 'create', 'write')
    if ptype == 'read':
        if doc.member_user == user:
            return True
        return clinic_admin(user, doc.clinic)
    if ptype == 'create':
        return bool(getattr(frappe.local, 'tele_tena_clinic_membership_admin', False)
                    and clinic_admin(user, doc.clinic))
    if ptype == 'write':
        if getattr(frappe.local, 'tele_tena_clinic_membership_admin', False):
            return clinic_admin(user, doc.clinic)
        if getattr(frappe.local, 'tele_tena_clinic_membership_invitee', False):
            return ((doc.status == 'Active' and doc.member_user == user)
                    or doc.status == 'Declined')
        return False
    return False


def clinic_admin(user, clinic):
    owner = frappe.db.get_value('Tele Tena Clinic', clinic, 'submitted_by')
    if owner == user:
        return True
    return bool(frappe.db.exists('Tele Tena Clinic Membership', {
        'clinic': clinic, 'member_user': user, 'membership_role': 'Clinic Manager', 'status': 'Active'
    }))
