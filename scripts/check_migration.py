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

BENCH = Path(__file__).resolve().parents[3]
SITE = 'erp.localhost'
os.chdir(BENCH / 'sites')


def snapshot():
    frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
    frappe.connect()
    result = {}
    for table in (*TABLES, *PHONE_AUTH_TABLES, 'consultation', 'contact_identity', 'onboarding'):
        records = frappe.db.sql(f'SELECT * FROM tt_{table}', as_dict=True)
        encoded = sorted(json.dumps(dict(row), sort_keys=True, default=str) for row in records)
        result[table] = hashlib.sha256(json.dumps(encoded).encode()).digest()
    frappe.destroy()
    return result


before = snapshot()
frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
frappe.connect()
scope_before = sorted(tuple(row) for row in frappe.db.sql('''SELECT name,clinician,service,status,
    creation,modified FROM `tabTele Tena Service Scope`'''))
frappe.destroy()
for attempt in (1, 2):
    with open(f'/tmp/tele-tena-pr2-migrate-{attempt}.log', 'w') as output:
        status = subprocess.run(['bench', '--site', SITE, 'migrate', '--skip-search-index'], cwd=BENCH, stdout=output, stderr=subprocess.STDOUT)
    assert status.returncode == 0, f'Migration {attempt} failed; inspect local migration log'
    assert snapshot() == before, 'Migration changed legacy records'
frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
frappe.connect()
for patch in ('v1_0_command_storage', 'v1_1_native_catalog', 'v1_2_catalog_adoption_check', 'v1_3_phone_auth', 'v1_3_consultations', 'v1_4_consultation_close_state', 'v1_5_contact_onboarding'):
    assert frappe.db.exists('Patch Log', {'patch': 'tele_tena.patches.' + patch})
for table in ('tt_phone_identity', 'tt_otp_challenge', 'tt_otp_rate_limit', 'tt_otp_gate'):
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
print('PASS: additive upgrade, seven numbered Patch Log entries, phone-auth tables/key, catalog copy, no scope changes, repeat migration and all existing command/OTP/consultation/onboarding records preserved')
