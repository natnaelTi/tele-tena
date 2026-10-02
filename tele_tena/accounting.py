"""Balanced, immutable demonstration postings; never calls an external provider."""
import json
import uuid
from datetime import datetime, timezone

import frappe


BUCKET_SIDE = {
    'opening_control': 'D', 'cash_clearing': 'D',
    'available': 'C', 'reserved': 'C', 'pending': 'C',
    'earnings_available': 'C', 'payout_reserved': 'C',
    'platform_fee_revenue': 'C',
}


def account_id(kind, owner, bucket):
    return f'{kind}:{owner}:{bucket}' if owner else f'demo:{bucket}'


def _ensure(account, owner, bucket):
    side = BUCKET_SIDE[bucket]
    frappe.db.sql('''INSERT IGNORE INTO tt_financial_account
        (id,owner,bucket,normal_side,balance_minor) VALUES (%s,%s,%s,%s,0)''',
        (account, owner or '', bucket, side))


def post(event_ref, event_type, idempotency_key, entries, metadata=None):
    """Post balanced (account_id, debit, credit) lines once under caller transaction."""
    raw = [(str(a), int(d), int(c)) for a, d, c in entries if int(d) or int(c)]
    if not raw or any(d < 0 or c < 0 or bool(d) == bool(c) for _, d, c in raw):
        frappe.throw('Invalid financial posting', frappe.ValidationError)
    canonical = []
    for account, debit, credit in raw:
        parts = account.split(':', 2)
        if len(parts) == 3 and parts[0] in ('patient', 'clinician'):
            _, owner, bucket = parts
        else:
            owner, bucket = '', parts[-1].replace('-', '_')
        if bucket not in BUCKET_SIDE:
            frappe.throw('Invalid financial account', frappe.ValidationError)
        _ensure(account, owner, bucket)
        # A regular SELECT can reuse a repeatable-read snapshot established by
        # account/profile authorization earlier in the request. During a
        # concurrent first posting, that snapshot may predate the account's
        # creation even though INSERT IGNORE has waited for the competing
        # transaction. Locking read observes the committed canonical account.
        found = frappe.db.sql('SELECT id FROM tt_financial_account WHERE owner=%s AND bucket=%s FOR UPDATE',
                              (owner, bucket), as_dict=True)
        canonical.append((found[0].id, debit, credit))
    normalized = sorted(canonical)
    if sum(d for _, d, _ in normalized) != sum(c for _, _, c in normalized):
        frappe.throw('Financial posting is unbalanced', frappe.ValidationError)
    existing = frappe.db.sql('SELECT id FROM tt_journal WHERE event_ref=%s OR idempotency_key=%s',
                             (event_ref, idempotency_key), as_dict=True)
    if existing:
        if len(existing) != 1:
            frappe.throw('Financial retry reference conflict', frappe.ValidationError)
        old = frappe.db.sql('''SELECT account_id,debit_minor,credit_minor FROM tt_journal_line
            WHERE journal_id=%s ORDER BY account_id,debit_minor,credit_minor''',
            (existing[0].id,), as_dict=True)
        if [(x.account_id, int(x.debit_minor), int(x.credit_minor)) for x in old] != normalized:
            frappe.local.response['tele_tena_error'] = 'financial_retry_changed'
            frappe.throw('Financial retry payload changed', frappe.ValidationError)
        return existing[0].id, True

    account_ids = sorted({a for a, _, _ in normalized})
    accounts = frappe.db.sql('''SELECT id,normal_side,balance_minor FROM tt_financial_account
        WHERE id IN %s ORDER BY id FOR UPDATE''', (tuple(account_ids),), as_dict=True)
    by_id = {row.id: row for row in accounts}
    updates = {}
    for account, debit, credit in normalized:
        side = by_id[account].normal_side
        updates[account] = int(updates.get(account, 0)) + (debit-credit if side == 'D' else credit-debit)
    for account, delta in updates.items():
        if int(by_id[account].balance_minor) + delta < 0:
            frappe.local.response['tele_tena_error'] = 'financial_balance_insufficient'
            frappe.throw('Financial balance is insufficient for this action', frappe.ValidationError)

    journal_id = str(uuid.uuid4())
    frappe.db.sql('''INSERT INTO tt_journal
        (id,event_ref,idempotency_key,event_type,created,metadata)
        VALUES (%s,%s,%s,%s,UTC_TIMESTAMP(6),%s)''',
        (journal_id, event_ref, idempotency_key, event_type,
         json.dumps(metadata or {}, separators=(',', ':'), sort_keys=True)))
    for line_no, (account, debit, credit) in enumerate(normalized, 1):
        frappe.db.sql('''INSERT INTO tt_journal_line
            (id,journal_id,line_no,account_id,debit_minor,credit_minor)
            VALUES (%s,%s,%s,%s,%s,%s)''',
            (str(uuid.uuid4()), journal_id, line_no, account, debit, credit))
    for account, delta in updates.items():
        frappe.db.sql('UPDATE tt_financial_account SET balance_minor=balance_minor+%s WHERE id=%s',
                      (delta, account))
    return journal_id, False


def balance(kind, owner, bucket):
    account = account_id(kind, owner, bucket)
    row = frappe.db.sql('SELECT balance_minor FROM tt_financial_account WHERE id=%s',
                        (account,), as_dict=True)
    return int(row[0].balance_minor) if row else 0


def check_wallet_projection(patient, wallet):
    if balance('patient', patient, 'available') != int(wallet.available) or balance('patient', patient, 'reserved') != int(wallet.reserved):
        frappe.local.response['tele_tena_error'] = 'financial_reconciliation_required'
        frappe.throw('Balance needs authorized reconciliation before this action', frappe.ValidationError)


def totals(kind, owner, buckets):
    return {bucket: balance(kind, owner, bucket) for bucket in buckets}


def _event_rows(account_ids, limit=100):
    return frappe.db.sql('''SELECT j.event_ref,j.event_type,j.created,
        MAX(GREATEST(l.debit_minor,l.credit_minor)) amount
        FROM tt_journal j JOIN tt_journal_line l ON l.journal_id=j.id
        WHERE l.account_id IN %s AND j.event_type<>'Opening'
        GROUP BY j.id,j.event_ref,j.event_type,j.created ORDER BY j.created DESC,j.id DESC LIMIT %s''',
        (tuple(account_ids), limit), as_dict=True)


@frappe.whitelist()
def clinician_earnings():
    clinician = frappe.session.user
    if clinician == 'Guest' or 'Tele Tena Clinician' not in frappe.get_roles(clinician):
        frappe.throw('Clinician account required', frappe.PermissionError)
    from tele_tena.api.journey import profile
    profile('clinician')
    buckets = ('pending', 'earnings_available', 'payout_reserved')
    balances = totals('clinician', clinician, buckets)
    earnings = frappe.db.sql('''SELECT id,appointment,gross_minor,fee_minor,net_minor,state,
        completed_at,release_at FROM tt_earning WHERE clinician=%s ORDER BY created DESC LIMIT 100''',
        (clinician,), as_dict=True)
    payouts = frappe.db.sql('''SELECT id,amount_minor,state,created,cancelled_at FROM tt_payout
        WHERE clinician=%s ORDER BY created DESC LIMIT 100''', (clinician,), as_dict=True)
    for item in earnings + payouts:
        for key in ('completed_at', 'release_at', 'created', 'cancelled_at'):
            if item.get(key):
                item[key] = item[key].isoformat() + 'Z'
    account_ids = [account_id('clinician', clinician, bucket) for bucket in buckets]
    activity = _event_rows(account_ids)
    for item in activity:
        item.created = item.created.isoformat() + 'Z'
    return {'balances': balances, 'earnings': earnings, 'payouts': payouts, 'activity': activity,
            'external_settlement': False}


@frappe.whitelist(methods=['POST'])
def request_payout(amount_minor, idempotency_key):
    clinician = frappe.session.user
    if clinician == 'Guest' or 'Tele Tena Clinician' not in frappe.get_roles(clinician):
        frappe.throw('Clinician account required', frappe.PermissionError)
    from tele_tena.api.journey import integer, profile, text
    profile('clinician')
    amount = integer(amount_minor, 1, 100000000)
    key = text(idempotency_key, 80)
    frappe.db.sql('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    old = frappe.db.sql('''SELECT * FROM tt_payout WHERE clinician=%s AND idempotency_key=%s FOR UPDATE''',
                        (clinician, key), as_dict=True)
    if old:
        if int(old[0].amount_minor) != amount:
            frappe.local.response['tele_tena_error'] = 'financial_retry_changed'
            frappe.throw('Payout retry amount changed', frappe.ValidationError)
        return {'id': old[0].id, 'state': old[0].state, 'idempotent': True, 'external_transfer': False}
    payout_id = str(uuid.uuid4())
    reference = 'payout-request:' + payout_id
    from_account = account_id('clinician', clinician, 'earnings_available')
    to_account = account_id('clinician', clinician, 'payout_reserved')
    post(reference, 'PayoutRequested', reference,
         [(from_account, amount, 0), (to_account, 0, amount)], {'payout': payout_id})
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    frappe.db.sql('''INSERT INTO tt_payout
        (id,clinician,amount_minor,state,idempotency_key,created)
        VALUES (%s,%s,%s,'Requested',%s,%s)''', (payout_id, clinician, amount, key, now))
    return {'id': payout_id, 'state': 'Requested', 'external_transfer': False}


@frappe.whitelist(methods=['POST'])
def cancel_payout(payout, reason):
    clinician = frappe.session.user
    if clinician == 'Guest' or 'Tele Tena Clinician' not in frappe.get_roles(clinician):
        frappe.throw('Clinician account required', frappe.PermissionError)
    from tele_tena.api.journey import profile, text
    profile('clinician')
    reason = text(reason, 500, required=False)
    frappe.db.sql('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    result = frappe.db.sql('SELECT * FROM tt_payout WHERE id=%s AND clinician=%s FOR UPDATE',
                           (payout, clinician), as_dict=True)
    if not result:
        frappe.throw('Payout request unavailable', frappe.PermissionError)
    item = result[0]
    if item.state == 'Cancelled':
        return {'id': item.id, 'state': item.state, 'idempotent': True}
    if item.state != 'Requested':
        frappe.local.response['tele_tena_error'] = 'payout_cannot_cancel'
        frappe.throw('This payout request can no longer be cancelled', frappe.ValidationError)
    reference = 'payout-cancel:' + item.id
    post(reference, 'PayoutCancelled', reference,
         [(account_id('clinician', clinician, 'payout_reserved'), int(item.amount_minor), 0),
          (account_id('clinician', clinician, 'earnings_available'), 0, int(item.amount_minor))],
         {'payout': item.id, 'reason': reason})
    frappe.db.sql("UPDATE tt_payout SET state='Cancelled',cancelled_at=UTC_TIMESTAMP(6) WHERE id=%s", (item.id,))
    return {'id': item.id, 'state': 'Cancelled'}


@frappe.whitelist(methods=['POST'])
def open_earning_dispute(appointment, reason):
    patient = frappe.session.user
    if patient == 'Guest' or 'Tele Tena Patient' not in frappe.get_roles(patient):
        frappe.throw('Patient account required', frappe.PermissionError)
    from tele_tena.api.journey import profile, text
    profile('patient')
    reason = text(reason, 500)
    frappe.db.sql('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    earning = frappe.db.sql('''SELECT * FROM tt_earning WHERE appointment=%s AND patient=%s FOR UPDATE''',
                            (appointment, patient), as_dict=True)
    if not earning:
        frappe.throw('Earning record unavailable', frappe.PermissionError)
    item = earning[0]
    if item.state == 'Disputed':
        return {'state': 'Disputed', 'idempotent': True}
    if item.state != 'Pending' or not item.release_at or item.release_at <= datetime.now(timezone.utc).replace(tzinfo=None):
        frappe.local.response['tele_tena_error'] = 'dispute_window_closed'
        frappe.throw('This earning is outside the supported demonstration dispute window', frappe.ValidationError)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    dispute_id = str(uuid.uuid4())
    frappe.db.sql('''INSERT INTO tt_dispute
        (id,earning,opened_by,reason,status,opened_at)
        VALUES (%s,%s,%s,%s,'Open',%s)''', (dispute_id, item.id, patient, reason, now))
    frappe.db.sql("UPDATE tt_earning SET state='Disputed',modified=%s WHERE id=%s", (now, item.id))
    return {'id': dispute_id, 'state': 'Disputed'}


@frappe.whitelist(methods=['POST'])
def resolve_earning_dispute(appointment, resolution, reason):
    reviewer = frappe.session.user
    if reviewer == 'Guest' or 'Tele Tena Approver' not in frappe.get_roles(reviewer):
        frappe.throw('Authorized financial reviewer required', frappe.PermissionError)
    if resolution not in ('release', 'refund'):
        frappe.throw('Choose release or refund', frappe.ValidationError)
    from tele_tena.api.journey import text
    reason = text(reason, 500)
    frappe.db.sql('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    records = frappe.db.sql('''SELECT e.*,d.id dispute_id,d.status dispute_status FROM tt_earning e
        JOIN tt_dispute d ON d.earning=e.id WHERE e.appointment=%s FOR UPDATE''',
        (appointment,), as_dict=True)
    if not records:
        frappe.throw('Financial dispute unavailable', frappe.PermissionError)
    item = records[0]
    if item.dispute_status != 'Open' or item.state != 'Disputed':
        return {'state': item.state, 'idempotent': True}
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if resolution == 'release':
        frappe.db.sql("UPDATE tt_earning SET state='Pending',release_at=%s,modified=%s WHERE id=%s", (now, now, item.id))
    else:
        amount = int(item.net_minor)
        post('earning-refund:' + item.id, 'EarningRefunded', 'earning-refund:' + item.id,
             [(account_id('clinician', item.clinician, 'pending'), amount, 0),
              (account_id('patient', item.patient, 'available'), 0, amount)],
             {'appointment': item.appointment, 'dispute': item.dispute_id})
        frappe.db.sql('UPDATE tt_wallet SET available=available+%s WHERE patient=%s', (amount, item.patient))
        frappe.db.sql("UPDATE tt_earning SET state='Refunded',modified=%s WHERE id=%s", (now, item.id))
    frappe.db.sql('''UPDATE tt_dispute SET status='Resolved',resolved_by=%s,resolution=%s,
        resolution_reason=%s,resolved_at=%s WHERE id=%s''',
        (reviewer, resolution.title(), reason, now, item.dispute_id))
    return {'state': 'Resolved', 'resolution': resolution}


@frappe.whitelist()
def open_disputes():
    reviewer = frappe.session.user
    if reviewer == 'Guest' or 'Tele Tena Approver' not in frappe.get_roles(reviewer):
        frappe.throw('Authorized financial reviewer required', frappe.PermissionError)
    return frappe.db.sql('''SELECT e.id earning_id,e.appointment,e.net_minor,e.state,
        d.reason,d.opened_at FROM tt_earning e JOIN tt_dispute d ON d.earning=e.id
        WHERE d.status='Open' AND e.state='Disputed' ORDER BY d.opened_at LIMIT 100''', as_dict=True)


def release_eligible_earnings():
    """Retry-safe simulated release; no banking or ERPNext provider is invoked."""
    candidates = frappe.db.sql("""SELECT appointment FROM tt_earning
        WHERE state='Pending' AND release_at<=UTC_TIMESTAMP(6) ORDER BY release_at LIMIT 100""",
        as_dict=True)
    for candidate in candidates:
        frappe.db.sql('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
        rows = frappe.db.sql('SELECT * FROM tt_earning WHERE appointment=%s FOR UPDATE',
                             (candidate.appointment,), as_dict=True)
        if not rows or rows[0].state != 'Pending' or rows[0].release_at > datetime.now(timezone.utc).replace(tzinfo=None):
            continue
        item = rows[0]
        reference = 'earning-release:' + item.id
        amount = int(item.net_minor)
        post(reference, 'EarningReleased', reference,
             [(account_id('clinician', item.clinician, 'pending'), amount, 0),
              (account_id('clinician', item.clinician, 'earnings_available'), 0, amount)],
             {'appointment': item.appointment})
        frappe.db.sql("UPDATE tt_earning SET state='Released',modified=UTC_TIMESTAMP(6) WHERE id=%s", (item.id,))
        frappe.db.commit()
