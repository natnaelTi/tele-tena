"""Run with bench env Python. Real isolated-site MariaDB tests; synthetic only."""
import concurrent.futures
import json
import os
from pathlib import Path
import secrets
import sys
import threading
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import requests

BENCH = Path(__file__).resolve().parents[3]
os.chdir(BENCH / 'sites')
sys.path.insert(0, str(BENCH / 'apps/frappe'))
import frappe
from frappe.utils.password import update_password
from tele_tena.api import journey as api

SITE = 'erp.localhost'
PREFIX = 'tt-test-' + secrets.token_hex(5)
USERS = {kind: PREFIX + '-' + kind + '@example.invalid' for kind in ('p1', 'p2', 'c1', 'c2', 'c3', 'admin')}
PASSWORD = secrets.token_urlsafe(24)
BASE = 'http://127.0.0.1:5173'


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
        scope_names = frappe.db.sql('SELECT name FROM `tabTele Tena Service Scope` WHERE clinician IN %s', (tuple(USERS.values()),), pluck=True)
        for name in scope_names:
            frappe.db.sql('DELETE FROM tabVersion WHERE ref_doctype=%s AND docname=%s', ('Tele Tena Service Scope', name))
            frappe.db.sql('DELETE FROM `tabTele Tena Service Scope` WHERE name=%s', (name,))
        for name in (PREFIX, PREFIX + '-other'):
            frappe.db.sql('DELETE FROM tabVersion WHERE ref_doctype=%s AND docname=%s', ('Tele Tena Service', name))
            frappe.db.sql('DELETE FROM `tabTele Tena Service` WHERE name=%s', (name,))
        # Explicit synthetic fixture cleanup; never touch non-test records.
        for table, field in (('audit', 'subject'), ('ledger', 'patient'), ('appointment', 'patient'), ('wallet', 'patient'),
                             ('availability', 'clinician'), ('offering', 'clinician'), ('application', 'user'), ('profile', 'user')):
            for email in USERS.values():
                if table == 'appointment':
                    frappe.db.sql('DELETE FROM tt_consultation WHERE appointment IN (SELECT id FROM tt_appointment WHERE patient=%s OR clinician=%s)', (email, email))
                frappe.db.sql(f'DELETE FROM tt_{table} WHERE {field}=%s', (email,))
        frappe.db.sql('DELETE FROM tt_service WHERE id=%s', (PREFIX,))
        frappe.set_user('Administrator')
        for email in USERS.values():
            frappe.delete_doc('User', email)
        frappe.db.commit()
        frappe.destroy()

    def tearDown(self):
        frappe.db.rollback()

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
        login('p2')
        # Reset synthetic test-only balance using SQL; not an application command.
        frappe.db.sql('UPDATE tt_wallet SET available=600 WHERE patient=%s', (USERS['p2'],))
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
            close.assert_called_once_with(row.room_name)
            self.assertFalse(consultations.consultation(booking_id)['room_close_pending'])
            self.assertEqual(consultations.end(booking_id), {'state': 'Ended'})
            self.assertEqual(close.call_count, 2)
        with patch('tele_tena.livekit._credentials', return_value=('wss://example.invalid', 'key_123', 'x' * 32)):
            with self.assertRaises(frappe.ValidationError):
                consultations.join(booking_id)
        self.assertEqual(consultations.consultation(booking_id)['state'], 'Ended')


if __name__ == '__main__':
    unittest.main(verbosity=2)
