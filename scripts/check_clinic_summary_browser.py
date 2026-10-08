"""Run a real built-app patient-consent to Care Coordination summary journey."""
import json
import os
from pathlib import Path
import subprocess
import sys

APP = Path(__file__).resolve().parents[1]
BENCH = APP.parents[1]
SITE = os.environ.get('TELE_TENA_TEST_SITE', '')
if not SITE.startswith('tele-tena-') or not SITE.endswith('.localhost'):
    raise SystemExit('Set TELE_TENA_TEST_SITE to an isolated synthetic site.')
SITE_PATH = BENCH / 'sites' / SITE
SEED = json.loads((SITE_PATH / 'private' / 'tele_tena_review_seed.json').read_text())
USERS = SEED['users']
PATIENT = USERS['calendarpatient']
CLINICIAN = USERS['clinician']
COORDINATOR = USERS['patient']

os.chdir(BENCH / 'sites')
sys.path.insert(0, str(BENCH / 'apps' / 'frappe'))
import frappe

try:
    frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
    frappe.connect()
    appointment = frappe.db.sql('''SELECT DISTINCT a.id,a.clinician
        FROM tt_appointment a JOIN tt_note_revision n
          ON n.appointment=a.id AND n.summary_published=1
        WHERE a.patient=%s AND a.state='Completed'
        ORDER BY a.id LIMIT 1''', PATIENT, as_dict=True)
    if not appointment or appointment[0].clinician != CLINICIAN:
        raise SystemExit('No completed synthetic review-patient encounter with a published summary was found.')
    clinics = frappe.db.sql('''SELECT c.name,c.clinic_name FROM `tabTele Tena Clinic Affiliation` a
        JOIN `tabTele Tena Clinic` c ON c.name=a.clinic
        WHERE a.clinician=%s AND a.status='Verified' AND c.status='Verified'
          AND c.submitted_by=%s
        ORDER BY c.name LIMIT 1''', (CLINICIAN, CLINICIAN), as_dict=True)
    if not clinics:
        raise SystemExit('No synthetic verified clinic is affiliated with the review clinician.')
    clinic = clinics[0]
    # These accounts are synthetic review accounts. The browser test follows
    # the real password/session and invitation endpoints; this fixture records
    # their already-established test contact possession without bypassing auth.
    if not frappe.db.sql('''SELECT 1 FROM tt_contact_identity
        WHERE channel='email' AND contact=%s AND user=%s AND verified_at IS NOT NULL LIMIT 1''',
        (COORDINATOR, COORDINATOR)):
        frappe.db.sql('''INSERT INTO tt_contact_identity(channel,contact,user,verified_at)
            VALUES ('email',%s,%s,NOW(6))''', (COORDINATOR, COORDINATOR))
        frappe.db.commit()
    env = dict(os.environ)
    env.update({
        'TELE_TENA_REVIEW_SITE_PATH': str(SITE_PATH),
        'TELE_TENA_BROWSER_ORIGIN': env.get('TELE_TENA_BROWSER_ORIGIN', 'http://127.0.0.1:8017'),
        'TELE_TENA_SUMMARY_APPOINTMENT': appointment[0].id,
        'TELE_TENA_SUMMARY_CLINIC': clinic.name,
        'TELE_TENA_SUMMARY_CLINIC_NAME': clinic.clinic_name,
        'TELE_TENA_SUMMARY_PATIENT': PATIENT,
        'TELE_TENA_SUMMARY_CLINICIAN': CLINICIAN,
        'TELE_TENA_SUMMARY_COORDINATOR': COORDINATOR,
        'NODE_PATH': '/tmp/tele-tena-browser/node_modules',
    })
    frappe.destroy()
    result = subprocess.run(['node', str(APP / 'scripts' / 'browser-clinic-summary-sharing.cjs')],
                            cwd=APP, env=env, check=False)
    if result.returncode:
        raise SystemExit(result.returncode)
finally:
    try:
        frappe.destroy()
    except Exception:
        pass
