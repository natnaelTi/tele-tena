"""Two adults consent separately; payer funds one existing appointment ledger."""
import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import frappe
from tele_tena.api import journey as j
from tele_tena.api.relationships import _retry_token, _token_digest

CONSENT_VERSION = 'adult-couple-appointment-v1'


def plan_for(appointment):
    return j.rows('SELECT * FROM tt_couple_plan WHERE appointment=%s', (appointment,))


def participants(plan):
    return j.rows('SELECT * FROM tt_couple_participant WHERE plan=%s ORDER BY consented_at,id', (plan,))


def participant(appointment, user, require_active=True):
    plans = plan_for(appointment)
    if not plans:
        return None
    found = [p for p in participants(plans[0].id) if p.user == user]
    if not found or (require_active and found[0].state != 'Consented'):
        frappe.throw('This consultation is unavailable.', frappe.PermissionError)
    return found[0]


def ready(appointment):
    plans = plan_for(appointment)
    if not plans:
        return True
    people = participants(plans[0].id)
    return len(people) == 2 and all(p.state == 'Consented' and
        frappe.db.get_value('User', p.user, 'enabled') and
        'Tele Tena Patient' in frappe.get_roles(p.user) for p in people)


def conflicts(users, start, end):
    for user in users:
        if j.rows('''SELECT a.id FROM tt_appointment a WHERE
            (a.patient=%s OR EXISTS (SELECT 1 FROM tt_couple_plan cp
             JOIN tt_couple_participant p ON p.plan=cp.id
             WHERE cp.appointment=a.id AND p.user=%s AND p.state='Consented'))
            AND a.state IN ('Booked','PendingConfirmation')
            AND (a.expires_at IS NULL OR a.expires_at>UTC_TIMESTAMP(6))
            AND a.start<%s AND a.end>%s FOR UPDATE''', (user, user, end, start)):
            j.fail('A participant already has an appointment at this time.', 'appointment_conflict')


def _offering(offering):
    item = j.one('''SELECT o.*,s.participant_structure FROM tt_offering o
        JOIN `tabTele Tena Service` s ON s.name=o.service WHERE o.id=%s AND o.active=1''', (offering,))
    if item.participant_structure != 'couple':
        j.fail('Choose a couples service.', 'couple_service_required')
    j.approved(item.clinician, True)
    j.approved_service(item.clinician, item.service, True)
    return item


def _consent(plan, user, request_text, sharing, expected_disclosure, adult_confirmed):
    p = j.profile('patient', True)
    if not j.boolean(adult_confirmed):
        j.fail('Each participant must confirm they are 18 or older.', 'adult_required')
    selected = j.choices(sharing)
    shared = j.disclosure(p, request_text, selected)
    if isinstance(expected_disclosure, str):
        expected_disclosure = json.loads(expected_disclosure)
    if shared != expected_disclosure:
        j.fail('Review your disclosure again before consenting.', 'preview_changed')
    j.one('SELECT name FROM tabUser WHERE name=%s AND enabled=1 FOR UPDATE', (user,))
    frappe.db.sql('''INSERT INTO tt_couple_participant
        (id,plan,user,state,disclosure,choices,consent_version,consented_at,room_identity)
        VALUES (%s,%s,%s,'Consented',%s,%s,%s,UTC_TIMESTAMP(6),%s)''',
        (str(uuid.uuid4()), plan, user, json.dumps(shared), json.dumps(selected),
         CONSENT_VERSION, secrets.token_urlsafe(32)))


@j.command
def invite(offering, start, request_text, sharing, expected_disclosure,
           adult_confirmed, retry_key, booked_timezone='UTC'):
    payer = j.actor('Tele Tena Patient')
    j.one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    key = j.text(retry_key, 80)
    start = j.instant(start)
    payload = json.dumps([offering,j.iso(start),request_text,sharing,expected_disclosure,booked_timezone], sort_keys=True)
    digest = hashlib.sha256(payload.encode()).hexdigest()
    token = _retry_token(payer, 'couple-' + key)
    existing = j.rows('SELECT * FROM tt_couple_plan WHERE payer=%s AND retry_key=%s FOR UPDATE', (payer,key))
    if existing:
        if existing[0].payload_hash != digest:
            j.fail('Retry details changed.', 'retry_changed')
        if existing[0].state != 'Invited' or existing[0].expires_at <= datetime.now(timezone.utc).replace(tzinfo=None):
            j.fail('This invitation is no longer available.', 'couple_invitation_unavailable')
        return {'id':existing[0].id,'token':token,'idempotent':True}
    offer = _offering(offering)
    from tele_tena.api.scheduling import validate_slot, _zone
    _zone(booked_timezone)
    validate_slot(offer,start,payer)
    plan = str(uuid.uuid4())
    frappe.db.sql('''INSERT INTO tt_couple_plan
        (id,payer,offering,start,timezone,price,minutes,retry_key,payload_hash,token_digest,state,created,expires_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Invited',UTC_TIMESTAMP(6),
        LEAST(%s,DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 24 HOUR)))''',
        (plan,payer,offering,start,booked_timezone,offer.price,offer.minutes,key,digest,_token_digest(token),start))
    _consent(plan,payer,request_text,sharing,expected_disclosure,adult_confirmed)
    return {'id':plan,'token':token,'idempotent':False}


def _visible(plan, user):
    people = participants(plan.id)
    own = next((p for p in people if p.user == user),None)
    clinician = j.one('''SELECT p.display_name,o.title,s.service_label FROM tt_offering o
        JOIN tt_profile p ON p.user=o.clinician JOIN `tabTele Tena Service` s ON s.name=o.service
        WHERE o.id=%s''', (plan.offering,))
    lifecycle = j.rows('''SELECT a.state appointment_state,c.state call_state
        FROM tt_appointment a LEFT JOIN tt_consultation c ON c.appointment=a.id
        WHERE a.id=%s''', (plan.appointment,)) if plan.appointment and own and own.state=='Consented' else []
    status = lifecycle[0] if lifecycle else {}
    return {'id':plan.id,'state':plan.state,'appointment':plan.appointment,
        'appointment_state':status.get('appointment_state'), 'call_state':status.get('call_state'),
        'service':clinician.title or clinician.service_label,'clinician':clinician.display_name,
        'start':j.iso(plan.start),'timezone':plan.timezone,'price':plan.price,'minutes':plan.minutes,
        'expires_at':j.iso(plan.expires_at),'consent_version':CONSENT_VERSION,
        'you_consented':bool(own and own.state=='Consented'),
        'you_pay':plan.payer==user,'participant_count':sum(p.state=='Consented' for p in people),
        'your_disclosure':json.loads(own.disclosure) if own else None}


@j.query(method='POST')
def preview_invitation(token):
    user = j.actor('Tele Tena Patient')
    j.profile('patient')
    plan = j.one('''SELECT * FROM tt_couple_plan WHERE token_digest=%s
        AND state IN ('Invited','Consented') AND expires_at>UTC_TIMESTAMP(6)''', (_token_digest(token),))
    return _visible(plan,user)


@j.command
def consent(token, request_text, sharing, expected_disclosure, adult_confirmed):
    user = j.actor('Tele Tena Patient')
    j.one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    plan = j.one('''SELECT * FROM tt_couple_plan WHERE token_digest=%s
        AND state IN ('Invited','Consented') AND expires_at>UTC_TIMESTAMP(6) FOR UPDATE''', (_token_digest(token),))
    own = next((p for p in participants(plan.id) if p.user==user),None)
    if own:
        # A retry must match the saved consent; later profile changes do not rewrite it.
        selected = j.choices(sharing)
        expected = json.loads(expected_disclosure) if isinstance(expected_disclosure,str) else expected_disclosure
        if not isinstance(expected,dict) or not j.boolean(adult_confirmed) or request_text != expected.get('request') or own.state!='Consented' or json.loads(own.choices)!=selected or json.loads(own.disclosure)!=expected:
            j.fail('Consent details changed. Start a new invitation.', 'retry_changed')
        return _visible(plan,user)
    if plan.state!='Invited' or len(participants(plan.id))!=1:
        frappe.throw('Invitation unavailable.',frappe.PermissionError)
    _consent(plan.id,user,request_text,sharing,expected_disclosure,adult_confirmed)
    frappe.db.sql("UPDATE tt_couple_plan SET state='Consented' WHERE id=%s", (plan.id,))
    plan.state='Consented'
    return _visible(plan,user)


@j.query()
def my_plans():
    user = j.actor('Tele Tena Patient')
    return [_visible(plan,user) for plan in j.rows('''SELECT cp.* FROM tt_couple_plan cp
        JOIN tt_couple_participant p ON p.plan=cp.id WHERE p.user=%s
        ORDER BY cp.created DESC LIMIT 50''', (user,))]


@j.command
def confirm(plan_id):
    payer = j.actor('Tele Tena Patient')
    j.one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    plan = j.one('SELECT * FROM tt_couple_plan WHERE id=%s AND payer=%s FOR UPDATE', (plan_id,payer))
    if plan.state=='Booked':
        return {'id':plan.appointment,'idempotent':True}
    if plan.state!='Consented' or plan.expires_at<=datetime.now(timezone.utc).replace(tzinfo=None):
        j.fail('Both adults must consent before booking.', 'couple_consent_required')
    people = participants(plan.id)
    if len(people)!=2 or not all(p.state=='Consented' and frappe.db.get_value('User',p.user,'enabled')
                                and 'Tele Tena Patient' in frappe.get_roles(p.user) for p in people):
        j.fail('Both adults must have active consent.', 'couple_consent_required')
    offer = _offering(plan.offering)
    conflicts([p.user for p in people], plan.start, plan.start+timedelta(minutes=plan.minutes))
    own = next(p for p in people if p.user==payer)
    frappe.local.tele_tena_couple_booking = plan
    try:
        result = j.book(plan.offering,j.iso(plan.start),json.loads(own.disclosure)['request'],
                        json.loads(own.choices),'couple-'+plan.id,plan.price,plan.minutes,
                        json.loads(own.disclosure),plan.timezone,couple_plan_id=plan.id)
        frappe.db.sql("UPDATE tt_couple_plan SET state='Booked',appointment=%s WHERE id=%s", (result['id'],plan.id))
        return result
    finally:
        frappe.local.tele_tena_couple_booking = None


def recipient_ids(appointment, supplied):
    if not plan_for(appointment):
        if supplied not in (None, [], '[]'):
            j.fail('Recipient selection is only for shared sessions.')
        return []
    if isinstance(supplied,str):
        try:supplied=json.loads(supplied)
        except ValueError:j.fail('Choose summary recipients.')
    if not isinstance(supplied,list) or any(not isinstance(p,str) for p in supplied):
        j.fail('Choose summary recipients explicitly.', 'summary_recipients_required')
    allowed={p.id for p in participants(plan_for(appointment)[0].id) if p.state=='Consented'}
    if len(supplied)!=len(set(supplied)) or not set(supplied)<=allowed:
        j.fail('A selected participant no longer has consent.', 'couple_consent_required')
    return sorted(supplied)


@frappe.whitelist(methods=['POST'])
def withdraw(plan_id):
    user = j.actor('Tele Tena Patient')
    j.one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    plan = j.one('SELECT * FROM tt_couple_plan WHERE id=%s FOR UPDATE', (plan_id,))
    people = participants(plan.id)
    own = next((p for p in people if p.user == user), None)
    if not own:
        frappe.throw('Shared session unavailable.', frappe.PermissionError)
    if own.state == 'Withdrawn':
        _close_withdrawn_room(plan, people)
        return {'withdrawn':True,'idempotent':True}
    if plan.appointment:
        item = j.one('SELECT * FROM tt_appointment WHERE id=%s FOR UPDATE', (plan.appointment,))
        if item.state in ('Booked','PendingConfirmation') and item.start > datetime.now(timezone.utc).replace(tzinfo=None):
            frappe.db.sql("UPDATE tt_consultation SET state='Ended',ended_by=%s,ended=UTC_TIMESTAMP(6),room_closed=0 WHERE appointment=%s AND state='Open'", (user,item.id))
            from tele_tena.api.presentation import cancel_appointment
            cancel_appointment(item.id, 'A participant withdrew consent for the shared session.')
        else:
            # Never silently adjudicate post-start refunds or a completed fee.
            session = j.rows('SELECT * FROM tt_consultation WHERE appointment=%s', (item.id,))
            if session and session[0].state != 'Ended':
                frappe.db.sql("UPDATE tt_consultation SET state='Ended',ended_by=%s,ended=UTC_TIMESTAMP(6),room_closed=0 WHERE appointment=%s", (user,item.id))
            from tele_tena.api.presentation import _event
            _event(item.id,'ParticipantConsentWithdrawn',user)
    frappe.db.sql("UPDATE tt_couple_participant SET state='Withdrawn',withdrawn_at=UTC_TIMESTAMP(6) WHERE id=%s", (own.id,))
    frappe.db.sql("UPDATE tt_couple_plan SET state='Withdrawn' WHERE id=%s", (plan.id,))
    _close_withdrawn_room(plan, people)
    return {'withdrawn':True,'idempotent':False}


def _close_withdrawn_room(plan, people):
    if not plan.appointment:
        return
    session = j.rows("SELECT * FROM tt_consultation WHERE appointment=%s AND state='Ended' AND room_closed=0", (plan.appointment,))
    if not session:
        return
    frappe.db.commit()  # Deny new tokens even during provider outage.
    from tele_tena.livekit import close_room
    identities = list(dict.fromkeys([p.room_identity for p in people] + [session[0].clinician_identity]))
    try:
        close_room(session[0].room_name,identities)
    except Exception:
        j.fail('Consent withdrawn; room closure is pending. Retry withdrawing consent.', 'consultation_close_pending')
    frappe.db.sql('UPDATE tt_consultation SET room_closed=1 WHERE appointment=%s', (plan.appointment,))


def expire_invitations():
    frappe.db.sql("UPDATE tt_couple_plan SET state='Expired' WHERE state IN ('Invited','Consented') AND expires_at<=UTC_TIMESTAMP(6)")


def room_labels(appointment, viewer, clinician_identity):
    plans = plan_for(appointment)
    if not plans:
        return []
    item = j.one('SELECT clinician FROM tt_appointment WHERE id=%s',(appointment,))
    clinician_name = j.one('SELECT display_name FROM tt_profile WHERE user=%s',(item.clinician,)).display_name
    labels = [{'identity':clinician_identity,'label':clinician_name,'role':'clinician'}]
    for index,p in enumerate(participants(plans[0].id),1):
        # Consent to clinician disclosure does not imply disclosure to a partner.
        label = json.loads(p.disclosure).get('name') if viewer == item.clinician else None
        labels.append({'identity':p.room_identity,'label':label or 'Participant '+str(index),'role':'patient'})
    return labels
