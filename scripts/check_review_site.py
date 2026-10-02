"""Invoked only inside the disposable fresh-install harness, never on customer sites."""
import base64
import json
import os
from pathlib import Path
import subprocess
import shutil
import time
from unittest.mock import patch

import frappe
import requests

APP = Path(__file__).resolve().parents[1]
BENCH = APP.parents[1]
SITE = 'tele-tena-pr2-test.localhost'
BASE = 'http://127.0.0.1:8017'


def verify():
    print('Review check: configure and seed', flush=True)
    assert frappe.local.site == SITE
    from tele_tena import review
    from tele_tena.api import journey, presentation
    frappe.set_user('Administrator')
    # Exercise the actual invisible/setup code with only nonsecret confirmation inputs.
    with patch('builtins.input', side_effect=[SITE, 'https://review.example.invalid']):
        review.configure()
    frappe.conf.update(tele_tena_review_site=SITE, tele_tena_review_enabled=True)
    assert not frappe.conf.get('developer_mode')
    assert frappe.db.get_single_value('Website Settings', 'disable_signup')
    review.seed()
    print('Review check: seed created', flush=True)
    first = frappe.db.sql('SELECT COUNT(*) FROM tt_appointment')[0][0]
    assert review.seed()['already_present']
    assert frappe.db.sql('SELECT COUNT(*) FROM tt_appointment')[0][0] == first
    marker = json.loads(Path(frappe.get_site_path('private', 'tele_tena_review_seed.json')).read_text())
    accounts = json.loads(Path(frappe.get_site_path('private', 'tele_tena_review_accounts.json')).read_text())
    users = marker['users']
    appointment = marker['appointment']
    assert journey.simulation_enabled()
    with patch.dict(frappe.conf, tele_tena_review_site='another-site.invalid'):
        assert not review.enabled() and not journey.simulation_enabled()
        try:
            review.seed()
            raise AssertionError('Cross-site seed allowed')
        except frappe.PermissionError:
            pass
    # Synthetic PDF evidence inserted through the real upload flow before submission.
    frappe.set_user('Administrator')
    applicant = 'review-applicant@example.invalid'
    doc = frappe.get_doc(dict(doctype='User', email=applicant, first_name='Review applicant',
                             send_welcome_email=0, user_type='Website User'))
    doc.insert()
    doc.add_roles('Tele Tena Clinician')
    frappe.set_user(applicant)
    journey.save_profile('clinician', 'Review applicant', True)
    presentation.upload_resume('review.pdf', base64.b64encode(b'%PDF-1.4\nSynthetic fixture\n%%EOF').decode())
    journey.apply('Synthetic evidence only')
    # Isolate documentation authorization from provider behavior: no media claim here.
    import uuid
    frappe.db.sql('''INSERT INTO tt_consultation
        (appointment,id,room_name,patient_identity,clinician_identity,state,created,ended)
        VALUES (%s,%s,%s,%s,%s,'Ended',UTC_TIMESTAMP(6),UTC_TIMESTAMP(6))''',
        (appointment, str(uuid.uuid4()), uuid.uuid4().hex, uuid.uuid4().hex, uuid.uuid4().hex))
    frappe.set_user(users['clinician'])
    presentation.save_note_draft(appointment, 'PRIVATE SYNTHETIC REVIEW NOTE', 'Synthetic shared next step')
    presentation.finalize_consultation(appointment, 1)
    frappe.db.commit()
    frappe.set_user('Administrator')
    frappe.destroy()
    print('Review check: permissions fixtures ready; repeat migrations', flush=True)
    # Real repeat migrations, without development mode or skipping failures.
    for _ in range(2):
        subprocess.run([shutil.which('bench'), '--site', SITE, 'migrate', '--skip-search-index'],
                       cwd=BENCH, check=True, stdout=subprocess.DEVNULL)
    print('Review check: starting built WSGI browser checks', flush=True)
    process = subprocess.Popen([str(BENCH / 'env/bin/gunicorn'), '--bind', '127.0.0.1:8017',
        '--workers', '2', '--pythonpath', str(APP), '--chdir', str(BENCH / 'sites'), 'scripts.review_test_wsgi:application'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                if requests.get(BASE + '/teletena/', timeout=2).status_code == 200:
                    break
            except requests.RequestException:
                pass
            time.sleep(.5)
        else:
            raise AssertionError('Disposable production WSGI server unavailable')
        for path in ('/teletena/', '/teletena/patient/appointments', '/teletena/clinician/availability', '/teletena/consultation/guessed/room'):
            response = requests.get(BASE + path)
            assert response.status_code == 200 and 'no-store' in response.headers['Cache-Control']
            assert '/assets/tele_tena/review/assets/' in response.text and '5173' not in response.text
        for path in ('/api/method/frappe.auth.get_logged_user', '/private/files/nonexistent.pdf', '/login', '/app'):
            response = requests.get(BASE + path)
            assert 'id="root"' not in response.text, 'SPA intercepted framework route'
        for path in ('/private/tele_tena_review_accounts.json', '/private/tele_tena_review_seed.json', '/api/method/tele_tena.review.seed', '/api/method/tele_tena.review.configure'):
            assert requests.get(BASE + path).status_code in (403,404,405), 'Private helper or credential route exposed'
        guest = requests.get(BASE + '/api/method/tele_tena.api.journey.wallet')
        assert guest.status_code == 403
        assert 'no-store' in guest.headers['Cache-Control']
        def login(role):
            session = requests.Session()
            result = session.post(BASE + '/api/method/login', json={'usr': users[role], 'pwd': accounts[users[role]]})
            assert result.status_code == 200, 'Password authentication failed'
            result = session.get(BASE + '/api/method/tele_tena.api.journey.session').json()['message']
            session.headers['X-Frappe-CSRF-Token'] = result['csrf_token']
            return session
        patient, clinician, reviewer = [login(role) for role in ('patient', 'clinician', 'reviewer')]
        detail = '/api/method/tele_tena.api.presentation.appointment_detail'
        result = patient.get(BASE + detail, params={'appointment': appointment})
        assert result.status_code == 200 and 'PRIVATE SYNTHETIC' not in result.text and 'private_note' not in result.json()['message']
        assert 'Synthetic shared next step' in result.text
        assert 'PRIVATE SYNTHETIC' in clinician.get(BASE + detail, params={'appointment': appointment}).text
        assert reviewer.get(BASE + detail, params={'appointment': appointment}).status_code == 403
        resume = '/api/method/tele_tena.api.presentation.download_resume'
        assert reviewer.get(BASE + resume, params={'clinician': applicant}).content.startswith(b'%PDF-')
        assert patient.get(BASE + resume, params={'clinician': applicant}).status_code == 403
        assert requests.get(BASE + resume, params={'clinician': applicant}).status_code == 403
        for module in ('contact_auth', 'phone_auth'):
            response = patient.post(BASE + '/api/method/tele_tena.api.' + module + '.request_code',
                json=({'channel':'email','contact':'review@example.invalid','request_id':'a'*24} if module=='contact_auth'
                      else {'phone':'+251911000001','purpose':'patient_signup','request_id':'a'*24}))
            assert response.status_code == 403 and 'review_password_required' in response.text
        # CSRF must still reject an authenticated mutation without its header.
        unsafe = requests.Session()
        unsafe.cookies.update(patient.cookies)
        assert unsafe.post(BASE + '/api/method/tele_tena.api.journey.simulated_deposit',
                           json={'amount':100,'retry_key':'csrf-rejected'}).status_code == 400
        assert patient.post(BASE + '/api/method/logout').status_code == 200
        assert patient.get(BASE + '/api/method/tele_tena.api.journey.wallet').status_code == 403
        env = dict(os.environ, NODE_PATH='/tmp/tele-tena-browser/node_modules',
                   TELE_TENA_REVIEW_SITE_PATH=str(BENCH / 'sites' / SITE))
        subprocess.run(['node', str(APP / 'scripts/browser-review-package.cjs')], env=env, check=True, cwd=APP)
        # Reuse the existing development Cloud project only on this disposable site.
        source = BENCH / 'sites/erp.localhost/private/tele_tena_livekit.json'
        assert source.is_file() and (source.stat().st_mode & 0o777) == 0o600
        review.write_private(BENCH / 'sites' / SITE / 'private/tele_tena_livekit.json', json.loads(source.read_text()))
        subprocess.run([str(BENCH / 'env/bin/python'), str(APP / 'scripts/check_hosted_livekit_revocation.py')],
            env=dict(os.environ, TELE_TENA_TEST_SITE=SITE, TELE_TENA_BROWSER_BASE=BASE+'/teletena'),
            check=True, cwd=APP, timeout=540)
        print('PASS: built Frappe/Gunicorn routes, namespace isolation, sessions/CSRF, enrollment guard, private notes and resume permissions')
    finally:
        process.terminate()
        process.wait(timeout=20)
    verify_job()


def verify_job():
    marker = json.loads((BENCH / 'sites' / SITE / 'private/tele_tena_review_seed.json').read_text())
    users = marker['users']
    frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
    frappe.connect()
    frappe.set_user('Administrator')
    frappe.db.sql('UPDATE tt_appointment SET expires_at=UTC_TIMESTAMP()-INTERVAL 1 MINUTE WHERE id=%s', (marker['pending'],))
    frappe.db.commit()
    before_reserved = frappe.db.sql('SELECT reserved FROM tt_wallet WHERE patient=%s', (users['patient'],))[0][0]
    # Use the real worker function with explicit site binding; no cross-site scheduler configuration edits.
    from frappe.utils.background_jobs import enqueue
    from rq import SimpleWorker
    from frappe.utils.background_jobs import get_queue, get_queues_timeout
    # Only this process knows this disposable queue name; no live worker can take it.
    timeouts = {**get_queues_timeout(), 'teletena_review_check':300}
    with patch('frappe.utils.background_jobs.get_queues_timeout', return_value=timeouts):
        job = enqueue('tele_tena.api.presentation.expire_pending_appointments', queue='teletena_review_check',
                      job_id='tele-tena-disposable-review-expiry')
        queue = get_queue('teletena_review_check')
    assert job.kwargs['site'] == SITE
    assert frappe.db.exists('Scheduled Job Type', {'method':'tele_tena.api.presentation.expire_pending_appointments'})
    # Execute only this job, not any existing development site's queue entries.
    worker = SimpleWorker([queue], connection=queue.connection)
    assert worker.perform_job(job, queue), 'Site-scoped scheduling job failed'
    job.delete()
    frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
    frappe.connect()
    assert frappe.db.sql('SELECT state FROM tt_appointment WHERE id=%s', (marker['pending'],))[0][0] == 'Expired'
    assert frappe.db.sql('SELECT reserved FROM tt_wallet WHERE patient=%s', (users['patient'],))[0][0] == before_reserved - 60000
    print('PASS: real RQ expiry job bound to disposable site released its reservation')


if __name__ == '__main__':
    os.chdir(BENCH / 'sites')
    frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
    frappe.connect()
    try:
        import sys
        verify_job() if '--job-only' in sys.argv else verify()
    except Exception as error:
        import traceback
        for frame in traceback.extract_tb(error.__traceback__):
            print('Failure location:', Path(frame.filename).name, frame.lineno, frame.name)
        raise SystemExit('Review verification failed: ' + type(error).__name__ + ' (values withheld)')
    finally:
        frappe.destroy()
