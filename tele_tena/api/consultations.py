"""Appointment-bound LiveKit call authorization and lifecycle commands."""
import secrets
from datetime import datetime, timedelta, timezone

import frappe

from tele_tena.api.journey import actor, fail, iso, one, query


def _minutes(config_key, default, maximum=240):
    try:
        value = int(frappe.conf.get(config_key, default))
    except (TypeError, ValueError):
        value = default
    return max(0, min(maximum, value))


def _authorized_appointment(appointment, allow_completed=False):
    from tele_tena.api.presentation import _authorized
    item,user,role = _authorized(appointment)
    if item.state != 'Booked' and not (allow_completed and item.state == 'Completed'):
        fail('Appointment is not active', 'appointment_inactive')
    return item,user,role


def _window(item):
    early = _minutes('tele_tena_consultation_early_minutes', 15)
    late = _minutes('tele_tena_consultation_late_minutes', 30)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return item.start - timedelta(minutes=early) <= now <= item.end + timedelta(minutes=late)


@query()
def consultation(appointment):
    item, _, role = _authorized_appointment(appointment, allow_completed=True)
    session = frappe.db.sql('SELECT id,state,room_closed FROM tt_consultation WHERE appointment=%s',
                            (item.id,), as_dict=True)
    state = session[0].state if session else 'Not started'
    closed = bool(session and session[0].room_closed)
    from tele_tena.api.couples import ready, plan_for
    note = frappe.db.sql('SELECT status FROM tt_consultation_note WHERE appointment=%s', (item.id,), as_dict=True)
    return {'join_opens_at': iso(item.start - timedelta(minutes=_minutes('tele_tena_consultation_early_minutes', 15))),
            'join_closes_at': iso(item.end + timedelta(minutes=_minutes('tele_tena_consultation_late_minutes', 30))),
            'appointment_state': item.state, 'documentation_state': note[0].status if note else 'None',
            'state': state, 'role': role, 'is_couple':bool(plan_for(item.id)),
            'can_join': item.state == 'Booked' and state != 'Ended' and _window(item) and ready(item.id),
            'can_end': item.state == 'Booked' and role == 'clinician' and (state == 'Open' or (state == 'Ended' and not closed)),
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
        from tele_tena.api.presentation import _authorized
        item,_,_ = _authorized(item.id,lock=True)
        from tele_tena.api.couples import ready
        if not ready(item.id):
            fail('Both adults must have active consent.', 'couple_consent_required')
        if item.state != 'Booked':
            fail('Appointment is not active', 'appointment_inactive')
        if not _window(item):
            fail('Outside the consultation join window', 'outside_join_window')
        session = frappe.db.sql('SELECT * FROM tt_consultation WHERE appointment=%s FOR UPDATE',
                                (item.id,), as_dict=True)
        if not session:
            room_id = secrets.token_urlsafe(27)
            room_name = secrets.token_urlsafe(42)
            from tele_tena.api.couples import plan_for, participant
            patient_identity = participant(item.id,item.patient).room_identity if plan_for(item.id) else secrets.token_urlsafe(32)
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
        from tele_tena.api.couples import plan_for, participant, room_labels
        identity = current.patient_identity if role == 'patient' else current.clinician_identity
        if role == 'patient' and plan_for(item.id):
            identity = participant(item.id,user).room_identity
        from tele_tena.livekit import _credentials, participant_token
        url, _, _ = _credentials()
        token = participant_token(current.room_name, identity, audio_only)
        return {'url': url, 'token': token, 'role': role, 'consultation_id': current.id,
                'audio_only': audio_only, 'participants': room_labels(item.id,user,current.clinician_identity)}
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
    from tele_tena.api.extensions import close_unstarted_extensions
    close_unstarted_extensions(item.id, user)
    if not session or session[0].state != 'Ended':
        if not session:
            fail('Consultation has not started', 'consultation_not_started')
        frappe.db.sql("UPDATE tt_consultation SET state='Ended',ended_by=%s,ended=UTC_TIMESTAMP(6) WHERE appointment=%s",
                      (user, item.id))
    room_name = session[0].room_name
    from tele_tena.api.couples import plan_for, participants
    identities = [session[0].patient_identity, session[0].clinician_identity]
    if plan_for(item.id):
        identities.extend(p.room_identity for p in participants(plan_for(item.id)[0].id))
    identities = list(dict.fromkeys(identities))
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
