"""Run the built clinic-membership browser flow with a temporary synthetic proof fixture."""
import json
import os
from pathlib import Path
import subprocess
import sys

APP = Path(__file__).resolve().parents[1]
BENCH = APP.parents[1]
SITE = os.environ.get('TELE_TENA_TEST_SITE', '')
if not SITE.startswith('tele-tena-') or not SITE.endswith('.localhost'):
    raise SystemExit('Set TELE_TENA_TEST_SITE to the isolated synthetic review site.')
SITE_PATH = BENCH / 'sites' / SITE
SEED = json.loads((SITE_PATH / 'private' / 'tele_tena_review_seed.json').read_text())
patient = SEED['users']['patient']

os.chdir(BENCH / 'sites')
sys.path.insert(0, str(BENCH / 'apps' / 'frappe'))
import frappe

created_identity = False
try:
    frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
    frappe.connect()
    exists = frappe.db.exists('tt_contact_identity', {
        'channel': 'email', 'contact': patient, 'user': patient,
    })
    if not exists:
        # This temporary synthetic fixture represents an already verified
        # account contact; it does not bypass any HTTP endpoint or OTP policy.
        frappe.db.sql('''INSERT INTO tt_contact_identity(channel,contact,user,verified_at)
            VALUES ('email',%s,%s,NOW(6))''', (patient, patient))
        frappe.db.commit()
        created_identity = True
    frappe.destroy()

    env = dict(os.environ)
    env['TELE_TENA_REVIEW_SITE_PATH'] = str(SITE_PATH)
    env.setdefault('TELE_TENA_BROWSER_ORIGIN', 'http://127.0.0.1:8017')
    env['NODE_PATH'] = '/tmp/tele-tena-browser/node_modules'
    result = subprocess.run(['node', str(APP / 'scripts' / 'browser-clinic-membership.cjs')],
                            cwd=APP, env=env, check=False)
    if result.returncode:
        raise SystemExit(result.returncode)
finally:
    try:
        frappe.destroy()
    except Exception:
        pass
    if created_identity:
        frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
        frappe.connect()
        frappe.db.sql('''DELETE FROM tt_contact_identity
            WHERE channel='email' AND contact=%s AND user=%s''', (patient, patient))
        frappe.db.commit()
        frappe.destroy()
