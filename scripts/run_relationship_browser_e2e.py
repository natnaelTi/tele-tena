"""Create short-lived synthetic patients, run the built-app E2E, then clean up.

Run with Bench Python and TELE_TENA_TEST_SITE set to the isolated review site.
Credentials exist only in a mode-600 site-private file during the run.
"""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import uuid

APP = Path(__file__).resolve().parents[1]
BENCH = APP.parents[1]
os.chdir(BENCH / 'sites')
SITE = os.environ.get('TELE_TENA_TEST_SITE', '')
if not SITE.startswith(('tele-tena-', 'teletena-')) or not SITE.endswith('.localhost'):
    raise SystemExit('Set TELE_TENA_TEST_SITE to an isolated TeleTena localhost site.')
sys.path.insert(0, str(BENCH / 'apps' / 'frappe'))
sys.path.insert(0, str(APP))

import frappe
from frappe.utils.password import update_password
from tele_tena.api import journey

frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
frappe.connect()
frappe.local.lang = 'en'
frappe.set_user('Administrator')

prefix = 'rel-browser-' + uuid.uuid4().hex[:16]
users = [
    {'email': prefix + '-a@example.invalid', 'password': secrets.token_urlsafe(32), 'display_name': 'Link Test Patient A'},
    {'email': prefix + '-b@example.invalid', 'password': secrets.token_urlsafe(32), 'display_name': 'Link Test Patient B'},
]
credential_path = Path(frappe.get_site_path('private', 'tele_tena_relationship_browser_fixture_' + prefix + '.json'))
created = []
credential_created = False


def clean_up():
    frappe.set_user('Administrator')
    emails = tuple(item['email'] for item in users)
    invitations = frappe.db.sql('''SELECT id FROM tt_relationship_invitation
        WHERE inviter IN %s OR accepted_by IN %s''', (emails, emails), pluck=True)
    relationships = frappe.db.sql('''SELECT id FROM tt_relationship_link
        WHERE participant_a IN %s OR participant_b IN %s''', (emails, emails), pluck=True)
    invitation_ids = tuple(invitations)
    relationship_ids = tuple(relationships)
    if invitation_ids:
        frappe.db.sql('DELETE FROM tt_relationship_event WHERE subject_type=%s AND subject_id IN %s',
                      ('Invitation', invitation_ids))
    if relationship_ids:
        frappe.db.sql('DELETE FROM tt_relationship_event WHERE subject_type=%s AND subject_id IN %s',
                      ('Relationship', relationship_ids))
        frappe.db.sql('DELETE FROM tt_relationship_link WHERE id IN %s', (relationship_ids,))
    if invitation_ids:
        frappe.db.sql('DELETE FROM tt_relationship_invitation WHERE id IN %s', (invitation_ids,))
    for account in users:
        email = account['email']
        frappe.db.sql('DELETE FROM tt_audit WHERE subject=%s OR actor=%s', (email, email))
        for table, field in (('profile', 'user'), ('wallet', 'patient'), ('phone_identity', 'user'),
                             ('contact_identity', 'user'), ('onboarding', 'user')):
            if frappe.db.table_exists('tt_' + table):
                frappe.db.sql(f'DELETE FROM `tt_{table}` WHERE `{field}`=%s', (email,))
        if email in created and frappe.db.exists('User', email):
            frappe.delete_doc('User', email, force=True)
    frappe.db.commit()
    if credential_created and credential_path.exists():
        credential_path.unlink()


try:
    for account in users:
        frappe.set_user('Administrator')
        user = frappe.get_doc({
            'doctype': 'User', 'email': account['email'], 'first_name': account['display_name'],
            'send_welcome_email': 0, 'user_type': 'Website User',
        })
        user.insert()
        created.append(account['email'])
        user.add_roles('Tele Tena Patient')
        update_password(account['email'], account['password'])
        frappe.set_user(account['email'])
        journey.save_profile('patient', account['display_name'], 1)
        frappe.db.commit()
    payload = json.dumps({'users': users}, separators=(',', ':')).encode('utf-8')
    descriptor = os.open(credential_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'wb') as output:
        output.write(payload)
    os.chmod(credential_path, 0o600)
    credential_created = True
    env = os.environ.copy()
    env['TELE_TENA_RELATIONSHIP_BROWSER_FIXTURE'] = str(credential_path)
    env.setdefault('TELE_TENA_SCREENSHOT_DIR', str(APP / 'docs' / 'screenshots' / 'adult-relationship-links'))
    env.setdefault('NODE_PATH', '/tmp/tele-tena-browser/node_modules')
    subprocess.run(['node', str(APP / 'scripts' / 'browser-relationship-links-e2e.cjs')],
                   cwd=APP, env=env, check=True)
finally:
    try:
        clean_up()
    finally:
        frappe.destroy()
