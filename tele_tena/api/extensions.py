"""Explicit, prefunded consultation extensions using the existing subledger."""
import json
import uuid
from datetime import datetime, timedelta, timezone

import frappe

from tele_tena.api.journey import actor, approved_service, command, fail, integer, one, query, rows, text
from tele_tena.api.presentation import _authorized, _event


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _block_policy(item):
    duration = integer(frappe.conf.get('tele_tena_demo_extension_block_minutes', 15), 1, 60)
    maximum = integer(frappe.conf.get('tele_tena_demo_extension_max_minutes', 60), duration, 240)
    expiry_minutes = integer(frappe.conf.get('tele_tena_demo_extension_offer_minutes', 10), 1, 60)
    # Published ETB price is prorated with integer ceiling; no binary floats or
    # undisclosed fee. The exact result is snapshotted on the proposed block.
    amount = (int(item.price) * duration + int(item.minutes) - 1) // int(item.minutes)
    if amount <= 0:
        fail('This offering cannot be extended under the current price policy.', 'extension_policy_invalid')
    return duration, amount, maximum, expiry_minutes


def _is_participant_open(item, user, role):
    if item.state != 'Booked':
        fail('An extension is available only during a confirmed consultation.', 'extension_appointment_inactive')
    call = rows('SELECT state FROM tt_consultation WHERE appointment=%s', (item.id,))
    if not call or call[0].state != 'Open':
        fail('The consultation is not open for an extension.', 'extension_call_inactive')
    if role == 'clinician' and item.clinician == user:
        service = one('SELECT service FROM tt_offering WHERE id=%s', (item.offering,))
        approved_service(item.clinician, service.service)
    return call[0]


def _lines_for_reservation(patient, amount):
    from tele_tena.accounting import account_id
    return [(account_id('patient', patient, 'available'), amount, 0),
            (account_id('patient', patient, 'reserved'), 0, amount)]


def _release(extension, actor_user, reason):
    if extension.state != 'Accepted':
        return False
    wallet = one('SELECT available,reserved FROM tt_wallet WHERE patient=%s FOR UPDATE', (extension.patient,))
    amount = int(extension.amount_minor)
    if int(wallet.reserved) < amount:
        fail('The extension reservation needs financial review.', 'extension_reservation_inconsistent')
    from tele_tena.accounting import account_id, check_wallet_projection, post
    from tele_tena.api.journey import simulation_log
    check_wallet_projection(extension.patient, wallet)
    reference = 'extension-release:' + extension.id
    if rows('SELECT id FROM tt_ledger WHERE reference=%s', (reference,)):
        return False
    frappe.db.sql('UPDATE tt_wallet SET available=available+%s,reserved=reserved-%s WHERE patient=%s',
                  (amount, amount, extension.patient))
    simulation_log(extension.patient, 'Release', amount, reference)
    post(reference, 'ExtensionReservationRelease', reference, [
        (account_id('patient', extension.patient, 'reserved'), amount, 0),
        (account_id('patient', extension.patient, 'available'), 0, amount)],
        {'appointment': extension.appointment, 'extension': extension.id, 'reason': reason})
    frappe.db.sql("UPDATE tt_consultation_extension SET state='Released',closed_at=UTC_TIMESTAMP(6) WHERE id=%s AND state='Accepted'",
                  (extension.id,))
    _event(extension.appointment, 'ExtensionReleased', actor_user, reason)
    return True


@query()
def extension_status(appointment):
    item, user, role = _authorized(appointment)
    result = rows('''SELECT id,IF(state='Proposed' AND expires_at<=UTC_TIMESTAMP(6),'Expired',state) state,
        duration_minutes,amount_minor,expires_at,proposed_at,
        start_after,accepted_at,started_at,closed_at FROM tt_consultation_extension
        WHERE appointment=%s ORDER BY proposed_at''', (item.id,))
    return {'items': result, 'can_propose': role == 'clinician' and item.state == 'Booked',
            'can_accept': role == 'patient' and item.state == 'Booked',
            'currency': 'ETB'}


@command
def propose_extension(appointment, retry_key):
    clinician = actor('Tele Tena Clinician')
    key = text(retry_key, 80)
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    item, _, role = _authorized(appointment, True)
    if role != 'clinician' or item.clinician != clinician:
        frappe.throw('Consultation unavailable', frappe.PermissionError)
    previous = rows('SELECT id,state,duration_minutes,amount_minor,expires_at FROM tt_consultation_extension WHERE appointment=%s AND retry_key=%s',
                    (item.id, key))
    if previous:
        row = previous[0]
        return {'id': row.id, 'state': row.state, 'duration_minutes': int(row.duration_minutes),
                'amount_minor': int(row.amount_minor), 'expires_at': row.expires_at, 'idempotent': True}
    _is_participant_open(item, clinician, role)
    stale = rows("""SELECT id FROM tt_consultation_extension WHERE appointment=%s
        AND state='Proposed' AND expires_at<=UTC_TIMESTAMP(6) FOR UPDATE""", (item.id,))
    for extension in stale:
        frappe.db.sql("UPDATE tt_consultation_extension SET state='Expired',closed_at=UTC_TIMESTAMP(6) WHERE id=%s AND state='Proposed'",
                      (extension.id,))
        _event(item.id, 'ExtensionExpired', 'System')
    current = rows("""SELECT id,state,duration_minutes,amount_minor,expires_at FROM tt_consultation_extension
        WHERE appointment=%s AND state IN ('Proposed','Accepted') ORDER BY proposed_at DESC LIMIT 1 FOR UPDATE""",
        (item.id,))
    if current:
        # The command has no client-controlled pricing or duration payload.
        # Return the existing unresolved proposal so a retry with a lost or
        # regenerated key cannot create a duplicate or strand the clinician.
        row = current[0]
        return {'id': row.id, 'state': row.state, 'duration_minutes': int(row.duration_minutes),
                'amount_minor': int(row.amount_minor), 'expires_at': row.expires_at, 'idempotent': True}
    duration, amount, maximum, expiry_minutes = _block_policy(item)
    previous_minutes = one("SELECT COALESCE(SUM(duration_minutes),0) AS minutes FROM tt_consultation_extension WHERE appointment=%s AND state IN ('Started','Settled')",
                           (item.id,))
    if int(previous_minutes.minutes) + duration > maximum:
        fail('The demonstration extension limit has been reached.', 'extension_limit_reached')
    now = _now()
    expiry = now + timedelta(minutes=expiry_minutes)
    policy = {'version': 'demo-extension-v1', 'block_minutes': duration,
              'pricing': 'ceil(published_price_minor * block_minutes / booked_minutes)',
              'max_added_minutes': maximum, 'external_settlement': False}
    extension = str(uuid.uuid4())
    price_snapshot = {'published_price_minor': int(item.price), 'booked_minutes': int(item.minutes),
                      'amount_minor': amount, 'currency': 'ETB'}
    frappe.db.sql('''INSERT INTO tt_consultation_extension
        (id,appointment,patient,clinician,retry_key,state,duration_minutes,amount_minor,
         price_snapshot,policy_snapshot,start_after,expires_at,proposed_at)
        VALUES (%s,%s,%s,%s,%s,'Proposed',%s,%s,%s,%s,%s,%s,%s)''',
        (extension, item.id, item.patient, item.clinician, key, duration, amount,
         json.dumps(price_snapshot, separators=(',', ':'), sort_keys=True),
         json.dumps(policy, separators=(',', ':'), sort_keys=True), item.end, expiry, now))
    _event(item.id, 'ExtensionProposed', clinician)
    return {'id': extension, 'state': 'Proposed', 'duration_minutes': duration,
            'amount_minor': amount, 'expires_at': expiry, 'idempotent': False}


@command
def respond_extension(appointment, extension_id, decision):
    patient = actor('Tele Tena Patient')
    if decision not in ('accept', 'decline'):
        fail('Choose accept or decline.')
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    item, _, role = _authorized(appointment, True)
    if role != 'patient' or item.patient != patient:
        frappe.throw('Consultation unavailable', frappe.PermissionError)
    _is_participant_open(item, patient, role)
    extension = one('''SELECT * FROM tt_consultation_extension
        WHERE id=%s AND appointment=%s AND patient=%s FOR UPDATE''',
        (extension_id, item.id, patient))
    if extension.state == 'Accepted' and decision == 'accept':
        return {'state': 'Accepted', 'idempotent': True}
    if extension.state != 'Proposed':
        fail('This extension offer is no longer available.', 'extension_offer_unavailable')
    now = _now()
    if extension.expires_at <= now:
        frappe.db.sql("UPDATE tt_consultation_extension SET state='Expired',closed_at=%s WHERE id=%s",
                      (now, extension.id))
        _event(item.id, 'ExtensionExpired', 'System')
        return {'state': 'Expired'}
    if decision == 'decline':
        frappe.db.sql("UPDATE tt_consultation_extension SET state='Declined',closed_at=%s WHERE id=%s",
                      (now, extension.id))
        _event(item.id, 'ExtensionDeclined', patient)
        return {'state': 'Declined'}
    new_end = item.end + timedelta(minutes=int(extension.duration_minutes))
    conflicts = rows('''SELECT id FROM tt_appointment WHERE clinician=%s AND id<>%s
        AND state IN ('Booked','PendingConfirmation') AND start<%s AND end>%s FOR UPDATE''',
        (item.clinician, item.id, new_end + timedelta(minutes=int(item.buffer_after or 0)), item.end))
    if conflicts:
        fail('That added time conflicts with another appointment. Ask the clinician about another option.',
             'extension_time_unavailable')
    wallet = one('SELECT available,reserved FROM tt_wallet WHERE patient=%s FOR UPDATE', (patient,))
    amount = int(extension.amount_minor)
    if int(wallet.available) < amount:
        shortfall_minor = amount - int(wallet.available)
        shortfall_etb = f'{shortfall_minor // 100}.{shortfall_minor % 100:02d}'
        fail(f'Add ETB {shortfall_etb} to your balance, then retry while this offer is available.',
             'extension_insufficient_funds')
    from tele_tena.accounting import check_wallet_projection, post
    from tele_tena.api.journey import simulation_log
    check_wallet_projection(patient, wallet)
    reference = 'extension-reserve:' + extension.id
    frappe.db.sql('UPDATE tt_wallet SET available=available-%s,reserved=reserved+%s WHERE patient=%s',
                  (amount, amount, patient))
    simulation_log(patient, 'Reservation', amount, reference)
    post(reference, 'ExtensionReservation', reference, _lines_for_reservation(patient, amount),
         {'appointment': item.id, 'extension': extension.id, 'simulated': True})
    frappe.db.sql("UPDATE tt_consultation_extension SET state='Accepted',accepted_at=%s WHERE id=%s AND state='Proposed'",
                  (now, extension.id))
    frappe.db.sql('UPDATE tt_appointment SET end=%s WHERE id=%s', (new_end, item.id))
    _event(item.id, 'ExtensionAccepted', patient)
    return {'state': 'Accepted', 'amount_minor': amount,
            'effective_end': new_end, 'idempotent': False}


@command
def withdraw_extension(appointment, extension_id):
    clinician = actor('Tele Tena Clinician')
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    item, _, role = _authorized(appointment, True)
    if role != 'clinician' or item.clinician != clinician:
        frappe.throw('Consultation unavailable', frappe.PermissionError)
    extension = one('''SELECT * FROM tt_consultation_extension WHERE id=%s
        AND appointment=%s AND clinician=%s FOR UPDATE''',
        (extension_id, item.id, clinician))
    if extension.state == 'Withdrawn':
        return {'state': 'Withdrawn', 'idempotent': True}
    if extension.state != 'Proposed':
        fail('Only an unanswered extension offer can be withdrawn.', 'extension_withdraw_unavailable')
    frappe.db.sql("UPDATE tt_consultation_extension SET state='Withdrawn',closed_at=UTC_TIMESTAMP(6) WHERE id=%s",
                  (extension.id,))
    _event(item.id, 'ExtensionWithdrawn', clinician)
    return {'state': 'Withdrawn', 'idempotent': False}


@command
def start_extension(appointment, extension_id):
    clinician = actor('Tele Tena Clinician')
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    item, _, role = _authorized(appointment, True)
    if role != 'clinician' or item.clinician != clinician:
        frappe.throw('Consultation unavailable', frappe.PermissionError)
    call = _is_participant_open(item, clinician, role)
    extension = one('''SELECT * FROM tt_consultation_extension WHERE id=%s
        AND appointment=%s AND clinician=%s FOR UPDATE''',
        (extension_id, item.id, clinician))
    if extension.state == 'Started':
        return {'state': 'Started', 'idempotent': True}
    if extension.state != 'Accepted':
        fail('The patient must accept and fund the extension before it can start.',
             'extension_not_accepted')
    now = _now()
    if extension.start_after > now:
        fail('The agreed extension block has not started yet.', 'extension_not_due')
    if call.state != 'Open':
        fail('The consultation has ended.', 'extension_call_inactive')
    frappe.db.sql("UPDATE tt_consultation_extension SET state='Started',started_at=%s WHERE id=%s AND state='Accepted'",
                  (now, extension.id))
    _event(item.id, 'ExtensionStarted', clinician)
    return {'state': 'Started', 'idempotent': False}


def close_unstarted_extensions(appointment, clinician):
    """Called inside the End transaction; release every accepted unstarted block."""
    items = rows('''SELECT * FROM tt_consultation_extension WHERE appointment=%s
        AND state IN ('Proposed','Accepted') ORDER BY proposed_at FOR UPDATE''', (appointment,))
    for extension in items:
        if extension.state == 'Accepted':
            _release(extension, clinician, 'consultation ended before the extension started')
            frappe.db.sql('UPDATE tt_appointment SET end=%s WHERE id=%s',
                          (extension.start_after, appointment))
        else:
            frappe.db.sql("UPDATE tt_consultation_extension SET state='Withdrawn',closed_at=UTC_TIMESTAMP(6) WHERE id=%s",
                          (extension.id,))
            _event(appointment, 'ExtensionWithdrawn', clinician, 'consultation ended')


def expire_extensions():
    """Scheduler transition for expired, unanswered extension offers."""
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    items = rows("""SELECT id,appointment FROM tt_consultation_extension
        WHERE state='Proposed' AND expires_at<=UTC_TIMESTAMP(6)
        ORDER BY expires_at LIMIT 200 FOR UPDATE""")
    now = _now()
    for item in items:
        frappe.db.sql("""UPDATE tt_consultation_extension SET state='Expired',closed_at=%s
            WHERE id=%s AND state='Proposed' AND expires_at<=%s""", (now, item.id, now))
        _event(item.appointment, 'ExtensionExpired', 'System')
