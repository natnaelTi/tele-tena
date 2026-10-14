"""Additive profile upgrade: compare every existing app table using old columns.

Only named local review/test sites are accepted. Stop their writers first.
Output contains counts, never profile, clinical or financial content.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import frappe

APP = Path(__file__).resolve().parents[1]
BENCH = APP.parents[1]
SITE = os.environ.get('TELE_TENA_TEST_SITE')
assert SITE in ('teletena-mvp-presentation.localhost', 'tele-tena-pr12-fresh.localhost')
os.chdir(BENCH / 'sites')

def connect():
    frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
    frappe.connect()

def digest(table, columns):
    records = frappe.db.sql('SELECT ' + ','.join('`'+key+'`' for key in columns) + ' FROM `'+table+'`', as_dict=True)
    encoded = sorted(json.dumps(dict(row), sort_keys=True, default=str) for row in records)
    return hashlib.sha256(json.dumps(encoded).encode()).hexdigest(), len(records)

connect()
columns = {table: [row[0] for row in frappe.db.sql('SHOW COLUMNS FROM `'+table+'`')] for table in frappe.db.get_tables(cached=False) if table.startswith('tt_')}
before = {table: digest(table, keys) for table, keys in columns.items()}
frappe.destroy()
for attempt in (1, 2):
    with open('/tmp/tt-profile-migrate-'+SITE+'-'+str(attempt)+'.log', 'w') as output:
        subprocess.run(['bench', '--site', SITE, 'migrate', '--skip-search-index'], cwd=BENCH, stdout=output, stderr=subprocess.STDOUT, check=True, timeout=180)
    connect()
    assert {table: digest(table, keys) for table, keys in columns.items()} == before, 'Existing app data changed during additive migration'
    assert frappe.db.sql("SHOW COLUMNS FROM tt_profile LIKE 'introduction'")
    assert frappe.db.sql('SELECT COUNT(*) FROM tt_profile WHERE introduction IS NOT NULL')[0][0] == 0, 'Migration inferred public content'
    for table in ('tt_shared_change_consent','tt_note_followup'):
        assert table in frappe.db.get_tables(cached=False)
    frappe.destroy()
print('PASS: two native migrations; all '+str(len(columns))+' existing app tables and '+str(sum(count for _, count in before.values()))+' rows preserved; no inferred introduction.')
