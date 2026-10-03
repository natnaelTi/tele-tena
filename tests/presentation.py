"""State, recurring calendar and private-record regressions on isolated synthetic fixtures."""
import base64
import concurrent.futures
import importlib.util
import json
import secrets
import sys
import unittest
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fixtures', APP / 'tests/integration.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
import frappe
from tele_tena.api import journey
from tele_tena.api import presentation
from tele_tena.api import scheduling


def day_offset(days=14, weekday=None, zone='Africa/Addis_Ababa'):
    local = datetime.now(ZoneInfo(zone)).date() + timedelta(days=days)
    if weekday is not None:
        local += timedelta(days=(weekday - local.weekday()) % 7)
    return local


def schedule_payload(offering, day, mode='manual', zone='Africa/Addis_Ababa', exceptions=None):
    weekday = day.weekday()
    return dict(offering=offering, schedule_name='Synthetic weekly hours', timezone_name=zone,
                consultation_format='video', confirmation_mode=mode,
                minimum_notice_minutes=60, horizon_days=60, buffer_before=15,
                buffer_after=15, intervals=[{'weekday': weekday, 'start': '09:00', 'end': '12:00'},
                                           {'weekday': weekday, 'start': '14:00', 'end': '16:00'}],
                exceptions=exceptions or [], status='Published')


class Presentation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.Integration.setUpClass()

    @classmethod
    def tearDownClass(cls):
        fixtures.Integration.tearDownClass()

    def setUp(self):
        fixtures.login('admin')

    def fund_patient(self, kind='p1', amount=10000):
        fixtures.login(kind)
        journey.simulated_deposit(amount, secrets.token_hex(12))
        frappe.db.commit()

    def make_schedule(self, day=None, mode='manual', exceptions=None, offering=None):
        day = day or day_offset()
        fixtures.login('c1')
        payload = schedule_payload(offering or fixtures.Integration.offers['c1'], day,
                                   mode=mode, exceptions=exceptions)
        result = scheduling.save_schedule(**payload)
        frappe.db.commit()
        return day, result['id'], payload

    def slots(self, offering, day, who='p1', zone='Africa/Addis_Ababa'):
        fixtures.login(who)
        result = scheduling.calendar(offering, day.isoformat(), 1, zone)
        return [slot for item in result['days'] for slot in item['slots']]

    def book_slot(self, offering, slot, key=None, share_name=False, who='p1'):
        fixtures.login(who)
        request = 'A synthetic request for a presentation test'
        sharing = {'name': share_name, 'history': False}
        preview = journey.preview(request, sharing)['disclosure']
        start = slot['start']
        price = int(journey.one('SELECT price FROM tt_offering WHERE id=%s', (offering,)).price)
        return journey.book(offering=offering, start=start, request_text=request, sharing=sharing,
                            retry_key=key or secrets.token_hex(8), expected_price=price,
                            expected_minutes=30, expected_disclosure=preview,
                            booked_timezone=slot['timezone'])

    def test_01_recurrence_exceptions_timezone_and_dst(self):
        day = day_offset(14)
        exceptions = [
            {'date': day.isoformat(), 'kind': 'break', 'start': '10:00', 'end': '10:30'},
            {'date': (day + timedelta(days=1)).isoformat(), 'kind': 'replace', 'start': '11:00', 'end': '12:00'},
            {'date': (day + timedelta(days=2)).isoformat(), 'kind': 'unavailable'},
        ]
        day, _, saved = self.make_schedule(day, exceptions=exceptions)
        self.assertEqual(saved['timezone_name'], 'Africa/Addis_Ababa')
        slots = self.slots(fixtures.Integration.offers['c1'], day)
        times = {slot['local_time'] for slot in slots}
        self.assertIn('09:00', times)
        self.assertNotIn('10:00', times)
        self.assertIn('10:30', times)
        self.assertIn('11:00', times)
        for offset, expected in ((1, {'11:00', '11:15', '11:30'}), (2, set())):
            day_slots = self.slots(fixtures.Integration.offers['c1'], day + timedelta(days=offset))
            self.assertEqual({s['local_time'] for s in day_slots}, expected)
        new_york = ZoneInfo('America/New_York')
        self.assertIsNone(scheduling._valid_local(datetime(2026, 3, 8, 2, 30), new_york))
        self.assertIsNone(scheduling._valid_local(datetime(2026, 11, 1, 1, 30), new_york))

    def test_schedule_ui_payload_roundtrips_html_time_values(self):
        day = day_offset(18)
        fixtures.login('c1')
        payload = schedule_payload(fixtures.Integration.offers['c1'], day)
        payload['intervals'] = [
            {'weekday': item['weekday'], 'start_local': item['start'], 'end_local': item['end']}
            for item in payload['intervals']
        ]
        result = scheduling.save_schedule(**payload)
        frappe.db.commit()
        loaded = next(item for item in scheduling.schedules() if item.id == result['id'])
        self.assertEqual(
            [(item.start_local, item.end_local) for item in loaded.intervals],
            [('09:00', '12:00'), ('14:00', '16:00')],
        )

    def test_schedule_invalid_intervals_are_specific_and_atomic(self):
        day = day_offset(19)
        _, schedule_id, payload = self.make_schedule(day)
        original = frappe.db.sql('''SELECT weekday,start_local,end_local FROM tt_schedule_rule
            WHERE schedule_id=%s ORDER BY weekday,start_local''', (schedule_id,))
        fixtures.login('c1')
        invalid = {**payload, 'intervals': [
            {'weekday': day.weekday(), 'start_local': '09:00', 'end_local': '11:00'},
            {'weekday': day.weekday(), 'start_local': '10:30', 'end_local': '12:00'},
        ]}
        with self.assertRaises(frappe.ValidationError):
            scheduling.save_schedule(**invalid)
        self.assertEqual(frappe.local.response.get('tele_tena_error'), 'schedule_interval_overlap')
        after = frappe.db.sql('''SELECT weekday,start_local,end_local FROM tt_schedule_rule
            WHERE schedule_id=%s ORDER BY weekday,start_local''', (schedule_id,))
        self.assertEqual(after, original)
        invalid['intervals'] = [{'weekday': day.weekday(), 'start_local': '12:00', 'end_local': '11:00'}]
        with self.assertRaises(frappe.ValidationError):
            scheduling.save_schedule(**invalid)
        self.assertEqual(frappe.local.response.get('tele_tena_error'), 'schedule_interval_order')

    def test_other_clinician_cannot_change_schedule(self):
        day, schedule_id, payload = self.make_schedule(day_offset(20))
        before = frappe.db.sql('''SELECT weekday,start_local,end_local FROM tt_schedule_rule
            WHERE schedule_id=%s ORDER BY weekday,start_local''', (schedule_id,))
        fixtures.login('c2')
        with self.assertRaises(frappe.ValidationError):
            scheduling.save_schedule(**payload)
        after = frappe.db.sql('''SELECT weekday,start_local,end_local FROM tt_schedule_rule
            WHERE schedule_id=%s ORDER BY weekday,start_local''', (schedule_id,))
        self.assertEqual(after, before)

    def test_balanced_earnings_dispute_release_and_payout(self):
        from tele_tena import accounting
        offering = fixtures.Integration.offers['c1']
        fixtures.login('c1')
        journey.publish(fixtures.PREFIX, 30000, 30)
        with patch.dict(frappe.conf, {'tele_tena_demo_platform_fee_bps': 0,
                                     'tele_tena_demo_dispute_window_minutes': 0}):
            fixtures.login('p2')
            before_wallet = journey.wallet()
            self.fund_patient(kind='p2', amount=100000)
            day, _, _ = self.make_schedule(mode='automatic', offering=offering)
            slot = self.slots(offering, day)[0]
            booked = self.book_slot(offering, slot, 'earnings-acceptance', who='p2')
            patient = fixtures.USERS['p2']
            self.assertEqual(journey.wallet()['available'], before_wallet['available'] + 70000)
            self.assertEqual(journey.wallet()['reserved'], before_wallet['reserved'] + 30000)
            self.assertEqual(accounting.balance('patient', patient, 'available'), before_wallet['available'] + 70000)
            self.assertEqual(accounting.balance('patient', patient, 'reserved'), before_wallet['reserved'] + 30000)
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            frappe.db.sql('''INSERT INTO tt_consultation
                (appointment,id,room_name,patient_identity,clinician_identity,state,created,ended)
                VALUES (%s,%s,%s,%s,%s,'Ended',%s,%s)''',
                (booked['id'], str(uuid.uuid4()), uuid.uuid4().hex, uuid.uuid4().hex,
                 uuid.uuid4().hex, now, now))
            fixtures.login('c1')
            presentation.save_note_draft(booked['id'], 'Synthetic private note', 'Synthetic patient summary')
            with patch.dict(frappe.conf, {'tele_tena_demo_platform_fee_bps': 5000,
                                         'tele_tena_demo_dispute_window_minutes': 100}):
                presentation.finalize_consultation(booked['id'], 1)
                self.assertEqual(presentation.finalize_consultation(booked['id'], 1)['idempotent'], True)
            accepted_earning = journey.one('SELECT fee_minor,release_at,policy_snapshot FROM tt_earning WHERE appointment=%s',
                                           (booked['id'],))
            self.assertEqual(int(accepted_earning.fee_minor), 0)
            self.assertEqual(json.loads(accepted_earning.policy_snapshot)['dispute_window_minutes'], 0)
            fixtures.login('p2')
            self.assertEqual(journey.wallet()['reserved'], before_wallet['reserved'])
            clinician = fixtures.USERS['c1']
            before_pending = accounting.balance('clinician', clinician, 'pending') - 30000
            self.assertGreaterEqual(before_pending, 0)
            self.assertEqual(accounting.balance('clinician', clinician, 'pending'), before_pending + 30000)
            self.assertEqual(journey.one('SELECT COUNT(*) n FROM tt_journal WHERE event_ref=%s',
                                         ('completion:' + booked['id'],)).n, 1)
            fixtures.login('p2')
            patient_refs = {item.event_ref for item in presentation.wallet_summary()['activity'] if hasattr(item, 'event_ref')}
            fixtures.login('c1')
            clinician_refs = {item.event_ref for item in accounting.clinician_earnings()['activity']}
            self.assertIn('completion:' + booked['id'], patient_refs)
            self.assertIn('completion:' + booked['id'], clinician_refs)
            frappe.db.sql('UPDATE tt_earning SET release_at=UTC_TIMESTAMP(6)-INTERVAL 1 SECOND WHERE appointment=%s',
                          (booked['id'],))
            frappe.db.commit()
            accounting.release_eligible_earnings()
            accounting.release_eligible_earnings()
            self.assertEqual(accounting.balance('clinician', clinician, 'pending'), before_pending)
            before_available = accounting.balance('clinician', clinician, 'earnings_available') - 30000
            self.assertGreaterEqual(before_available, 0)
            self.assertEqual(accounting.balance('clinician', clinician, 'earnings_available'), before_available + 30000)
            payout = accounting.request_payout(20000, 'payout-acceptance')
            balances = accounting.clinician_earnings()['balances']
            self.assertEqual(balances['earnings_available'], before_available + 10000)
            self.assertEqual(balances['payout_reserved'], 20000)
            with self.assertRaises(frappe.ValidationError):
                accounting.request_payout(20000, 'payout-insufficient')
            self.assertEqual(accounting.cancel_payout(payout['id'], 'Synthetic cancel')['state'], 'Cancelled')
            self.assertTrue(accounting.cancel_payout(payout['id'], 'Synthetic cancel')['idempotent'])
            self.assertEqual(accounting.clinician_earnings()['balances']['earnings_available'], before_available + 30000)

    def test_dispute_serializes_release_and_resolves_as_refund(self):
        from tele_tena import accounting
        offering = fixtures.Integration.offers['c1']
        fixtures.login('c1')
        journey.publish(fixtures.PREFIX, 600, 30)
        with patch.dict(frappe.conf, {'tele_tena_demo_platform_fee_bps': 0,
                                     'tele_tena_demo_dispute_window_minutes': 60}):
            fixtures.login('p2')
            before_wallet = journey.wallet()
            self.fund_patient(kind='p2', amount=5000)
            day, _, _ = self.make_schedule(mode='automatic', offering=offering)
            booked = self.book_slot(offering, self.slots(offering, day, who='p2')[0], 'earnings-dispute', who='p2')
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            frappe.db.sql('''INSERT INTO tt_consultation
                (appointment,id,room_name,patient_identity,clinician_identity,state,created,ended)
                VALUES (%s,%s,%s,%s,%s,'Ended',%s,%s)''',
                (booked['id'], str(uuid.uuid4()), uuid.uuid4().hex, uuid.uuid4().hex,
                 uuid.uuid4().hex, now, now))
            fixtures.login('c1')
            presentation.save_note_draft(booked['id'], 'Synthetic private note', 'Synthetic summary')
            presentation.finalize_consultation(booked['id'], 0)
            fixtures.login('p2')
            self.assertEqual(accounting.open_earning_dispute(booked['id'], 'Synthetic dispute')['state'], 'Disputed')
            frappe.db.sql('UPDATE tt_earning SET release_at=UTC_TIMESTAMP(6)-INTERVAL 1 SECOND WHERE appointment=%s',
                          (booked['id'],))
            frappe.db.commit()
            accounting.release_eligible_earnings()
            clinician = fixtures.USERS['c1']
            before_pending = accounting.balance('clinician', clinician, 'pending')
            earning = journey.one('SELECT state FROM tt_earning WHERE appointment=%s', (booked['id'],))
            self.assertEqual(earning.state, 'Disputed')
            fixtures.login('admin')
            self.assertEqual(accounting.resolve_earning_dispute(booked['id'], 'refund', 'Synthetic resolution')['resolution'], 'refund')
            self.assertEqual(accounting.resolve_earning_dispute(booked['id'], 'refund', 'Synthetic resolution')['idempotent'], True)
            self.assertEqual(accounting.balance('clinician', clinician, 'pending'), before_pending - 600)
            fixtures.login('p2')
            self.assertEqual(journey.wallet()['available'], before_wallet['available'] + 5000)
            self.assertEqual(journey.wallet()['reserved'], before_wallet['reserved'])
            self.assertEqual(journey.one('SELECT COUNT(*) n FROM tt_journal WHERE event_ref=%s',
                                         ('earning-refund:' + journey.one('SELECT id FROM tt_earning WHERE appointment=%s', (booked['id'],)).id,)).n, 1)

    def test_release_first_closes_automated_dispute_refund_path(self):
        from tele_tena import accounting
        offering = fixtures.Integration.offers['c1']
        self.fund_patient('p2', 1000)
        day, _, _ = self.make_schedule(mode='automatic', offering=offering)
        booked = self.book_slot(offering, self.slots(offering, day, who='p2')[0], 'release-wins', who='p2')
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        frappe.db.sql('''INSERT INTO tt_consultation
            (appointment,id,room_name,patient_identity,clinician_identity,state,created,ended)
            VALUES (%s,%s,%s,%s,%s,'Ended',%s,%s)''',
            (booked['id'], str(uuid.uuid4()), uuid.uuid4().hex, uuid.uuid4().hex,
             uuid.uuid4().hex, now, now))
        fixtures.login('c1')
        presentation.save_note_draft(booked['id'], 'Synthetic private note', '')
        presentation.finalize_consultation(booked['id'], 0)
        frappe.db.sql('UPDATE tt_earning SET release_at=UTC_TIMESTAMP(6)-INTERVAL 1 SECOND WHERE appointment=%s',
                      (booked['id'],))
        frappe.db.commit()
        accounting.release_eligible_earnings()
        earning = journey.one('SELECT id,state FROM tt_earning WHERE appointment=%s', (booked['id'],))
        self.assertEqual(earning.state, 'Released')
        fixtures.login('p2')
        with self.assertRaises(frappe.ValidationError):
            accounting.open_earning_dispute(booked['id'], 'Synthetic late dispute')
        self.assertEqual(journey.one('SELECT COUNT(*) n FROM tt_dispute WHERE earning=%s', (earning.id,)).n, 0)
        self.assertEqual(journey.one('SELECT COUNT(*) n FROM tt_journal WHERE event_ref=%s',
                                     ('earning-refund:' + earning.id,)).n, 0)

    def test_concurrent_payouts_cannot_overreserve_earnings(self):
        from tele_tena import accounting
        clinician = fixtures.USERS['c2']
        account = accounting.account_id('clinician', clinician, 'earnings_available')
        control = accounting.account_id('', '', 'opening_control')
        accounting.post('test-payout-opening:' + clinician, 'TestOpening',
                        'test-payout-opening:' + clinician,
                        [(control, 30000, 0), (account, 0, 30000)], {'synthetic': True})
        frappe.db.commit()
        barrier = threading.Barrier(2)
        def request(key):
            fixtures.connect()
            try:
                fixtures.login('c2')
                barrier.wait(timeout=10)
                result = accounting.request_payout(20000, key)
                frappe.db.commit()
                return 'ok', result['id']
            except frappe.ValidationError:
                frappe.db.rollback()
                return 'insufficient', None
            finally:
                frappe.destroy()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(request, ('concurrent-payout-a', 'concurrent-payout-b')))
        frappe.db.rollback()
        self.assertEqual(sum(result[0] == 'ok' for result in results), 1)
        self.assertEqual(accounting.balance('clinician', clinician, 'earnings_available'), 10000)
        self.assertEqual(accounting.balance('clinician', clinician, 'payout_reserved'), 20000)
        fixtures.login('c2')
        self.assertEqual(len(accounting.clinician_earnings()['payouts']), 1)
        fixtures.login('c1')
        self.assertNotIn(results[0][1] or results[1][1],
                         [item.id for item in accounting.clinician_earnings()['payouts']])
        fixtures.login('p1')
        with self.assertRaises(frappe.PermissionError):
            accounting.clinician_earnings()

    def test_02_manual_hold_confirm_cancel_and_expiry_release_once(self):
        self.fund_patient(amount=5000)
        day, _, _ = self.make_schedule()
        offering = fixtures.Integration.offers['c1']
        first = self.slots(offering, day)[0]
        booked = self.book_slot(offering, first, 'manual-confirm')
        self.assertEqual(booked['state'], 'PendingConfirmation')
        self.assertEqual(journey.wallet()['reserved'], 600)
        fixtures.login('c1')
        self.assertEqual(presentation.respond_to_request(booked['id'], 'confirm')['state'], 'Booked')
        self.assertEqual(presentation.respond_to_request(booked['id'], 'confirm')['idempotent'], True)
        fixtures.login('p1')
        self.assertTrue(presentation.cancel_appointment(booked['id'], 'Plans changed')['released'])
        self.assertTrue(presentation.cancel_appointment(booked['id'], 'Plans changed')['idempotent'])
        self.assertEqual(journey.wallet()['reserved'], 0)
        release_count = journey.one('SELECT COUNT(*) n FROM tt_ledger WHERE reference=%s',
                                    ('release:' + booked['id'],)).n
        second = self.slots(offering, day)[0]
        next_booking = self.book_slot(offering, second, 'manual-expiry')
        frappe.db.sql('UPDATE tt_appointment SET expires_at=UTC_TIMESTAMP(6)-INTERVAL 1 MINUTE WHERE id=%s',
                      (next_booking['id'],))
        frappe.db.commit()
        presentation.expire_pending_appointments()
        presentation.expire_pending_appointments()
        state = journey.one('SELECT state FROM tt_appointment WHERE id=%s', (next_booking['id'],)).state
        self.assertEqual(state, 'Expired')
        count = journey.one('SELECT COUNT(*) n FROM tt_ledger WHERE reference=%s',
                            ('release:' + next_booking['id'],)).n
        self.assertEqual(release_count, 1)
        self.assertEqual(count, 1)
        self.assertEqual(journey.wallet()['reserved'], 0)

    def test_03_global_conflict_across_offerings_and_timezone_snapshot(self):
        self.fund_patient('p1', 4000)
        fixtures.login('admin')
        service2 = fixtures.PREFIX + '-second-service'
        journey.save_service(service2, 'Synthetic second service')
        journey.review_service_scope(fixtures.USERS['c1'], service2, 'Approved')
        fixtures.login('c1')
        journey.publish(service2, 600, 30)
        offering2 = journey.one('SELECT id FROM tt_offering WHERE clinician=%s AND service=%s',
                                (fixtures.USERS['c1'], service2)).id
        day, _, _ = self.make_schedule(offering=offering2)
        offering1 = fixtures.Integration.offers['c1']
        # Both service schedules expose the same weekly interval; edits preserve saved instants.
        fixtures.login('c1')
        scheduling.save_schedule(**schedule_payload(offering1, day, mode='automatic'))
        frappe.db.commit()
        slot = self.slots(offering1, day)[0]
        first = self.book_slot(offering1, slot, 'global-conflict')
        fixtures.login('p2')
        journey.simulated_deposit(1000, secrets.token_hex(12))
        frappe.db.commit()
        second_slot = slot
        with self.assertRaises(frappe.ValidationError):
            self.book_slot(offering2, second_slot, 'other-offering', who='p2')
        original = journey.one('SELECT start,timezone FROM tt_appointment WHERE id=%s', (first['id'],))
        fixtures.login('c1')
        changed = schedule_payload(offering1, day, zone='UTC', mode='automatic')
        scheduling.save_schedule(**changed)
        after = journey.one('SELECT start,timezone FROM tt_appointment WHERE id=%s', (first['id'],))
        self.assertEqual(after.start, original.start)
        self.assertEqual(after.timezone, 'Africa/Addis_Ababa')

    def test_04_notes_privacy_revision_completion_and_encounter_scope(self):
        self.fund_patient('p1', 3000)
        day, _, _ = self.make_schedule(mode='automatic')
        offering = fixtures.Integration.offers['c1']
        slot = self.slots(offering, day)[0]
        booked = self.book_slot(offering, slot, 'notes-privacy', share_name=False)
        appointment = booked['id']
        fixtures.login('c1')
        directory = presentation.care_directory(page=1, page_size=5)
        record = next(row for row in directory['rows'] if row['id'] == appointment)
        self.assertEqual(record['patient_label'], 'Private patient')
        self.assertNotIn('patient', record)
        person = presentation.care_patient_record(appointment)
        self.assertEqual(len(person['encounters']), 1)
        self.assertEqual(person['encounters'][0]['patient_identity'], 'Private patient')
        with self.assertRaises(frappe.PermissionError):
            presentation.care_detail('not-this-clinician-record')
        fixtures.login('p2')
        with self.assertRaises(frappe.PermissionError):
            presentation.care_detail(appointment)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        clinician = fixtures.USERS['c1']
        frappe.db.sql('''INSERT INTO tt_consultation
            (appointment,id,room_name,patient_identity,clinician_identity,state,created,ended_by,ended,room_closed)
            VALUES (%s,%s,%s,%s,%s,'Ended',%s,%s,%s,1)''',
            (appointment, secrets.token_hex(16), secrets.token_hex(32), secrets.token_hex(24),
             secrets.token_hex(24), now, clinician, now))
        frappe.db.commit()
        fixtures.login('c1')
        presentation.save_note_draft(appointment, 'Private synthetic observation', 'Helpful next steps')
        detail = presentation.appointment_detail(appointment)
        self.assertEqual(detail['documentation_state'], 'Draft')
        self.assertEqual(detail['private_note']['text'], 'Private synthetic observation')
        fixtures.login('c2')
        with self.assertRaises(frappe.PermissionError):
            presentation.appointment_detail(appointment)
        fixtures.login('p1')
        patient_detail = presentation.appointment_detail(appointment)
        self.assertNotIn('private_note', patient_detail)
        self.assertNotIn('Private synthetic observation', str(patient_detail))
        fixtures.login('admin')
        with self.assertRaises(frappe.PermissionError):
            presentation.appointment_detail(appointment)
        fixtures.login('c1')
        presentation.finalize_consultation(appointment, 1)
        self.assertEqual(journey.one('SELECT state FROM tt_appointment WHERE id=%s', (appointment,)).state,
                         'Completed')
        fixtures.login('p1')
        shared = presentation.appointment_detail(appointment)
        self.assertNotIn('private_note', shared)
        self.assertEqual(shared['patient_summary_revisions'][0]['summary'], 'Helpful next steps')
        fixtures.login('c1')
        presentation.save_note_draft(appointment, 'Amended private observation', 'New next steps')
        presentation.finalize_consultation(appointment, 0)
        fixtures.login('p1')
        history = presentation.appointment_detail(appointment)['patient_summary_revisions']
        self.assertEqual([item['summary'] for item in history], ['Helpful next steps'])

    def test_05_private_resume_scope_application_evidence_and_tour_preferences(self):
        clinician = fixtures.USERS['c3']
        pdf = b'%PDF-1.7\n1 0 obj<</Type/Catalog>>endobj\n%%EOF\n'
        encoded = base64.b64encode(pdf).decode()
        fixtures.login('c3')
        # The shared integration fixture has an existing synthetic submission;
        # rewind only that disposable row to model upload-before-submit.
        frappe.db.sql('DELETE FROM tt_application WHERE user=%s', (clinician,))
        uploaded = presentation.upload_resume('synthetic resume.pdf', encoded)
        self.assertTrue(uploaded['uploaded'])
        self.assertTrue(presentation.resume_status()['uploaded'])
        from tele_tena.account_context import authorized_user_change
        user_doc = frappe.get_doc('User', clinician)
        with authorized_user_change():
            user_doc.remove_roles('Tele Tena Clinician')
        self.assertEqual(presentation.tour_state('clinician-onboarding')['role'], 'applicant')
        with authorized_user_change():
            user_doc.add_roles('Tele Tena Clinician')
        with self.assertRaises(frappe.ValidationError):
            presentation.upload_resume('resume.pdf', base64.b64encode(b'not a pdf %%EOF').decode())
        services = [fixtures.PREFIX]
        journey.apply('Synthetic application narrative', services)
        with self.assertRaises(frappe.ValidationError):
            presentation.remove_resume()
        fixtures.login('admin')
        item = next(a for a in journey.applications() if a.user == clinician)
        self.assertEqual(item.display_name, 'Synthetic Test')
        self.assertEqual(item.requested_services, services)
        self.assertTrue(item.resume_uploaded)
        fixtures.login('p1')
        with self.assertRaises(frappe.PermissionError):
            presentation.download_resume(clinician)
        fixtures.login('admin')
        presentation.download_resume(clinician)
        self.assertEqual(frappe.local.response.filename, 'synthetic resume.pdf')
        fixtures.login('p1')
        presentation.save_preferences('om', 'Africa/Addis_Ababa')
        self.assertEqual(presentation.preferences().locale, 'om')
        self.assertEqual(presentation.tour_state('patient-home')['state'], None)
        presentation.save_tour_state('patient-home', 'Dismissed')
        self.assertEqual(presentation.tour_state('patient-home')['state'], 'Dismissed')
        fixtures.login('p1')
        with self.assertRaises(frappe.PermissionError):
            presentation.tour_state('clinician-availability')

    def test_06_legacy_wallet_events_after_opening_snapshot_reconcile_once(self):
        from tele_tena import accounting
        from tele_tena.patches.v1_8_legacy_event_reconciliation import reconcile_wallet_events
        savepoint = 'tt_fin_reconcile_' + uuid.uuid4().hex[:16]
        frappe.db.sql('SAVEPOINT ' + savepoint)
        patient = 'legacy-' + uuid.uuid4().hex[:16] + '@example.invalid'
        try:
            frappe.db.sql('INSERT INTO tt_wallet (patient,available,reserved) VALUES (%s,60000,540000)',
                          (patient,))
            available = accounting.account_id('patient', patient, 'available')
            reserved = accounting.account_id('patient', patient, 'reserved')
            accounting.post('opening:' + patient, 'Opening', 'opening:' + patient,
                            [(available, 0, 260000), (reserved, 0, 240000),
                             ('demo:opening-control', 500000, 0)], {'source': 'synthetic migration test'})
            from tele_tena.api.journey import simulation_log
            simulation_log(patient, 'Deposit', 100000, 'deposit:synthetic-unposted')
            for index in range(5):
                simulation_log(patient, 'Reservation', 60000, 'booking:synthetic-unposted-' + str(index))
            legacy_count = int(journey.one('SELECT COUNT(*) n FROM tt_ledger WHERE patient=%s', (patient,)).n)
            self.assertEqual(reconcile_wallet_events(patient), 6)
            self.assertEqual(reconcile_wallet_events(patient), 0)
            self.assertEqual(accounting.balance('patient', patient, 'available'), 60000)
            self.assertEqual(accounting.balance('patient', patient, 'reserved'), 540000)
            wallet = journey.one('SELECT available,reserved FROM tt_wallet WHERE patient=%s', (patient,))
            accounting.check_wallet_projection(patient, wallet)
            self.assertEqual(int(journey.one('SELECT COUNT(*) n FROM tt_ledger WHERE patient=%s', (patient,)).n), legacy_count)
            self.assertEqual(int(journey.one('''SELECT COUNT(*) n FROM tt_journal
                WHERE event_type='LegacyEventImported' AND
                (event_ref='deposit:synthetic-unposted' OR event_ref LIKE 'booking:synthetic-unposted-%%')''').n), 6)
        finally:
            frappe.db.sql('ROLLBACK TO SAVEPOINT ' + savepoint)
            frappe.db.sql('RELEASE SAVEPOINT ' + savepoint)


if __name__ == '__main__':
    unittest.main(verbosity=2)
