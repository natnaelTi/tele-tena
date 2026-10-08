"""Verify additive upgrade and repeat migration without exposing stored content."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import frappe
from tele_tena.schema import TABLES, PHONE_AUTH_TABLES
from tele_tena.patches.v1_6_presentation_release import TABLES as PRESENTATION_TABLES
from tele_tena.patches.v1_7_demo_subledger import TABLES as FINANCIAL_TABLES

BENCH = Path(__file__).resolve().parents[3]
SITE = os.environ.get('TELE_TENA_TEST_SITE')
assert SITE and SITE.endswith('.localhost') and SITE.startswith(('tele-tena-', 'teletena-')), \
    'Set TELE_TENA_TEST_SITE to a disposable TeleTena site; development sites are refused'
os.chdir(BENCH / 'sites')


def snapshot(include_legacy_activity=True):
    frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
    frappe.connect()
    result = {}
    existing_tables = set(frappe.db.get_tables(cached=False))
    for table in (*TABLES, *PHONE_AUTH_TABLES, *PRESENTATION_TABLES, *FINANCIAL_TABLES,
                  'financial_reconciliation', 'session_feedback', 'consultation', 'contact_identity', 'onboarding'):
        if table == 'ledger' and not include_legacy_activity:
            continue
        records = (frappe.db.sql(f'SELECT * FROM tt_{table}', as_dict=True)
                   if f'tt_{table}' in existing_tables else [])
        encoded = sorted(json.dumps(dict(row), sort_keys=True, default=str) for row in records)
        result[table] = hashlib.sha256(json.dumps(encoded).encode()).digest()
    frappe.destroy()
    return result


before = snapshot(include_legacy_activity=False)
frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
frappe.connect()
legacy_before = {row.id: tuple(row) for row in frappe.db.sql(
    'SELECT id,patient,kind,amount,reference,created FROM tt_ledger', as_dict=True)}
scope_before = sorted(tuple(row) for row in frappe.db.sql('''SELECT name,clinician,service,status,
    creation,modified FROM `tabTele Tena Service Scope`'''))
frappe.destroy()
for attempt in (1, 2):
    with open(f'/tmp/tele-tena-pr2-migrate-{attempt}.log', 'w') as output:
        status = subprocess.run(['bench', '--site', SITE, 'migrate', '--skip-search-index'], cwd=BENCH, stdout=output, stderr=subprocess.STDOUT)
    assert status.returncode == 0, f'Migration {attempt} failed; inspect local migration log'
    assert snapshot(include_legacy_activity=False) == before, 'Migration changed existing non-ledger records'
    frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
    frappe.connect()
    current_ledger = {row.id: tuple(row) for row in frappe.db.sql(
        'SELECT id,patient,kind,amount,reference,created FROM tt_ledger', as_dict=True)}
    assert all(current_ledger.get(row_id) == row for row_id, row in legacy_before.items()), \
        'Migration modified or removed an existing simulation activity event'
    added = [row for row_id, row in current_ledger.items() if row_id not in legacy_before]
    for _, patient, kind, amount, reference, created in added:
        assert kind == 'Consumption' and reference.startswith('completion:'), \
            'Migration appended an unexpected legacy activity event'
        evidence = frappe.db.sql('''SELECT j.event_type,j.created,e.gross_minor,e.patient
            FROM tt_journal j JOIN tt_earning e ON j.event_ref=CONCAT('completion:',e.appointment)
            WHERE j.event_ref=%s''', (reference,), as_dict=True)
        assert evidence and evidence[0].event_type == 'ConsultationFinalized' and \
            evidence[0].patient == patient and int(evidence[0].gross_minor) == int(amount), \
            'Backfilled activity lacks matching immutable completion evidence'
    missing = frappe.db.sql('''SELECT COUNT(*) FROM tt_earning e
        JOIN tt_journal j ON j.event_ref=CONCAT('completion:',e.appointment)
        LEFT JOIN tt_ledger l ON l.reference=j.event_ref
        WHERE e.completed_at IS NOT NULL AND j.event_type='ConsultationFinalized'
          AND l.id IS NULL''')[0][0]
    assert int(missing) == 0, 'A journal-proven completion is still missing its activity event'
    frappe.destroy()
frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
frappe.connect()
for patch in ('v1_0_command_storage', 'v1_1_native_catalog', 'v1_2_catalog_adoption_check',
              'v1_3_phone_auth', 'v1_3_consultations', 'v1_4_consultation_close_state',
              'v1_5_contact_onboarding', 'v1_6_presentation_release', 'v1_7_demo_subledger',
              'v1_8_legacy_event_reconciliation', 'v1_13_financial_reconciliation_audit',
              'v1_14_session_feedback', 'v1_24_legacy_completion_activity'):
    assert frappe.db.exists('Patch Log', {'patch': 'tele_tena.patches.' + patch})
for table in ('tt_phone_identity', 'tt_otp_challenge', 'tt_otp_rate_limit', 'tt_otp_gate',
              *(f'tt_{name}' for name in PRESENTATION_TABLES),
              *(f'tt_{name}' for name in FINANCIAL_TABLES), 'tt_financial_reconciliation',
              'tt_session_feedback'):
    assert table in frappe.db.get_tables(cached=False), 'Missing phone-auth table'
key_path = Path(frappe.get_site_path('private', 'tele_tena_otp.key'))
assert key_path.is_file() and not key_path.is_symlink()
assert stat.S_IMODE(key_path.stat().st_mode) == 0o600
for row in frappe.db.sql('SELECT id,label,active FROM tt_service', as_dict=True):
    migrated = frappe.db.get_value('Tele Tena Service', row.id, ['service_label', 'active'])
    assert migrated == (row.label, row.active), 'Catalog migration mismatch'
assert frappe.db.sql("SHOW TABLES LIKE 'tt_consultation'")
assert frappe.db.sql("SHOW COLUMNS FROM tt_consultation LIKE 'room_closed'")
scope_after = sorted(tuple(row) for row in frappe.db.sql('''SELECT name,clinician,service,status,
    creation,modified FROM `tabTele Tena Service Scope`'''))
assert scope_after == scope_before, 'Migration changed service scopes'
frappe.destroy()
print('PASS: additive upgrade, patch log, phone-auth, presentation, subledger and reconciliation schemas/key, catalog copy, no scope changes, repeat migration, all pre-existing records preserved, and only journal-proven completion activity added')
