"""Appointment-bound LiveKit call authorization and lifecycle commands."""
import secrets
from datetime import datetime, timedelta, timezone

import frappe

from tele_tena.api.journey import actor, fail, one, query


def _minutes(config_key, default, maximum=240):
    try:
        value = int(frappe.conf.get(config_key, default))
    except (TypeError, ValueError):
        value = default
    return max(0, min(maximum, value))


def _authorized_appointment(appointment):
    user = actor()
    found = frappe.db.sql('''SELECT id,patient,clinician,start,end,state
        FROM tt_appointment WHERE id=%s AND (patient=%s OR clinician=%s)''',
        (appointment, user, user), as_dict=True)
    if not found:
        frappe.throw('Appointment unavailable', frappe.PermissionError)
    item = found[0]
    if item.state != 'Booked':
        fail('Appointment is not active', 'appointment_inactive')
    if user == item.patient:
        if 'Tele Tena Patient' not in frappe.get_roles(user):
            frappe.throw('Appointment unavailable', frappe.PermissionError)
        return item, user, 'patient'
    if 'Tele Tena Clinician' not in frappe.get_roles(user):
        frappe.throw('Appointment unavailable', frappe.PermissionError)
    return item, user, 'clinician'


def _window(item):
    early = _minutes('tele_tena_consultation_early_minutes', 15)
    late = _minutes('tele_tena_consultation_late_minutes', 30)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return item.start - timedelta(minutes=early) <= now <= item.end + timedelta(minutes=late)


@query()
def consultation(appointment):
    item, _, role = _authorized_appointment(appointment)
    session = frappe.db.sql('SELECT id,state,room_closed FROM tt_consultation WHERE appointment=%s',
                            (item.id,), as_dict=True)
    state = session[0].state if session else 'Not started'
    closed = bool(session and session[0].room_closed)
    return {'state': state, 'role': role, 'can_join': state != 'Ended' and _window(item),
            'can_end': role == 'clinician' and (state == 'Open' or (state == 'Ended' and not closed)),
            'room_close_pending': state == 'Ended' and not closed}


@frappe.whitelist(methods=['POST'])
def join(appointment, audio_only=0):
    """Return an authorized, short-lived token; never log or persist the token."""
    from tele_tena.api.journey import boolean
    user = actor()
    savepoint = 'tt_join_' + secrets.token_hex(12)
    frappe.db.savepoint(savepoint)
    try:
        item, user, role = _authorized_appointment(appointment)
        if not _window(item):
            fail('Outside the consultation join window', 'outside_join_window')
        audio_only = boolean(audio_only)
        item = one('''SELECT id,patient,clinician,start,end,state FROM tt_appointment
            WHERE id=%s AND (patient=%s OR clinician=%s) FOR UPDATE''', (item.id, user, user))
        if item.state != 'Booked':
            fail('Appointment is not active', 'appointment_inactive')
        if not _window(item):
            fail('Outside the consultation join window', 'outside_join_window')
        session = frappe.db.sql('SELECT * FROM tt_consultation WHERE appointment=%s FOR UPDATE',
                                (item.id,), as_dict=True)
        if not session:
            room_id = secrets.token_urlsafe(27)
            room_name = secrets.token_urlsafe(42)
            patient_identity = secrets.token_urlsafe(32)
            clinician_identity = secrets.token_urlsafe(32)
            frappe.db.sql('''INSERT INTO tt_consultation
                (appointment,id,room_name,patient_identity,clinician_identity,state,created)
                VALUES (%s,%s,%s,%s,%s,'Open',UTC_TIMESTAMP(6))''',
                (item.id, room_id, room_name, patient_identity, clinician_identity))
            session = [frappe._dict(id=room_id, room_name=room_name,
                                    patient_identity=patient_identity,
                                    clinician_identity=clinician_identity, state='Open')]
        current = session[0]
        if current.state != 'Open':
            fail('Consultation has ended', 'consultation_ended')
        identity = current.patient_identity if role == 'patient' else current.clinician_identity
        from tele_tena.livekit import _credentials, participant_token
        url, _, _ = _credentials()
        token = participant_token(current.room_name, identity, audio_only)
        return {'url': url, 'token': token, 'role': role, 'consultation_id': current.id,
                'audio_only': audio_only}
    except (frappe.PermissionError, frappe.ValidationError):
        frappe.db.rollback(save_point=savepoint)
        raise
    except Exception:
        frappe.db.rollback(save_point=savepoint)
        frappe.local.response['tele_tena_error'] = 'consultation_unavailable'
        frappe.throw('Unable to prepare the consultation; check local LiveKit configuration')


@frappe.whitelist(methods=['POST'])
def end(appointment):
    """Serialize against Join, persist Ended, revoke both Cloud identities, close the room."""
    item, user, role = _authorized_appointment(appointment)
    if role != 'clinician':
        frappe.throw('Only the appointment clinician can end the consultation', frappe.PermissionError)
    # Join takes this same lock first, so no token can be minted concurrently
    # after the End transition has committed.
    item = one('''SELECT id,patient,clinician,state FROM tt_appointment
        WHERE id=%s AND (patient=%s OR clinician=%s) FOR UPDATE''', (item.id, user, user))
    if item.state != 'Booked':
        fail('Appointment is not active', 'appointment_inactive')
    session = frappe.db.sql('SELECT * FROM tt_consultation WHERE appointment=%s FOR UPDATE',
                            (item.id,), as_dict=True)
    if not session or session[0].state != 'Ended':
        if not session:
            fail('Consultation has not started', 'consultation_not_started')
        frappe.db.sql("UPDATE tt_consultation SET state='Ended',ended_by=%s,ended=UTC_TIMESTAMP(6) WHERE appointment=%s",
                      (user, item.id))
    room_name = session[0].room_name
    identities = (session[0].patient_identity, session[0].clinician_identity)
    # The committed ended state denies new application tokens even if Cloud
    # revocation or room closure fails; repeated End retries both operations.
    frappe.db.commit()
    from tele_tena.livekit import close_room
    try:
        close_room(room_name, identities)
    except Exception:
        frappe.throw('Consultation ended; room closure is pending. Retry ending to confirm closure',
                     frappe.ValidationError)
    frappe.db.sql('UPDATE tt_consultation SET room_closed=1 WHERE appointment=%s', (item.id,))
    return {'state': 'Ended'}
