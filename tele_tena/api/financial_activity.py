"""Owner-scoped, read-only financial activity details."""
import json
import re

import frappe


UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)


def _unavailable():
    frappe.local.response['tele_tena_error'] = 'transaction_unavailable'
    frappe.throw('Transaction unavailable', frappe.PermissionError)


def _actor_accounts(user, role):
    from tele_tena.accounting import account_id
    if role == 'patient':
        buckets = ('available', 'reserved')
    else:
        buckets = ('pending', 'earnings_available', 'payout_reserved')
    return {bucket: account_id(role, user, bucket) for bucket in buckets}


def _appointment_summary(appointment_id, user):
    if not appointment_id or not UUID_RE.fullmatch(str(appointment_id)):
        return None
    rows = frappe.db.sql('''SELECT id,start,timezone,service_label,state,price,minutes
        FROM tt_appointment WHERE id=%s AND (patient=%s OR clinician=%s)''',
        (appointment_id, user, user), as_dict=True)
    if not rows:
        return None
    item = rows[0]
    item.start = item.start.isoformat() + 'Z'
    return item


def _journal_detail(journal_id, user, role):
    from tele_tena.accounting import BUCKET_SIDE
    accounts = _actor_accounts(user, role)
    rows = frappe.db.sql('''SELECT j.id,j.event_type,j.created,j.metadata
        FROM tt_journal j WHERE j.id=%s AND EXISTS (
          SELECT 1 FROM tt_journal_line l WHERE l.journal_id=j.id AND l.account_id IN %s)''',
        (journal_id, tuple(accounts.values())), as_dict=True)
    if not rows:
        _unavailable()
    journal = rows[0]
    lines = frappe.db.sql('''SELECT a.bucket,l.debit_minor,l.credit_minor
        FROM tt_journal_line l JOIN tt_financial_account a ON a.id=l.account_id
        WHERE l.journal_id=%s AND l.account_id IN %s ORDER BY a.bucket''',
        (journal_id, tuple(accounts.values())), as_dict=True)
    changes = []
    for line in lines:
        if line.bucket not in BUCKET_SIDE:
            continue
        delta = int(line.credit_minor) - int(line.debit_minor)
        if delta:
            changes.append({'bucket': line.bucket, 'delta_minor': delta})
    if not changes:
        _unavailable()
    amount = max(abs(change['delta_minor']) for change in changes)
    try:
        metadata = json.loads(journal.metadata or '{}')
    except (TypeError, ValueError):
        metadata = {}
    appointment = _appointment_summary(metadata.get('appointment'), user)
    event_labels = {
        'Deposit': 'Funds added', 'Reservation': 'Appointment funds reserved',
        'ReservationRelease': 'Appointment reservation released',
        'ConsultationFinalized': 'Consultation completed',
        'EarningReleased': 'Earnings released', 'PayoutRequested': 'Payout requested',
        'PayoutCancelled': 'Payout request cancelled', 'EarningRefunded': 'Refund recorded',
        'ExtensionReservation': 'Extension funds reserved',
        'ExtensionReservationRelease': 'Extension reservation released',
        'ExtensionSettlement': 'Extension completed',
    }
    return {
        'activity_id': 'journal-' + journal.id,
        'kind': event_labels.get(journal.event_type, journal.event_type),
        'created': journal.created.isoformat() + 'Z',
        'amount_minor': amount,
        'currency': 'ETB',
        'state': 'Recorded',
        'account_changes': changes,
        'appointment': appointment,
        'external_transfer': False,
    }


@frappe.whitelist()
def transaction_detail(activity_id):
    """Return one transaction only when its accounts belong to the caller."""
    user = frappe.session.user
    if not isinstance(activity_id, str) or len(activity_id) > 64 or user == 'Guest':
        _unavailable()
    roles = set(frappe.get_roles(user))
    from tele_tena.api.journey import profile

    if 'Tele Tena Patient' in roles:
        profile('patient')
        role = 'patient'
    elif 'Tele Tena Clinician' in roles:
        profile('clinician')
        role = 'clinician'
    else:
        _unavailable()

    prefix, separator, item_id = activity_id.partition('-')
    if not separator or not UUID_RE.fullmatch(item_id):
        _unavailable()
    if prefix == 'log' and role == 'patient':
        rows = frappe.db.sql('''SELECT id,kind,amount,created FROM tt_ledger
            WHERE id=%s AND patient=%s''', (item_id, user), as_dict=True)
        if not rows:
            _unavailable()
        row = rows[0]
        kind = {'Deposit': 'Funds added', 'Reservation': 'Appointment funds reserved',
                'Release': 'Appointment reservation released'}.get(row.kind, row.kind)
        return {'activity_id': 'log-' + row.id, 'kind': kind,
                'created': row.created.isoformat() + 'Z', 'amount_minor': int(row.amount),
                'currency': 'ETB', 'state': 'Recorded', 'account_changes': [],
                'appointment': None, 'source': 'simulation_log', 'external_transfer': False}
    if prefix == 'journal':
        return _journal_detail(item_id, user, role)
    if prefix == 'earning' and role == 'clinician':
        rows = frappe.db.sql('''SELECT e.id,e.appointment,e.gross_minor,e.fee_minor,e.net_minor,
            e.state,e.completed_at,e.release_at,a.start,a.timezone,a.service_label
            FROM tt_earning e JOIN tt_appointment a ON a.id=e.appointment
            WHERE e.id=%s AND e.clinician=%s''', (item_id, user), as_dict=True)
        if not rows:
            _unavailable()
        row = rows[0]
        appointment = _appointment_summary(row.appointment, user)
        return {'activity_id': 'earning-' + row.id, 'kind': 'Consultation earnings',
                'created': (row.completed_at or row.start).isoformat() + 'Z',
                'amount_minor': int(row.net_minor), 'currency': 'ETB', 'state': row.state,
                'gross_minor': int(row.gross_minor), 'fee_minor': int(row.fee_minor),
                'net_minor': int(row.net_minor),
                'release_at': row.release_at.isoformat() + 'Z' if row.release_at else None,
                'appointment': appointment, 'external_transfer': False}
    if prefix == 'payout' and role == 'clinician':
        rows = frappe.db.sql('''SELECT id,amount_minor,state,created,cancelled_at FROM tt_payout
            WHERE id=%s AND clinician=%s''', (item_id, user), as_dict=True)
        if not rows:
            _unavailable()
        row = rows[0]
        return {'activity_id': 'payout-' + row.id, 'kind': 'Payout request',
                'created': row.created.isoformat() + 'Z',
                'amount_minor': int(row.amount_minor), 'currency': 'ETB', 'state': row.state,
                'cancelled_at': row.cancelled_at.isoformat() + 'Z' if row.cancelled_at else None,
                'external_transfer': False}
    _unavailable()
