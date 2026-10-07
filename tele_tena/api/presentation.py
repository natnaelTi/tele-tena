"""State transitions and privacy-scoped presentation release APIs."""
import base64
import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import frappe

from tele_tena.api.journey import (actor, approved, approved_service, command, fail, integer, iso,
                                   one, profile, query, rows, text)

DEMO_CANCELLATION_POLICY = 'demo-full-release-before-start-v1'
TOUR_VERSION = 1
MAX_RESUME_BYTES = 5 * 1024 * 1024


def _event(appointment, event_type, event_actor=None, reason=None):
    frappe.db.sql('''INSERT INTO tt_appointment_event
        (id,appointment,event_type,actor,reason,created) VALUES (%s,%s,%s,%s,%s,UTC_TIMESTAMP(6))''',
        (str(uuid.uuid4()), appointment, event_type, event_actor or actor(), reason))


def _authorized(appointment, lock=False):
    user = actor()
    item = rows('''SELECT * FROM tt_appointment WHERE id=%s AND (patient=%s OR clinician=%s)''',
                (appointment, user, user))
    if not item:
        frappe.throw('Appointment unavailable', frappe.PermissionError)
    item = item[0]
    if user == item.patient:
        if 'Tele Tena Patient' not in frappe.get_roles(user):
            frappe.throw('Appointment unavailable', frappe.PermissionError)
        role = 'patient'
    else:
        if 'Tele Tena Clinician' not in frappe.get_roles(user):
            frappe.throw('Appointment unavailable', frappe.PermissionError)
        role = 'clinician'
    if lock:
        item = one('''SELECT * FROM tt_appointment WHERE id=%s
            AND (patient=%s OR clinician=%s) FOR UPDATE''', (appointment, user, user))
    return item, user, role


def _wallet_release(item, reference_suffix):
    wallet = one('SELECT available,reserved FROM tt_wallet WHERE patient=%s FOR UPDATE', (item.patient,))
    reference = 'release:' + item.id
    if rows('SELECT id FROM tt_ledger WHERE reference=%s', (reference,)):
        return False
    if int(wallet.reserved) < int(item.price):
        fail('Reservation is inconsistent; contact support', 'reservation_inconsistent')
    from tele_tena.accounting import account_id, check_wallet_projection, post
    check_wallet_projection(item.patient, wallet)
    frappe.db.sql('UPDATE tt_wallet SET available=available+%s,reserved=reserved-%s WHERE patient=%s',
                  (item.price, item.price, item.patient))
    from tele_tena.api.journey import simulation_log
    simulation_log(item.patient, 'Release', item.price, reference)
    post(reference, 'ReservationRelease', reference, [
        (account_id('patient', item.patient, 'reserved'), item.price, 0),
        (account_id('patient', item.patient, 'available'), 0, item.price)],
        {'appointment': item.id, 'reason': reference_suffix})
    return True


@frappe.whitelist(methods=['POST'])
def respond_to_request(appointment, decision):
    clinician = actor('Tele Tena Clinician')
    if decision not in ('confirm', 'decline'):
        fail('Choose confirm or decline')
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    item, _, role = _authorized(appointment, True)
    if role != 'clinician' or item.clinician != clinician:
        frappe.throw('Appointment unavailable', frappe.PermissionError)
    if item.state != 'PendingConfirmation':
        if decision == 'confirm' and item.state == 'Booked':
            return {'state': item.state, 'idempotent': True}
        if decision == 'decline' and item.state == 'Cancelled' and item.cancelled_by == clinician:
            return {'state': item.state, 'idempotent': True}
        fail('This request is no longer awaiting a response', 'request_resolved')
    if item.expires_at and item.expires_at <= datetime.now(timezone.utc).replace(tzinfo=None):
        _wallet_release(item, 'expiry')
        frappe.db.sql("UPDATE tt_appointment SET state='Expired' WHERE id=%s", (item.id,))
        _event(item.id, 'Expired', 'System')
        return {'state': 'Expired'}
    if decision == 'confirm':
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        frappe.db.sql("UPDATE tt_appointment SET state='Booked',confirmed_at=%s WHERE id=%s", (now, item.id))
        _event(item.id, 'Confirmed', clinician)
        return {'state': 'Booked'}
    _wallet_release(item, 'decline')
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    frappe.db.sql("UPDATE tt_appointment SET state='Cancelled',cancelled_by=%s,cancelled_at=%s,cancel_reason=%s WHERE id=%s",
                  (clinician, now, 'Clinician declined the request', item.id))
    _event(item.id, 'Declined', clinician, 'Clinician declined the request')
    return {'state': 'Cancelled'}


@frappe.whitelist(methods=['POST'])
def cancel_appointment(appointment, reason):
    user = actor()
    reason = text(reason, 500, required=False)
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    item, _, role = _authorized(appointment, True)
    if role == 'clinician' and item.clinician != user:
        frappe.throw('Appointment unavailable', frappe.PermissionError)
    if item.state == 'Cancelled' and item.cancelled_by == user and item.cancel_reason == reason:
        return {'state': 'Cancelled', 'idempotent': True}
    if item.state not in ('Booked', 'PendingConfirmation'):
        fail('This appointment cannot be cancelled in its current state', 'cancellation_unavailable')
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if item.start <= now:
        fail('Cancellations are available before the scheduled start', 'cancellation_cutoff')
    snapshot = json.loads(item.policy_snapshot) if item.policy_snapshot else {}
    if snapshot.get('version') != DEMO_CANCELLATION_POLICY:
        fail('The accepted cancellation policy is unavailable', 'policy_unavailable')
    _wallet_release(item, 'cancel')
    frappe.db.sql("UPDATE tt_reschedule_proposal SET state='Superseded',responded_at=UTC_TIMESTAMP(6) WHERE appointment=%s AND state='Pending'",
                  (item.id,))
    frappe.db.sql("UPDATE tt_appointment SET state='Cancelled',cancelled_by=%s,cancelled_at=%s,cancel_reason=%s WHERE id=%s",
                  (user, now, reason, item.id))
    _event(item.id, 'Cancelled', user, reason)
    return {'state': 'Cancelled', 'released': True}


def _reschedule_expiry():
    # 48 hours is a demonstration default, not an agreed commercial policy.
    try:
        hours = int(frappe.conf.get('tele_tena_reschedule_expiry_hours', 48))
    except (TypeError, ValueError):
        hours = 48
    return max(1, min(hours, 168))


def _can_change_time(item):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return (item.state == 'Booked' and item.start > now and
            not rows('SELECT appointment FROM tt_consultation WHERE appointment=%s', (item.id,)) and
            not rows('SELECT appointment FROM tt_consultation_note WHERE appointment=%s AND status=%s',
                     (item.id, 'Finalized')))


@command
def propose_reschedule(appointment, start, retry_key):
    """Propose a generated replacement time; the current slot remains held."""
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    item, user, role = _authorized(appointment, True)
    if not _can_change_time(item):
        fail('This appointment can no longer be rescheduled', 'reschedule_unavailable')
    start = journey_instant(start)
    key = text(retry_key, 80)
    payload_hash = hashlib.sha256(json.dumps(
        [appointment, iso(start)], separators=(',', ':')).encode()).hexdigest()
    prior = rows('''SELECT id,payload_hash,state FROM tt_reschedule_proposal
        WHERE appointment=%s AND proposer=%s AND retry_key=%s FOR UPDATE''', (item.id, user, key))
    if prior:
        if prior[0].payload_hash != payload_hash:
            fail('Retry key payload changed', 'retry_changed')
        return {'id': prior[0].id, 'state': prior[0].state, 'idempotent': True}
    active = rows('''SELECT id FROM tt_reschedule_proposal WHERE appointment=%s AND state='Pending'
        AND expires_at>UTC_TIMESTAMP(6) FOR UPDATE''', (item.id,))
    if active:
        fail('Another time-change request is awaiting a response', 'reschedule_pending')
    from tele_tena.api import scheduling
    offer = one('''SELECT o.*,s.service_label FROM tt_offering o
        JOIN `tabTele Tena Service` s ON s.name=o.service
        WHERE o.id=%s AND o.clinician=%s AND o.active=1 AND s.active=1 FOR UPDATE''',
        (item.offering, item.clinician))
    approved(item.clinician, True)
    approved_service(item.clinician, offer.service, True)
    if int(offer.minutes) != int(item.minutes):
        fail('The booked service duration has changed; support must review this appointment',
             'reschedule_service_changed')
    schedule = scheduling.validate_slot(offer, start, item.patient, lock=True,
                                        exclude_appointment=item.id)
    if schedule and schedule.consultation_format != item.consultation_format:
        fail('Choose an available time in the same consultation format', 'slot_unavailable')
    proposal_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires = now + timedelta(hours=_reschedule_expiry())
    frappe.db.sql('''INSERT INTO tt_reschedule_proposal
        (id,appointment,proposer,start,end,timezone,retry_key,payload_hash,state,created_at,expires_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'Pending',%s,%s)''',
        (proposal_id, item.id, user, start, start + timedelta(minutes=int(item.minutes)),
         schedule.timezone if schedule else item.timezone, key, payload_hash, now, expires))
    _event(item.id, 'RescheduleProposed', user, 'A new appointment time was proposed')
    return {'id': proposal_id, 'state': 'Pending', 'expires_at': iso(expires),
            'start': iso(start), 'timezone': schedule.timezone if schedule else item.timezone}


def journey_instant(value):
    from tele_tena.api.journey import instant
    return instant(value)


@command
def respond_to_reschedule(appointment, proposal, decision):
    if decision not in ('accept', 'decline'):
        fail('Choose whether to accept or decline the proposed time')
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    item, user, role = _authorized(appointment, True)
    record = rows('''SELECT * FROM tt_reschedule_proposal WHERE id=%s AND appointment=%s FOR UPDATE''',
                  (proposal, item.id))
    if not record:
        frappe.throw('Appointment unavailable', frappe.PermissionError)
    record = record[0]
    if record.state in ('Accepted', 'Declined'):
        if decision == 'accept' and record.state == 'Accepted':
            return {'state': 'Accepted', 'start': iso(record.start), 'idempotent': True}
        if decision == 'decline' and record.state == 'Declined' and record.responded_by == user:
            return {'state': 'Declined', 'idempotent': True}
        fail('This time-change request is already resolved', 'reschedule_resolved')
    if record.proposer == user:
        frappe.throw('Only the other appointment participant may respond', frappe.PermissionError)
    if record.state != 'Pending':
        fail('This time-change request is no longer available', 'reschedule_resolved')
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if record.expires_at <= now:
        frappe.db.sql("UPDATE tt_reschedule_proposal SET state='Expired',responded_at=%s WHERE id=%s",
                      (now, record.id))
        _event(item.id, 'RescheduleExpired', 'System')
        return {'state': 'Expired'}
    if decision == 'decline':
        frappe.db.sql("UPDATE tt_reschedule_proposal SET state='Declined',responded_by=%s,responded_at=%s WHERE id=%s",
                      (user, now, record.id))
        _event(item.id, 'RescheduleDeclined', user)
        return {'state': 'Declined'}
    if not _can_change_time(item):
        frappe.db.sql("UPDATE tt_reschedule_proposal SET state='Superseded',responded_by=%s,responded_at=%s WHERE id=%s",
                      (user, now, record.id))
        _event(item.id, 'RescheduleUnavailable', 'System')
        return {'state': 'Unavailable', 'message': 'This appointment can no longer be rescheduled.'}
    from tele_tena.api import scheduling
    offer = rows('''SELECT o.*,s.service_label FROM tt_offering o
        JOIN `tabTele Tena Service` s ON s.name=o.service
        WHERE o.id=%s AND o.clinician=%s AND o.active=1 AND s.active=1 FOR UPDATE''',
        (item.offering, item.clinician))
    if not offer:
        fail('The booked service is no longer available for a time change', 'reschedule_service_changed')
    offer = offer[0]
    approved(item.clinician, True)
    approved_service(item.clinician, offer.service, True)
    if int(offer.minutes) != int(item.minutes):
        fail('The booked service duration has changed; support must review this appointment',
             'reschedule_service_changed')
    try:
        schedule = scheduling.validate_slot(offer, record.start, item.patient, lock=True,
                                            exclude_appointment=item.id)
    except frappe.ValidationError:
        frappe.db.sql("UPDATE tt_reschedule_proposal SET state='Unavailable',responded_by=%s,responded_at=%s WHERE id=%s",
                      (user, now, record.id))
        _event(item.id, 'RescheduleSlotUnavailable', 'System')
        return {'state': 'Unavailable', 'message': 'That time is no longer available. Ask for another time.'}
    if schedule and (schedule.timezone != record.timezone or
                     schedule.consultation_format != item.consultation_format):
        frappe.db.sql("UPDATE tt_reschedule_proposal SET state='Unavailable',responded_by=%s,responded_at=%s WHERE id=%s",
                      (user, now, record.id))
        _event(item.id, 'RescheduleSlotUnavailable', 'System')
        return {'state': 'Unavailable', 'message': 'That time is no longer available. Ask for another time.'}
    end = record.start + timedelta(minutes=int(item.minutes))
    # The original reservation and immutable price/disclosure/policy remain on
    # this same appointment. No financial posting is created by rescheduling.
    frappe.db.sql('''UPDATE tt_appointment SET start=%s,end=%s,timezone=%s,schedule_id=%s,
        buffer_before=%s,buffer_after=%s WHERE id=%s''',
        (record.start, end, schedule.timezone if schedule else record.timezone,
         schedule.id if schedule else item.schedule_id,
         schedule.buffer_before if schedule else item.buffer_before,
         schedule.buffer_after if schedule else item.buffer_after, item.id))
    frappe.db.sql("UPDATE tt_reschedule_proposal SET state='Accepted',responded_by=%s,responded_at=%s WHERE id=%s",
                  (user, now, record.id))
    frappe.db.sql("UPDATE tt_reschedule_proposal SET state='Superseded',responded_at=%s WHERE appointment=%s AND id<>%s AND state='Pending'",
                  (now, item.id, record.id))
    _event(item.id, 'RescheduleAccepted', user)
    return {'state': 'Accepted', 'start': iso(record.start), 'end': iso(end),
            'timezone': schedule.timezone if schedule else record.timezone}


@command
def withdraw_reschedule(appointment, proposal):
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    item, user, _ = _authorized(appointment, True)
    record = rows('''SELECT id,proposer,state FROM tt_reschedule_proposal
        WHERE id=%s AND appointment=%s FOR UPDATE''', (proposal, item.id))
    if not record:
        frappe.throw('Appointment unavailable', frappe.PermissionError)
    if record[0].proposer != user:
        frappe.throw('Only the proposer may withdraw this request', frappe.PermissionError)
    if record[0].state == 'Withdrawn':
        return {'state': 'Withdrawn', 'idempotent': True}
    if record[0].state != 'Pending':
        fail('This time-change request is already resolved', 'reschedule_resolved')
    frappe.db.sql("UPDATE tt_reschedule_proposal SET state='Withdrawn',responded_by=%s,responded_at=UTC_TIMESTAMP(6) WHERE id=%s",
                  (user, record[0].id))
    _event(item.id, 'RescheduleWithdrawn', user)
    return {'state': 'Withdrawn'}


def expire_reschedule_proposals():
    """Expire pending mutual-time proposals without changing appointments."""
    candidates = rows("SELECT id,appointment FROM tt_reschedule_proposal WHERE state='Pending' "
                      "AND expires_at<=UTC_TIMESTAMP(6) ORDER BY expires_at LIMIT 100")
    for candidate in candidates:
        savepoint = 'tt_reschedule_expire_' + uuid.uuid4().hex
        frappe.db.savepoint(savepoint)
        try:
            one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
            record = rows("SELECT id,appointment FROM tt_reschedule_proposal WHERE id=%s "
                          "AND state='Pending' AND expires_at<=UTC_TIMESTAMP(6) FOR UPDATE",
                          (candidate.id,))
            if not record:
                frappe.db.rollback(save_point=savepoint)
                continue
            frappe.db.sql("UPDATE tt_reschedule_proposal SET state='Expired',responded_at=UTC_TIMESTAMP(6) WHERE id=%s",
                          (candidate.id,))
            _event(candidate.appointment, 'RescheduleExpired', 'System')
            frappe.db.commit()
        except Exception:
            frappe.db.rollback(save_point=savepoint)
            raise


def expire_pending_appointments():
    """Scheduled expiry; all paths serialize with booking and cancellation."""
    candidates = rows("SELECT id FROM tt_appointment WHERE state='PendingConfirmation' "
                      "AND expires_at<=UTC_TIMESTAMP(6) ORDER BY expires_at LIMIT 100")
    for candidate in candidates:
        savepoint = 'tt_expire_' + uuid.uuid4().hex
        frappe.db.savepoint(savepoint)
        try:
            one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
            current = rows("SELECT * FROM tt_appointment WHERE id=%s FOR UPDATE", (candidate.id,))
            if not current or current[0].state != 'PendingConfirmation' or not current[0].expires_at \
                    or current[0].expires_at > datetime.now(timezone.utc).replace(tzinfo=None):
                frappe.db.rollback(save_point=savepoint)
                continue
            item = current[0]
            _wallet_release(item, 'expiry')
            frappe.db.sql("UPDATE tt_appointment SET state='Expired' WHERE id=%s", (item.id,))
            _event(item.id, 'Expired', 'System')
            frappe.db.commit()
        except Exception:
            frappe.db.rollback(save_point=savepoint)
            raise


@query()
def appointment_detail(appointment):
    item, user, role = _authorized(appointment)
    from tele_tena.api.consultations import _window
    call = rows('SELECT state,created,ended FROM tt_consultation WHERE appointment=%s', (item.id,))
    note = rows('SELECT status,current_revision FROM tt_consultation_note WHERE appointment=%s', (item.id,))
    events = rows('''SELECT event_type,actor,reason,created FROM tt_appointment_event
        WHERE appointment=%s ORDER BY created,id''', (item.id,))
    event_labels = {
        'Booked': 'Appointment booked', 'Requested': 'Confirmation requested',
        'Confirmed': 'Appointment confirmed', 'Declined': 'Appointment declined',
        'Cancelled': 'Appointment cancelled', 'Expired': 'Appointment expired',
        'Completed': 'Consultation finalized', 'DocumentationDraftSaved': 'Notes draft saved',
        'DocumentationFinalized': 'Consultation finalized',
        'RescheduleProposed': 'New time proposed', 'RescheduleAccepted': 'New time accepted',
        'RescheduleDeclined': 'New time declined', 'RescheduleWithdrawn': 'Time request withdrawn',
        'RescheduleExpired': 'Time request expired', 'RescheduleUnavailable': 'Time change unavailable',
        'RescheduleSlotUnavailable': 'Proposed time unavailable',
        'ClinicScheduleAccessGranted': 'Clinic scheduling access shared',
        'ClinicScheduleAccessRevoked': 'Clinic scheduling access stopped',
        'SessionFeedbackSubmitted': 'Session feedback submitted',
    }
    reschedule = rows('''SELECT id,proposer,start,timezone,state,expires_at FROM tt_reschedule_proposal
        WHERE appointment=%s AND state='Pending' AND expires_at>UTC_TIMESTAMP(6)
        ORDER BY created_at DESC LIMIT 1''', (item.id,))
    disclosure = json.loads(item.disclosure)
    selected = {
        'id': item.id,
        'status': item.state,
        'service': item.service_label,
        'start': iso(item.start),
        'end': iso(item.end),
        'timezone': item.timezone,
        'format': item.consultation_format,
        'booked_minutes': item.minutes,
        'price': item.price,
        'currency': 'ETB',
        'confirmation_mode': item.confirmation_mode,
        'expires_at': iso(item.expires_at) if item.expires_at else None,
        'disclosure': disclosure,
        'call_state': call[0].state if call else 'NotStarted',
        'can_join': item.state == 'Booked' and _window(item) and not (call and call[0].state == 'Ended'),
        'call_room_created_at': iso(call[0].created) if call else None,
        'call_ended_at': iso(call[0].ended) if call and call[0].ended else None,
        'actual_connected_time_available': False,
        'documentation_state': note[0].status if note else 'None',
        'patient_summary_revisions': [],
        'cancellation': {
            'actor': ('You' if item.cancelled_by == user else
                      'Care team' if role == 'patient' else 'Patient') if item.cancelled_by else None,
            'at': iso(item.cancelled_at) if item.cancelled_at else None,
            'reason': item.cancel_reason,
            'policy': json.loads(item.policy_snapshot) if item.policy_snapshot else None,
        },
        'timeline': [{'event': event_labels.get(e.event_type,
                      re.sub(r'(?<!^)(?=[A-Z])', ' ', e.event_type)), 'actor': 'You' if e.actor == user else
                      ('System' if e.actor == 'System' else
                       'Care team' if role == 'patient' else 'Patient'),
                      'reason': e.reason, 'at': iso(e.created)} for e in events],
        'can_cancel': item.state in ('Booked', 'PendingConfirmation') and
                      item.start > datetime.now(timezone.utc).replace(tzinfo=None),
        'can_respond': role == 'clinician' and item.state == 'PendingConfirmation',
        'offering': item.offering,
        'reschedule': ({'id': reschedule[0].id, 'proposed_by_you': reschedule[0].proposer == user,
                        'start': iso(reschedule[0].start), 'timezone': reschedule[0].timezone,
                        'expires_at': iso(reschedule[0].expires_at)} if reschedule else None),
        'can_propose_reschedule': _can_change_time(item) and not bool(reschedule),
    }
    earning = rows('SELECT state,release_at FROM tt_earning WHERE appointment=%s', (item.id,))
    if earning:
        selected['financial_state'] = earning[0].state
        selected['dispute_release_at'] = iso(earning[0].release_at) if earning[0].release_at else None
        selected['can_open_financial_dispute'] = (role == 'patient' and earning[0].state == 'Pending' and
            earning[0].release_at and earning[0].release_at > datetime.now(timezone.utc).replace(tzinfo=None))
    if role == 'patient':
        clinician = one('SELECT display_name FROM tt_profile WHERE user=%s AND kind=%s',
                        (item.clinician, 'clinician'))
        selected['clinician'] = clinician.display_name
        feedback = rows('''SELECT rating,created_at FROM tt_session_feedback
            WHERE appointment=%s AND patient=%s''', (item.id, item.patient))
        selected['session_feedback'] = ({'submitted': True, 'rating': int(feedback[0].rating),
                                         'submitted_at': iso(feedback[0].created_at)}
                                        if feedback else {'submitted': False, 'rating': None,
                                                          'submitted_at': None})
        call_ended = bool(call and call[0].state == 'Ended')
        selected['can_submit_feedback'] = (item.state == 'Completed' and call_ended and
                                           not feedback)
        # Critically, this SELECT never reads private_note.
        revisions = rows('''SELECT revision,patient_summary,created FROM tt_note_revision
            WHERE appointment=%s AND summary_published=1 ORDER BY revision''', (item.id,))
        selected['patient_summary_revisions'] = [
            {'revision': r.revision, 'summary': r.patient_summary, 'published_at': iso(r.created)}
            for r in revisions]
    else:
        selected['patient_identity'] = disclosure.get('name') or 'Private patient'
        selected['sharing_snapshot'] = disclosure
        if note:
            current = rows('''SELECT revision,private_note,patient_summary,summary_published,author,created
                FROM tt_note_revision WHERE appointment=%s AND revision=%s''',
                (item.id, note[0].current_revision))
            if current:
                selected['private_note'] = {
                    'revision': current[0].revision,
                    'text': current[0].private_note,
                    'patient_summary': current[0].patient_summary,
                    'summary_published': bool(current[0].summary_published),
                    'author': 'You' if current[0].author == user else 'Treating clinician',
                }
        selected['prior_shared_revisions'] = [
            {'revision': r.revision, 'published_at': iso(r.created)}
            for r in rows('''SELECT revision,created FROM tt_note_revision
                WHERE appointment=%s AND summary_published=1 ORDER BY revision''', (item.id,))]
    return selected


@frappe.whitelist(methods=['POST'])
def save_note_draft(appointment, private_note, patient_summary):
    clinician = actor('Tele Tena Clinician')
    private_note = text(private_note, 12000, required=False)
    patient_summary = text(patient_summary, 6000, required=False)
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    item, _, role = _authorized(appointment, True)
    if role != 'clinician' or item.clinician != clinician:
        frappe.throw('Consultation record unavailable', frappe.PermissionError)
    call = rows("SELECT state FROM tt_consultation WHERE appointment=%s", (item.id,))
    if not call or call[0].state != 'Ended' or item.state not in ('Booked', 'Completed'):
        fail('End the consultation before documenting it', 'documentation_not_ready')
    existing = rows('SELECT status,current_revision FROM tt_consultation_note WHERE appointment=%s FOR UPDATE',
                     (item.id,))
    revision = (int(existing[0].current_revision) if existing else 0) + 1
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    frappe.db.sql('''INSERT INTO tt_note_revision
        (id,appointment,clinician,revision,private_note,patient_summary,summary_published,author,created)
        VALUES (%s,%s,%s,%s,%s,%s,0,%s,%s)''',
        (str(uuid.uuid4()), item.id, clinician, revision, private_note, patient_summary, clinician, now))
    if existing:
        frappe.db.sql("UPDATE tt_consultation_note SET status='Draft',current_revision=%s,modified=%s WHERE appointment=%s",
                      (revision, now, item.id))
    else:
        frappe.db.sql("INSERT INTO tt_consultation_note (appointment,clinician,status,current_revision,created,modified) VALUES (%s,%s,'Draft',%s,%s,%s)",
                      (item.id, clinician, revision, now, now))
    _event(item.id, 'DocumentationDraftSaved', clinician)
    return {'status': 'Draft', 'revision': revision}


@frappe.whitelist(methods=['POST'])
def preview_patient_summary(appointment, summary=None):
    clinician = actor('Tele Tena Clinician')
    item, _, role = _authorized(appointment)
    if role != 'clinician' or item.clinician != clinician:
        frappe.throw('Consultation record unavailable', frappe.PermissionError)
    note = one('SELECT current_revision,status FROM tt_consultation_note WHERE appointment=%s', (item.id,))
    revision = one('''SELECT revision,patient_summary FROM tt_note_revision
        WHERE appointment=%s AND revision=%s''', (item.id, note.current_revision))
    visible = text(summary, 6000, required=False) if summary is not None else revision.patient_summary
    return {'revision': revision.revision, 'summary': visible,
            'note_status': note.status, 'preview_only': True}


@command
def finalize_consultation(appointment, publish_summary=0):
    clinician = actor('Tele Tena Clinician')
    publish = publish_summary in (True, 1, '1')
    if publish_summary not in (True, False, 0, 1, '0', '1'):
        fail('Choose whether to publish the patient summary')
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    item, _, role = _authorized(appointment, True)
    if role != 'clinician' or item.clinician != clinician:
        frappe.throw('Consultation record unavailable', frappe.PermissionError)
    call = rows("SELECT state FROM tt_consultation WHERE appointment=%s", (item.id,))
    note = one('SELECT current_revision,status FROM tt_consultation_note WHERE appointment=%s FOR UPDATE', (item.id,))
    if item.state == 'Completed' and note.status == 'Finalized':
        earnings = rows('SELECT state,net_minor,release_at FROM tt_earning WHERE appointment=%s', (item.id,))
        return {'status': 'Finalized', 'revision': note.current_revision,
                'idempotent': True, 'earning_state': earnings[0].state if earnings else 'LegacyHold'}
    if not call or call[0].state != 'Ended' or note.status != 'Draft':
        fail('Save a documentation draft after ending the call', 'documentation_not_ready')
    current = one('''SELECT * FROM tt_note_revision WHERE appointment=%s AND revision=%s''',
                  (item.id, note.current_revision))
    if publish and not current.patient_summary.strip():
        fail('Add a patient summary before publishing it', 'summary_required')
    finalized_revision = int(note.current_revision) + 1
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    frappe.db.sql('''INSERT INTO tt_note_revision
        (id,appointment,clinician,revision,private_note,patient_summary,summary_published,author,created)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
        (str(uuid.uuid4()), item.id, clinician, finalized_revision, current.private_note,
         current.patient_summary, int(publish), clinician, now))
    frappe.db.sql("UPDATE tt_consultation_note SET status='Finalized',current_revision=%s,modified=%s WHERE appointment=%s",
                  (finalized_revision, now, item.id))
    if item.state != 'Completed':
        import json
        from tele_tena.accounting import account_id, check_wallet_projection, post
        extensions = rows('''SELECT id,duration_minutes,amount_minor,price_snapshot,policy_snapshot
            FROM tt_consultation_extension WHERE appointment=%s AND state='Started'
            ORDER BY started_at FOR UPDATE''', (item.id,))
        extension_total = sum(int(extension.amount_minor) for extension in extensions)
        gross = int(item.price) + extension_total
        wallet = one('SELECT available,reserved FROM tt_wallet WHERE patient=%s FOR UPDATE', (item.patient,))
        snapshot = json.loads(item.policy_snapshot) if item.policy_snapshot else {}
        finance = snapshot.get('financial', {})
        if finance.get('version') != 'demo-earnings-v1' or finance.get('external_settlement') is not False:
            fail('Accepted earnings policy is unavailable for this appointment', 'financial_policy_missing')
        fee = (gross * int(finance.get('fee_bps', 0))) // 10000
        net = gross - fee
        if int(wallet.reserved) < gross:
            fail('Reservation is inconsistent; consultation remains unfinalized', 'reservation_inconsistent')
        check_wallet_projection(item.patient, wallet)
        earning_id = str(uuid.uuid4())
        release_at = now + timedelta(minutes=int(finance.get('dispute_window_minutes', 60)))
        frappe.db.sql('''UPDATE tt_wallet SET reserved=reserved-%s WHERE patient=%s''', (gross, item.patient))
        entries = [(account_id('patient', item.patient, 'reserved'), gross, 0),
                   (account_id('clinician', clinician, 'pending'), 0, net)]
        if fee:
            entries.append((account_id('', '', 'platform_fee_revenue'), 0, fee))
        reference = 'completion:' + item.id
        policy_snapshot = {**finance, 'extension_blocks': [
            {'id': extension.id, 'duration_minutes': int(extension.duration_minutes),
             'amount_minor': int(extension.amount_minor), 'price_snapshot': json.loads(extension.price_snapshot),
             'policy_snapshot': json.loads(extension.policy_snapshot)} for extension in extensions]}
        post(reference, 'ConsultationFinalized', reference, entries,
             {'appointment': item.id, 'simulated': True,
              'extension_ids': [extension.id for extension in extensions]})
        frappe.db.sql('''INSERT INTO tt_earning
            (id,appointment,patient,clinician,gross_minor,fee_minor,net_minor,policy_snapshot,
             state,completed_at,release_at,created,modified)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'Pending',%s,%s,%s,%s)''',
            (earning_id, item.id, item.patient, clinician, gross, fee, net,
             json.dumps(policy_snapshot, separators=(',', ':'), sort_keys=True), now, release_at, now, now))
        for extension in extensions:
            frappe.db.sql("UPDATE tt_consultation_extension SET state='Settled',closed_at=%s WHERE id=%s AND state='Started'",
                          (now, extension.id))
            _event(item.id, 'ExtensionSettled', clinician)
        frappe.db.sql("UPDATE tt_appointment SET state='Completed' WHERE id=%s", (item.id,))
        _event(item.id, 'Completed', clinician)
    _event(item.id, 'DocumentationFinalized', clinician)
    return {'status': 'Finalized', 'revision': finalized_revision,
            'patient_summary_published': publish}


@query()
def care_directory(search='', service='', status='', from_date='', to_date='', page=1, page_size=20):
    clinician = actor('Tele Tena Clinician')
    profile('clinician')
    search = text(search, 120, required=False)
    page = integer(page, 1, 100000)
    page_size = integer(page_size, 5, 50)
    allowed = ('PendingConfirmation', 'Booked', 'Cancelled', 'Expired', 'Completed', 'NoShow')
    if status and status not in allowed:
        fail('Invalid care status filter')
    if service and not frappe.db.exists('Tele Tena Service', service):
        fail('Invalid service filter')
    try:
        if from_date:
            datetime.strptime(from_date, '%Y-%m-%d')
        if to_date:
            datetime.strptime(to_date, '%Y-%m-%d')
    except ValueError:
        fail('Invalid date filter')
    where = ['a.clinician=%s']
    params = [clinician]
    if status:
        where.append('a.state=%s'); params.append(status)
    if service:
        where.append('a.offering IN (SELECT id FROM tt_offering WHERE service=%s)'); params.append(service)
    if from_date:
        where.append('DATE(a.start)>=%s'); params.append(from_date)
    if to_date:
        where.append('DATE(a.start)<=%s'); params.append(to_date)
    if search:
        where.append("JSON_UNQUOTE(JSON_EXTRACT(a.disclosure,'$.name')) LIKE %s")
        params.append('%' + search.replace('%', '\\%').replace('_', '\\_') + '%')
    sql_where = ' AND '.join(where)
    found = rows('''SELECT a.id,a.start,a.end,a.state,a.service_label,a.disclosure,a.timezone,a.minutes,
        a.price,c.state call_state,n.status documentation_state
        FROM tt_appointment a LEFT JOIN tt_consultation c ON c.appointment=a.id
        LEFT JOIN tt_consultation_note n ON n.appointment=a.id WHERE ''' + sql_where +
        ' ORDER BY a.start DESC,a.id', tuple(params))
    groups = {}
    for item in found:
        disclosure = json.loads(item.disclosure)
        name = disclosure.get('name')
        key = 'shared:' + name if name else 'encounter:' + item.id
        group = groups.setdefault(key, {'id': item.id, 'patient_label': name or 'Private patient',
                                        'encounters': [], 'last_consultation': None,
                                        'next_appointment': None, 'service_label': item.service_label,
                                        'state': item.state, 'disclosure': disclosure,
                                        'start': item.start, 'timezone': item.timezone})
        group['encounters'].append(item.id)
        if item.start < datetime.now(timezone.utc).replace(tzinfo=None) and (
                item.state == 'Completed' or item.call_state == 'Ended'):
            if not group['last_consultation'] or item.start > group['last_consultation']:
                group['last_consultation'] = item.start
        elif item.state in ('Booked', 'PendingConfirmation') and (
                not group['next_appointment'] or item.start < group['next_appointment']):
            group['next_appointment'] = item.start
        if item.start > group['start']:
            group.update(id=item.id, service_label=item.service_label, state=item.state,
                         disclosure=disclosure, start=item.start, timezone=item.timezone)
    found = list(groups.values())
    for item in found:
        item['start'] = iso(item['start'])
        item['last_consultation'] = iso(item['last_consultation']) if item['last_consultation'] else None
        item['next_appointment'] = iso(item['next_appointment']) if item['next_appointment'] else None
        item['encounter_count'] = len(item['encounters'])
    total = len(found)
    found = found[(page - 1) * page_size:page * page_size]
    return {'rows': found, 'total': total, 'page': page, 'page_size': page_size,
            'pages': (total + page_size - 1) // page_size}


@query()
def care_patient_record(appointment):
    item, clinician, role = _authorized(appointment)
    if role != 'clinician':
        frappe.throw('Care record unavailable', frappe.PermissionError)
    disclosure = json.loads(item.disclosure)
    shared_name = disclosure.get('name')
    if shared_name:
        matches = rows('''SELECT id FROM tt_appointment WHERE clinician=%s
            AND JSON_UNQUOTE(JSON_EXTRACT(disclosure,'$.name'))=%s ORDER BY start DESC''',
            (clinician, shared_name))
    else:
        matches = [{'id': item.id}]
    return {'patient_label': shared_name or 'Private patient',
            'encounters': [appointment_detail(row['id']) for row in matches]}


@query()
def care_detail(appointment):
    item, _, role = _authorized(appointment)
    if role != 'clinician':
        frappe.throw('Care record unavailable', frappe.PermissionError)
    return appointment_detail(appointment)


@query()
def preferences():
    user = actor()
    result = rows('SELECT locale,timezone,notification_preferences FROM tt_preferences WHERE user=%s', (user,))
    return result[0] if result else {'locale': 'en', 'timezone': None, 'notification_preferences': None}


@frappe.whitelist(methods=['POST'])
def save_preferences(locale, timezone_name):
    user = actor()
    if locale not in ('en', 'am', 'om'):
        fail('Choose an available language')
    if timezone_name:
        try:
            zone = ZoneInfo(timezone_name)
        except (ZoneInfoNotFoundError, ValueError):
            fail('Choose a valid timezone')
        timezone_name = zone.key
    frappe.db.sql('''INSERT INTO tt_preferences (user,locale,timezone,modified)
        VALUES (%s,%s,%s,UTC_TIMESTAMP(6)) ON DUPLICATE KEY UPDATE
        locale=VALUES(locale),timezone=VALUES(timezone),modified=VALUES(modified)''',
        (user, locale, timezone_name or None))
    return {'locale': locale, 'timezone': timezone_name or None, 'saved': True}


@query()
def wallet_summary():
    patient = actor('Tele Tena Patient')
    profile('patient')
    wallet = one('SELECT available,reserved FROM tt_wallet WHERE patient=%s', (patient,))
    legacy = rows('''SELECT l.kind,l.amount,l.created,l.reference FROM tt_ledger l
        LEFT JOIN tt_journal j ON j.event_ref=l.reference
        WHERE l.patient=%s AND j.id IS NULL ORDER BY l.created DESC,l.id DESC LIMIT 50''', (patient,))
    from tele_tena.accounting import _event_rows, account_id
    activity = legacy + _event_rows([
        account_id('patient', patient, 'available'), account_id('patient', patient, 'reserved')])
    for item in legacy:
        item.source = 'simulation_log'
        item.event_ref = item.reference
        item.kind = {'Deposit': 'Demonstration funds added', 'Reservation': 'Appointment funds reserved',
                     'Release': 'Appointment reservation released'}.get(item.kind, item.kind)
    event_labels = {'Deposit': 'Demonstration funds added', 'Reservation': 'Appointment funds reserved',
                    'ReservationRelease': 'Appointment reservation released',
                    'ConsultationFinalized': 'Consultation completed', 'EarningRefunded': 'Refund recorded'}
    for item in activity[len(legacy):]:
        item.source = 'demo_subledger'
        item.kind = event_labels.get(item.event_type, item.event_type)
    activity.sort(key=lambda item: (item.created, getattr(item, 'reference', '')), reverse=True)
    activity = activity[:50]
    for item in activity:
        item.created = iso(item.created)
    return {'available': wallet.available, 'reserved': wallet.reserved, 'currency': 'ETB',
            'activity': activity}


TOURS = {
    'patient': {'patient-home', 'patient-discovery', 'patient-appointments', 'patient-account'},
    'clinician': {'clinician-today', 'clinician-availability', 'clinician-notes', 'clinician-care', 'clinician-account'},
    'approver': {'reviewer-applications', 'reviewer-scopes'},
    'applicant': {'clinician-onboarding'},
}


def _tour_role(user):
    roles = set(frappe.get_roles(user))
    if 'Tele Tena Approver' in roles:
        return 'approver'
    if 'Tele Tena Clinician' in roles:
        return 'clinician'
    if 'Tele Tena Patient' in roles:
        return 'patient'
    p = rows('SELECT kind FROM tt_profile WHERE user=%s', (user,))
    if p and p[0].kind == 'clinician':
        return 'applicant'
    draft = rows('SELECT kind,completed FROM tt_onboarding WHERE user=%s', (user,))
    return 'applicant' if draft and draft[0].kind == 'clinician' and not draft[0].completed else None


@query()
def tour_state(tour_id):
    user = actor()
    role = _tour_role(user)
    if not role or tour_id not in TOURS[role]:
        frappe.throw('Tour unavailable', frappe.PermissionError)
    saved = rows('''SELECT state FROM tt_tour_progress
        WHERE user=%s AND role=%s AND tour_id=%s AND version=%s''',
        (user, role, tour_id, TOUR_VERSION))
    return {'role': role, 'tour_id': tour_id, 'version': TOUR_VERSION,
            'state': saved[0].state if saved else None}


@frappe.whitelist(methods=['POST'])
def save_tour_state(tour_id, state):
    user = actor()
    role = _tour_role(user)
    if not role or tour_id not in TOURS[role] or state not in ('Dismissed', 'Completed'):
        frappe.throw('Tour unavailable', frappe.PermissionError)
    frappe.db.sql('''INSERT INTO tt_tour_progress (user,role,tour_id,version,state,modified)
        VALUES (%s,%s,%s,%s,%s,UTC_TIMESTAMP(6)) ON DUPLICATE KEY UPDATE
        state=VALUES(state),modified=VALUES(modified)''',
        (user, role, tour_id, TOUR_VERSION, state))
    return {'state': state, 'saved': True}


def _resume_owner():
    user = actor()
    p = rows('SELECT kind FROM tt_profile WHERE user=%s', (user,))
    draft = rows('SELECT kind,completed FROM tt_onboarding WHERE user=%s', (user,))
    if not ((p and p[0].kind == 'clinician') or
            (draft and draft[0].kind == 'clinician' and not draft[0].completed)):
        frappe.throw('Resume unavailable', frappe.PermissionError)
    return user


@query()
def resume_status():
    user = _resume_owner()
    found = rows('SELECT filename,content_size,revision,uploaded_at FROM tt_resume_evidence WHERE clinician=%s', (user,))
    return {'uploaded': bool(found), **(dict(found[0]) if found else {})}


@frappe.whitelist(methods=['POST'])
def upload_resume(filename, content_base64):
    user = _resume_owner()
    if not isinstance(filename, str) or len(filename) > 255 or not filename.lower().endswith('.pdf'):
        fail('Upload a PDF resume')
    filename = re.sub(r'[^A-Za-z0-9 ._()-]', '_', filename.split('/')[-1].split('\\')[-1])[:180]
    if not isinstance(content_base64, str) or len(content_base64) > ((MAX_RESUME_BYTES + 2) // 3) * 4 + 8:
        fail('The PDF must be 5 MiB or smaller')
    try:
        content = base64.b64decode(content_base64, validate=True)
    except (ValueError, TypeError):
        fail('Invalid PDF data')
    if (not content or len(content) > MAX_RESUME_BYTES or not content.startswith(b'%PDF-')
            or b'%%EOF' not in content[-1024:]):
        fail('The uploaded file is not a valid PDF within the 5 MiB limit')
    app = rows('SELECT status FROM tt_application WHERE user=%s', (user,))
    if app and app[0].status not in ('Rejected',):
        fail('Resume changes are available before application submission')
    old = rows('SELECT revision FROM tt_resume_evidence WHERE clinician=%s FOR UPDATE', (user,))
    revision = int(old[0].revision) + 1 if old else 1
    frappe.db.sql('''INSERT INTO tt_resume_evidence
        (clinician,filename,content,content_size,content_sha256,revision,uploaded_by,uploaded_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,UTC_TIMESTAMP(6)) ON DUPLICATE KEY UPDATE
        filename=VALUES(filename),content=VALUES(content),content_size=VALUES(content_size),
        content_sha256=VALUES(content_sha256),revision=VALUES(revision),uploaded_by=VALUES(uploaded_by),
        uploaded_at=VALUES(uploaded_at)''',
        (user, filename, content, len(content), hashlib.sha256(content).hexdigest(), revision, user))
    return {'uploaded': True, 'filename': filename, 'size': len(content), 'revision': revision}


@frappe.whitelist(methods=['POST'])
def remove_resume():
    user = _resume_owner()
    app = rows('SELECT status FROM tt_application WHERE user=%s', (user,))
    if app and app[0].status not in ('Rejected',):
        fail('Resume removal is available before application submission')
    frappe.db.sql('DELETE FROM tt_resume_evidence WHERE clinician=%s', (user,))
    return {'removed': True}


@frappe.whitelist()
def download_resume(clinician):
    user = actor()
    if user != clinician and 'Tele Tena Approver' not in frappe.get_roles(user):
        frappe.throw('Resume unavailable', frappe.PermissionError)
    if user == clinician:
        _resume_owner()
    elif not rows('SELECT user FROM tt_application WHERE user=%s', (clinician,)):
        frappe.throw('Resume unavailable', frappe.PermissionError)
    found = rows('SELECT filename,content FROM tt_resume_evidence WHERE clinician=%s', (clinician,))
    if not found:
        frappe.throw('Resume unavailable', frappe.DoesNotExistError)
    frappe.local.response.filename = found[0].filename
    frappe.local.response.filecontent = bytes(found[0].content)
    frappe.local.response.type = 'download'
    frappe.local.response.display_content_as = 'attachment'
