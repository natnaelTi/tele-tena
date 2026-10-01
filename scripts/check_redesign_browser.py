"""Disposable synthetic browser fixtures; no live SMS/email and no retained-data reset."""
import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fixtures', APP / 'tests/integration.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
import frappe
from tele_tena.api import journey, contact_auth, phone_auth, scheduling, presentation


def main():
    ready = False
    newcomers = []
    try:
        fixtures.Integration.setUpClass()
        ready = True
        fixtures.login('p1')
        journey.simulated_deposit(10000, secrets.token_hex(12))
        appointment = journey.book(**fixtures.booking(fixtures.Integration.offers['c1'], fixtures.at(1), secrets.token_hex(12)))['id']
        frappe.db.sql('UPDATE tt_appointment SET start=UTC_TIMESTAMP()-INTERVAL 1 MINUTE,end=UTC_TIMESTAMP()+INTERVAL 29 MINUTE WHERE id=%s', (appointment,))
        fixtures.login('c1')
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo
        local_today = datetime.now(ZoneInfo('Africa/Addis_Ababa')).date()
        scheduling.save_schedule(fixtures.Integration.offers['c1'], 'Synthetic browser hours',
            'Africa/Addis_Ababa', 'video', 'automatic', 60, 30, 0, 0,
            [{'weekday': day, 'start': '09:00', 'end': '17:00'} for day in range(7)], [], 'Published')
        for kind in ('newpatient', 'newclinician'):
            user = fixtures.PREFIX + '-' + kind + '@example.invalid'
            newcomers.append(user)
            frappe.set_user('Administrator')
            frappe.get_doc(dict(doctype='User', email=user, first_name='Synthetic new member', user_type='Website User', send_welcome_email=0)).insert()
            from frappe.utils.password import update_password
            update_password(user, fixtures.PASSWORD)
            frappe.db.sql("INSERT INTO tt_contact_identity VALUES ('email',%s,%s,UTC_TIMESTAMP(6))", (user, user))
            frappe.db.sql("INSERT INTO tt_onboarding (user,kind,answers,modified) VALUES (%s,%s,'{}',UTC_TIMESTAMP(6))", (user, 'clinician' if kind == 'newclinician' else 'patient'))
            fixtures.USERS[kind] = user
        review_applicant = fixtures.PREFIX + '-reviewapplicant@example.invalid'
        newcomers.append(review_applicant)
        fixtures.USERS['reviewapplicant'] = review_applicant
        frappe.set_user('Administrator')
        frappe.get_doc(dict(doctype='User', email=review_applicant, first_name='Synthetic applicant', user_type='Website User', send_welcome_email=0)).insert()
        from frappe.utils.password import update_password
        update_password(review_applicant, fixtures.PASSWORD)
        frappe.db.sql("INSERT INTO tt_contact_identity VALUES ('email',%s,%s,UTC_TIMESTAMP(6))", (review_applicant, review_applicant))
        frappe.db.sql("INSERT INTO tt_onboarding (user,kind,answers,modified) VALUES (%s,'clinician','{}',UTC_TIMESTAMP(6))", (review_applicant,))
        frappe.set_user(review_applicant)
        contact_auth.save_onboarding('clinician',1,{'name':'Synthetic Applicant','adult':True,'consent':True,'requested_services':[fixtures.PREFIX]},0)
        import base64
        presentation.upload_resume('synthetic-review-evidence.pdf',base64.b64encode(b'%PDF-1.4\nSynthetic review evidence\n%%EOF').decode('ascii'))
        contact_auth.save_onboarding('clinician',3,{'name':'Synthetic Applicant','statement':'Synthetic application for browser review only.','adult':True,'consent':True,'requested_services':[fixtures.PREFIX]},1)
        frappe.db.commit()
        with tempfile.TemporaryDirectory(prefix='tele-tena-redesign-') as directory:
            path = Path(directory) / 'fixture.json'
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as stream:
                json.dump({'users': fixtures.USERS, 'password': fixtures.PASSWORD, 'appointment_id': appointment,
                           'offering': fixtures.Integration.offers['c1'], 'booking_start': fixtures.at(4)}, stream)
            result = subprocess.run(['node', str(APP / 'scripts/browser-presentation-release.cjs')],
                                    env=dict(os.environ, TELE_TENA_REDESIGN_FIXTURE=str(path), NODE_PATH='/tmp/tele-tena-browser/node_modules'),
                                    cwd=APP, timeout=300)
            if result.returncode:
                raise RuntimeError('Redesign browser assertions failed')
    finally:
        if ready:
            frappe.db.rollback()
            frappe.set_user('Administrator')
            for user in newcomers:
                for table, key in (('contact_identity', 'user'), ('onboarding', 'user'), ('profile', 'user'), ('wallet', 'patient'), ('application', 'user')):
                    frappe.db.sql(f'DELETE FROM tt_{table} WHERE {key}=%s', (user,))
            # Base cleanup owns all synthetic users and appointment/balance rows.
            fixtures.Integration.tearDownClass()


if __name__ == '__main__':
    main()
