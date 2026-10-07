"""Run with bench env Python. Real isolated-site MariaDB tests; synthetic only."""
import concurrent.futures
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import sys
import threading
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import requests

BENCH = Path(__file__).resolve().parents[3]
os.chdir(BENCH / 'sites')
sys.path.insert(0, str(BENCH / 'apps/frappe'))
import frappe
from frappe.utils.password import update_password
from tele_tena.api import journey as api
from tele_tena.api import phone_auth, contact_auth

SITE = os.environ.get('TELE_TENA_TEST_SITE')
if not SITE or not SITE.endswith('.localhost') or not SITE.startswith(('tele-tena-', 'teletena-')):
    raise SystemExit('Set TELE_TENA_TEST_SITE to a disposable TeleTena site; development sites are refused')
PREFIX = 'tt-test-' + secrets.token_hex(5)
USERS = {kind: PREFIX + '-' + kind + '@example.invalid' for kind in ('p1', 'p2', 'c1', 'c2', 'c3', 'admin')}
PASSWORD = secrets.token_urlsafe(24)
BASE = os.environ.get('TELE_TENA_TEST_API_ORIGIN', os.environ.get('TELE_TENA_TEST_BASE', 'http://127.0.0.1:8017'))
from urllib.parse import urlsplit
assert urlsplit(BASE).hostname in ('127.0.0.1', 'localhost'), 'Integration tests require a loopback server'


def connect():
    frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
    frappe.connect()


def login(kind):
    frappe.set_user(USERS[kind])


def at(hour=0):
    return (datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=3, hours=hour)).isoformat()


def booking(offering, start, key='test', history=False):
    return dict(offering=offering, start=start, retry_key=key, request_text='Synthetic request',
                sharing={'name': False, 'history': history}, expected_price=600,
                expected_minutes=30, expected_disclosure={'request': 'Synthetic request', **({'history': 'Synthetic private history'} if history else {})})


class Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        connect()
        cls._original_enqueue = frappe.enqueue
        # Regression fixtures must not fill a retained site queue. Worker
        # behavior has separate controlled checks; never drain an old queue as
        # a side effect of an API test run.
        frappe.enqueue = lambda *args, **kwargs: None
        frappe.set_user('Administrator')
        for kind, email in USERS.items():
            role = 'Tele Tena ' + ('Patient' if kind.startswith('p') else 'Clinician' if kind.startswith('c') else 'Approver')
            user = frappe.get_doc(dict(doctype='User', email=email, first_name='Synthetic Test', send_welcome_email=0, user_type='Website User'))
            user.insert()
            user.add_roles(role)
            update_password(email, PASSWORD)
        frappe.db.commit()
        for kind in ('p1', 'p2', 'c1', 'c2', 'c3'):
            login(kind)
            api.save_profile('patient' if kind.startswith('p') else 'clinician', 'Synthetic Test', True, history='Synthetic private history')
            if kind.startswith('c'):
                api.apply('Synthetic credentials for testing only')
        login('admin')
        api.save_service(PREFIX, 'Synthetic test consultation')
        for kind in ('c1', 'c2'):
            api.review(USERS[kind], 'Approved')
            api.review_service_scope(USERS[kind], PREFIX, 'Approved')
            login(kind)
            api.publish(PREFIX, 600, 30)
            api.add_availability(at(), at(12))
            login('admin')
        cls.offers = {kind: api.one('SELECT id FROM tt_offering WHERE clinician=%s', (USERS[kind],)).id for kind in ('c1', 'c2')}
        frappe.db.commit()

    @classmethod
    def tearDownClass(cls):
        frappe.db.rollback()
        frappe.set_user('Administrator')
        request_ids = frappe.db.sql('''SELECT DISTINCT r.id FROM tt_open_request r
            LEFT JOIN tt_request_recipient rr ON rr.request_id=r.id
            WHERE r.patient IN %s OR rr.clinician IN %s''',
            (tuple(USERS.values()), tuple(USERS.values())), pluck=True)
        if request_ids:
            frappe.db.sql('DELETE FROM tt_request_metric WHERE request_id IN %s', (tuple(request_ids),))
            frappe.db.sql('DELETE FROM tt_request_offer WHERE request_id IN %s', (tuple(request_ids),))
            frappe.db.sql('DELETE FROM tt_request_recipient WHERE request_id IN %s', (tuple(request_ids),))
            frappe.db.sql('DELETE FROM tt_open_request WHERE id IN %s', (tuple(request_ids),))
        frappe.db.sql('DELETE FROM tt_clinician_request_presence WHERE clinician IN %s', (tuple(USERS.values()),))
        appointment_ids = frappe.db.sql('SELECT id FROM tt_appointment WHERE patient IN %s OR clinician IN %s',
                                       (tuple(USERS.values()), tuple(USERS.values())), pluck=True)
        if appointment_ids:
            frappe.db.sql('DELETE FROM tt_dispute WHERE earning IN (SELECT id FROM tt_earning WHERE appointment IN %s)',
                          (tuple(appointment_ids),))
            frappe.db.sql('DELETE FROM tt_earning WHERE appointment IN %s', (tuple(appointment_ids),))
        frappe.db.sql('DELETE FROM tt_payout WHERE clinician IN %s', (tuple(USERS.values()),))
        account_ids = frappe.db.sql('SELECT id FROM tt_financial_account WHERE owner IN %s',
                                    (tuple(USERS.values()),), pluck=True)
        if account_ids:
            journal_ids = frappe.db.sql('SELECT DISTINCT journal_id FROM tt_journal_line WHERE account_id IN %s',
                                        (tuple(account_ids),), pluck=True)
            if journal_ids:
                frappe.db.sql('DELETE FROM tt_journal_line WHERE journal_id IN %s', (tuple(journal_ids),))
                frappe.db.sql('DELETE FROM tt_journal WHERE id IN %s', (tuple(journal_ids),))
            frappe.db.sql('DELETE FROM tt_financial_account WHERE id IN %s', (tuple(account_ids),))
        for appointment in appointment_ids:
            frappe.db.sql('DELETE FROM tt_note_revision WHERE appointment=%s', (appointment,))
            frappe.db.sql('DELETE FROM tt_consultation_note WHERE appointment=%s', (appointment,))
            frappe.db.sql('DELETE FROM tt_appointment_event WHERE appointment=%s', (appointment,))
        schedule_ids = frappe.db.sql('SELECT id FROM tt_schedule WHERE clinician IN %s',
                                     (tuple(USERS.values()),), pluck=True)
        for schedule_id in schedule_ids:
            frappe.db.sql('DELETE FROM tt_schedule_rule WHERE schedule_id=%s', (schedule_id,))
            frappe.db.sql('DELETE FROM tt_schedule_exception WHERE schedule_id=%s', (schedule_id,))
            frappe.db.sql('DELETE FROM tt_schedule WHERE id=%s', (schedule_id,))
        for email in USERS.values():
            # Clinic applications retain their submitter Link as audit history;
            # remove only rows created by this synthetic fixture before users.
            clinic_ids = frappe.db.sql('SELECT name FROM `tabTele Tena Clinic` WHERE submitted_by=%s',
                                       (email,), pluck=True)
            if clinic_ids:
                frappe.db.sql('DELETE FROM `tabTele Tena Clinic Membership` WHERE clinic IN %s',
                              (tuple(clinic_ids),))
            frappe.db.sql('DELETE FROM `tabTele Tena Clinic Affiliation` WHERE clinician=%s', (email,))
            frappe.db.sql('DELETE FROM `tabTele Tena Clinic` WHERE submitted_by=%s', (email,))
            frappe.db.sql('DELETE FROM tt_resume_evidence WHERE clinician=%s', (email,))
            frappe.db.sql('DELETE FROM tt_tour_progress WHERE user=%s', (email,))
            frappe.db.sql('DELETE FROM tt_preferences WHERE user=%s', (email,))
        scope_names = frappe.db.sql('SELECT name FROM `tabTele Tena Service Scope` WHERE clinician IN %s', (tuple(USERS.values()),), pluck=True)
        for name in scope_names:
            frappe.db.sql('DELETE FROM tabVersion WHERE ref_doctype=%s AND docname=%s', ('Tele Tena Service Scope', name))
            frappe.db.sql('DELETE FROM `tabTele Tena Service Scope` WHERE name=%s', (name,))
        vetting_names = frappe.db.sql('SELECT name FROM `tabTele Tena Vetting Scope Application` WHERE clinician IN %s',
                                     (tuple(USERS.values()),), pluck=True)
        if vetting_names:
            frappe.db.sql('DELETE FROM `tabTele Tena Vetting Assessment` WHERE scope_application IN %s',
                          (tuple(vetting_names),))
            frappe.db.sql('DELETE FROM tabVersion WHERE ref_doctype=%s AND docname IN %s',
                          ('Tele Tena Vetting Scope Application', tuple(vetting_names)))
            frappe.db.sql('DELETE FROM `tabTele Tena Vetting Scope Application` WHERE name IN %s',
                          (tuple(vetting_names),))
        for name in (PREFIX, PREFIX + '-other', PREFIX + '-vetting-scope'):
            frappe.db.sql('DELETE FROM tabVersion WHERE ref_doctype=%s AND docname=%s', ('Tele Tena Service', name))
            frappe.db.sql('DELETE FROM `tabTele Tena Service` WHERE name=%s', (name,))
        # Explicit synthetic fixture cleanup; never touch non-test records.
        for table, field in (('audit', 'subject'), ('ledger', 'patient'), ('appointment', 'patient'), ('wallet', 'patient'),
                             ('availability', 'clinician'), ('offering', 'clinician'), ('application', 'user'), ('profile', 'user')):
            for email in USERS.values():
                if table == 'appointment':
                    frappe.db.sql('DELETE FROM tt_consultation WHERE appointment IN (SELECT id FROM tt_appointment WHERE patient=%s OR clinician=%s)', (email, email))
                frappe.db.sql(f'DELETE FROM tt_{table} WHERE {field}=%s', (email,))
        for email in PHONE_AUTH_TEST_USERS:
            for table, field in (('audit', 'subject'), ('phone_identity', 'user'), ('contact_identity', 'user'),
                                 ('onboarding', 'user'), ('wallet', 'patient'), ('application', 'user'), ('profile', 'user')):
                frappe.db.sql(f'DELETE FROM tt_{table} WHERE {field}=%s', (email,))
            if frappe.db.exists('User', email):
                frappe.delete_doc('User', email)
        for digest in PHONE_AUTH_TEST_DIGESTS:
            frappe.db.sql('DELETE FROM tt_otp_challenge WHERE phone_digest=%s', (digest,))
        for bucket_key in PHONE_AUTH_TEST_BUCKET_KEYS:
            frappe.db.sql('DELETE FROM tt_otp_rate_limit WHERE bucket_key=%s', (bucket_key,))
        frappe.db.sql('DELETE FROM tt_service WHERE id=%s', (PREFIX,))
        for email in USERS.values():
            frappe.delete_doc('User', email)
        # Fixture cleanup removes its own journals; restore only the cached
        # account totals from the remaining immutable journal lines.
        frappe.db.sql('''UPDATE tt_financial_account a SET balance_minor=COALESCE((
            SELECT SUM(CASE WHEN a.normal_side='D' THEN l.debit_minor-l.credit_minor
                            ELSE l.credit_minor-l.debit_minor END)
            FROM tt_journal_line l WHERE l.account_id=a.id),0)''')
        frappe.db.commit()
        frappe.destroy()
        frappe.enqueue = cls._original_enqueue

    def tearDown(self):
        frappe.db.rollback()
        for email in USERS.values():
            frappe.clear_cache(user=email)

    def fund(self, kind, amount):
        login(kind)
        api.simulated_deposit(amount, secrets.token_hex(12))
        frappe.db.commit()

    def test_01_approval_and_stale_offering(self):
        login('c3')
        with self.assertRaises(frappe.ValidationError):
            api.publish(PREFIX, 600, 30)
        login('admin')
        api.review(USERS['c1'], 'Rejected')
        login('p1')
        self.assertNotIn(self.offers['c1'], [o.id for o in api.discover(PREFIX)])
        with self.assertRaises(frappe.ValidationError):
            api.book(**booking(self.offers['c1'], at(1)))
        login('c1')
        with self.assertRaises(frappe.PermissionError):
            api.review(USERS['c1'], 'Approved')

    def test_02_private_preview_snapshot_and_retry(self):
        self.fund('p1', 1200)
        args = booking(self.offers['c1'], at(1), 'private')
        preview = api.preview(args['request_text'], args['sharing'])
        self.assertEqual(preview['disclosure'], args['expected_disclosure'])
        result = api.book(**args)
        self.assertEqual(api.book(**args)['id'], result['id'])
        self.assertEqual(api.wallet()['reserved'], 600)
        with self.assertRaises(frappe.ValidationError):
            api.book(**{**args, 'start': at(2)})
        frappe.db.commit()
        login('p2')
        self.assertEqual(api.appointments(), [])
        with self.assertRaises(TypeError):
            api.wallet(patient=USERS['p1'])
        login('c1')
        appointments = api.appointments()
        self.assertEqual(appointments[0].disclosure, {'request': 'Synthetic request'})
        self.assertNotIn('patient', appointments[0])
        self.assertNotIn('history', appointments[0].disclosure)
        login('admin')
        with self.assertRaises(frappe.ValidationError):
            api.appointments()
        login('p1')
        api.save_profile('patient', 'Changed Synthetic', True, history='Changed history')
        login('c1')
        self.assertEqual(api.appointments()[0].disclosure, {'request': 'Synthetic request'})

    def test_03_failure_rolls_back_entire_command(self):
        self.fund('p2', 1200)
        login('p2')
        before = dict(api.wallet())
        with patch.object(api, 'simulation_log', side_effect=RuntimeError('Injected synthetic failure')):
            with self.assertRaises(RuntimeError):
                api.book(**booking(self.offers['c2'], at(2), 'failure'))
        # Commit after failure proves rollback isn't merely deferred to request cleanup.
        frappe.db.commit()
        self.assertEqual(dict(api.wallet()), before)
        self.assertEqual(api.appointments(), [])
        self.assertEqual(api.rows('SELECT id FROM tt_ledger WHERE patient=%s AND kind=%s', (USERS['p2'], 'Reservation')), [])
        with self.assertRaises(frappe.ValidationError):
            api.book(**booking(self.offers['c2'], at(23)))
        with patch.object(api, 'simulation_log', side_effect=RuntimeError('Deposit failure')):
            with self.assertRaises(RuntimeError):
                api.simulated_deposit(100, 'failed-deposit')
        self.assertEqual(dict(api.wallet()), before)

    def concurrent(self, jobs):
        # Main connection must not retain a read view across threaded commits.
        frappe.db.rollback()
        barrier = threading.Barrier(len(jobs))
        def worker(job):
            connect()
            try:
                login(job[0])
                barrier.wait(timeout=10)
                result = api.book(**job[1])
                frappe.db.commit()
                return ('ok', result['id'])
            except frappe.ValidationError:
                frappe.db.rollback()
                return ('rejected', None)
            finally:
                frappe.destroy()
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(jobs)) as pool:
            result = list(pool.map(worker, jobs))
        frappe.db.rollback()
        return result

    def test_04_concurrent_double_booking(self):
        self.fund('p1', 1200)
        self.fund('p2', 1200)
        result = self.concurrent([('p1', booking(self.offers['c1'], at(4), 'race-slot-1')),
                                  ('p2', booking(self.offers['c1'], at(4), 'race-slot-2'))])
        self.assertEqual(sum(r[0] == 'ok' for r in result), 1)
        self.assertEqual(api.one('SELECT COUNT(*) AS n FROM tt_appointment WHERE clinician=%s AND start=%s', (USERS['c1'], api.instant(at(4)))).n, 1)

    def test_05_concurrent_overspend(self):
        from tele_tena.accounting import account_id, check_wallet_projection, post
        login('p2')
        wallet = api.one('SELECT available,reserved FROM tt_wallet WHERE patient=%s FOR UPDATE', (USERS['p2'],))
        check_wallet_projection(USERS['p2'], wallet)
        available = int(wallet.available)
        desired = 600
        if available > desired:
            amount = available - desired
            lines = [(account_id('patient', USERS['p2'], 'available'), amount, 0),
                     (account_id('', '', 'cash_clearing'), 0, amount)]
        else:
            amount = desired - available
            lines = [(account_id('', '', 'cash_clearing'), amount, 0),
                     (account_id('patient', USERS['p2'], 'available'), 0, amount)]
        if amount:
            reference = 'integration-fixture-balance:' + USERS['p2'] + ':' + secrets.token_hex(8)
            post(reference, 'TestFixtureBalanceAdjustment', reference, lines, {'synthetic_fixture': True})
            frappe.db.sql('UPDATE tt_wallet SET available=%s WHERE patient=%s', (desired, USERS['p2']))
        frappe.db.commit()
        result = self.concurrent([('p2', booking(self.offers['c1'], at(6), 'spend-1')),
                                  ('p2', booking(self.offers['c2'], at(7), 'spend-2'))])
        self.assertEqual(sum(r[0] == 'ok' for r in result), 1)
        login('p2')
        self.assertEqual(api.wallet()['available'], 0)

    def test_06_concurrent_repeated_submission(self):
        self.fund('p1', 1200)
        args = booking(self.offers['c2'], at(9), 'race-retry')
        result = self.concurrent([('p1', args), ('p1', args)])
        self.assertEqual(result[0], result[1])
        self.assertEqual(result[0][0], 'ok')
        found = api.one('SELECT COUNT(*) AS n FROM tt_ledger WHERE reference=%s', ('booking:' + result[0][1],))
        self.assertEqual(found.n, 1)

    def test_07_http_auth_csrf_and_generic_denial(self):
        client = requests.Session()
        method = BASE + '/api/method/tele_tena.api.journey.'
        self.assertEqual(client.get(method + 'session').status_code, 403)
        response = client.post(BASE + '/api/method/login', data={'usr': USERS['p1'], 'pwd': PASSWORD})
        self.assertEqual(response.status_code, 200)
        session = client.get(method + 'session').json()['message']
        self.assertEqual(client.get(method + 'session').headers.get('Cache-Control'), 'no-store, private')
        csrf = session['csrf_token']
        payload = dict(kind='patient', display_name='Synthetic HTTP', adult=True)
        self.assertEqual(client.post(method + 'save_profile', json=payload).status_code, 400)
        client.headers['X-Frappe-CSRF-Token'] = csrf
        self.assertEqual(client.post(method + 'save_profile', json=payload).status_code, 200)
        self.assertEqual(client.get(method + 'save_profile', params=payload).status_code, 403)
        for resource in ('tt_profile', 'tt_wallet', 'tt_appointment', 'tt_ledger'):
            self.assertNotEqual(client.get(BASE + '/api/resource/' + resource).status_code, 200)
        rejection = client.post(method + 'book', json=booking(self.offers['c2'], at(23), 'http-window'))
        self.assertNotEqual(rejection.status_code, 200)
        self.assertEqual(rejection.json()['tele_tena_error'], 'outside_availability')
        other = client.get(method + 'wallet', params={'patient': USERS['p2']})
        self.assertEqual(other.status_code, 200)
        self.assertEqual(other.json()['message']['available'], api.one('SELECT available FROM tt_wallet WHERE patient=%s', (USERS['p1'],)).available)
        self.assertNotEqual(client.post(method + 'review', json={'clinician': USERS['c3'], 'decision': 'Approved'}).status_code, 200)
        client.post(BASE + '/api/method/logout')

    def test_07b_availability_rejections_are_specific(self):
        client = requests.Session()
        method = BASE + '/api/method/tele_tena.api.journey.'
        self.assertEqual(client.post(BASE + '/api/method/login', data={'usr': USERS['c1'], 'pwd': PASSWORD}).status_code, 200)
        csrf = client.get(method + 'session').json()['message']['csrf_token']
        client.headers['X-Frappe-CSRF-Token'] = csrf
        past = datetime.now(timezone.utc) - timedelta(minutes=1)
        response = client.post(method + 'add_availability', json={
            'start': past.isoformat(), 'end': (past + timedelta(minutes=30)).isoformat()
        })
        self.assertEqual(response.json()['tele_tena_error'], 'invalid_availability_window')
        response = client.post(method + 'add_availability', json={
            'start': at(1), 'end': at(2)
        })
        self.assertEqual(response.json()['tele_tena_error'], 'availability_overlap')
        client.post(BASE + '/api/method/logout')

    def test_08_selected_history_and_stale_preview(self):
        self.fund('p1', 1200)
        login('p1')
        api.save_profile('patient', 'Synthetic Test', True, history='Synthetic private history')
        args = booking(self.offers['c2'], at(10), 'selected', True)
        self.assertEqual(api.preview(args['request_text'], args['sharing'])['disclosure'], args['expected_disclosure'])
        result = api.book(**args)
        login('c2')
        record = next(a for a in api.appointments() if a.id == result['id'])
        self.assertEqual(record.disclosure['history'], 'Synthetic private history')
        self.assertNotIn('name', record.disclosure)
        login('p1')
        api.save_profile('patient', 'Synthetic Test', True, history='Changed synthetic history')
        with self.assertRaises(frappe.ValidationError):
            api.book(**{**args, 'start': at(11), 'retry_key': 'stale-preview'})

    def test_09_stale_price_duration_and_partial_window(self):
        self.fund('p1', 1200)
        login('p1')
        before = dict(api.wallet())
        args = booking(self.offers['c2'], at(11), 'stale-price')
        with self.assertRaises(frappe.ValidationError):
            api.book(**{**args, 'expected_price': 599})
        with self.assertRaises(frappe.ValidationError):
            api.book(**{**args, 'expected_minutes': 60})
        # A start within a window still fails if its fixed session overruns the end.
        overrun = (api.instant(at(12)) - timedelta(minutes=15)).replace(tzinfo=timezone.utc).isoformat()
        with self.assertRaises(frappe.ValidationError):
            api.book(**{**args, 'start': overrun})
        self.assertEqual(dict(api.wallet()), before)

    def test_10_simulation_isolation_and_exact_money(self):
        login('p1')
        with patch.object(api, 'simulation_enabled', return_value=False):
            with self.assertRaises(frappe.PermissionError):
                api.simulated_deposit(100, 'disabled')
        for amount in (1.5, '1.5', True, -1):
            with self.assertRaises(frappe.ValidationError):
                api.simulated_deposit(amount, 'invalid')
        api.simulated_deposit(100, 'same-deposit')
        before = api.wallet()['available']
        api.simulated_deposit(100, 'same-deposit')
        self.assertEqual(api.wallet()['available'], before)
        with self.assertRaises(frappe.ValidationError):
            api.simulated_deposit(101, 'same-deposit')

    def test_11_general_approval_does_not_grant_service_scope(self):
        self.fund('p1', 1200)
        login('admin')
        other = PREFIX + '-other'
        api.save_service(other, 'Synthetic unapproved specialty')
        login('c1')
        with self.assertRaises(frappe.ValidationError):
            api.publish(other, 600, 30)
        # Simulate an existing/stale offering; no scope inferred from its existence.
        stale = secrets.token_hex(16)
        frappe.db.sql('INSERT INTO tt_offering (id,clinician,service,price,minutes,active) VALUES (%s,%s,%s,600,30,1)', (stale, USERS['c1'], other))
        login('p1')
        before = dict(api.wallet())
        self.assertEqual(api.discover(other), [])
        with self.assertRaises(frappe.ValidationError):
            api.windows(stale)
        with self.assertRaises(frappe.ValidationError):
            api.book(**booking(stale, at(8), 'unapproved-service'))
        self.assertEqual(dict(api.wallet()), before)
        login('admin')
        api.review_service_scope(USERS['c1'], other, 'Approved')
        login('c1')
        api.publish(other, 600, 30)
        login('p1')
        self.assertIn(stale, [o.id for o in api.discover(other)])
        login('admin')
        api.review_service_scope(USERS['c1'], other, 'Revoked')
        login('p1')
        self.assertEqual(api.discover(other), [])
        with self.assertRaises(frappe.ValidationError):
            api.book(**booking(stale, at(8), 'revoked-service'))
        self.assertEqual(dict(api.wallet()), before)
        login('admin')
        frappe.db.sql('UPDATE tt_application SET requested_services=%s WHERE user=%s',
                      (json.dumps([PREFIX]), USERS['c1']))
        reviewed = next(item for item in api.applications() if item.user == USERS['c1'])
        self.assertEqual(reviewed.requested_services, [PREFIX])
        self.assertEqual(reviewed.requested_service_labels, ['Synthetic test consultation'])

    def test_12_successful_retry_precedes_mutable_profile_validation(self):
        self.fund('p1', 1200)
        login('p1')
        api.save_profile('patient', 'Synthetic Original', True, history='Synthetic original history')
        args = booking(self.offers['c1'], at(8), 'retry-profile')
        args['sharing'] = {'name': True, 'history': True}
        args['expected_disclosure'] = {'request': args['request_text'], 'name': 'Synthetic Original', 'history': 'Synthetic original history'}
        result = api.book(**args)
        frappe.db.commit()
        before = dict(api.wallet())
        api.save_profile('patient', 'Synthetic Changed', True, history='Synthetic changed history', share_name=True, share_history=True)
        frappe.db.commit()
        self.assertEqual(api.book(**args)['id'], result['id'])
        self.assertEqual(dict(api.wallet()), before)
        self.assertEqual(api.one('SELECT COUNT(*) AS n FROM tt_ledger WHERE reference=%s', ('booking:' + result['id'],)).n, 1)
        for changed in ({'request_text': 'Changed synthetic request'}, {'expected_disclosure': {'request': args['request_text']}}, {'sharing': {'name': False, 'history': True}}):
            with self.assertRaises(frappe.ValidationError):
                api.book(**{**args, **changed})
        # HTTP uses another connection; release locks held by direct test calls.
        frappe.db.commit()
        client = requests.Session()
        self.assertEqual(client.post(BASE + '/api/method/login', data={'usr': USERS['p1'], 'pwd': PASSWORD}).status_code, 200)
        method = BASE + '/api/method/tele_tena.api.journey.'
        token = client.get(method + 'session').json()['message']['csrf_token']
        client.headers['X-Frappe-CSRF-Token'] = token
        replay = client.post(method + 'book', json=args)
        self.assertEqual(replay.status_code, 200, replay.json().get('tele_tena_error', 'unknown'))
        self.assertEqual(replay.json()['message']['id'], result['id'])
        changed = client.post(method + 'book', json={**args, 'request_text': 'Different synthetic HTTP retry'})
        self.assertNotEqual(changed.status_code, 200)
        self.assertEqual(changed.json()['tele_tena_error'], 'retry_changed')
        client.post(BASE + '/api/method/logout')
        # Current eligibility changes do not undo a successful command's replay.
        login('admin')
        api.review_service_scope(USERS['c1'], PREFIX, 'Revoked')
        login('p1')
        self.assertEqual(api.book(**args)['id'], result['id'])
        self.assertEqual(dict(api.wallet()), before)

    def test_13_request_overrides_never_change_profile_defaults(self):
        self.fund('p1', 1200)
        login('p1')
        api.save_profile('patient', 'Synthetic Defaults', True, history='Synthetic default history', share_name=True, share_history=True)
        api.book(**booking(self.offers['c2'], at(11), 'privacy-override'))
        p = api.profile('patient')
        self.assertEqual((p.share_name, p.share_history), (1, 1))
        # Omitted defaults during an unrelated profile edit preserve saved defaults.
        api.save_profile('patient', 'Synthetic Edited', True, history='Synthetic edited history')
        p = api.profile('patient')
        self.assertEqual((p.share_name, p.share_history), (1, 1))
        record = next(a for a in api.appointments() if a.start == api.iso(api.instant(at(11))))
        self.assertEqual(record.choices, {'name': False, 'history': False})
        self.assertEqual(record.disclosure, {'request': 'Synthetic request'})

    def test_14_native_permissions_validation_versions_and_migration_copy(self):
        from tele_tena.backoffice import scope_name
        from tele_tena.patches.v1_1_native_catalog import execute
        login('admin')
        name = scope_name(USERS['c1'], PREFIX)
        api.review_service_scope(USERS['c1'], PREFIX, 'Revoked')
        self.assertGreater(frappe.db.count('Version', {'ref_doctype': 'Tele Tena Service Scope', 'docname': name}), 0)
        login('p1')
        self.assertFalse(frappe.has_permission('Tele Tena Service Scope', 'read'))
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc('Tele Tena Service Scope', name).save()
        # Dual-role approvers cannot self-approve through generic native writes.
        frappe.set_user('Administrator')
        frappe.get_doc('User', USERS['c1']).add_roles('Tele Tena Approver')
        login('c1')
        doc = frappe.get_doc('Tele Tena Service Scope', name)
        doc.status = 'Approved'
        with self.assertRaises(frappe.PermissionError):
            doc.save()
        login('admin')
        service = frappe.get_doc('Tele Tena Service', PREFIX)
        service.service_label = 'Synthetic edited native label'
        service.save()
        execute()
        self.assertEqual(frappe.db.get_value('Tele Tena Service', PREFIX, 'service_label'), 'Synthetic edited native label')

    def test_15_consultation_authorization_window_tokens_rejoin_and_end(self):
        from tele_tena.api import consultations
        self.fund('p1', 1200)
        login('p1')
        args = booking(self.offers['c1'], at(2), 'consultation-call')
        booking_id = api.book(**args)['id']
        frappe.db.commit()
        login('p2')
        with self.assertRaises(frappe.PermissionError):
            consultations.consultation(booking_id)
        with self.assertRaises(frappe.PermissionError):
            consultations.consultation(secrets.token_hex(16))
        frappe.set_user('Guest')
        with self.assertRaises(frappe.PermissionError):
            consultations.consultation(booking_id)
        login('p1')
        with patch.object(consultations, '_window', return_value=False):
            with self.assertRaises(frappe.ValidationError):
                consultations.join(booking_id)
        with patch.object(consultations, '_window', return_value=True), \
             patch('tele_tena.livekit._credentials', return_value=('wss://example.invalid', 'key_123', 'x' * 32)):
            first = consultations.join(booking_id, audio_only=1)
        self.assertEqual(first['role'], 'patient')
        self.assertTrue(first['audio_only'])
        login('c1')
        state = consultations.consultation(booking_id)
        self.assertEqual(state['state'], 'Open')
        with patch.object(consultations, '_window', return_value=True), \
             patch('tele_tena.livekit._credentials', return_value=('wss://example.invalid', 'key_123', 'x' * 32)):
            second = consultations.join(booking_id, audio_only=0)
        self.assertEqual(first['consultation_id'], second['consultation_id'])
        import jwt
        audio_claims = jwt.decode(first['token'], options={'verify_signature': False})
        video_claims = jwt.decode(second['token'], options={'verify_signature': False})
        self.assertNotEqual(audio_claims['sub'], USERS['p1'])
        self.assertNotEqual(video_claims['sub'], USERS['c1'])
        self.assertNotEqual(audio_claims['sub'], video_claims['sub'])
        self.assertNotIn('name', audio_claims)
        self.assertNotIn('metadata', audio_claims)
        self.assertNotIn('attributes', audio_claims)
        for claims, sources in ((audio_claims, ['microphone']), (video_claims, ['microphone', 'camera'])):
            grants = claims['video']
            self.assertTrue(grants['roomJoin'])
            self.assertEqual(grants['room'], video_claims['video']['room'])
            self.assertTrue(grants['canPublish'])
            self.assertTrue(grants['canSubscribe'])
            self.assertFalse(grants['canPublishData'])
            self.assertEqual(grants['canPublishSources'], sources)
            self.assertFalse(grants.get('roomAdmin', False))
            self.assertFalse(grants.get('roomCreate', False))
            self.assertFalse(grants.get('roomRecord', False))
        seconds_remaining = video_claims['exp'] - int(datetime.now(timezone.utc).timestamp())
        self.assertTrue(60 <= seconds_remaining <= 600)
        room_names = {audio_claims['video']['room'], video_claims['video']['room']}
        self.assertEqual(len(room_names), 1)
        row = api.one('SELECT * FROM tt_consultation WHERE appointment=%s', (booking_id,))
        for value in (row.id, row.room_name, row.patient_identity, row.clinician_identity):
            self.assertNotIn('@example.invalid', value)
        # Rejoining after an ordinary participant departure reuses this open room and identity.
        login('p1')
        with patch.object(consultations, '_window', return_value=True), \
             patch('tele_tena.livekit._credentials', return_value=('wss://example.invalid', 'key_123', 'x' * 32)):
            rejoin = consultations.join(booking_id, audio_only=1)
        self.assertEqual(rejoin['consultation_id'], first['consultation_id'])
        self.assertEqual(jwt.decode(rejoin['token'], options={'verify_signature': False})['sub'], audio_claims['sub'])
        with self.assertRaises(frappe.PermissionError):
            consultations.end(booking_id)
        login('c1')
        with patch('tele_tena.api.consultations._window', return_value=False):
            with self.assertRaises(frappe.ValidationError):
                consultations.join(booking_id)
        with patch('tele_tena.livekit._credentials', return_value=('wss://example.invalid', 'key_123', 'x' * 32)), \
             patch('tele_tena.livekit.close_room', side_effect=RuntimeError('synthetic LiveKit close failure')):
            with self.assertRaises(frappe.ValidationError):
                consultations.end(booking_id)
        ended = consultations.consultation(booking_id)
        self.assertEqual(ended['state'], 'Ended')
        self.assertTrue(ended['room_close_pending'])
        self.assertTrue(ended['can_end'])
        with patch('tele_tena.livekit._credentials', return_value=('wss://example.invalid', 'key_123', 'x' * 32)), \
             patch('tele_tena.livekit.close_room') as close:
            self.assertEqual(consultations.end(booking_id), {'state': 'Ended'})
            close.assert_called_once_with(row.room_name, (row.patient_identity, row.clinician_identity))
            self.assertFalse(consultations.consultation(booking_id)['room_close_pending'])
            self.assertEqual(consultations.end(booking_id), {'state': 'Ended'})
            self.assertEqual(close.call_count, 2)
        with patch('tele_tena.livekit._credentials', return_value=('wss://example.invalid', 'key_123', 'x' * 32)):
            with self.assertRaises(frappe.ValidationError):
                consultations.join(booking_id)
        self.assertEqual(consultations.consultation(booking_id)['state'], 'Ended')

    def test_16_cloud_close_revokes_both_opaque_identities_with_future_cutoffs(self):
        from livekit import api as livekit_api
        from tele_tena import livekit
        class Room:
            def __init__(self):
                self.removed = []
                self.deleted = []
            async def remove_participant(self, request):
                self.removed.append(request)
            async def delete_room(self, request):
                self.deleted.append(request)
        class Client:
            def __init__(self):
                self.room = Room()
                self.closed = False
            async def aclose(self):
                self.closed = True
        client = Client()
        before = int(datetime.now(timezone.utc).timestamp())
        with patch('livekit.api.LiveKitAPI', return_value=client), \
             patch('tele_tena.livekit._credentials', return_value=('wss://synthetic.livekit.cloud', 'key_123', 'x' * 32)):
            livekit.close_room('opaque-room', ('opaque-patient', 'opaque-clinician'))
        self.assertEqual([item.identity for item in client.room.removed], ['opaque-patient', 'opaque-clinician'])
        self.assertTrue(all(item.room == 'opaque-room' for item in client.room.removed))
        self.assertTrue(all(before + 29 <= item.revoke_token_ts <= before + 31 for item in client.room.removed))
        self.assertEqual(len(client.room.deleted), 1)
        self.assertTrue(client.closed)

    def test_17_join_and_end_are_serialized_on_the_appointment(self):
        from tele_tena.api import consultations
        self.fund('p1', 600)
        login('p1')
        booking_id = api.book(**booking(self.offers['c1'], at(3), 'join-end-race'))['id']
        frappe.db.commit()
        token_entered = threading.Event()
        allow_token = threading.Event()
        ending_started = threading.Event()
        ended = threading.Event()
        outcome = {}
        def issue_token(*args, **kwargs):
            token_entered.set()
            if not allow_token.wait(timeout=10):
                raise RuntimeError('join race test timed out')
            return 'synthetic-token'
        def join_worker():
            connect()
            try:
                login('p1')
                with patch.object(consultations, '_window', return_value=True), \
                     patch('tele_tena.livekit._credentials', return_value=('wss://example.invalid', 'key_123', 'x' * 32)), \
                     patch('tele_tena.livekit.participant_token', side_effect=issue_token):
                    outcome['join'] = consultations.join(booking_id)
                frappe.db.commit()
            finally:
                frappe.destroy()
        def end_worker():
            connect()
            try:
                login('c1')
                ending_started.set()
                with patch('tele_tena.livekit.close_room'):
                    outcome['end'] = consultations.end(booking_id)
                frappe.db.commit()
                ended.set()
            finally:
                frappe.destroy()
        joining_thread = threading.Thread(target=join_worker)
        ending_thread = threading.Thread(target=end_worker)
        joining_thread.start()
        self.assertTrue(token_entered.wait(timeout=10))
        ending_thread.start()
        self.assertTrue(ending_started.wait(timeout=10))
        self.assertFalse(ended.wait(timeout=0.2), 'End must wait for the in-flight Join lock')
        allow_token.set()
        joining_thread.join(timeout=10)
        ending_thread.join(timeout=10)
        self.assertFalse(joining_thread.is_alive())
        self.assertFalse(ending_thread.is_alive())
        self.assertEqual(outcome['end'], {'state': 'Ended'})
        login('p1')
        self.assertEqual(consultations.consultation(booking_id)['state'], 'Ended')
        with patch.object(consultations, '_window', return_value=True):
            with self.assertRaises(frappe.ValidationError):
                consultations.join(booking_id)

    def test_15_phone_normalization_and_provider_contract(self):
        from tele_tena import sms
        self.assertEqual(phone_auth.normalize_phone('0911 234 567'), '+251911234567')
        self.assertEqual(phone_auth.normalize_phone('00251 (91) 123-4567'), '+251911234567')
        self.assertEqual(phone_auth.normalize_phone('+251911234567'), '+251911234567')
        for invalid in ('091123456', '+254711234567', '+251111234567', 'not a phone'):
            with self.assertRaises(frappe.ValidationError):
                phone_auth.normalize_phone(invalid)
        response = Mock(status_code=200)
        response.json.return_value = {'status': 'success', 'message': 'Accepted Successfully'}
        with patch.object(sms, '_config', return_value='synthetic-key'), \
             patch.object(sms.requests, 'post', return_value=response) as send:
            self.assertEqual(sms.send_otp('+251911234567', '012345'), 'accepted')
        args, kwargs = send.call_args
        self.assertEqual(args[0], 'https://smsethiopia.com/api/sms/send')
        self.assertEqual(kwargs['headers']['KEY'], 'synthetic-key')
        self.assertNotIn('Authorization', kwargs['headers'])
        self.assertEqual(kwargs['json']['msisdn'], '251911234567')
        self.assertEqual(kwargs['timeout'], (3, 8))
        self.assertIn('012345', kwargs['json']['text'])
        response.status_code = 503
        with patch.object(sms, '_config', return_value='synthetic-key'), \
             patch.object(sms.requests, 'post', return_value=response):
            with self.assertRaises(sms.SMSUncertain):
                sms.send_otp('+251911234567', '012345')

    def test_16_patient_phone_signup_is_hmac_single_use_and_privilege_bounded(self):
        import uuid
        phone = '+2519' + f'{secrets.randbelow(100_000_000):08d}'
        secret = 'test-key-' + secrets.token_hex(24)
        sent = []
        login('admin')
        frappe.set_user('Guest')
        with patch.object(phone_auth.sms, 'otp_hmac_key', return_value=secret), \
             patch.object(phone_auth.sms, 'send_otp', side_effect=lambda number, code: sent.append((number, code)) or 'accepted'), \
             patch.object(phone_auth, '_establish_login', side_effect=frappe.set_user):
            request_id = str(uuid.uuid4())
            response = contact_auth.request_code('phone', phone, request_id)
            replay = contact_auth.request_code('phone', phone, request_id)
            self.assertEqual(response['challenge_id'], replay['challenge_id'])
            self.assertEqual(len(sent), 1, 'idempotent replay must not call provider twice')
            self.assertNotIn(sent[0][1], json.dumps(response))
            digest = phone_auth._keyed('contact:phone', phone)
            track_phone(phone_auth, phone, digest)
            challenge = api.one('SELECT * FROM tt_otp_challenge WHERE id=%s', (response['challenge_id'],))
            self.assertEqual(challenge.dispatch_state, 'Accepted')
            self.assertNotIn(sent[0][1], json.dumps(dict(challenge), default=str))
            self.assertTrue(contact_auth.verify_code('phone', phone, response['challenge_id'], sent[0][1])['authenticated'])
            phone_user = frappe.session.user
            PHONE_AUTH_TEST_USERS.append(phone_user)
            self.assertEqual(frappe.get_value('User', phone_user, 'user_type'), 'Website User')
            roles = set(frappe.get_roles(phone_user))
            self.assertNotIn('Tele Tena Patient', roles)
            self.assertNotIn('Tele Tena Clinician', roles)
            self.assertNotIn('Tele Tena Approver', roles)
            self.assertFalse(frappe.db.exists('tt_profile', phone_user))
            self.assertEqual(api.one('SELECT contact FROM tt_contact_identity WHERE user=%s AND channel=%s',
                                     (phone_user, 'phone')).contact, phone)
            with self.assertRaises(frappe.ValidationError):
                contact_auth.save_onboarding('patient', 3, {'name': 'Synthetic alias', 'adult': True, 'consent': False}, 1)
            frappe.set_user(phone_user)
            contact_auth.save_onboarding('patient', 3, {'name': 'Synthetic alias', 'adult': True, 'consent': True}, 1)
            self.assertIn('Tele Tena Patient', set(frappe.get_roles(phone_user)))
            self.assertEqual(api.one('SELECT attempts FROM tt_otp_challenge WHERE id=%s',
                                     (response['challenge_id'],)).attempts, 1)
            with self.assertRaises(frappe.ValidationError):
                contact_auth.verify_code('phone', phone, response['challenge_id'], sent[0][1])
            with self.assertRaises(frappe.ValidationError):
                contact_auth.request_code('phone', phone, str(uuid.uuid4()))
            self.assertEqual(len(sent), 1, 'cooldown must not trigger another SMS')
        frappe.db.commit()

    def test_17_clinician_phone_signup_stays_unprivileged_until_manual_approval(self):
        import uuid
        phone = '+2517' + f'{secrets.randbelow(100_000_000):08d}'
        secret = 'test-key-' + secrets.token_hex(24)
        sent = []
        login('admin')
        frappe.set_user('Guest')
        with patch.object(phone_auth.sms, 'otp_hmac_key', return_value=secret), \
             patch.object(phone_auth.sms, 'send_otp', side_effect=lambda number, code: sent.append(code) or 'accepted'), \
             patch.object(phone_auth, '_establish_login', side_effect=frappe.set_user):
            response = contact_auth.request_code('phone', phone, str(uuid.uuid4()))
            digest = phone_auth._keyed('contact:phone', phone)
            track_phone(phone_auth, phone, digest)
            contact_auth.verify_code('phone', phone, response['challenge_id'], sent[0])
            phone_user = frappe.session.user
            PHONE_AUTH_TEST_USERS.append(phone_user)
            self.assertNotIn('Tele Tena Applicant', frappe.get_roles(phone_user))
            self.assertNotIn('Tele Tena Clinician', frappe.get_roles(phone_user))
            self.assertFalse(frappe.db.exists('tt_application', phone_user))
            frappe.set_user(phone_user)
            service = api.one('SELECT name AS id FROM `tabTele Tena Service` WHERE active=1 ORDER BY service_label LIMIT 1')
            contact_auth.save_onboarding('clinician', 1, {'name': 'Synthetic applicant',
                'adult': True, 'consent': True, 'requested_services': [service.id]}, 0)
            resume = ('%PDF-1.4\nSynthetic resume fixture\n%%EOF').encode('ascii')
            from tele_tena.api import presentation
            presentation.upload_resume('synthetic-resume.pdf', base64.b64encode(resume).decode('ascii'))
            contact_auth.save_onboarding('clinician', 3, {'name': 'Synthetic applicant',
                'statement': 'Synthetic application', 'adult': True, 'consent': True,
                'requested_services': [service.id]}, 1)
            self.assertIn('Tele Tena Applicant', frappe.get_roles(phone_user))
            self.assertEqual(api.one('SELECT status FROM tt_application WHERE user=%s', (phone_user,)).status, 'Pending')
            login('admin')
            api.review(phone_user, 'Approved')
            self.assertIn('Tele Tena Clinician', frappe.get_roles(phone_user),
                          'only the manual approver transition may grant clinician access')
            self.assertNotIn('Tele Tena Applicant', frappe.get_roles(phone_user))
        frappe.db.commit()

    def test_18_phone_auth_guest_csrf_and_wrong_code_attempts_are_persisted(self):
        phone = '+2519' + f'{secrets.randbelow(100_000_000):08d}'
        secret = 'test-key-' + secrets.token_hex(24)
        sent = []
        login('admin')
        frappe.set_user('Guest')
        with patch.object(phone_auth.sms, 'otp_hmac_key', return_value=secret), \
             patch.object(phone_auth.sms, 'send_otp', side_effect=lambda number, code: sent.append(code) or 'accepted'):
            response = contact_auth.request_code('phone', phone, str(uuid.uuid4()))
            digest = phone_auth._keyed('contact:phone', phone)
            track_phone(phone_auth, phone, digest)
            challenge = response['challenge_id']
            wrong_code = '000000' if sent[0] != '000000' else '000001'
            for _ in range(phone_auth.MAX_ATTEMPTS):
                with self.assertRaises(frappe.ValidationError):
                    contact_auth.verify_code('phone', phone, challenge, wrong_code)
            self.assertEqual(api.one('SELECT attempts FROM tt_otp_challenge WHERE id=%s', (challenge,)).attempts, phone_auth.MAX_ATTEMPTS)
            with self.assertRaises(frappe.ValidationError):
                contact_auth.verify_code('phone', phone, challenge, sent[0])
        frappe.db.commit()
        client = requests.Session()
        url = BASE + '/api/method/tele_tena.api.contact_auth.'
        # CSRF issuance remains on the shared legacy-named helper.
        token_response = client.get(BASE + '/api/method/tele_tena.api.phone_auth.csrf_token')
        self.assertEqual(token_response.status_code, 200)
        payload = {'channel': 'invalid', 'contact': phone, 'request_id': str(uuid.uuid4())}
        self.assertNotEqual(client.post(url + 'request_code', json=payload).status_code, 200)
        client.headers['X-Frappe-CSRF-Token'] = token_response.json()['message']['csrf_token']
        rejected = client.post(url + 'request_code', json=payload)
        self.assertNotEqual(rejected.status_code, 200)
        self.assertEqual(rejected.json()['tele_tena_error'], 'invalid_contact')

    def test_19_uncertain_sms_is_never_retried_and_limits_are_enforced(self):
        import uuid
        from tele_tena import sms
        secret = 'test-key-' + secrets.token_hex(24)
        phone = '+2519' + f'{secrets.randbelow(100_000_000):08d}'
        login('admin')
        frappe.set_user('Guest')
        with patch.object(phone_auth.sms, 'otp_hmac_key', return_value=secret), \
             patch.object(phone_auth.sms, 'send_otp', side_effect=sms.SMSUncertain('provider_outcome_unknown')) as send:
            first_id = str(uuid.uuid4())
            first = contact_auth.request_code('phone', phone, first_id)
            replay = contact_auth.request_code('phone', phone, first_id)
            digest = phone_auth._keyed('contact:phone', phone)
            track_phone(phone_auth, phone, digest)
            self.assertEqual(first['challenge_id'], replay['challenge_id'])
            self.assertEqual(first['delivery_state'], 'uncertain')
            self.assertEqual(send.call_count, 1)
            self.assertEqual(api.one('SELECT dispatch_state FROM tt_otp_challenge WHERE id=%s',
                                     (first['challenge_id'],)).dispatch_state, 'Uncertain')

        capped_phone = '+2517' + f'{secrets.randbelow(100_000_000):08d}'
        digest = phone_auth._keyed('contact:phone', capped_phone)
        track_phone(phone_auth, capped_phone, digest)
        increment = contact_auth.otp._increment_limit
        with patch.object(phone_auth.sms, 'otp_hmac_key', return_value=secret), \
             patch.object(contact_auth.otp, '_increment_limit',
                           side_effect=lambda kind, *args: False if kind == 'contact-window' else increment(kind, *args)), \
             patch.object(phone_auth.sms, 'send_otp') as send:
            with self.assertRaises(frappe.ValidationError):
                contact_auth.request_code('phone', capped_phone, str(uuid.uuid4()))
            send.assert_not_called()

        ip = 'synthetic-test-peer-' + secrets.token_hex(8)
        ip_phone = '+2519' + f'{secrets.randbelow(100_000_000):08d}'
        ip_digest = phone_auth._keyed('contact:phone', ip_phone)
        track_phone(phone_auth, ip_phone, ip_digest, ip)
        increment = contact_auth.otp._increment_limit
        with patch.object(phone_auth.sms, 'otp_hmac_key', return_value=secret), \
             patch.object(phone_auth, '_peer_ip', return_value=ip), \
             patch.object(contact_auth.otp, '_increment_limit',
                           side_effect=lambda kind, *args: False if kind == 'contact-ip' else increment(kind, *args)), \
             patch.object(phone_auth.sms, 'send_otp') as send:
            with self.assertRaises(frappe.ValidationError):
                contact_auth.request_code('phone', ip_phone, str(uuid.uuid4()))
            send.assert_not_called()
        frappe.db.commit()

    def test_20_concurrent_phone_attempts_and_success_are_atomic(self):
        import uuid
        phone = '+2519' + f'{secrets.randbelow(100_000_000):08d}'
        secret = 'test-key-' + secrets.token_hex(24)
        sent = []
        login('admin')
        frappe.set_user('Guest')
        with patch.object(phone_auth.sms, 'otp_hmac_key', return_value=secret), \
             patch.object(phone_auth.sms, 'send_otp', side_effect=lambda number, code: sent.append(code) or 'accepted'):
            response = contact_auth.request_code('phone', phone, str(uuid.uuid4()))
            digest = phone_auth._keyed('contact:phone', phone)
            track_phone(phone_auth, phone, digest)
        frappe.db.commit()
        wrong = '000000' if sent[0] != '000000' else '000001'

        def verify_worker(code):
            connect()
            try:
                frappe.set_user('Guest')
                with patch.object(phone_auth.sms, 'otp_hmac_key', return_value=secret):
                    contact_auth.verify_code('phone', phone, response['challenge_id'], code)
                    frappe.db.commit()
                    return 'ok'
            except frappe.ValidationError:
                frappe.db.rollback()
                return 'rejected'
            finally:
                frappe.destroy()

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            wrong_results = list(pool.map(verify_worker, [wrong, wrong]))
        self.assertEqual(wrong_results, ['rejected', 'rejected'])
        self.assertEqual(api.one('SELECT attempts FROM tt_otp_challenge WHERE id=%s', (response['challenge_id'],)).attempts, 2)
        frappe.db.commit()
        with patch.object(phone_auth, '_establish_login', side_effect=frappe.set_user):
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                success_results = list(pool.map(verify_worker, [sent[0], sent[0]]))
        self.assertEqual(success_results.count('ok'), 1)
        frappe.db.commit()
        identity = frappe.db.sql('SELECT user FROM tt_contact_identity WHERE contact=%s AND channel=%s',
                                 (phone, 'phone'), as_dict=True)
        self.assertTrue(identity)
        identity = identity[0]
        PHONE_AUTH_TEST_USERS.append(identity.user)
        # The duplicate successful retry is rejected and still consumes a
        # verification attempt, so the durable counter is 2 wrong + 1 success
        # + 1 replay rejection.
        self.assertEqual(api.one('SELECT attempts FROM tt_otp_challenge WHERE id=%s', (response['challenge_id'],)).attempts, 4)
        self.assertIsNotNone(api.one('SELECT consumed FROM tt_otp_challenge WHERE id=%s', (response['challenge_id'],)).consumed)


PHONE_AUTH_TEST_DIGESTS = []
PHONE_AUTH_TEST_BUCKET_KEYS = []
PHONE_AUTH_TEST_USERS = []


def track_phone(phone_auth_module, phone, phone_digest, peer='unknown-peer'):
    PHONE_AUTH_TEST_DIGESTS.append(phone_digest)
    for kind, subject in (
        ('limit:phone-window', phone_digest), ('limit:phone-day', phone_digest),
        ('limit:ip-window', peer), ('limit:verify-phone', phone_digest),
        ('limit:verify-ip', peer),
        ('limit:contact-window', phone_digest), ('limit:contact-day', phone_digest),
        ('limit:contact-ip', peer), ('limit:contact-verify', phone_digest),
        ('limit:contact-verify-ip', peer),
    ):
        PHONE_AUTH_TEST_BUCKET_KEYS.append(phone_auth_module._keyed(kind, subject))


if __name__ == '__main__':
    unittest.main(verbosity=2)
