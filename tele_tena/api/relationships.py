"""Private patient-controlled links for future adult shared care.

An accepted link exposes only the other participant's chosen profile name. It
does not grant access to appointments, clinical records, disclosures, balances,
or consultation rooms.
"""
import hashlib
import base64
import hmac
import uuid
import frappe

from tele_tena.api.journey import actor, boolean, command, fail, one, profile, query, rows, text

CONSENT_VERSION = 'adult-shared-care-link-v1'
MAX_PENDING_INVITES_PER_DAY = 5


def _token_digest(token):
    if not isinstance(token, str) or not 32 <= len(token) <= 160:
        fail('Invitation unavailable', 'relationship_invitation_unavailable')
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def _event(subject_type, subject_id, event_type):
    frappe.db.sql('''INSERT INTO tt_relationship_event
        (id,subject_id,subject_type,actor,event_type,consent_version,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,UTC_TIMESTAMP(6))''',
        (str(uuid.uuid4()), subject_id, subject_type, actor(), event_type, CONSENT_VERSION))


def _retry_token(inviter, retry_key):
    key = frappe.conf.get('encryption_key')
    if not isinstance(key, str) or len(key) < 32:
        fail('Secure invitation links are not configured on this site.', 'relationship_unavailable')
    message = ('tele-tena-relationship-v1:' + inviter + ':' + retry_key).encode('utf-8')
    raw = hmac.new(key.encode('utf-8'), message, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')


def _invite_hours():
    try:
        value = int(frappe.conf.get('tele_tena_relationship_invite_hours', 72))
    except (TypeError, ValueError):
        value = 72
    return min(168, max(24, value))


@command
def create_relationship_invitation(adult_confirmed, retry_key):
    """Create or safely retry a manually shared invitation link."""
    inviter = actor('Tele Tena Patient')
    profile('patient', lock=True)
    if not boolean(adult_confirmed):
        fail('Confirm that you are 18 or older to invite another adult.', 'adult_required')
    key = text(retry_key, 80)
    payload_hash = hashlib.sha256(CONSENT_VERSION.encode('ascii')).hexdigest()
    token = _retry_token(inviter, key)
    digest = _token_digest(token)
    invitation_id = str(uuid.uuid4())
    frappe.db.sql('SELECT id FROM tt_relationship_gate WHERE id=1 FOR UPDATE')
    previous = rows('''SELECT id,state,expires_at,payload_hash FROM tt_relationship_invitation
        WHERE inviter=%s AND retry_key=%s FOR UPDATE''', (inviter, key))
    if previous:
        previous = previous[0]
        if previous.payload_hash != payload_hash:
            fail('This submission key was already used for different invitation details.',
                 'relationship_retry_changed')
        if previous.state != 'Pending':
            fail('This invitation is no longer active. Start a new invitation.',
                 'relationship_invitation_unavailable')
        if rows('SELECT id FROM tt_relationship_invitation WHERE id=%s AND expires_at<=UTC_TIMESTAMP(6)',
                (previous.id,)):
            fail('This invitation has expired. Start a new invitation.', 'relationship_invitation_expired')
        # HMAC-derived bearer tokens make same-key retries return the exact
        # same link without storing recoverable token material.
        invitation_id = previous.id
    else:
        rate = rows('''SELECT COUNT(*) amount FROM tt_relationship_invitation
            WHERE inviter=%s AND created_at>=DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 1 DAY)
            ''', (inviter,))[0].amount
        if int(rate) >= MAX_PENDING_INVITES_PER_DAY:
            fail('You have reached the daily limit for active invitations. Try again later.',
                 'relationship_invitation_rate_limited')
        frappe.db.sql('''INSERT INTO tt_relationship_invitation
            (id,inviter,token_digest,retry_key,payload_hash,state,consent_version,
             inviter_adult_attested_at,created_at,expires_at)
            VALUES (%s,%s,%s,%s,%s,'Pending',%s,UTC_TIMESTAMP(6),UTC_TIMESTAMP(6),
             DATE_ADD(UTC_TIMESTAMP(6),INTERVAL %s HOUR))''',
            (invitation_id, inviter, digest, key, payload_hash, CONSENT_VERSION, _invite_hours()))
        _event('Invitation', invitation_id, 'InviteCreated')
    expires = one('SELECT expires_at FROM tt_relationship_invitation WHERE id=%s',
                  (invitation_id,)).expires_at
    return {'invitation_id': invitation_id, 'token': token,
            'expires_at': expires.isoformat(timespec='seconds') + 'Z',
            'consent_version': CONSENT_VERSION, 'reissued': bool(previous)}


@query(method='POST')
def preview_relationship_invitation(token):
    """Authenticated, non-mutating preview; token is accepted only in POST body."""
    invitee = actor('Tele Tena Patient')
    profile('patient')
    digest = _token_digest(token)
    invitation = rows('''SELECT i.id,i.inviter,i.state,i.expires_at,p.display_name
        FROM tt_relationship_invitation i JOIN tt_profile p ON p.user=i.inviter AND p.kind='patient'
        WHERE i.token_digest=%s AND i.expires_at>UTC_TIMESTAMP(6)''', (digest,))
    if not invitation or invitation[0].state != 'Pending':
        fail('Invitation unavailable. It may have expired, been used, or been withdrawn.',
             'relationship_invitation_unavailable')
    item = invitation[0]
    if item.inviter == invitee:
        fail('You cannot accept your own invitation.', 'relationship_self_invite')
    return {'inviter_name': item.display_name, 'expires_at': item.expires_at.isoformat(timespec='seconds') + 'Z',
            'consent_version': CONSENT_VERSION,
            'notice': 'A relationship link shares no appointments, records, or notes.'}


@command
def respond_to_relationship_invitation(token, decision, adult_confirmed=0):
    invitee = actor('Tele Tena Patient')
    profile('patient', lock=True)
    if decision not in ('accept', 'decline'):
        fail('Choose accept or decline.', 'relationship_decision_invalid')
    if decision == 'accept' and not boolean(adult_confirmed):
        fail('Confirm that you are 18 or older to accept this invitation.', 'adult_required')
    digest = _token_digest(token)
    frappe.db.sql('SELECT id FROM tt_relationship_gate WHERE id=1 FOR UPDATE')
    invitations = rows('''SELECT id,inviter,state,expires_at,accepted_by,relationship_id,
        inviter_adult_attested_at
        FROM tt_relationship_invitation WHERE token_digest=%s FOR UPDATE''', (digest,))
    if not invitations:
        fail('Invitation unavailable. It may have expired, been used, or been withdrawn.',
             'relationship_invitation_unavailable')
    invitation = invitations[0]
    if invitation.inviter == invitee:
        fail('You cannot accept your own invitation.', 'relationship_self_invite')
    if invitation.state == 'Accepted' and invitation.accepted_by == invitee and decision == 'accept':
        return {'state': 'Active', 'relationship_id': invitation.relationship_id, 'idempotent': True}
    if invitation.state != 'Pending':
        fail('Invitation unavailable. It may have expired, been used, or been withdrawn.',
             'relationship_invitation_unavailable')
    if rows('SELECT id FROM tt_relationship_invitation WHERE id=%s AND expires_at<=UTC_TIMESTAMP(6)',
            (invitation.id,)):
        fail('This invitation has expired.', 'relationship_invitation_expired')
    if decision == 'decline':
        frappe.db.sql("UPDATE tt_relationship_invitation SET state='Declined' WHERE id=%s",
                      (invitation.id,))
        _event('Invitation', invitation.id, 'InviteDeclined')
        return {'state': 'Declined', 'idempotent': False}

    pair = sorted((invitation.inviter, invitee))
    accepted_at = rows('SELECT UTC_TIMESTAMP(6) AS accepted_at')[0].accepted_at
    consent_a_at, consent_b_at = ((invitation.inviter_adult_attested_at, accepted_at)
        if pair[0] == invitation.inviter else
        (accepted_at, invitation.inviter_adult_attested_at))
    existing = rows('''SELECT id FROM tt_relationship_link
        WHERE participant_a=%s AND participant_b=%s AND state='Active' FOR UPDATE''', tuple(pair))
    if existing:
        frappe.db.sql("UPDATE tt_relationship_invitation SET state='Superseded' WHERE id=%s",
                      (invitation.id,))
        _event('Relationship', existing[0].id, 'DuplicateSuperseded')
        return {'state': 'Active', 'relationship_id': existing[0].id, 'idempotent': True}
    relationship_id = str(uuid.uuid4())
    frappe.db.sql('''INSERT INTO tt_relationship_link
        (id,participant_a,participant_b,invitation_id,state,consent_version,
         consent_a_at,consent_b_at,created_at)
        VALUES (%s,%s,%s,%s,'Active',%s,%s,%s,UTC_TIMESTAMP(6))''',
        (relationship_id, pair[0], pair[1], invitation.id, CONSENT_VERSION, consent_a_at, consent_b_at))
    frappe.db.sql("""UPDATE tt_relationship_invitation SET state='Accepted',accepted_by=%s,
        accepted_at=UTC_TIMESTAMP(6),relationship_id=%s WHERE id=%s""",
        (invitee, relationship_id, invitation.id))
    _event('Relationship', relationship_id, 'RelationshipAccepted')
    return {'state': 'Active', 'relationship_id': relationship_id, 'idempotent': False}


@command
def revoke_relationship(relationship_id):
    participant = actor('Tele Tena Patient')
    profile('patient', lock=True)
    frappe.db.sql('SELECT id FROM tt_relationship_gate WHERE id=1 FOR UPDATE')
    link = rows('''SELECT id,state FROM tt_relationship_link
        WHERE id=%s AND %s IN (participant_a,participant_b) FOR UPDATE''', (relationship_id, participant))
    if not link:
        frappe.throw('Relationship link unavailable', frappe.PermissionError)
    if link[0].state == 'Revoked':
        return {'revoked': True, 'idempotent': True}
    frappe.db.sql("UPDATE tt_relationship_link SET state='Revoked',ended_at=UTC_TIMESTAMP(6),ended_by=%s WHERE id=%s",
                  (participant, relationship_id))
    _event('Relationship', relationship_id, 'RelationshipRevoked')
    return {'revoked': True, 'idempotent': False}


@command
def revoke_relationship_invitation(invitation_id):
    inviter = actor('Tele Tena Patient')
    profile('patient', lock=True)
    frappe.db.sql('SELECT id FROM tt_relationship_gate WHERE id=1 FOR UPDATE')
    invitation = rows('''SELECT id,state FROM tt_relationship_invitation
        WHERE id=%s AND inviter=%s FOR UPDATE''', (invitation_id, inviter))
    if not invitation:
        frappe.throw('Invitation unavailable', frappe.PermissionError)
    if invitation[0].state == 'Revoked':
        return {'revoked': True, 'idempotent': True}
    if invitation[0].state != 'Pending':
        fail('Only a pending invitation can be withdrawn.', 'relationship_invitation_unavailable')
    frappe.db.sql("UPDATE tt_relationship_invitation SET state='Revoked' WHERE id=%s", (invitation_id,))
    _event('Invitation', invitation_id, 'InviteRevoked')
    return {'revoked': True, 'idempotent': False}


@query()
def my_relationships():
    participant = actor('Tele Tena Patient')
    profile('patient')
    links = rows('''SELECT r.id,r.state,r.created_at,r.ended_at,
        CASE WHEN r.participant_a=%s THEN b.display_name ELSE a.display_name END other_name
        FROM tt_relationship_link r
        JOIN tt_profile a ON a.user=r.participant_a AND a.kind='patient'
        JOIN tt_profile b ON b.user=r.participant_b AND b.kind='patient'
        WHERE %s IN (r.participant_a,r.participant_b) ORDER BY r.created_at DESC LIMIT 50''',
        (participant, participant))
    invitations = rows('''SELECT id,CASE WHEN state='Pending' AND expires_at<=UTC_TIMESTAMP(6)
            THEN 'Expired' ELSE state END state,created_at,expires_at,accepted_at
        FROM tt_relationship_invitation WHERE inviter=%s ORDER BY created_at DESC LIMIT 50''', (participant,))
    return {
        'relationships': [{'id': item.id, 'state': item.state, 'other_name': item.other_name,
                           'created_at': item.created_at.isoformat(timespec='seconds') + 'Z',
                           'ended_at': item.ended_at.isoformat(timespec='seconds') + 'Z' if item.ended_at else None}
                          for item in links],
        'invitations': [{'id': item.id, 'state': item.state,
                         'created_at': item.created_at.isoformat(timespec='seconds') + 'Z',
                         'expires_at': item.expires_at.isoformat(timespec='seconds') + 'Z',
                         'accepted_at': item.accepted_at.isoformat(timespec='seconds') + 'Z' if item.accepted_at else None}
                        for item in invitations],
        'permissions_notice': 'Relationship links do not provide access to appointments, records, notes, or calls.'
    }


def expire_relationship_invitations():
    """Idempotent scheduler cleanup; acceptance also checks expiry directly."""
    frappe.db.sql("UPDATE tt_relationship_invitation SET state='Expired' WHERE state='Pending' AND expires_at<=UTC_TIMESTAMP(6)")
