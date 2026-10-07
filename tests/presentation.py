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
from tele_tena.api import open_requests
from tele_tena.api import vetting


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
        cls._original_enqueue = frappe.enqueue
        # Prevent synthetic fixture setup from filling the retained isolated
        # bench queue. Scheduler behavior is verified in a separate controlled
        # test, never by draining pre-existing jobs.
        frappe.enqueue = lambda *args, **kwargs: None
        fixtures.Integration.setUpClass()
        cls._previous_immediate_policy = frappe.conf.get('tele_tena_demo_immediate_care_enabled')
        # This isolated synthetic suite explicitly models a review site whose
        # operator enabled immediate care for its legacy demo catalog.
        frappe.conf.update(tele_tena_demo_immediate_care_enabled=True)

    @classmethod
    def tearDownClass(cls):
        if cls._previous_immediate_policy is None:
            frappe.conf.pop('tele_tena_demo_immediate_care_enabled', None)
        else:
            frappe.conf.update(tele_tena_demo_immediate_care_enabled=cls._previous_immediate_policy)
        fixtures.Integration.tearDownClass()
        frappe.enqueue = cls._original_enqueue

    def setUp(self):
        fixtures.login('admin')

    def fund_patient(self, kind='p1', amount=10000):
        fixtures.login(kind)
        journey.simulated_deposit(amount, secrets.token_hex(12))
        frappe.db.commit()

    def test_structured_scope_vetting_blocks_legacy_approval_bypass(self):
        service = fixtures.PREFIX + '-vetting-scope'
        fixtures.login('admin')
        frappe.get_doc({'doctype':'Tele Tena Service','service_key':service,
            'service_label':'Synthetic vetted service','active':1,'catalog_status':'Active',
            'category':'psychotherapy','description':'Synthetic test definition',
            'population_restriction':'Adults only','participant_structure':'individual',
            'clinical_review_status':'Approved','vetting_required':1,
            'definition_version':'test-v1'}).insert()
        fixtures.login('c1')
        submitted = vetting.save_scope_application(service, {
            'professional_category':'Synthetic clinician','qualification':'Synthetic qualification',
            'issuing_institution':'Synthetic institution','registration_number':'TEST-ONLY',
            'issuing_authority':'Synthetic issuer','jurisdiction':'Synthetic jurisdiction',
            'experience_years':'4','approach_keys':'','population_adults':True,
            'independent_practice':True,'relevant_training':'Synthetic training',
            'applicant_statement':'Synthetic evidence only.'})
        self.assertEqual(submitted['status'],'Draft')
        app=frappe.get_doc('Tele Tena Vetting Scope Application',submitted['name'])
        fixtures.login('c2')
        self.assertFalse(frappe.has_permission(app.doctype,'read',doc=app,user=fixtures.USERS['c2']))
        self.assertFalse(any(row.name==submitted['name'] for row in vetting.my_scope_applications()))
        app.status='Approved'
        with self.assertRaises(frappe.PermissionError): app.save()
        fixtures.login('admin')
        with self.assertRaises(frappe.ValidationError):
            journey.review_service_scope(fixtures.USERS['c1'],service,'Approved')
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc({'doctype':'Tele Tena Vetting Assessment',
                'scope_application':submitted['name'],'reviewer':fixtures.USERS['admin'],
                'decision':'Approved','findings':'Synthetic direct-write attempt'}).insert()
        fixtures.login('c1')
        with self.assertRaises(frappe.ValidationError): journey.publish(service,50000,30)

    def test_vetting_draft_clarification_resubmission_and_scope_decision(self):
        service = fixtures.PREFIX + '-reviewed-scope'
        fixtures.login('admin')
        frappe.get_doc({'doctype':'Tele Tena Service','service_key':service,
            'service_label':'Synthetic adult counseling scope','active':1,'catalog_status':'Active',
            'category':'counseling','description':'Synthetic only; reviewer lifecycle regression.',
            'population_restriction':'Adults only','participant_structure':'individual',
            'clinical_review_status':'Approved','vetting_required':1,
            'definition_version':'synthetic-v1'}).insert()
        email = 'vetting-' + secrets.token_hex(6) + '@example.invalid'
        fixtures.USERS['vetting'] = email
        frappe.set_user('Administrator')
        user = frappe.get_doc({'doctype':'User','email':email,'first_name':'Synthetic vetting applicant',
            'user_type':'Website User','send_welcome_email':0})
        user.insert()
        user.add_roles('Tele Tena Clinician')
        fixtures.login('vetting')
        journey.save_profile('clinician','Synthetic vetting applicant',True,languages=['en'])
        presentation.upload_resume('synthetic-vetting-evidence.pdf',
                                   base64.b64encode(b'%PDF-1.4\nSynthetic evidence\n%%EOF').decode())
        journey.apply('Synthetic application for vetting lifecycle test.', json.dumps([service]))
        fixtures.login('admin')
        journey.review(email,'Approved')
        fixtures.login('vetting')
        application = vetting.save_scope_application(service, {
            'professional_category':'Synthetic counselor','qualification':'Synthetic qualification',
            'issuing_institution':'Synthetic institution','registration_number':'TEST-ONLY',
            'issuing_authority':'Synthetic issuer','jurisdiction':'Synthetic jurisdiction',
            'experience_years':'4','approach_keys':'','population_adults':True,
            'independent_practice':True,'relevant_training':'Synthetic supervised practice',
            'applicant_statement':'Synthetic evidence; no external credential claim.'})
        self.assertEqual(application['status'], 'Draft')
        application = vetting.save_scope_application(service, {
            'professional_category':'Synthetic counselor','qualification':'Synthetic qualification',
            'issuing_institution':'Synthetic institution','registration_number':'TEST-ONLY',
            'issuing_authority':'Synthetic issuer','jurisdiction':'Synthetic jurisdiction',
            'experience_years':'4','approach_keys':'','population_adults':True,
            'independent_practice':True,'relevant_training':'Synthetic supervised practice',
            'applicant_statement':'Synthetic evidence; no external credential claim.'}, submit=True)
        self.assertEqual(application['status'], 'Submitted')
        fixtures.login('admin')
        vetting.assign_scope_reviewer(application['name'], fixtures.USERS['admin'])
        vetting.review_scope_application(application['name'], 'Clarification', findings='Synthetic missing detail')
        fixtures.login('vetting')
        resubmitted = vetting.save_scope_application(service, {
            'professional_category':'Synthetic counselor','qualification':'Synthetic qualification',
            'issuing_institution':'Synthetic institution','registration_number':'TEST-ONLY',
            'issuing_authority':'Synthetic issuer','jurisdiction':'Synthetic jurisdiction',
            'experience_years':'4','approach_keys':'','population_adults':True,
            'independent_practice':True,'relevant_training':'Synthetic supervised practice',
            'applicant_statement':'Synthetic evidence; no external credential claim.',
            'applicant_response':'Synthetic clarification response.'}, submit=True)
        self.assertEqual(resubmitted['status'], 'Resubmitted')
        fixtures.login('admin')
        result = vetting.review_scope_application(application['name'], 'Approved',
            identity_reviewed=True, credential_verified=True, qualification_relevant=True,
            experience_adequate=True, approach_evidence_reviewed=True,
            adult_scope_appropriate=True, interview_completed=True,
            findings='Synthetic reviewer assessment; test only.')
        self.assertEqual(result['status'], 'Approved')
        self.assertTrue(journey.service_scope_is_current(email, service))
        assessments = journey.rows('SELECT name FROM `tabTele Tena Vetting Assessment` WHERE scope_application=%s',
                                   (application['name'],))
        self.assertEqual(len(assessments), 2)
        with self.assertRaises(frappe.PermissionError):
            assessment = frappe.get_doc('Tele Tena Vetting Assessment', result['assessment'])
            assessment.findings = 'Attempted overwrite'
            assessment.save()

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

    def test_private_request_competing_offers_insufficient_funds_and_atomic_match(self):
        offering1 = fixtures.Integration.offers['c1']
        offering2 = fixtures.Integration.offers['c2']
        service = fixtures.PREFIX
        day = day_offset(21)
        for who, offering in (('c1', offering1), ('c2', offering2)):
            fixtures.login(who)
            journey.save_profile('clinician', 'Synthetic clinician ' + who, 1, languages=['en'])
            schedule_payload_value = schedule_payload(offering, day, mode='automatic')
            schedule_payload_value['minimum_notice_minutes'] = 0
            scheduling.save_schedule(**schedule_payload_value)
        fixtures.login('p1')
        discovery = journey.discover(service=service)
        public = next(item for item in discovery if item.clinician_id)
        self.assertNotIn(fixtures.USERS['c1'], json.dumps(discovery))
        profile = open_requests.clinician_profile(public.clinician_id)
        self.assertNotIn(fixtures.USERS['c1'], json.dumps(profile))
        self.assertNotIn('email', json.dumps(profile).lower())
        with self.assertRaises(frappe.ValidationError):
            open_requests.clinician_profile('00000000-0000-0000-0000-000000000000')
        wallet_before = journey.wallet()
        immediate_key = 'immediate-retry-' + secrets.token_hex(6)
        immediate_payload = dict(service=service, request_text='Synthetic immediate retry payload.',
            urgency='immediate', language='en', consultation_format='audio',
            sharing={'name': False, 'history': False}, retry_key=immediate_key,
            timezone_name='Africa/Addis_Ababa')
        first_immediate = open_requests.publish_request(**immediate_payload)
        retried_immediate = open_requests.publish_request(**immediate_payload)
        self.assertEqual(first_immediate['id'], retried_immediate['id'])
        self.assertTrue(retried_immediate['idempotent'])
        self.assertEqual(frappe.db.sql("SELECT COUNT(*) FROM tt_open_request WHERE patient=%s AND retry_key=%s",
                                      (fixtures.USERS['p1'], immediate_key))[0][0], 1)
        open_requests.close_request(first_immediate['id'])
        slot = self.slots(offering1, day)[0]
        request = open_requests.publish_request(
            service=service, request_text='Synthetic request for private offer regression.',
            urgency='scheduled', language='en', consultation_format='video',
            sharing={'name': False, 'history': False}, retry_key='private-offer-' + secrets.token_hex(6),
            timezone_name='Africa/Addis_Ababa', earliest_start=slot['start'], latest_start=slot['start'],
            max_price_minor=wallet_before['available'] + 10000)
        self.assertEqual(request['state'], 'Open')
        req_id = request['id']
        default_c2_price = int(journey.one('SELECT price FROM tt_offering WHERE id=%s', (offering2,)).price)
        for who, offering, price in (('c1', offering1, wallet_before['available'] + 5000),
                                     ('c2', offering2, default_c2_price)):
            fixtures.login(who)
            inbox = open_requests.clinician_requests()
            visible = next(item for item in inbox if item.id == req_id)
            self.assertNotIn(fixtures.USERS['p1'], json.dumps(visible))
            self.assertNotIn('email', json.dumps(visible).lower())
            response = open_requests.submit_offer(req_id, offering, slot['start'], price)
            self.assertEqual(response['state'], 'Active')
            if who == 'c1':
                duplicate_offer = open_requests.submit_offer(req_id, offering, slot['start'], price)
                self.assertTrue(duplicate_offer['idempotent'])
                self.assertEqual(duplicate_offer['id'], response['id'])
        fixtures.login('c1')
        c1_view = next(item for item in open_requests.clinician_requests() if item.id == req_id)
        self.assertTrue(c1_view.own_offer_id)
        self.assertEqual(int(c1_view.own_offer_price), wallet_before['available'] + 5000)
        fixtures.login('c2')
        c2_view = next(item for item in open_requests.clinician_requests() if item.id == req_id)
        self.assertTrue(c2_view.own_offer_id)
        self.assertEqual(int(c2_view.own_offer_price), default_c2_price)
        self.assertNotEqual(c1_view.own_offer_id, c2_view.own_offer_id)
        fixtures.login('c1')
        with self.assertRaises(frappe.PermissionError):
            open_requests.withdraw_offer(c2_view.own_offer_id)
        fixtures.login('p1')
        visible = next(item for item in open_requests.my_requests() if item.id == req_id)
        self.assertEqual(len([offer for offer in visible.offers if offer.state == 'Active']), 2)
        losing = next(offer for offer in visible.offers if offer.clinician_name == 'Synthetic clinician c2')
        fixtures.login('p2')
        with self.assertRaises(frappe.ValidationError):
            open_requests.respond_offer(req_id, losing.id, 'accept', None, visible.disclosure_snapshot)
        fixtures.login('p1')
        winning = next(offer for offer in visible.offers if offer.clinician_name == 'Synthetic clinician c1')
        with self.assertRaises(frappe.ValidationError):
            open_requests.respond_offer(req_id, winning.id, 'accept', None, visible.disclosure_snapshot)
        self.assertEqual(frappe.local.response.get('tele_tena_error'), 'insufficient_funds')
        # The request and offer stay active; funding followed by retry succeeds.
        self.assertEqual(journey.one('SELECT state FROM tt_open_request WHERE id=%s', (req_id,)).state, 'Open')
        self.assertEqual(journey.one('SELECT state FROM tt_request_offer WHERE id=%s', (winning.id,)).state, 'Active')
        journey.simulated_deposit(10000, 'request-fund-' + secrets.token_hex(8))
        match = open_requests.respond_offer(req_id, winning.id, 'accept', None, visible.disclosure_snapshot)
        self.assertEqual(match['state'], 'Matched')
        self.assertEqual(journey.one('SELECT state FROM tt_open_request WHERE id=%s', (req_id,)).state, 'Matched')
        self.assertEqual(journey.one('SELECT state FROM tt_request_offer WHERE id=%s', (losing.id,)).state, 'Superseded')
        duplicate = open_requests.respond_offer(req_id, winning.id, 'accept', None, visible.disclosure_snapshot)
        self.assertEqual(duplicate['appointment'], match['appointment'])
        self.assertEqual(journey.one('SELECT COUNT(*) n FROM tt_appointment WHERE retry_key=%s',
                                     ('open-request:' + req_id,)).n, 1)
        self.assertGreaterEqual(journey.wallet()['reserved'], wallet_before['reserved'] + 1)
        # Own offer history remains available after matching, without competitor
        # quotes, account identifiers or copied clinical narrative.
        with self.assertRaises(frappe.PermissionError):
            open_requests.clinician_offers()
        fixtures.login('c1')
        history = open_requests.clinician_offers()
        own = next(item for item in history['items'] if item.id == winning.id)
        self.assertEqual(own.state, 'Accepted')
        self.assertEqual(own.appointment, match['appointment'])
        self.assertEqual(own.patient_label, 'Patient · alias')
        self.assertNotIn(losing.id, json.dumps(history))
        self.assertNotIn(fixtures.USERS['p1'], json.dumps(history))
        self.assertNotIn('Synthetic request for private offer regression.', json.dumps(history))
        self.assertNotIn('disclosure_snapshot', json.dumps(history))
        with self.assertRaises(frappe.ValidationError):
            open_requests.clinician_offers(-1)
        fixtures.login('c2')
        own_loser = next(item for item in open_requests.clinician_offers()['items'] if item.id == losing.id)
        self.assertEqual(own_loser.state, 'Superseded')
        self.assertIsNone(own_loser.appointment)

    def test_immediate_request_matches_continuous_time_between_booking_grid_points(self):
        """Fresh presence plus continuous time must not require a 15-minute grid start."""
        from zoneinfo import ZoneInfo
        offering = fixtures.Integration.offers['c1']
        service = fixtures.PREFIX
        zone = ZoneInfo('Africa/Addis_Ababa')
        local_day = datetime.now(zone).date() + timedelta(days=2)
        local_now = datetime.combine(local_day, datetime.min.time().replace(hour=10, minute=5), zone)
        current = local_now.astimezone(timezone.utc).replace(tzinfo=None)
        interval_start = '10:00'
        interval_end = '10:40'
        today = local_day

        fixtures.login('c1')
        journey.save_profile('clinician', 'Synthetic immediate clinician', 1, languages=['en'])
        schedule = dict(offering=offering, schedule_name='Immediate continuous-time regression',
            timezone_name='Africa/Addis_Ababa', consultation_format='video',
            confirmation_mode='automatic', minimum_notice_minutes=60, horizon_days=30,
            buffer_before=0, buffer_after=0,
            intervals=[{'weekday': today.weekday(), 'start': interval_start,
                        'end': interval_end}], exceptions=[], status='Published')
        scheduling.save_schedule(**schedule)
        with patch.object(open_requests, 'now', return_value=current):
            ready = open_requests.set_request_presence(True)
            self.assertTrue(ready['ready'])
            fixtures.login('p1')
            immediate = open_requests.publish_request(
                service=service, request_text='Synthetic immediate request for the grid-boundary regression.',
                urgency='immediate', language='en', consultation_format='video',
                sharing={'name': False, 'history': False}, retry_key='immediate-grid-' + secrets.token_hex(8),
                timezone_name='Africa/Addis_Ababa')
            self.assertGreaterEqual(immediate['eligible_supply'], 1)
            self.assertGreaterEqual(immediate['notified'], 1)
        persisted = journey.one('SELECT * FROM tt_open_request WHERE id=%s', (immediate['id'],))
        schedule_row = scheduling._schedule_for(offering)
        offer_row = journey.one('SELECT * FROM tt_offering WHERE id=%s', (offering,))
        appointment_window = open_requests._has_slot(
            frappe._dict(offering=offering, clinician=fixtures.USERS['c1']), persisted)
        self.assertTrue(appointment_window)

        # The old direct-booking grid starts at the interval's opening and advances
        # in 15-minute increments; none of those generated starts belongs to this
        # request window even though a full continuous session fits.
        grid = scheduling._slots_for_day(schedule_row, offer_row, today, [], [],
                                         minimum_notice_override=0)
        self.assertFalse(any(persisted.earliest_start <= slot[0] <= persisted.latest_start
                             for slot in grid))
        start = scheduling.immediate_start(schedule_row, offer_row, fixtures.USERS['c1'],
            fixtures.USERS['p1'], persisted.earliest_start, persisted.latest_start)
        self.assertIsNotNone(start)
        fixtures.login('c1')
        with patch.dict(frappe.conf, tele_tena_demo_immediate_care_enabled=False):
            self.assertFalse(any(item.id == immediate['id'] for item in open_requests.clinician_requests()))
        inbox_item = next(item for item in open_requests.clinician_requests() if item.id == immediate['id'])
        self.assertNotIn(fixtures.USERS['p1'], json.dumps(inbox_item))
        self.assertNotIn('_routing_patient', inbox_item)
        self.assertIsNotNone(inbox_item.suggested_start)
        open_requests.acknowledge_inbox_fetch([immediate['id']])
        self.assertTrue(journey.rows("SELECT id FROM tt_request_route_log WHERE request_id=%s AND clinician=%s AND event='InboxFetched'",
                                    (immediate['id'], fixtures.USERS['c1'])))
        with patch.dict(frappe.conf, tele_tena_demo_immediate_care_enabled=False):
            with self.assertRaises(frappe.ValidationError):
                open_requests.submit_offer(immediate['id'], offering,
                    start.isoformat(timespec='seconds') + 'Z')
        with patch.object(open_requests, 'now', return_value=current):
            proposed = open_requests.submit_offer(immediate['id'], offering,
                start.isoformat(timespec='seconds') + 'Z')
        self.assertEqual(proposed['state'], 'Active')
        fixtures.login('p1')
        journey.simulated_deposit(100000, 'immediate-grid-fund-' + secrets.token_hex(8))
        patient_request = next(item for item in open_requests.my_requests() if item.id == immediate['id'])
        with patch.dict(frappe.conf, tele_tena_demo_immediate_care_enabled=False):
            with self.assertRaises(frappe.ValidationError):
                open_requests.respond_offer(immediate['id'], proposed['id'], 'accept', None,
                                            patient_request.disclosure_snapshot)
        accepted = open_requests.respond_offer(immediate['id'], proposed['id'], 'accept', None,
                                               patient_request.disclosure_snapshot)
        self.assertEqual(accepted['state'], 'Matched')
        self.assertEqual(journey.one('SELECT state FROM tt_open_request WHERE id=%s',
                                     (immediate['id'],)).state, 'Matched')

    def test_immediate_request_policy_is_explicit_and_site_scoped(self):
        offering = fixtures.Integration.offers['c1']
        self.make_schedule(offering=offering)
        fixtures.login('c1')
        with patch.dict(frappe.conf, tele_tena_demo_immediate_care_enabled=False):
            with self.assertRaises(frappe.ValidationError):
                open_requests.set_request_presence(True)
            self.assertEqual(frappe.local.response.get('tele_tena_error'), 'immediate_policy_required')
            fixtures.login('p1')
            with self.assertRaises(frappe.ValidationError):
                open_requests.publish_request(service=fixtures.PREFIX,
                    request_text='Synthetic immediate policy test.', urgency='immediate',
                    language='en', consultation_format='video',
                    sharing={'name':False,'history':False}, retry_key='policy-' + secrets.token_hex(8),
                    timezone_name='Africa/Addis_Ababa')
            self.assertEqual(frappe.local.response.get('tele_tena_error'), 'immediate_care_unavailable')

        fixtures.login('c1')
        with patch.dict(frappe.conf, tele_tena_demo_immediate_care_enabled=True), \
                patch.object(open_requests, '_has_immediate_capacity', return_value=False):
            with self.assertRaises(frappe.ValidationError):
                open_requests.set_request_presence(True)
            self.assertEqual(frappe.local.response.get('tele_tena_error'), 'no_immediate_capacity')
            self.assertIn('no_immediate_capacity', open_requests.request_presence()['reasons'])

    def test_two_patients_cannot_claim_one_offer_slot_concurrently(self):
        offering = fixtures.Integration.offers['c1']
        service = fixtures.PREFIX
        day = day_offset(28)
        fixtures.login('c1')
        journey.save_profile('clinician', 'Synthetic slot clinician', 1, languages=['en'])
        journey.publish(service, 30000, 30)
        payload = schedule_payload(offering, day, mode='automatic')
        payload['minimum_notice_minutes'] = 0
        scheduling.save_schedule(**payload)
        slot = self.slots(offering, day, who='p1')[0]
        requests = []
        for patient in ('p1', 'p2'):
            fixtures.login(patient)
            journey.simulated_deposit(100000, 'request-race-' + patient + '-' + secrets.token_hex(6))
            request = open_requests.publish_request(
                service=service, request_text='Synthetic concurrent slot request.', urgency='scheduled',
                language='en', consultation_format='video', sharing={'name': False, 'history': False},
                retry_key='request-race-' + patient + '-' + secrets.token_hex(6),
                timezone_name='Africa/Addis_Ababa', earliest_start=slot['start'],
                latest_start=slot['start'], max_price_minor=100000)
            requests.append(request['id'])
            frappe.db.commit()
        fixtures.login('c1')
        offers = [open_requests.submit_offer(request_id, offering, slot['start'])['id']
                  for request_id in requests]
        frappe.db.commit()
        barrier = threading.Barrier(2)

        def accept(index):
            fixtures.connect()
            try:
                fixtures.login('p' + str(index + 1))
                req = next(item for item in open_requests.my_requests() if item.id == requests[index])
                self.assertTrue(any(item.id == offers[index] for item in req.offers))
                barrier.wait(timeout=10)
                result = open_requests.respond_offer(requests[index], offers[index], 'accept',
                    None, req.disclosure_snapshot)
                frappe.db.commit()
                return 'matched', result.get('appointment')
            except frappe.ValidationError:
                frappe.db.rollback()
                return 'conflict', None
            finally:
                frappe.destroy()

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(accept, (0, 1)))
        frappe.db.rollback()
        self.assertEqual(sum(state == 'matched' for state, _appointment in results), 1)
        self.assertEqual(sum(state == 'conflict' for state, _appointment in results), 1)
        self.assertEqual(journey.one("SELECT COUNT(*) n FROM tt_appointment WHERE start=%s AND state='Booked'",
                                     (slot['start'],)).n, 1)
        self.assertEqual(journey.one("SELECT COUNT(*) n FROM tt_request_offer WHERE id IN %s AND state='Accepted'",
                                     (tuple(offers),)).n, 1)

    def test_booking_link_is_opaque_owner_scoped_and_revocable(self):
        offering = fixtures.Integration.offers['c1']
        self.make_schedule(offering=offering)
        fixtures.login('c1')
        token = scheduling.booking_link(offering)['token']
        self.assertEqual(len(token), 64)
        self.assertNotIn(offering, token)
        frappe.set_user('Guest')
        with self.assertRaises(frappe.PermissionError):
            scheduling.resolve_booking_link(token)
        fixtures.login('c2')
        with self.assertRaises(frappe.PermissionError):
            scheduling.resolve_booking_link(token)
        fixtures.login('p1')
        preview = scheduling.resolve_booking_link(token)
        self.assertEqual(preview['offering'], offering)
        self.assertNotIn('patient', preview)
        self.assertNotIn('email', preview)
        fixtures.login('c2')
        with self.assertRaises(frappe.ValidationError):
            scheduling.booking_link(offering)
        fixtures.login('admin')
        from tele_tena.api.journey import review_service_scope
        review_service_scope(fixtures.USERS['c1'], fixtures.PREFIX, 'Revoked')
        fixtures.login('p1')
        with self.assertRaises(frappe.ValidationError):
            scheduling.resolve_booking_link(token)
        fixtures.login('admin')
        review_service_scope(fixtures.USERS['c1'], fixtures.PREFIX, 'Approved')
        frappe.db.commit()

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
