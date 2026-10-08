"""Record legacy wallet projection mismatches without rewriting financial history."""
import json

import frappe


def _legacy_projection(patient):
    available = reserved = 0
    events = frappe.db.sql('''SELECT id,kind,amount,reference,created FROM tt_ledger
        WHERE patient=%s ORDER BY created,id''', (patient,), as_dict=True)
    unknown = []
    for event in events:
        amount = int(event.amount)
        if event.kind == 'Deposit':
            available += amount
        elif event.kind == 'Reservation':
            available -= amount
            reserved += amount
        elif event.kind == 'Release':
            reserved -= amount
            available += amount
        elif event.kind == 'Consumption':
            # Explicit completion activity: reserved patient funds were applied
            # to the finalized consultation. The balanced journal remains the
            # authoritative subledger posting.
            reserved -= amount
        elif event.kind == 'Refund':
            # A resolved demo dispute may return clinician earnings to the
            # patient's available wallet. It does not recreate a reservation.
            available += amount
        else:
            unknown.append(event.id)
    return available, reserved, events, unknown


def audit_wallet(patient):
    wallet = frappe.db.sql('SELECT available,reserved FROM tt_wallet WHERE patient=%s',
                           (patient,), as_dict=True)
    if not wallet:
        return None
    legacy_available, legacy_reserved, events, unknown = _legacy_projection(patient)
    opening = frappe.db.sql('SELECT created FROM tt_journal WHERE event_ref=%s',
                            ('opening:' + patient,), as_dict=True)
    boundary = int(frappe.db.sql('''SELECT COUNT(*) FROM tt_ledger
        WHERE patient=%s AND created=%s''', (patient, opening[0].created))[0][0]) if opening else 0
    accounts = frappe.db.sql('''SELECT bucket,balance_minor FROM tt_financial_account
        WHERE owner=%s AND bucket IN ('available','reserved')''', (patient,), as_dict=True)
    subledger = {r.bucket: int(r.balance_minor) for r in accounts}
    actual = {'available': int(wallet[0].available), 'reserved': int(wallet[0].reserved)}
    legacy = {'available': legacy_available, 'reserved': legacy_reserved}
    projected = {bucket: subledger.get(bucket, 0) for bucket in ('available', 'reserved')}
    mismatch = bool(unknown or boundary or legacy != actual or projected != actual or
                    legacy_available < 0 or legacy_reserved < 0)
    audit_id = 'wallet:' + patient
    existing = frappe.db.sql('SELECT * FROM tt_financial_reconciliation WHERE id=%s',
                             (audit_id,), as_dict=True)
    if mismatch and not existing:
        frappe.db.sql('''INSERT INTO tt_financial_reconciliation
            (id,patient,legacy_available,legacy_reserved,wallet_available,wallet_reserved,
             subledger_available,subledger_reserved,event_count,unknown_event_count,boundary_event_count,status,
             reason,created,modified)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'ReviewRequired',%s,UTC_TIMESTAMP(6),UTC_TIMESTAMP(6))''',
            (audit_id, patient, legacy_available, legacy_reserved,
             actual['available'], actual['reserved'], projected['available'], projected['reserved'],
             len(events), len(unknown), boundary, json.dumps({'unknown_event_ids': unknown,
                 'boundary_event_count': boundary,
                 'legacy_diff': {k: actual[k] - legacy[k] for k in actual},
                 'subledger_diff': {k: actual[k] - projected[k] for k in actual}},
                 separators=(',', ':'), sort_keys=True)))
    elif existing:
        # Refresh the visible projection but retain the prior evidence inside
        # the private audit record. Never clear a hold or decision here.
        previous = existing[0]
        previous_snapshot = {
            'observed_at': previous.modified.isoformat() if previous.modified else None,
            'legacy': {'available': int(previous.legacy_available), 'reserved': int(previous.legacy_reserved)},
            'wallet': {'available': int(previous.wallet_available), 'reserved': int(previous.wallet_reserved)},
            'subledger': {'available': int(previous.subledger_available), 'reserved': int(previous.subledger_reserved)},
            'event_count': int(previous.event_count),
            'unknown_event_count': int(previous.unknown_event_count),
            'boundary_event_count': int(previous.boundary_event_count),
            'status': previous.status,
            'reason': previous.reason,
        }
        try:
            prior_reason = json.loads(previous.reason or '{}')
        except (TypeError, ValueError):
            prior_reason = {'preserved_legacy_reason': previous.reason}
        if not isinstance(prior_reason, dict):
            prior_reason = {'preserved_legacy_reason': prior_reason}
        history = prior_reason.get('audit_history', [])
        if not isinstance(history, list):
            history = []
        projection_changed = (previous_snapshot['legacy'] != legacy or
                              previous_snapshot['wallet'] != actual or
                              previous_snapshot['subledger'] != projected or
                              previous_snapshot['event_count'] != len(events) or
                              previous_snapshot['unknown_event_count'] != len(unknown) or
                              previous_snapshot['boundary_event_count'] != boundary)
        if projection_changed:
            history.append(previous_snapshot)
        reason = {'unknown_event_ids': unknown, 'boundary_event_count': boundary,
                  'legacy_diff': {k: actual[k] - legacy[k] for k in actual},
                  'subledger_diff': {k: actual[k] - projected[k] for k in actual},
                  'audit_history': history}
        if projection_changed:
            frappe.db.sql('''UPDATE tt_financial_reconciliation SET legacy_available=%s,legacy_reserved=%s,
                wallet_available=%s,wallet_reserved=%s,subledger_available=%s,subledger_reserved=%s,
                event_count=%s,unknown_event_count=%s,boundary_event_count=%s,reason=%s,
                modified=UTC_TIMESTAMP(6) WHERE id=%s''',
                (legacy_available, legacy_reserved, actual['available'], actual['reserved'],
                 projected['available'], projected['reserved'], len(events), len(unknown), boundary,
                 json.dumps(reason, separators=(',', ':'), sort_keys=True), audit_id))
    return {'matches': not mismatch, 'legacy': legacy, 'wallet': actual,
            'subledger': projected, 'unknown_event_count': len(unknown)}


def execute():
    columns = '''id varchar(180) PRIMARY KEY, patient varchar(140) NOT NULL UNIQUE,
        legacy_available bigint NOT NULL, legacy_reserved bigint NOT NULL,
        wallet_available bigint NOT NULL, wallet_reserved bigint NOT NULL,
        subledger_available bigint NOT NULL, subledger_reserved bigint NOT NULL,
        event_count int NOT NULL, unknown_event_count int NOT NULL,
        boundary_event_count int NOT NULL DEFAULT 0,
        status varchar(32) NOT NULL, reason longtext NOT NULL,
        reviewed_by varchar(140) NULL, decision varchar(40) NULL,
        decision_reason varchar(500) NULL, decided_at datetime(6) NULL,
        created datetime(6) NOT NULL, modified datetime(6) NOT NULL,
        KEY status_created (status,created)'''
    frappe.db.sql_ddl(f'CREATE TABLE IF NOT EXISTS `tt_financial_reconciliation` ({columns}) ENGINE=InnoDB')
    for row in frappe.db.sql('SELECT patient FROM tt_wallet ORDER BY patient', as_dict=True):
        audit_wallet(row.patient)
