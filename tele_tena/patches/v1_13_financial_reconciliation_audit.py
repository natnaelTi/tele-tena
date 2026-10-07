"""Record legacy wallet projection mismatches without rewriting financial history."""
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
    existing = frappe.db.sql('SELECT id FROM tt_financial_reconciliation WHERE id=%s',
                             (audit_id,))
    if mismatch and not existing:
        import json
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
        # Do not erase a previous exception or overwrite an authorized decision.
        # The latest projection is checked on each operation; the row is an audit anchor.
        pass
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
