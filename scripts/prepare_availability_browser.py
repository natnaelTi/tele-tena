"""Create one synthetic patient for the production-route availability regression."""
import json
import os
from pathlib import Path
import secrets
import uuid

APP = Path(__file__).resolve().parents[1]
BENCH = APP.parents[1]
SITE = os.environ.get('TELE_TENA_TEST_SITE')
if not SITE or not SITE.startswith('tele-tena-') or not SITE.endswith('.localhost'):
    raise SystemExit('Set TELE_TENA_TEST_SITE to a disposable TeleTena .localhost site')
OUT = Path(os.environ.get('TELE_TENA_AVAILABILITY_FIXTURE', '/tmp/tele-tena-availability-browser.json'))
os.chdir(BENCH / 'sites')
import sys
sys.path.insert(0, str(BENCH / 'apps/frappe'))
import frappe
frappe.enqueue = lambda *args, **kwargs: None

frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
frappe.connect()
try:
    seed = json.loads((BENCH / 'sites' / SITE / 'private' / 'tele_tena_review_seed.json').read_text())
    clinician = seed['users']['clinician']
    offering = seed['offering']
    email = 'tt-browser-' + secrets.token_hex(8) + '@example.invalid'
    password = secrets.token_urlsafe(30)
    frappe.set_user('Administrator')
    frappe.get_doc(dict(doctype='User', email=email, first_name='Synthetic Calendar Patient',
                        user_type='Website User', send_welcome_email=0)).insert()
    frappe.get_doc('User', email).add_roles('Tele Tena Patient')
    from frappe.utils.password import update_password
    update_password(email, password)
    frappe.set_user(email)
    from tele_tena.api import journey
    journey.save_profile('patient', 'Synthetic Calendar Patient', True, '', False, False)
    journey.simulated_deposit(100000, 'browser-' + uuid.uuid4().hex)
    frappe.db.commit()
    payload = {'clinician': clinician, 'offering': offering, 'patient': email, 'password': password}
    fd = os.open(OUT, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(payload, stream)
finally:
    frappe.destroy()
print('Prepared isolated synthetic browser patient; credentials stored in a mode-600 local file.')
