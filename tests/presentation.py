"""State, recurring calendar and private-record regressions on isolated synthetic fixtures."""
import base64
import importlib.util
import secrets
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
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
        return journey.book(offering=offering, start=start, request_text=request, sharing=sharing,
                            retry_key=key or secrets.token_hex(8), expected_price=600,
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
