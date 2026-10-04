"""Add a balanced demonstration subledger without changing legacy balances/events."""
import frappe


TABLES = {
    'financial_account': '''id varchar(100) PRIMARY KEY, owner varchar(140) NOT NULL DEFAULT '',
        bucket varchar(32) NOT NULL, normal_side char(1) NOT NULL,
        balance_minor bigint NOT NULL DEFAULT 0, UNIQUE KEY owner_bucket (owner,bucket),
        CHECK (balance_minor >= 0)''',
    'journal': '''id varchar(36) PRIMARY KEY, event_ref varchar(180) NOT NULL UNIQUE,
        idempotency_key varchar(180) NOT NULL UNIQUE, event_type varchar(32) NOT NULL,
        created datetime(6) NOT NULL, metadata longtext NOT NULL''',
    'journal_line': '''id varchar(36) PRIMARY KEY, journal_id varchar(36) NOT NULL,
        line_no tinyint NOT NULL, account_id varchar(100) NOT NULL,
        debit_minor bigint NOT NULL DEFAULT 0, credit_minor bigint NOT NULL DEFAULT 0,
        UNIQUE KEY journal_line (journal_id,line_no), KEY account_journal (account_id,journal_id),
        CHECK (debit_minor >= 0), CHECK (credit_minor >= 0),
        CHECK ((debit_minor = 0) <> (credit_minor = 0))''',
    'earning': '''id varchar(36) PRIMARY KEY, appointment varchar(36) NOT NULL UNIQUE,
        patient varchar(140) NOT NULL, clinician varchar(140) NOT NULL,
        gross_minor bigint NOT NULL, fee_minor bigint NOT NULL, net_minor bigint NOT NULL,
        policy_snapshot longtext NOT NULL, state varchar(24) NOT NULL,
        completed_at datetime(6) NULL, release_at datetime(6) NULL,
        created datetime(6) NOT NULL, modified datetime(6) NOT NULL,
        KEY clinician_state (clinician,state,release_at)''',
    'dispute': '''id varchar(36) PRIMARY KEY, earning varchar(36) NOT NULL UNIQUE,
        opened_by varchar(140) NOT NULL, reason varchar(500) NOT NULL,
        status varchar(24) NOT NULL, opened_at datetime(6) NOT NULL,
        resolved_by varchar(140) NULL, resolution varchar(24) NULL,
        resolution_reason varchar(500) NULL, resolved_at datetime(6) NULL''',
    'payout': '''id varchar(36) PRIMARY KEY, clinician varchar(140) NOT NULL,
        amount_minor bigint NOT NULL, state varchar(20) NOT NULL,
        idempotency_key varchar(80) NOT NULL, created datetime(6) NOT NULL,
        cancelled_at datetime(6) NULL, UNIQUE KEY clinician_retry (clinician,idempotency_key),
        KEY clinician_state (clinician,state,created)''',
}


def execute():
    for name, columns in TABLES.items():
        frappe.db.sql_ddl(f'CREATE TABLE IF NOT EXISTS `tt_{name}` ({columns}) ENGINE=InnoDB')
    _account('demo:opening-control', '', 'opening_control', 'D')
    _account('demo:cash-clearing', '', 'cash_clearing', 'D')
    # Cut over balances once as a single balanced opening journal per wallet.
    # The pre-existing wallet and simulation log are deliberately untouched.
    for wallet in frappe.db.sql('SELECT patient,available,reserved FROM tt_wallet ORDER BY patient', as_dict=True):
        reference = 'opening:' + wallet.patient
        if frappe.db.sql('SELECT id FROM tt_journal WHERE event_ref=%s', (reference,)):
            continue
        available, reserved = int(wallet.available), int(wallet.reserved)
        if available + reserved == 0:
            continue
        lines = [(f'patient:{wallet.patient}:available', 0, available),
                 (f'patient:{wallet.patient}:reserved', 0, reserved)]
        _insert_journal(reference, reference, 'Opening', lines,
                        {'source': 'v1_7 wallet snapshot', 'patient': wallet.patient})
    # Completed legacy sessions are review holds, never automatic settlements.
    rows = frappe.db.sql('''SELECT a.* FROM tt_appointment a
        JOIN tt_ledger reserve ON reserve.reference=CONCAT('booking:',a.id)
        LEFT JOIN tt_ledger rel ON rel.reference=CONCAT('release:',a.id)
        WHERE a.state='Completed' AND rel.id IS NULL ORDER BY a.id''', as_dict=True)
    for item in rows:
        now = frappe.utils.now_datetime()
        frappe.db.sql('''INSERT IGNORE INTO tt_earning
            (id,appointment,patient,clinician,gross_minor,fee_minor,net_minor,policy_snapshot,
             state,completed_at,release_at,created,modified)
            VALUES (%s,%s,%s,%s,%s,0,%s,%s,'LegacyHold',NULL,NULL,%s,%s)''',
            (frappe.generate_hash(length=32), item.id, item.patient, item.clinician,
             item.price, item.price, '{"version":"legacy-hold-v1","settled":false}', now, now))


def _account(account_id, owner, bucket, normal_side):
    frappe.db.sql('''INSERT IGNORE INTO tt_financial_account
        (id,owner,bucket,normal_side,balance_minor) VALUES (%s,%s,%s,%s,0)''',
        (account_id, owner, bucket, normal_side))


def _insert_journal(reference, idempotency_key, event_type, lines, metadata):
    import json
    import uuid
    total_credit = sum(int(line[2]) for line in lines)
    if sum(int(line[1]) for line in lines) != 0 or total_credit <= 0:
        raise ValueError('Opening snapshot has invalid balance lines')
    journal_id = str(uuid.uuid4())
    frappe.db.sql('''INSERT INTO tt_journal
        (id,event_ref,idempotency_key,event_type,created,metadata)
        VALUES (%s,%s,%s,%s,UTC_TIMESTAMP(6),%s)''',
        (journal_id, reference, idempotency_key, event_type, json.dumps(metadata, separators=(',', ':'))))
    _account('demo:opening-control', '', 'opening_control', 'D')
    line_no = 0
    for account_id, debit, credit in lines:
        if int(debit) == int(credit) == 0:
            continue
        line_no += 1
        owner, bucket = _owner_bucket(account_id)
        side = 'D' if bucket in ('opening_control', 'cash_clearing') else 'C'
        _account(account_id, owner, bucket, side)
        frappe.db.sql('''INSERT INTO tt_journal_line
            (id,journal_id,line_no,account_id,debit_minor,credit_minor)
            VALUES (%s,%s,%s,%s,%s,%s)''',
            (str(uuid.uuid4()), journal_id, line_no, account_id, debit, credit))
        delta = int(debit) - int(credit) if side == 'D' else int(credit) - int(debit)
        frappe.db.sql('UPDATE tt_financial_account SET balance_minor=balance_minor+%s WHERE id=%s',
                      (delta, account_id))
    frappe.db.sql('''INSERT INTO tt_journal_line
        (id,journal_id,line_no,account_id,debit_minor,credit_minor)
        VALUES (%s,%s,%s,'demo:opening-control',%s,0)''',
        (str(uuid.uuid4()), journal_id, line_no + 1, total_credit))
    frappe.db.sql('UPDATE tt_financial_account SET balance_minor=balance_minor+%s WHERE id=%s',
                  (total_credit, 'demo:opening-control'))


def _owner_bucket(account_id):
    parts = account_id.split(':')
    return (parts[1], parts[2]) if len(parts) == 3 else ('', parts[-1])
