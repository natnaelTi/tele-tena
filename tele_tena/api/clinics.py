"""Private clinic registration and affiliation verification workflows.

Clinic affiliation is operational evidence only. It never grants patient-record
access or establishes competence for a clinical service scope.
"""
import frappe
from frappe.utils import now_datetime

from tele_tena.api.journey import actor, command, fail, one, rows, text
from tele_tena.tele_tena.doctype.tele_tena_clinic_membership.tele_tena_clinic_membership import clinic_admin


def clinic_applicant():
    user = actor()
    if not set(frappe.get_roles(user)).intersection({'Tele Tena Clinician', 'Tele Tena Applicant'}):
        frappe.throw('Clinician application access required.', frappe.PermissionError)
    if not frappe.db.get_value('User', user, 'enabled') or not frappe.db.sql(
            'SELECT user FROM tt_profile WHERE user=%s AND kind=%s', (user, 'clinician')):
        frappe.throw('Complete the clinician profile first.', frappe.PermissionError)
    return user


@frappe.whitelist()
def my_clinic_applications():
    clinician = clinic_applicant()
    return frappe.get_list('Tele Tena Clinic',
        fields=['name', 'clinic_name', 'legal_name', 'registration_reference',
                'jurisdiction', 'public_description', 'status', 'submitted_at',
                'reviewed_at', 'decision_reason'],
        filters={'submitted_by': clinician}, order_by='modified desc', limit_page_length=50)


@command
def submit_clinic_application(clinic_name, legal_name, registration_reference,
                              jurisdiction, public_description=''):
    clinician = clinic_applicant()
    if not frappe.db.get_value('User', clinician, 'enabled'):
        frappe.throw('Account unavailable', frappe.PermissionError)
    clinic_name = text(clinic_name, 160)
    legal_name = text(legal_name, 180)
    registration_reference = text(registration_reference, 120)
    jurisdiction = text(jurisdiction, 120)
    public_description = text(public_description or '', 1000, required=False)
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    previous = rows('''SELECT name,submitted_by,clinic_name,legal_name,jurisdiction,
        public_description,status FROM `tabTele Tena Clinic`
        WHERE registration_reference=%s AND jurisdiction=%s FOR UPDATE''',
        (registration_reference, jurisdiction))
    if previous:
        matching = next((item for item in previous if item.submitted_by == clinician), None)
        if matching and matching.status == 'Submitted':
            if (matching.clinic_name, matching.legal_name, matching.jurisdiction,
                    matching.public_description) == (clinic_name, legal_name, jurisdiction,
                                                       public_description):
                return {'application': matching.name, 'status': matching.status, 'idempotent': True}
            fail('A clinic application is already awaiting review for this registration.',
                 'clinic_application_exists')
        if any(item.status in ('Submitted', 'Verified', 'Suspended') for item in previous):
            fail('A clinic application already uses this registration reference in this jurisdiction.',
                 'clinic_application_exists')
        # A rejected applicant may correct and resubmit the same registration.
        # Keep the rejected document as history and link the new submission to it.
        if not matching or matching.status != 'Rejected':
            fail('Only the same applicant may resubmit a rejected clinic registration.',
                 'clinic_application_exists')
    doc = frappe.new_doc('Tele Tena Clinic')
    doc.update({
        'clinic_name': clinic_name,
        'legal_name': legal_name,
        'registration_reference': registration_reference,
        'jurisdiction': jurisdiction,
        'public_description': public_description,
        'submitted_by': clinician,
        'status': 'Submitted',
    })
    if previous:
        doc.previous_application = matching.name
    doc.insert()
    return {'application': doc.name, 'status': doc.status}


@command
def review_clinic(application, decision, reason):
    reviewer = actor('Tele Tena Approver')
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    if decision not in ('Verified', 'Rejected', 'Suspended'):
        fail('Choose a supported clinic verification decision.')
    reason = text(reason, 1000)
    doc = frappe.get_doc('Tele Tena Clinic', application)
    if doc.status == decision and doc.reviewed_by == reviewer and doc.decision_reason == reason:
        return {'application': doc.name, 'status': doc.status, 'idempotent': True}
    allowed = ((doc.status == 'Submitted' and decision in ('Verified', 'Rejected'))
               or (doc.status == 'Verified' and decision == 'Suspended'))
    if not allowed:
        fail('This clinic verification decision is not valid from its current status.')
    if doc.submitted_by == reviewer:
        frappe.throw('A reviewer cannot decide their own clinic application.', frappe.PermissionError)
    frappe.local.tele_tena_clinic_review = True
    try:
        doc.status = decision
        doc.reviewed_by = reviewer
        doc.reviewed_at = now_datetime()
        doc.decision_reason = reason
        doc.save()
    finally:
        frappe.local.tele_tena_clinic_review = False
    from tele_tena.api.journey import audit
    audit(reviewer, 'ClinicVerification', {'clinic': doc.name, 'decision': decision})
    return {'application': doc.name, 'status': doc.status}


@frappe.whitelist()
def my_affiliations():
    clinician = clinic_applicant()
    result = frappe.get_list('Tele Tena Clinic Affiliation',
        fields=['name', 'clinic', 'professional_role', 'evidence_summary',
                'status', 'submitted_at', 'reviewed_at', 'decision_reason'],
        filters={'clinician': clinician}, order_by='modified desc', limit_page_length=50)
    for item in result:
        item.clinic_name = frappe.db.get_value('Tele Tena Clinic', item.clinic, 'clinic_name') or 'Clinic unavailable'
    return result


@frappe.whitelist()
def verified_clinics():
    clinic_applicant()
    # These are approved public organization fields only; legal and registration
    # references remain private to their applicant and authorized reviewers.
    return frappe.db.sql('''SELECT name,clinic_name,jurisdiction FROM `tabTele Tena Clinic`
        WHERE status='Verified' ORDER BY clinic_name LIMIT 200''', as_dict=True)


@command
def submit_affiliation(clinic, professional_role, evidence_summary, application=None):
    clinician = clinic_applicant()
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    if not frappe.db.get_value('User', clinician, 'enabled'):
        frappe.throw('Account unavailable', frappe.PermissionError)
    if frappe.db.get_value('Tele Tena Clinic', clinic, 'status') != 'Verified':
        fail('Choose a clinic whose registration has been verified.', 'clinic_not_verified')
    role = text(professional_role, 120)
    evidence = text(evidence_summary, 2000)
    if application:
        doc = frappe.get_doc('Tele Tena Clinic Affiliation', application)
        if doc.clinician != clinician or doc.status != 'Clarification':
            frappe.throw('This affiliation cannot be resubmitted.', frappe.PermissionError)
        if doc.clinic != clinic:
            fail('The clinic for this application cannot change.')
        # The previous reviewer decision remains in Frappe Version history and
        # the audit stream; current decision fields now describe the new review.
        doc.reviewed_by = None
        doc.reviewed_at = None
        doc.decision_reason = None
    else:
        existing = frappe.get_list('Tele Tena Clinic Affiliation',
            filters={'clinic': clinic, 'clinician': clinician,
                     'status': ['in', ['Submitted', 'Verified']]},
            fields=['name'], limit_page_length=1)
        if existing:
            doc = frappe.get_doc('Tele Tena Clinic Affiliation', existing[0].name)
            if doc.professional_role == role and doc.evidence_summary == evidence:
                return {'application': doc.name, 'status': doc.status, 'idempotent': True}
            fail('An affiliation application is already awaiting review or is verified.')
        doc = frappe.new_doc('Tele Tena Clinic Affiliation')
        doc.clinic = clinic
        doc.clinician = clinician
    doc.professional_role = role
    doc.evidence_summary = evidence
    doc.status = 'Submitted'
    doc.submitted_at = now_datetime()
    doc.insert() if doc.is_new() else doc.save()
    return {'application': doc.name, 'status': doc.status}


@command
def review_affiliation(application, decision, reason):
    reviewer = actor('Tele Tena Approver')
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    if decision not in ('Verified', 'Clarification', 'Rejected', 'Revoked'):
        fail('Choose a supported affiliation decision.')
    reason = text(reason, 1000)
    doc = frappe.get_doc('Tele Tena Clinic Affiliation', application)
    if doc.clinician == reviewer:
        frappe.throw('A reviewer cannot decide their own clinic affiliation.', frappe.PermissionError)
    if decision == 'Verified' and frappe.db.get_value('Tele Tena Clinic', doc.clinic, 'status') != 'Verified':
        fail('The associated clinic is no longer verified.')
    if decision == 'Revoked':
        if doc.status != 'Verified':
            fail('Only a verified affiliation can be revoked.')
    elif doc.status not in ('Submitted', 'Clarification'):
        fail('Only submitted affiliations can be reviewed.')
    frappe.local.tele_tena_affiliation_review = True
    try:
        doc.status = decision
        doc.reviewed_by = reviewer
        doc.reviewed_at = now_datetime()
        doc.decision_reason = reason
        doc.save()
    finally:
        frappe.local.tele_tena_affiliation_review = False
    from tele_tena.api.journey import audit
    audit(reviewer, 'ClinicAffiliationReview',
          {'affiliation': doc.name, 'decision': decision})
    return {'application': doc.name, 'status': doc.status}


@frappe.whitelist()
def review_queue():
    actor('Tele Tena Approver')
    clinics = frappe.get_list('Tele Tena Clinic',
        fields=['name', 'clinic_name', 'legal_name', 'registration_reference',
                'jurisdiction', 'status', 'submitted_by', 'submitted_at'],
        filters={'status': ['in', ['Submitted', 'Verified']]},
        order_by='status asc,submitted_at asc', limit_page_length=100)
    affiliations = frappe.get_list('Tele Tena Clinic Affiliation',
        fields=['name', 'clinic', 'clinician', 'professional_role',
                'evidence_summary', 'status', 'submitted_at'],
        filters={'status': ['in', ['Submitted', 'Clarification', 'Verified']]},
        order_by='status asc,submitted_at asc', limit_page_length=100)
    for item in affiliations:
        name = frappe.db.sql('SELECT display_name FROM tt_profile WHERE user=%s',
                             (item.clinician,), as_dict=True)
        item.clinician_display_name = name[0].display_name if name else 'Clinician profile unavailable'
        item.clinic_name = frappe.db.get_value('Tele Tena Clinic', item.clinic, 'clinic_name') or 'Clinic unavailable'
    return {'clinics': clinics, 'affiliations': affiliations}


def _clinic_manager(user, clinic):
    return clinic_admin(user, clinic)


@frappe.whitelist()
def managed_clinics():
    user = actor()
    return frappe.db.sql('''SELECT DISTINCT c.name,c.clinic_name,c.jurisdiction,c.status
        FROM `tabTele Tena Clinic` c
        LEFT JOIN `tabTele Tena Clinic Membership` m
          ON m.clinic=c.name AND m.member_user=%s
          AND m.membership_role='Clinic Manager' AND m.status='Active'
        WHERE c.submitted_by=%s OR m.name IS NOT NULL
        ORDER BY c.clinic_name LIMIT 100''', (user, user), as_dict=True)


@command
def clinic_team(clinic):
    user = actor()
    if not _clinic_manager(user, clinic):
        frappe.throw('Clinic manager access required.', frappe.PermissionError)
    if not frappe.db.exists('Tele Tena Clinic', clinic):
        frappe.throw('Clinic unavailable.', frappe.PermissionError)
    return frappe.get_list('Tele Tena Clinic Membership',
        fields=['name', 'invite_email', 'membership_role', 'status',
                'invited_at', 'accepted_at', 'revoked_at', 'revocation_reason'],
        filters={'clinic': clinic}, order_by='invited_at desc', limit_page_length=100)


@command
def invite_clinic_member(clinic, invite_email, membership_role):
    user = actor()
    if not _clinic_manager(user, clinic):
        frappe.throw('Clinic manager access required.', frappe.PermissionError)
    if frappe.db.get_value('Tele Tena Clinic', clinic, 'status') != 'Verified':
        fail('Only a verified clinic may invite team members.', 'clinic_unavailable')
    if membership_role not in ('Clinic Manager', 'Scheduling', 'Billing', 'Care Coordination'):
        fail('Choose a supported clinic role.', 'invalid_membership_role')
    from tele_tena.api.contact_auth import normalize
    invite_email = normalize('email', invite_email)
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    existing = rows('''SELECT name,status,membership_role,invited_by FROM `tabTele Tena Clinic Membership`
        WHERE clinic=%s AND invite_email=%s AND status IN ('Invited','Active') FOR UPDATE''',
        (clinic, invite_email))
    if existing:
        if existing[0].membership_role == membership_role and existing[0].invited_by == user:
            return {'membership': existing[0].name, 'status': existing[0].status,
                    'idempotent': True}
        fail('An invitation or active membership already exists for this contact.',
             'membership_exists')
    doc = frappe.new_doc('Tele Tena Clinic Membership')
    doc.clinic = clinic
    doc.invite_email = invite_email
    doc.membership_role = membership_role
    doc.invited_by = user
    doc.status = 'Invited'
    frappe.local.tele_tena_clinic_membership_action = True
    frappe.local.tele_tena_clinic_membership_admin = True
    try:
        doc.insert()
    finally:
        frappe.local.tele_tena_clinic_membership_action = False
        frappe.local.tele_tena_clinic_membership_admin = False
    from tele_tena.api.journey import audit
    audit(user, 'ClinicMemberInvited', {'clinic': clinic, 'membership': doc.name,
                                        'role': membership_role})
    return {'membership': doc.name, 'status': doc.status}


@frappe.whitelist()
def my_clinic_memberships():
    user = actor()
    email_rows = frappe.db.sql('''SELECT contact FROM tt_contact_identity
        WHERE user=%s AND channel='email' ORDER BY verified_at DESC LIMIT 5''', (user,))
    emails = [row[0] for row in email_rows]
    invitations = []
    if emails:
        placeholders = ','.join(['%s'] * len(emails))
        invitations = frappe.db.sql(f'''SELECT m.name,m.clinic,m.membership_role,m.invited_at,
                c.clinic_name,c.jurisdiction
            FROM `tabTele Tena Clinic Membership` m
            JOIN `tabTele Tena Clinic` c ON c.name=m.clinic
            WHERE m.invite_email IN ({placeholders}) AND m.status='Invited'
              AND c.status='Verified'
            ORDER BY m.invited_at DESC LIMIT 50''', tuple(emails), as_dict=True)
    memberships = frappe.db.sql('''SELECT m.name,m.clinic,m.membership_role,m.status,
            m.invited_at,m.accepted_at,c.clinic_name,c.jurisdiction,c.status AS clinic_status
        FROM `tabTele Tena Clinic Membership` m
        JOIN `tabTele Tena Clinic` c ON c.name=m.clinic
        WHERE m.member_user=%s AND m.status IN ('Active','Revoked')
        ORDER BY m.invited_at DESC LIMIT 100''', (user,), as_dict=True)
    return {'invitations': invitations, 'memberships': memberships}


def _invitation_for_verified_contact(invitation, user):
    contacts = frappe.db.sql('''SELECT contact FROM tt_contact_identity
        WHERE user=%s AND channel='email' ''', (user,), pluck=True)
    if not contacts or invitation.invite_email not in contacts:
        frappe.throw('This invitation is unavailable for the signed-in account.',
                     frappe.PermissionError)


@command
def respond_to_clinic_invitation(membership, decision):
    user = actor()
    if decision not in ('accept', 'decline'):
        fail('Choose accept or decline.')
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    try:
        doc = frappe.get_doc('Tele Tena Clinic Membership', membership)
    except frappe.DoesNotExistError:
        frappe.throw('Invitation unavailable.', frappe.PermissionError)
    _invitation_for_verified_contact(doc, user)
    if doc.status == 'Active' and doc.member_user == user and decision == 'accept':
        return {'membership': doc.name, 'status': doc.status, 'idempotent': True}
    if doc.status == 'Declined' and decision == 'decline':
        return {'membership': doc.name, 'status': doc.status, 'idempotent': True}
    if doc.status != 'Invited':
        fail('This invitation is no longer active.', 'invitation_closed')
    if decision == 'accept' and frappe.db.get_value('Tele Tena Clinic', doc.clinic, 'status') != 'Verified':
        fail('This clinic is no longer verified.', 'clinic_unavailable')
    doc.status = 'Active' if decision == 'accept' else 'Declined'
    if decision == 'accept':
        doc.member_user = user
        doc.accepted_at = now_datetime()
    frappe.local.tele_tena_clinic_membership_action = True
    frappe.local.tele_tena_clinic_membership_invitee = True
    try:
        doc.save()
    finally:
        frappe.local.tele_tena_clinic_membership_action = False
        frappe.local.tele_tena_clinic_membership_invitee = False
    from tele_tena.api.journey import audit
    audit(user, 'ClinicInvitation' + ('Accepted' if decision == 'accept' else 'Declined'),
          {'clinic': doc.clinic, 'membership': doc.name})
    return {'membership': doc.name, 'status': doc.status}


@command
def revoke_clinic_membership(membership, reason):
    user = actor()
    reason = text(reason, 1000)
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    try:
        doc = frappe.get_doc('Tele Tena Clinic Membership', membership)
    except frappe.DoesNotExistError:
        frappe.throw('Membership unavailable.', frappe.PermissionError)
    if not _clinic_manager(user, doc.clinic):
        frappe.throw('Clinic manager access required.', frappe.PermissionError)
    if (doc.status == 'Revoked' and doc.revoked_by == user
            and doc.revocation_reason == reason):
        return {'membership': doc.name, 'status': doc.status, 'idempotent': True}
    if doc.status not in ('Invited', 'Active'):
        fail('Only an active membership or invitation may be revoked.')
    doc.status = 'Revoked'
    doc.revoked_by = user
    doc.revoked_at = now_datetime()
    doc.revocation_reason = reason
    frappe.local.tele_tena_clinic_membership_action = True
    frappe.local.tele_tena_clinic_membership_admin = True
    try:
        doc.save()
    finally:
        frappe.local.tele_tena_clinic_membership_action = False
        frappe.local.tele_tena_clinic_membership_admin = False
    from tele_tena.api.journey import audit
    audit(user, 'ClinicMembershipRevoked', {'clinic': doc.clinic,
                                             'membership': doc.name})
    return {'membership': doc.name, 'status': doc.status}
