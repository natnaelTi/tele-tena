"""Verify additive upgrade and repeat migration without exposing stored content."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import frappe
from tele_tena.schema import TABLES

BENCH = Path(__file__).resolve().parents[3]
SITE = 'erp.localhost'
os.chdir(BENCH / 'sites')


def snapshot():
    frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
    frappe.connect()
    result = {}
    for table in TABLES:
        records = frappe.db.sql(f'SELECT * FROM tt_{table}', as_dict=True)
        encoded = sorted(json.dumps(dict(row), sort_keys=True, default=str) for row in records)
        result[table] = hashlib.sha256(json.dumps(encoded).encode()).digest()
    frappe.destroy()
    return result


before = snapshot()
for attempt in (1, 2):
    with open(f'/tmp/tele-tena-pr2-migrate-{attempt}.log', 'w') as output:
        status = subprocess.run(['bench', '--site', SITE, 'migrate', '--skip-search-index'], cwd=BENCH, stdout=output, stderr=subprocess.STDOUT)
    assert status.returncode == 0, f'Migration {attempt} failed; inspect local migration log'
    assert snapshot() == before, 'Migration changed legacy records'
frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
frappe.connect()
for patch in ('v1_0_command_storage', 'v1_1_native_catalog', 'v1_2_catalog_adoption_check'):
    assert frappe.db.exists('Patch Log', {'patch': 'tele_tena.patches.' + patch})
for row in frappe.db.sql('SELECT id,label,active FROM tt_service', as_dict=True):
    migrated = frappe.db.get_value('Tele Tena Service', row.id, ['service_label', 'active'])
    assert migrated == (row.label, row.active), 'Catalog migration mismatch'
assert frappe.db.count('Tele Tena Service Scope') == 0, 'Migration inferred scopes'
frappe.destroy()
print('PASS: additive upgrade, three numbered Patch Log entries, catalog copy, no inferred scopes, repeat migration and all legacy records preserved')
