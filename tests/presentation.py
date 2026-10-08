"""State, recurring calendar and private-record regressions on isolated synthetic fixtures."""
import base64
import concurrent.futures
from copy import deepcopy
import hashlib
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
from tele_tena.api import trust
from tele_tena.api import clinics
from tele_tena.api import clinic_access
from tele_tena.api import extensions
from tele_tena.api import service_policy
from tele_tena.api import service_catalog
from tele_tena.api import financial_activity
from tele_tena.patches import v1_23_multiple_offerings
from tele_tena.patches import v1_24_legacy_completion_activity
from tele_tena.patches import v1_25_legacy_refund_activity
from tele_tena.patches import v1_26_appointment_acquisition_source
from tele_tena.patches import v1_27_vetting_rubric_assessment
from tele_tena.patches import v1_28_vetting_rubric_registry
from tele_tena.patches import v1_29_credential_verification_provenance


def proposed_rubric_scores(evidence=None):
    return {key: {'score': 2, 'rationale': 'Synthetic reviewer evidence note.',
                  'evidence': [evidence] if evidence and key == 'scope_education' else []}
            for key in ('scope_education','supervised_experience','approach_training',
                        'adult_population','ethics_safeguarding','assessment_interview')}


def credential_source_payload(evidence):
    return {'credential_source':'Synthetic licensing registry (test fixture)',
            'credential_checked_on':frappe.utils.today(),
            'credential_evidence':evidence,
            'credential_source_reference':'SYNTHETIC-REGISTRY-REF'}


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

    def test_clinician_can_publish_multiple_retry_safe_offerings_within_one_scope(self):
        service = fixtures.PREFIX
        keys = ['offering-multi-' + secrets.token_hex(10), 'offering-multi-' + secrets.token_hex(10)]
        created = []
        try:
            fixtures.login('c1')
            first = journey.publish(service, 5500, 30, 'Synthetic brief session',
                'Synthetic description for repeat-offering verification.', retry_key=keys[0])
            created.append(first['offering'])
            self.assertFalse(first['replayed'])
            self.assertEqual(journey.publish(service, 5500, 30, 'Synthetic brief session',
                'Synthetic description for repeat-offering verification.', retry_key=keys[0]),
                {'saved': True, 'offering': first['offering'], 'replayed': True})
            second = journey.publish(service, 8200, 45, 'Synthetic longer session',
                'A second offer under the same approved scope.', retry_key=keys[1])
            created.append(second['offering'])
            self.assertNotEqual(first['offering'], second['offering'])
            with self.assertRaises(frappe.ValidationError):
                journey.publish(service, 5600, 30, 'Changed title',
                    'Changed payload must not reuse a completed key.', retry_key=keys[0])
            updated = journey.publish(service, 5750, 30, 'Synthetic brief session revised',
                'Owner edit preserves offering identity.', offering_id=first['offering'])
            self.assertEqual(updated['offering'], first['offering'])

            own = journey.practice()['offerings']
            by_id = {item.id: item for item in own if item.id in created}
            self.assertEqual(set(by_id), set(created))
            self.assertEqual(int(by_id[first['offering']].price), 5750)
            self.assertEqual(by_id[first['offering']].title, 'Synthetic brief session revised')
            self.assertEqual(by_id[second['offering']].title, 'Synthetic longer session')

            fixtures.login('p1')
            visible = {item.id: item for item in journey.discover(service)}
            self.assertTrue(set(created).issubset(visible))
            self.assertEqual(int(visible[first['offering']].price), 5750)
            self.assertEqual(int(visible[second['offering']].price), 8200)

            fixtures.login('c2')
            with self.assertRaises(frappe.PermissionError):
                journey.publish(service, 9900, 30, 'Unauthorized edit', '',
                    offering_id=first['offering'])
        finally:
            fixtures.login('admin')
            if created:
                frappe.db.sql('DELETE FROM tt_offering WHERE id IN %s', (tuple(created),))
            frappe.db.commit()

    def test_discovery_exposes_declared_care_languages_without_account_identity(self):
        fixtures.login('c1')
        journey.save_profile('clinician', 'Synthetic language listing', True, languages=['en', 'am'])
        fixtures.login('p1')
        results = journey.discover(fixtures.PREFIX)
        self.assertTrue(results)
        target = next(item for item in results if item.display_name == 'Synthetic language listing')
        self.assertEqual(target.care_languages, ['am', 'en'])
        serialized = json.dumps([dict(item) for item in results], sort_keys=True)
        self.assertNotIn(fixtures.USERS['c1'], serialized)
        self.assertNotIn('example.invalid', serialized)
        self.assertNotIn('history', target)

    def test_multiple_offerings_migration_is_repeatable_and_preserves_legacy_row(self):
        offering_id = str(uuid.uuid4())
        clinician = fixtures.USERS['c1']
        service = fixtures.PREFIX
        fixtures.login('admin')
        frappe.db.sql('''INSERT INTO tt_offering
            (id,clinician,service,title,description,price,minutes,active,retry_key,payload_hash)
            VALUES (%s,%s,%s,'','',4321,35,1,NULL,NULL)''', (offering_id, clinician, service))
        frappe.db.commit()
        try:
            v1_23_multiple_offerings.execute()
            v1_23_multiple_offerings.execute()
            preserved = journey.one('''SELECT id,clinician,service,title,description,price,minutes,active
                FROM tt_offering WHERE id=%s''', (offering_id,))
            self.assertEqual((preserved.id, preserved.clinician, preserved.service,
                preserved.title, preserved.description, int(preserved.price), int(preserved.minutes),
                int(preserved.active)), (offering_id, clinician, service, 'Synthetic test consultation', '', 4321, 35, 1))
            indexes = {row[2] for row in frappe.db.sql('SHOW INDEX FROM tt_offering')}
            self.assertNotIn('clinician_service', indexes)
            self.assertIn('clinician_retry', indexes)
        finally:
            frappe.db.sql('DELETE FROM tt_offering WHERE id=%s', (offering_id,))
            frappe.db.commit()

    def test_authorized_user_change_preserves_authenticated_session_state(self):
        from tele_tena.account_context import authorized_user_change
        fixtures.login('p1')
        session = frappe.local.session
        original = deepcopy(session)
        try:
            session.sid = 'synthetic-active-session-id'
            session.csrf_token = 'synthetic-csrf-token'
            session.data = frappe._dict({'user': fixtures.USERS['p1'], 'session_marker': 'preserve'})
            before = deepcopy(session)
            with authorized_user_change():
                self.assertEqual(frappe.session.user, 'Administrator')
            self.assertIs(frappe.local.session, session)
            self.assertEqual(frappe.session.user, fixtures.USERS['p1'])
            self.assertEqual(session.sid, before.sid)
            self.assertEqual(session.csrf_token, before.csrf_token)
            self.assertEqual(dict(session.data), dict(before.data))
        finally:
            session.clear()
            session.update(original)

    def fund_patient(self, kind='p1', amount=10000):
        fixtures.login(kind)
        journey.simulated_deposit(amount, secrets.token_hex(12))
        frappe.db.commit()

    def test_patient_transaction_detail_is_owner_scoped_and_hides_counter_accounts(self):
        from tele_tena import accounting
        self.fund_patient('p1', 900)
        patient = fixtures.USERS['p1']
        legacy = journey.one('''SELECT id FROM tt_ledger WHERE patient=%s AND kind='Deposit'
            ORDER BY created DESC,id DESC LIMIT 1''', (patient,))
        fixtures.login('p1')
        legacy_detail = financial_activity.transaction_detail('log-' + legacy.id)
        self.assertEqual(legacy_detail['kind'], 'Funds added')
        self.assertEqual(int(legacy_detail['amount_minor']), 900)
        self.assertEqual(legacy_detail['source'], 'simulation_log')
        self.assertFalse(legacy_detail['external_transfer'])

        event_ref = 'transaction-detail-' + secrets.token_hex(8)
        accounting.post(event_ref, 'Reservation', event_ref, [
            (accounting.account_id('patient', patient, 'available'), 125, 0),
            (accounting.account_id('patient', patient, 'reserved'), 0, 125),
        ], {'synthetic': True})
        # Keep the legacy wallet projection aligned with the test posting; the
        # public API correctly refuses future spending on a mismatched wallet.
        frappe.db.sql('UPDATE tt_wallet SET available=available-125,reserved=reserved+125 WHERE patient=%s',
                      (patient,))
        journal_id = journey.one('SELECT id FROM tt_journal WHERE event_ref=%s', (event_ref,)).id
        detail = financial_activity.transaction_detail('journal-' + journal_id)
        self.assertEqual(int(detail['amount_minor']), 125)
        self.assertEqual({(change['bucket'], int(change['delta_minor']))
                          for change in detail['account_changes']},
                         {('available', -125), ('reserved', 125)})
        serialized = json.dumps(detail)
        self.assertNotIn(patient, serialized)
        self.assertNotIn(fixtures.USERS['p2'], serialized)
        self.assertNotIn('account_id', serialized)
        fixtures.login('p2')
        with self.assertRaises(frappe.PermissionError):
            financial_activity.transaction_detail('log-' + legacy.id)
        with self.assertRaises(frappe.PermissionError):
            financial_activity.transaction_detail('journal-' + journal_id)
        release_ref = event_ref + '-release'
        accounting.post(release_ref, 'ReservationRelease', release_ref, [
            (accounting.account_id('patient', patient, 'available'), 0, 125),
            (accounting.account_id('patient', patient, 'reserved'), 125, 0),
        ], {'synthetic': True})
        frappe.db.sql('UPDATE tt_wallet SET available=available+125,reserved=reserved-125 WHERE patient=%s',
                      (patient,))

    def test_clinician_payout_detail_is_private_and_never_claims_transfer(self):
        from tele_tena import accounting
        clinician = fixtures.USERS['c1']
        event_ref = 'transaction-detail-opening-' + secrets.token_hex(8)
        accounting.post(event_ref, 'TestOpening', event_ref, [
            (accounting.account_id('', '', 'opening_control'), 5000, 0),
            (accounting.account_id('clinician', clinician, 'earnings_available'), 0, 5000),
        ], {'synthetic': True})
        fixtures.login('c1')
        payout = accounting.request_payout(1200, 'transaction-detail-' + secrets.token_hex(8))
        detail = financial_activity.transaction_detail('payout-' + payout['id'])
        self.assertEqual(detail['state'], 'Requested')
        self.assertEqual(int(detail['amount_minor']), 1200)
        self.assertFalse(detail['external_transfer'])
        self.assertNotIn(clinician, json.dumps(detail))
        fixtures.login('c2')
        with self.assertRaises(frappe.PermissionError):
            financial_activity.transaction_detail('payout-' + payout['id'])

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

    def test_clinic_registration_and_affiliation_are_separate_from_scope_and_records(self):
        baseline_scopes = frappe.db.count('Tele Tena Service Scope',
            {'clinician': fixtures.USERS['c1']})
        fixtures.login('c1')
        values = dict(clinic_name='Synthetic North Clinic', legal_name='Synthetic North Care Ltd',
            registration_reference='TEST-CLINIC-' + secrets.token_hex(4),
            jurisdiction='Synthetic jurisdiction', public_description='Synthetic test clinic')
        clinic = clinics.submit_clinic_application(**values)
        self.assertEqual(clinic['status'], 'Submitted')
        self.assertTrue(clinics.submit_clinic_application(**values)['idempotent'])
        application = clinic['application']
        fixtures.login('c2')
        with self.assertRaises(frappe.ValidationError):
            clinics.submit_clinic_application(**values)
        self.assertFalse(frappe.has_permission('Tele Tena Clinic', 'read',
            doc=frappe.get_doc('Tele Tena Clinic', application), user=fixtures.USERS['c2']))
        self.assertEqual(frappe.get_list('Tele Tena Clinic', fields=['name']), [])
        fixtures.login('admin')
        reviewed = clinics.review_clinic(application, 'Verified',
            'Synthetic registry lookup recorded for test only.')
        self.assertEqual(reviewed['status'], 'Verified')
        with self.assertRaises(frappe.ValidationError):
            clinics.review_clinic(application, 'Rejected', 'Conflicting second decision.')
        from tele_tena.account_context import authorized_user_change
        clinician_user = frappe.get_doc('User', fixtures.USERS['c1'])
        with authorized_user_change():
            clinician_user.add_roles('Tele Tena Approver')
        frappe.clear_cache(user=clinician_user.name)
        fixtures.login('c1')
        with self.assertRaises(frappe.PermissionError):
            clinics.review_clinic(application, 'Suspended', 'Self-review is forbidden.')
        fixtures.login('admin')
        with authorized_user_change():
            clinician_user.remove_roles('Tele Tena Approver')
        frappe.clear_cache(user=clinician_user.name)
        self.assertIn('Tele Tena Clinician', frappe.get_roles(fixtures.USERS['c1']))
        fixtures.login('c1')
        affiliation = clinics.submit_affiliation(application, 'Synthetic counselor',
            'Synthetic affiliation evidence summary for test only.')
        self.assertEqual(affiliation['status'], 'Submitted')
        self.assertTrue(clinics.submit_affiliation(application, 'Synthetic counselor',
            'Synthetic affiliation evidence summary for test only.')['idempotent'])
        affiliation_id = affiliation['application']
        with self.assertRaises(frappe.PermissionError):
            clinics.review_affiliation(affiliation_id, 'Verified', 'Not authorized')
        applicant_doc = frappe.get_doc('Tele Tena Clinic Affiliation', affiliation_id)
        applicant_doc.status = 'Verified'
        with self.assertRaises(frappe.PermissionError):
            applicant_doc.save()
        fixtures.login('c2')
        self.assertEqual(clinics.my_affiliations(), [])
        self.assertEqual(frappe.get_list('Tele Tena Clinic Affiliation', fields=['name']), [])
        self.assertFalse(frappe.has_permission('Tele Tena Clinic Affiliation', 'read',
            doc=frappe.get_doc('Tele Tena Clinic Affiliation', affiliation_id),
            user=fixtures.USERS['c2']))
        fixtures.login('admin')
        requested = clinics.review_affiliation(affiliation_id, 'Clarification',
            'Synthetic reviewer requested supporting detail.')
        self.assertEqual(requested['status'], 'Clarification')
        fixtures.login('c1')
        resubmitted = clinics.submit_affiliation(application, 'Synthetic counselor',
            'Synthetic clarification response.', application=affiliation_id)
        self.assertEqual(resubmitted['status'], 'Submitted')
        fixtures.login('admin')
        approved_affiliation = clinics.review_affiliation(affiliation_id, 'Verified',
            'Synthetic affiliation evidence checked for test only.')
        self.assertEqual(approved_affiliation['status'], 'Verified')
        self.assertEqual(frappe.db.count('Tele Tena Service Scope',
            {'clinician': fixtures.USERS['c1']}), baseline_scopes)

        # A rejected registration remains immutable history while its owner can
        # correct and resubmit the same registration reference.
        rejected_values = dict(values, registration_reference='TEST-REJECT-' + secrets.token_hex(4))
        fixtures.login('c1')
        rejected = clinics.submit_clinic_application(**rejected_values)['application']
        fixtures.login('admin')
        clinics.review_clinic(rejected, 'Rejected', 'Synthetic missing evidence.')
        fixtures.login('c1')
        corrected_values = dict(rejected_values, public_description='Corrected synthetic evidence note')
        resubmission = clinics.submit_clinic_application(**corrected_values)
        self.assertEqual(resubmission['status'], 'Submitted')
        self.assertNotEqual(resubmission['application'], rejected)
        self.assertEqual(frappe.db.get_value('Tele Tena Clinic',
            resubmission['application'], 'previous_application'), rejected)
        fixtures.login('p1')
        with self.assertRaises(frappe.PermissionError):
            clinics.review_queue()

    def test_clinic_membership_requires_verified_contact_and_never_grants_clinical_access(self):
        fixtures.login('c1')
        submitted = clinics.submit_clinic_application(
            clinic_name='Synthetic Membership Clinic', legal_name='Synthetic Membership Care Ltd',
            registration_reference='TEST-MEMBER-' + secrets.token_hex(4),
            jurisdiction='Synthetic jurisdiction', public_description='Synthetic membership test')
        fixtures.login('admin')
        clinics.review_clinic(submitted['application'], 'Verified', 'Synthetic review fixture.')

        invite_email = fixtures.USERS['p2'].lower()
        self.assertFalse(frappe.db.exists('tt_contact_identity', {
            'channel': 'email', 'contact': invite_email}))
        fixtures.login('c1')
        invitation = clinics.invite_clinic_member(
            submitted['application'], invite_email, 'Scheduling')
        self.assertEqual(invitation['status'], 'Invited')
        self.assertTrue(clinics.invite_clinic_member(
            submitted['application'], invite_email, 'Scheduling')['idempotent'])
        self.assertEqual(clinics.clinic_team(submitted['application'])[0].invite_email,
                         invite_email)

        fixtures.login('admin')
        self.assertEqual(frappe.get_list('Tele Tena Clinic Membership', fields=['name']), [])
        self.assertFalse(frappe.has_permission('Tele Tena Clinic Membership', 'read',
            doc=frappe.get_doc('Tele Tena Clinic Membership', invitation['membership']),
            user=fixtures.USERS['admin']))
        fixtures.login('p2')
        self.assertEqual(frappe.get_list('Tele Tena Clinic Membership', fields=['name']), [])
        self.assertEqual(clinics.my_clinic_memberships()['invitations'], [])
        self.assertFalse(journey._clinic_workspace_available(fixtures.USERS['p2']))
        with self.assertRaises(frappe.PermissionError):
            clinics.respond_to_clinic_invitation(invitation['membership'], 'accept')
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc({'doctype': 'Tele Tena Clinic Membership',
                'clinic': submitted['application'], 'invite_email': invite_email,
                'membership_role': 'Clinic Manager', 'status': 'Invited',
                'invited_by': fixtures.USERS['p2']}).insert()
        self.assertFalse(frappe.has_permission('Tele Tena Clinic', 'read',
            doc=frappe.get_doc('Tele Tena Clinic', submitted['application']),
            user=fixtures.USERS['p2']))

        frappe.db.sql('''INSERT INTO tt_contact_identity(channel,contact,user,verified_at)
            VALUES ('email',%s,%s,NOW(6))''', (invite_email, fixtures.USERS['p2']))
        self.assertEqual(len(clinics.my_clinic_memberships()['invitations']), 1)
        self.assertTrue(journey._clinic_workspace_available(fixtures.USERS['p2']))
        accepted = clinics.respond_to_clinic_invitation(invitation['membership'], 'accept')
        self.assertEqual(accepted['status'], 'Active')
        self.assertTrue(journey._clinic_workspace_available(fixtures.USERS['p2']))
        self.assertTrue(clinics.respond_to_clinic_invitation(
            invitation['membership'], 'accept')['idempotent'])
        self.assertIn('Tele Tena Patient', frappe.get_roles(fixtures.USERS['p2']))
        self.assertNotIn('Tele Tena Clinician', frappe.get_roles(fixtures.USERS['p2']))
        self.assertFalse(frappe.has_permission('Tele Tena Clinic', 'read',
            doc=frappe.get_doc('Tele Tena Clinic', submitted['application']),
            user=fixtures.USERS['p2']))
        membership_doc = frappe.get_doc('Tele Tena Clinic Membership', invitation['membership'])
        self.assertTrue(frappe.has_permission('Tele Tena Clinic Membership', 'read',
            doc=membership_doc, user=fixtures.USERS['p2']))
        with self.assertRaises(frappe.PermissionError):
            membership_doc.delete()
        membership_doc.status = 'Revoked'
        with self.assertRaises(frappe.PermissionError):
            membership_doc.save()
        with self.assertRaises(frappe.PermissionError):
            clinics.clinic_team(submitted['application'])
        fixtures.login('c1')
        revoked = clinics.revoke_clinic_membership(invitation['membership'],
                                                    'Synthetic test revocation.')
        self.assertEqual(revoked['status'], 'Revoked')
        self.assertTrue(clinics.revoke_clinic_membership(invitation['membership'],
            'Synthetic test revocation.')['idempotent'])
        fixtures.login('p2')
        self.assertEqual(clinics.my_clinic_memberships()['memberships'][0].status, 'Revoked')
        self.assertFalse(journey._clinic_workspace_available(fixtures.USERS['p2']))
        self.assertTrue(frappe.has_permission('Tele Tena Clinic Membership', 'read',
            doc=frappe.get_doc('Tele Tena Clinic Membership', invitation['membership']),
            user=fixtures.USERS['p2']))

    def test_patient_clinic_grant_is_scheduling_only_revocable_and_membership_scoped(self):
        fixtures.login('c1')
        registration = clinics.submit_clinic_application(
            clinic_name='Synthetic Access Clinic', legal_name='Synthetic Access Clinic Ltd',
            registration_reference='TEST-ACCESS-' + secrets.token_hex(4),
            jurisdiction='Synthetic jurisdiction', public_description='Synthetic test clinic')
        clinic = registration['application']
        fixtures.login('admin')
        clinics.review_clinic(clinic, 'Verified', 'Synthetic reviewer fixture only.')
        fixtures.login('c1')
        affiliation = clinics.submit_affiliation(clinic, 'Synthetic clinician',
                                                   'Synthetic affiliation evidence only.')
        fixtures.login('admin')
        clinics.review_affiliation(affiliation['application'], 'Verified',
                                    'Synthetic affiliation review only.')

        self.fund_patient('p1', 3000)
        day, _, _ = self.make_schedule(mode='automatic')
        offering = fixtures.Integration.offers['c1']
        booked = self.book_slot(offering, self.slots(offering, day)[0],
                                'clinic-access-' + secrets.token_hex(6), share_name=False)
        appointment = booked['id']
        fixtures.login('p1')
        eligible = clinic_access.eligible_clinics_for_appointment(appointment)
        self.assertIn(clinic, [item['clinic'] for item in eligible])
        granted = clinic_access.grant_schedule_access(appointment, clinic)
        self.assertEqual(granted['status'], 'Active')
        self.assertFalse(granted['idempotent'])
        self.assertTrue(clinic_access.grant_schedule_access(appointment, clinic)['idempotent'])
        self.assertFalse(frappe.has_permission('Tele Tena Clinic Encounter Access', 'read',
            doc=frappe.get_doc('Tele Tena Clinic Encounter Access', granted['grant']),
            user=fixtures.USERS['p1']))
        self.assertEqual(frappe.get_list('Tele Tena Clinic Encounter Access', fields=['name']), [])
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc({'doctype':'Tele Tena Clinic Encounter Access', 'clinic':clinic,
                'appointment':appointment, 'patient':fixtures.USERS['p1'],
                'clinician':fixtures.USERS['c1'], 'purpose':'Scheduling coordination',
                'status':'Active', 'granted_by':fixtures.USERS['p1']}).insert()

        fixtures.login('c1')  # verified clinic owner
        self.assertTrue(journey._clinic_workspace_available(fixtures.USERS['c1']))
        schedule = clinic_access.clinic_schedule_access()
        self.assertEqual(len(schedule), 1)
        self.assertEqual(schedule[0]['patient_label'], 'Private patient')
        self.assertNotIn('appointment', schedule[0])
        self.assertNotIn('patient', schedule[0])
        self.assertNotIn('disclosure', schedule[0])
        self.assertNotIn('price', schedule[0])
        self.assertEqual(set(schedule[0]), {'access','clinic','patient_label','service',
            'start','end','timezone','format','minutes','status'})
        fixtures.login('c2')
        self.assertEqual(clinic_access.clinic_schedule_access(), [])
        with self.assertRaises(frappe.PermissionError):
            clinic_access.eligible_clinics_for_appointment(appointment)

        fixtures.login('c1')
        billing = clinics.invite_clinic_member(clinic, fixtures.USERS['c2'], 'Billing')
        frappe.db.sql('''INSERT INTO tt_contact_identity(channel,contact,user,verified_at)
            VALUES ('email',%s,%s,NOW(6))''', (fixtures.USERS['c2'], fixtures.USERS['c2']))
        fixtures.login('c2')
        clinics.respond_to_clinic_invitation(billing['membership'], 'accept')
        self.assertEqual(clinic_access.clinic_schedule_access(), [])
        self.assertFalse(journey._clinic_workspace_available(fixtures.USERS['c2']))

        fixtures.login('c1')
        scheduling = clinics.invite_clinic_member(clinic, fixtures.USERS['c3'], 'Scheduling')
        frappe.db.sql('''INSERT INTO tt_contact_identity(channel,contact,user,verified_at)
            VALUES ('email',%s,%s,NOW(6))''', (fixtures.USERS['c3'], fixtures.USERS['c3']))
        fixtures.login('c3')
        clinics.respond_to_clinic_invitation(scheduling['membership'], 'accept')
        self.assertEqual(len(clinic_access.clinic_schedule_access()), 1)
        fixtures.login('c1')
        clinics.revoke_clinic_membership(scheduling['membership'], 'Synthetic revocation test.')
        fixtures.login('c3')
        self.assertEqual(clinic_access.clinic_schedule_access(), [])

        fixtures.login('p2')
        with self.assertRaises(frappe.PermissionError):
            clinic_access.revoke_schedule_access(granted['grant'], 'Not the granting patient.')
        self.assertEqual(clinic_access.my_schedule_access(appointment), [])
        fixtures.login('p1')
        revoked = clinic_access.revoke_schedule_access(granted['grant'], 'Synthetic revoke test.')
        self.assertEqual(revoked['status'], 'Revoked')
        self.assertTrue(clinic_access.revoke_schedule_access(
            granted['grant'], 'Synthetic revoke test.')['idempotent'])
        self.assertEqual(clinic_access.my_schedule_access(appointment)[0]['status'], 'Revoked')
        fixtures.login('c1')
        self.assertEqual(clinic_access.clinic_schedule_access(), [])

    def test_vetting_rubric_definition_is_reviewer_scoped_and_migration_is_repeatable(self):
        before = journey.rows('''SELECT name,scope_application,decision,rubric_version,findings
            FROM `tabTele Tena Vetting Assessment` ORDER BY name''')
        v1_27_vetting_rubric_assessment.execute()
        v1_27_vetting_rubric_assessment.execute()
        self.assertTrue(frappe.db.sql(
            "SHOW COLUMNS FROM `tabTele Tena Vetting Assessment` LIKE 'scored_criteria_snapshot'"))
        after = journey.rows('''SELECT name,scope_application,decision,rubric_version,findings
            FROM `tabTele Tena Vetting Assessment` ORDER BY name''')
        self.assertEqual([tuple(row.values()) for row in after], [tuple(row.values()) for row in before])

        fixtures.login('p1')
        with self.assertRaises(frappe.PermissionError):
            vetting.rubric_definition()
        fixtures.login('admin')
        rubric = vetting.rubric_definition()
        self.assertEqual(rubric['version'], 'proposed-1.0')
        self.assertEqual(rubric['status'], 'Proposed')
        self.assertEqual(len(rubric['scored_criteria']), 6)
        self.assertIn('Human reviewers apply mandatory gates', rubric['decision_rule'])

    def test_credential_provenance_migration_is_repeatable_and_preserves_history(self):
        before = journey.rows('''SELECT name,scope_application,decision,rubric_version,
                credential_verified,findings FROM `tabTele Tena Vetting Assessment` ORDER BY name''')
        v1_29_credential_verification_provenance.execute()
        v1_29_credential_verification_provenance.execute()
        self.assertTrue(frappe.db.sql(
            "SHOW COLUMNS FROM `tabTele Tena Vetting Assessment` LIKE 'credential_verification_snapshot'"))
        after = journey.rows('''SELECT name,scope_application,decision,rubric_version,
                credential_verified,findings FROM `tabTele Tena Vetting Assessment` ORDER BY name''')
        self.assertEqual([tuple(row.values()) for row in after], [tuple(row.values()) for row in before])
        self.assertTrue(all(not row.credential_verification_snapshot for row in journey.rows(
            'SELECT credential_verification_snapshot FROM `tabTele Tena Vetting Assessment`')))

    def test_vetting_rubric_registry_is_immutable_and_requires_medical_lead(self):
        before = journey.rows('''SELECT version,status,definition_sha256,created_by,created_at,
                approved_by,approved_at,approval_reason
            FROM tt_vetting_rubric_version ORDER BY version''')
        v1_28_vetting_rubric_registry.execute()
        v1_28_vetting_rubric_registry.execute()
        after = journey.rows('''SELECT version,status,definition_sha256,created_by,created_at,
                approved_by,approved_at,approval_reason
            FROM tt_vetting_rubric_version ORDER BY version''')
        self.assertEqual([tuple(row.values()) for row in after], [tuple(row.values()) for row in before])

        proposal = 'proposed-9.' + str(secrets.randbelow(900000) + 100000)
        definition = {
            'title': 'Synthetic immutable rubric proposal',
            'approval_note': 'Synthetic test only; not a clinical standard.',
            'decision_rule': 'Scores support human review and cannot override mandatory gates.',
            'score_min': 0, 'score_max': 3,
            'scored_criteria': [{'key': 'scope_evidence', 'label': 'Scope evidence'}],
        }
        fixtures.login('p1')
        with self.assertRaises(frappe.PermissionError):
            vetting.rubric_versions()
        with self.assertRaises(frappe.PermissionError):
            vetting.propose_rubric_version('v7.1', definition)
        fixtures.login('admin')
        original_current = vetting.current_rubric_version()
        proposed = vetting.propose_rubric_version(proposal, definition)
        self.assertEqual(proposed['status'], 'Proposed')
        proposal_view = next(item for item in vetting.rubric_versions()['items']
                             if item.version == proposal)
        self.assertEqual(proposal_view.definition['title'], definition['title'])
        self.assertEqual(proposal_view.definition['definition_sha256'], proposed['definition_sha256'])
        self.assertEqual(proposal_view.definition['scored_criteria'], definition['scored_criteria'])
        self.assertEqual(vetting.current_rubric_version(), original_current)
        with self.assertRaises(frappe.ValidationError):
            vetting.propose_rubric_version(proposal, definition)
        with self.assertRaises(frappe.PermissionError):
            vetting.approve_rubric_version(proposal, 'Approver cannot approve medical rubric.')

        lead = frappe.get_doc('User', fixtures.USERS['c3'])
        from tele_tena.account_context import authorized_user_change
        with authorized_user_change():
            lead.add_roles('Tele Tena Medical Lead')
        frappe.clear_cache(user=lead.name)
        original_registry = journey.rows('''SELECT version,status,approved_by,approved_at,approval_reason
            FROM tt_vetting_rubric_version''')
        try:
            fixtures.login('c3')
            approved = vetting.approve_rubric_version(proposal, 'Synthetic medical-lead approval test.')
            self.assertEqual(approved['status'], 'Approved')
            self.assertTrue(vetting.approve_rubric_version(
                proposal, 'Synthetic retry rationale.')['idempotent'])
            self.assertEqual(vetting.current_rubric_version(), proposal)
            with self.assertRaises(frappe.ValidationError):
                vetting.propose_rubric_version(proposal, definition)
        finally:
            frappe.set_user('Administrator')
            frappe.db.sql('DELETE FROM tt_vetting_rubric_version WHERE version=%s', (proposal,))
            for item in original_registry:
                frappe.db.sql('''UPDATE tt_vetting_rubric_version SET status=%s,approved_by=%s,
                    approved_at=%s,approval_reason=%s WHERE version=%s''',
                    (item.status,item.approved_by,item.approved_at,item.approval_reason,item.version))
            with authorized_user_change():
                lead.remove_roles('Tele Tena Medical Lead')
            frappe.clear_cache(user=lead.name)
            frappe.db.commit()

        fixtures.login('admin')
        self.assertEqual(vetting.current_rubric_version(), original_current)
        row = journey.rows('SELECT definition_sha256 FROM tt_vetting_rubric_version WHERE version=%s',
                           ('proposed-1.0',))[0]
        original_digest = row.definition_sha256
        try:
            frappe.db.sql("UPDATE tt_vetting_rubric_version SET definition_sha256=%s WHERE version='proposed-1.0'",
                          ('0' * 64,))
            with self.assertRaises(frappe.ValidationError):
                vetting.rubric_definition('proposed-1.0')
        finally:
            frappe.db.sql("UPDATE tt_vetting_rubric_version SET definition_sha256=%s WHERE version='proposed-1.0'",
                          (original_digest,))
            frappe.db.commit()

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
        pdf = base64.b64encode(b'%PDF-1.4\nSynthetic service-scope evidence\n%%EOF').decode()
        first_evidence = vetting.upload_scope_evidence(application['name'], 'License or registration',
                                                       'synthetic-license.pdf', pdf)
        second_evidence = vetting.upload_scope_evidence(application['name'], 'License or registration',
                                                        'synthetic-license-revised.pdf', pdf)
        self.assertEqual(second_evidence['revision'], 2)
        listed = next(item for item in vetting.my_scope_applications()
                      if item.name == application['name'])
        self.assertEqual([item.revision for item in listed.scope_evidence], [2, 1])
        self.assertNotIn('content', listed.scope_evidence[0])
        stored = journey.one('SELECT content FROM tt_scope_evidence_content WHERE evidence=%s',
                             (first_evidence['id'],))
        self.assertEqual(bytes(stored.content), base64.b64decode(pdf))
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc('Tele Tena Scope Evidence', first_evidence['id']).insert()
        fixtures.login('c1')
        with self.assertRaises(frappe.PermissionError):
            vetting.download_scope_evidence(first_evidence['id'])
        fixtures.login('p1')
        with self.assertRaises(frappe.PermissionError):
            vetting.download_scope_evidence(first_evidence['id'])
        fixtures.login('admin')
        vetting.download_scope_evidence(first_evidence['id'])
        self.assertEqual(bytes(frappe.local.response.filecontent), base64.b64decode(pdf))
        fixtures.login('vetting')
        with self.assertRaises(frappe.ValidationError):
            vetting.upload_scope_evidence(application['name'], 'Other supporting evidence',
                                          'bad.pdf', base64.b64encode(b'not a pdf').decode())
        application = vetting.save_scope_application(service, {
            'professional_category':'Synthetic counselor','qualification':'Synthetic qualification',
            'issuing_institution':'Synthetic institution','registration_number':'TEST-ONLY',
            'issuing_authority':'Synthetic issuer','jurisdiction':'Synthetic jurisdiction',
            'experience_years':'4','approach_keys':'','population_adults':True,
            'independent_practice':True,'relevant_training':'Synthetic supervised practice',
            'applicant_statement':'Synthetic evidence; no external credential claim.'}, submit=True)
        self.assertEqual(application['status'], 'Submitted')
        with self.assertRaises(frappe.ValidationError):
            vetting.upload_scope_evidence(application['name'], 'Other supporting evidence',
                'after-submit.pdf', pdf)
        self.assertEqual(int(journey.one('''SELECT COUNT(*) n FROM `tabTele Tena Scope Evidence`
            WHERE scope_application=%s''', (application['name'],)).n), 2)
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
        with self.assertRaises(frappe.ValidationError):
            vetting.review_scope_application(application['name'], 'Approved',
                identity_reviewed=True, credential_verified=True, qualification_relevant=True,
                experience_adequate=True, adult_scope_appropriate=True, interview_completed=True,
                findings='A verified credential requires source provenance.',
                scored_criteria=proposed_rubric_scores(first_evidence['id']))
        self.assertEqual(frappe.local.response.get('tele_tena_error'), 'credential_provenance_required')
        source_without_verified_flag = credential_source_payload(first_evidence['id'])
        with self.assertRaises(frappe.ValidationError):
            vetting.review_scope_application(application['name'], 'Approved',
                findings='Credential provenance cannot be recorded without the verified flag.',
                credential_source=source_without_verified_flag['credential_source'],
                credential_checked_on=source_without_verified_flag['credential_checked_on'],
                credential_evidence=source_without_verified_flag['credential_evidence'],
                credential_source_reference=source_without_verified_flag['credential_source_reference'])
        self.assertEqual(frappe.local.response.get('tele_tena_error'), 'credential_verification_flag_required')
        future_check = credential_source_payload(first_evidence['id'])
        future_check['credential_checked_on'] = frappe.utils.add_days(frappe.utils.today(), 1)
        with self.assertRaises(frappe.ValidationError):
            vetting.review_scope_application(application['name'], 'Approved',
                identity_reviewed=True, credential_verified=True, qualification_relevant=True,
                experience_adequate=True, adult_scope_appropriate=True, interview_completed=True,
                findings='A future credential check date must fail closed.',
                scored_criteria=proposed_rubric_scores(first_evidence['id']), **future_check)
        self.assertEqual(frappe.local.response.get('tele_tena_error'), 'credential_check_date_invalid')
        invalid_credential_source = credential_source_payload('foreign-license-evidence')
        with self.assertRaises(frappe.ValidationError):
            vetting.review_scope_application(application['name'], 'Approved',
                identity_reviewed=True, credential_verified=True, qualification_relevant=True,
                experience_adequate=True, adult_scope_appropriate=True, interview_completed=True,
                findings='A credential source must cite license evidence from this scope.',
                scored_criteria=proposed_rubric_scores(first_evidence['id']),
                **invalid_credential_source)
        with self.assertRaises(frappe.ValidationError):
            vetting.review_scope_application(application['name'], 'Approved',
                identity_reviewed=True, credential_verified=True, qualification_relevant=True,
                experience_adequate=True, adult_scope_appropriate=True, interview_completed=True,
                findings='Missing rubric scores must fail closed.',
                **credential_source_payload(first_evidence['id']))
        invalid_scores = proposed_rubric_scores(first_evidence['id'])
        invalid_scores['unapproved_dimension'] = {'score': 3, 'rationale': 'Synthetic', 'evidence': []}
        with self.assertRaises(frappe.ValidationError):
            vetting.review_scope_application(application['name'], 'Approved',
                identity_reviewed=True, credential_verified=True, qualification_relevant=True,
                experience_adequate=True, adult_scope_appropriate=True, interview_completed=True,
                findings='Unknown dimensions must fail closed.', scored_criteria=invalid_scores,
                **credential_source_payload(first_evidence['id']))
        invalid_evidence_scores = proposed_rubric_scores('not-this-applications-evidence')
        with self.assertRaises(frappe.ValidationError):
            vetting.review_scope_application(application['name'], 'Approved',
                identity_reviewed=True, credential_verified=True, qualification_relevant=True,
                experience_adequate=True, adult_scope_appropriate=True, interview_completed=True,
                findings='Cross-application evidence references must fail closed.',
                scored_criteria=invalid_evidence_scores,
                **credential_source_payload(first_evidence['id']))
        self.assertEqual(frappe.db.get_value('Tele Tena Vetting Scope Application',
            application['name'], 'status'), 'Resubmitted')
        result = vetting.review_scope_application(application['name'], 'Approved',
            identity_reviewed=True, credential_verified=True, qualification_relevant=True,
            experience_adequate=True, approach_evidence_reviewed=True,
            adult_scope_appropriate=True, interview_completed=True,
            findings='Synthetic reviewer assessment; test only.',
            scored_criteria=proposed_rubric_scores(first_evidence['id']),
            **credential_source_payload(first_evidence['id']))
        self.assertEqual(result['status'], 'Approved')
        self.assertTrue(journey.service_scope_is_current(email, service))
        reviewer_view = next(item for item in vetting.my_scope_applications() if item.name == application['name'])
        self.assertEqual(reviewer_view.credential_verification['evidence']['id'], first_evidence['id'])
        fixtures.login('vetting')
        applicant_view = next(item for item in vetting.my_scope_applications() if item.name == application['name'])
        self.assertNotIn('credential_verification', applicant_view)
        fixtures.login('p1')
        with self.assertRaises(frappe.PermissionError):
            vetting.my_scope_applications()
        fixtures.login('admin')
        assessments = journey.rows('SELECT name FROM `tabTele Tena Vetting Assessment` WHERE scope_application=%s',
                                   (application['name'],))
        self.assertEqual(len(assessments), 2)
        latest_assessment = frappe.get_doc('Tele Tena Vetting Assessment', result['assessment'])
        evidence_snapshot = json.loads(latest_assessment.scope_evidence_snapshot)
        self.assertEqual(len(evidence_snapshot), 2)
        self.assertEqual({item['revision'] for item in evidence_snapshot}, {1, 2})
        rubric_snapshot = json.loads(latest_assessment.scored_criteria_snapshot)
        self.assertEqual(rubric_snapshot['version'], 'proposed-1.0')
        self.assertEqual(rubric_snapshot['status'], 'Proposed')
        self.assertEqual(rubric_snapshot['definition_sha256'],
            hashlib.sha256(json.dumps(rubric_snapshot['definition_snapshot'],
                separators=(',', ':'), sort_keys=True).encode()).hexdigest())
        self.assertEqual(len(rubric_snapshot['dimensions']), 6)
        self.assertEqual(rubric_snapshot['dimensions'][0]['evidence'][0]['id'], first_evidence['id'])
        self.assertEqual(rubric_snapshot['dimensions'][0]['evidence'][0]['revision'], 1)
        verification_snapshot=json.loads(latest_assessment.credential_verification_snapshot)
        self.assertEqual(verification_snapshot['source'],'Synthetic licensing registry (test fixture)')
        self.assertEqual(verification_snapshot['evidence']['id'],first_evidence['id'])
        self.assertEqual(verification_snapshot['evidence']['revision'],1)
        self.assertEqual(verification_snapshot['snapshot_sha256'],
            hashlib.sha256(json.dumps({key:value for key,value in verification_snapshot.items()
                if key!='snapshot_sha256'},separators=(',', ':'),sort_keys=True).encode()).hexdigest())
        saved_credential_snapshot=latest_assessment.credential_verification_snapshot
        try:
            tampered=json.loads(saved_credential_snapshot);tampered['source']='Changed after decision'
            frappe.db.sql('UPDATE `tabTele Tena Vetting Assessment` SET credential_verification_snapshot=%s WHERE name=%s',
                (json.dumps(tampered,separators=(',', ':'),sort_keys=True),latest_assessment.name))
            with self.assertRaises(frappe.ValidationError):
                vetting.my_scope_applications()
        finally:
            frappe.db.sql('UPDATE `tabTele Tena Vetting Assessment` SET credential_verification_snapshot=%s WHERE name=%s',
                (saved_credential_snapshot,latest_assessment.name))
        with self.assertRaises(frappe.PermissionError):
            assessment = frappe.get_doc('Tele Tena Vetting Assessment', result['assessment'])
            assessment.findings = 'Attempted overwrite'
            assessment.save()
        with self.assertRaises(frappe.PermissionError):
            assessment = frappe.get_doc('Tele Tena Vetting Assessment', result['assessment'])
            assessment.scored_criteria_snapshot = '{}'
            assessment.save()

        # A later suspension is appealable, but the appeal itself does not
        # grant practice. Reopening requires resubmission and a fresh decision.
        vetting.review_scope_application(application['name'], 'Suspended',
            findings='Synthetic suspension for reconsideration regression.')
        suspended_assessment = journey.one('''SELECT name FROM `tabTele Tena Vetting Assessment`
            WHERE scope_application=%s ORDER BY decided_at DESC,creation DESC LIMIT 1''',
            (application['name'],)).name
        fixtures.login('vetting')
        appeal = vetting.submit_scope_appeal(application['name'],
            'Synthetic request to reconsider this scope decision.')
        self.assertEqual(appeal['status'], 'Submitted')
        with self.assertRaises(frappe.ValidationError):
            vetting.submit_scope_appeal(application['name'],
                'A retry cannot replace the original reconsideration statement.')
        retry = vetting.submit_scope_appeal(application['name'],
            'Synthetic request to reconsider this scope decision.')
        self.assertTrue(retry['idempotent'])
        self.assertEqual(retry['id'], appeal['id'])
        self.assertEqual(journey.one('''SELECT applicant_statement FROM `tabTele Tena Vetting Appeal`
            WHERE name=%s''', (appeal['id'],)).applicant_statement,
            'Synthetic request to reconsider this scope decision.')
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc({'doctype':'Tele Tena Vetting Appeal',
                'scope_application':application['name'],'clinician':email,
                'basis_assessment':suspended_assessment,'sequence':99,
                'applicant_statement':'Direct API insertion attempt.',
                'submitted_at':frappe.utils.now_datetime(),'status':'Submitted'}).insert()
        own_appeal = next(item for item in vetting.my_scope_applications()
                          if item.name == application['name']).appeals[0]
        self.assertEqual(own_appeal.basis_assessment, suspended_assessment)
        appeal_doc = frappe.get_doc('Tele Tena Vetting Appeal', appeal['id'])
        appeal_doc.applicant_statement = 'tamper'
        with self.assertRaises(frappe.PermissionError):
            appeal_doc.save()
        fixtures.login('p1')
        with self.assertRaises(frappe.PermissionError):
            vetting.scope_appeals()
        with self.assertRaises(frappe.PermissionError):
            frappe.get_list('Tele Tena Vetting Appeal', fields=['name'])
        fixtures.login('admin')
        self.assertEqual(vetting.scope_appeals()[0].name, appeal['id'])
        vetting.review_scope_appeal(appeal['id'], 'Reopen',
            'Synthetic reviewer found a process issue; provide updated evidence.')
        reopened = frappe.get_doc('Tele Tena Vetting Scope Application', application['name'])
        self.assertEqual(reopened.status, 'Clarification')
        self.assertFalse(journey.service_scope_is_current(email, service))
        fixtures.login('vetting')
        self.assertTrue(vetting.submit_scope_appeal(application['name'],
            'Synthetic request to reconsider this scope decision.')['idempotent'])
        resubmitted = vetting.save_scope_application(service, {
            'professional_category':'Synthetic counselor','qualification':'Synthetic qualification',
            'issuing_institution':'Synthetic institution','registration_number':'TEST-ONLY',
            'issuing_authority':'Synthetic issuer','jurisdiction':'Synthetic jurisdiction',
            'experience_years':'4','approach_keys':'','population_adults':True,
            'independent_practice':True,'relevant_training':'Updated synthetic training',
            'applicant_statement':'Synthetic appeal resubmission.',
            'applicant_response':'Synthetic new evidence submitted after reopening.'}, submit=True)
        self.assertEqual(resubmitted['status'], 'Resubmitted')
        fixtures.login('admin')
        rejected = vetting.review_scope_application(application['name'], 'Rejected',
            findings='Synthetic rejection following full reconsideration review.')
        fixtures.login('vetting')
        second_appeal = vetting.submit_scope_appeal(application['name'],
            'Synthetic reconsideration after the new review decision.')
        fixtures.login('admin')
        upheld = vetting.review_scope_appeal(second_appeal['id'], 'Upheld',
            'Synthetic rationale supports the documented outcome.')
        self.assertEqual(upheld['status'], 'Upheld')
        self.assertEqual(frappe.db.get_value('Tele Tena Vetting Scope Application',
            application['name'], 'status'), 'Rejected')
        self.assertFalse(journey.service_scope_is_current(email, service))
        self.assertEqual(journey.one('''SELECT COUNT(*) n FROM `tabTele Tena Vetting Assessment`
            WHERE scope_application=%s''', (application['name'],)).n, 4)
        self.assertEqual(journey.one('''SELECT COUNT(*) n FROM `tabTele Tena Vetting Appeal`
            WHERE scope_application=%s''', (application['name'],)).n, 2)

    def test_scope_credential_reverification_is_separate_and_expiry_fails_closed(self):
        service = fixtures.PREFIX + '-credential-renewal'
        fixtures.login('admin')
        frappe.get_doc({'doctype':'Tele Tena Service','service_key':service,
            'service_label':'Synthetic credential renewal scope','active':1,'catalog_status':'Active',
            'category':'counseling','description':'Synthetic renewal behavior only.',
            'population_restriction':'Adults only','participant_structure':'individual',
            'clinical_review_status':'Approved','vetting_required':1,
            'definition_version':'synthetic-v1'}).insert()
        email = 'renewal-' + secrets.token_hex(6) + '@example.invalid'
        fixtures.USERS['renewal'] = email
        frappe.set_user('Administrator')
        user = frappe.get_doc({'doctype':'User','email':email,'first_name':'Synthetic renewal applicant',
            'user_type':'Website User','send_welcome_email':0})
        user.insert(); user.add_roles('Tele Tena Clinician')
        fixtures.login('renewal')
        journey.save_profile('clinician','Synthetic renewal applicant',True,languages=['en'])
        presentation.upload_resume('synthetic-renewal-cv.pdf',
                                   base64.b64encode(b'%PDF-1.4\nSynthetic CV\n%%EOF').decode())
        journey.apply('Synthetic renewal test profile.',json.dumps([service]))
        fixtures.login('admin'); journey.review(email,'Approved')
        values = {'professional_category':'Synthetic counselor','qualification':'Synthetic qualification',
            'issuing_institution':'Synthetic institution','registration_number':'TEST-RENEWAL',
            'issuing_authority':'Synthetic authority','jurisdiction':'Synthetic test jurisdiction',
            'credential_expiry':frappe.utils.add_days(frappe.utils.today(),90),
            'experience_years':'4','approach_keys':'','population_adults':True,
            'independent_practice':True,'relevant_training':'Synthetic continuing training',
            'applicant_statement':'Synthetic application; no external credential claim.'}
        fixtures.login('renewal')
        base = vetting.save_scope_application(service, values)
        pdf = base64.b64encode(b'%PDF-1.4\nSynthetic license evidence\n%%EOF').decode()
        base_evidence = vetting.upload_scope_evidence(base['name'],'License or registration','license-current.pdf',pdf)
        base = vetting.save_scope_application(service,values,submit=True)
        fixtures.login('admin')
        vetting.review_scope_application(base['name'],'Approved',identity_reviewed=True,
            credential_verified=True,qualification_relevant=True,experience_adequate=True,
            adult_scope_appropriate=True,interview_completed=True,findings='Synthetic approval for renewal test.',
            scored_criteria=proposed_rubric_scores(),
            **credential_source_payload(base_evidence['id']))
        self.assertTrue(journey.service_scope_is_current(email,service))

        renewed_values = {**values, 'credential_expiry':frappe.utils.add_days(frappe.utils.today(),365),
            'applicant_statement':'Synthetic renewal statement; no new credential claim.'}
        fixtures.login('renewal')
        draft = vetting.save_scope_application(service,renewed_values,reverification_of=base['name'])
        self.assertNotEqual(draft['name'],base['name'])
        fixtures.login('c1')
        with self.assertRaises(frappe.PermissionError):
            vetting.save_scope_application(service,renewed_values,reverification_of=base['name'])
        fixtures.login('renewal')
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc({'doctype':'Tele Tena Vetting Scope Application',
                'clinician':email,'service':service,'status':'Draft',
                'professional_category':'Synthetic counselor','qualification':'Synthetic qualification',
                'issuing_institution':'Synthetic institution','reverification_of':base['name']}).insert()
        with self.assertRaises(frappe.ValidationError):
            vetting.save_scope_application(service,renewed_values,submit=True,reverification_of=base['name'])
        new_evidence = vetting.upload_scope_evidence(draft['name'],'License or registration',
            'license-renewal.pdf',pdf)
        self.assertEqual(new_evidence['revision'],1)
        renewal = vetting.save_scope_application(service,renewed_values,submit=True,
            reverification_of=base['name'])
        retry = vetting.save_scope_application(service,renewed_values,submit=True,
            reverification_of=base['name'])
        self.assertEqual(renewal['name'],retry['name'])
        self.assertTrue(retry['idempotent'])
        changed = {**renewed_values,'applicant_statement':'Different changed payload.'}
        with self.assertRaises(frappe.ValidationError):
            vetting.save_scope_application(service,changed,submit=True,reverification_of=base['name'])
        self.assertTrue(journey.service_scope_is_current(email,service),
            'a pending renewal must not shorten still-valid prior credentials')
        self.assertEqual(str(frappe.db.get_value('Tele Tena Vetting Scope Application',base['name'],
            'credential_expiry')),str(values['credential_expiry']))
        journey.publish(service,600,30)
        offering = journey.one('SELECT id FROM tt_offering WHERE clinician=%s AND service=%s',
                               (email,service)).id
        fixtures.login('renewal')
        journey.add_availability(fixtures.at(0),fixtures.at(12))
        fixtures.login('p1')
        reserved_before = journey.one('SELECT reserved FROM tt_wallet WHERE patient=%s',
            (fixtures.USERS['p1'],)).reserved
        journey.simulated_deposit(600,'scope-review-' + secrets.token_hex(5))
        existing_booking = journey.book(**fixtures.booking(offering,fixtures.at(4),
            'scope-review-' + secrets.token_hex(5)))
        self.assertEqual(existing_booking['state'],'Booked')

        # Move only this synthetic test record across the expiry boundary. The
        # application workflow itself never edits the old approved snapshot.
        frappe.db.set_value('Tele Tena Vetting Scope Application',base['name'],
            'credential_expiry',frappe.utils.add_days(frappe.utils.today(),-1),update_modified=False)
        fixtures.login('admin')
        vetting.review_scope_application(base['name'],'Expired',
            findings='Synthetic renewal regression: old credential expired.')
        self.assertFalse(journey.service_scope_is_current(email,service))
        fixtures.login('renewal')
        fixtures.login('admin')
        self.assertEqual(vetting.flag_scope_appointments_for_review(email,service)['flagged'],0)
        self.assertEqual(vetting.flag_scope_appointments_for_review(email,service)['flagged'],0)
        review = journey.one('''SELECT * FROM `tabTele Tena Scope Appointment Review`
            WHERE appointment=%s''',(existing_booking['id'],))
        self.assertEqual(review.reason_code,'Credential expired')
        self.assertNotIn('patient',review.keys())
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc({'doctype':'Tele Tena Scope Appointment Review',
                'appointment':'forged-review-' + secrets.token_hex(5),
                'scope_application':base['name'],'eligibility_event':'forged',
                'clinician':email,'service':service,'scheduled_start':fixtures.at(4),
                'reason_code':'Credential expired','status':'Open',
                'flagged_at':frappe.utils.now_datetime()}).insert()
        review_payload = vetting.scope_appointment_reviews()
        self.assertNotIn('patient',review_payload[0].keys())
        self.assertNotIn('disclosure',review_payload[0].keys())
        fixtures.login('p1')
        with self.assertRaises(frappe.PermissionError):
            vetting.scope_appointment_reviews()
        with self.assertRaises(frappe.PermissionError):
            frappe.get_list('Tele Tena Scope Appointment Review')
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc('Tele Tena Scope Appointment Review',review.name).check_permission('read')
        fixtures.login('admin')
        with self.assertRaises(frappe.ValidationError):
            vetting.resolve_scope_appointment_review(review.name,'Clear','Scope remains expired.')
        self.assertEqual(journey.one('SELECT state FROM tt_appointment WHERE id=%s',
            (existing_booking['id'],)).state,'Booked')
        self.assertEqual(journey.one('SELECT reserved FROM tt_wallet WHERE patient=%s',
            (fixtures.USERS['p1'],)).reserved,reserved_before + 600)
        fixtures.login('renewal')
        with self.assertRaises(frappe.ValidationError):
            journey.publish(service,10000,50)
        fixtures.login('p1')
        stale_booking = fixtures.booking(offering,fixtures.at(),
            'expired-scope-' + secrets.token_hex(5))
        with self.assertRaises(frappe.ValidationError):
            journey.book(**stale_booking)
        self.assertNotIn(offering,[item.id for item in journey.discover(service)])
        self.assertFalse(journey.rows('SELECT id FROM tt_appointment WHERE retry_key=%s',
                                      (stale_booking['retry_key'],)))

        fixtures.login('admin')
        frappe.db.set_value('Tele Tena Vetting Scope Application',renewal['name'],
            'credential_expiry',frappe.utils.add_days(frappe.utils.today(),-1),update_modified=False)
        with self.assertRaises(frappe.ValidationError):
            vetting.review_scope_application(renewal['name'],'Approved',identity_reviewed=True,
                credential_verified=True,qualification_relevant=True,experience_adequate=True,
                adult_scope_appropriate=True,interview_completed=True,
                findings='Expired credential must not be accepted.',
                scored_criteria=proposed_rubric_scores(),
                **credential_source_payload(new_evidence['id']))
        self.assertEqual(frappe.db.get_value('Tele Tena Vetting Scope Application',renewal['name'],
            'status'),'Submitted')
        frappe.db.set_value('Tele Tena Vetting Scope Application',renewal['name'],
            'credential_expiry',renewed_values['credential_expiry'],update_modified=False)
        vetting.review_scope_application(renewal['name'],'Approved',identity_reviewed=True,
            credential_verified=True,qualification_relevant=True,experience_adequate=True,
            adult_scope_appropriate=True,interview_completed=True,findings='Synthetic re-verification approved.',
            scored_criteria=proposed_rubric_scores(),
            **credential_source_payload(new_evidence['id']))
        self.assertTrue(journey.service_scope_is_current(email,service))
        self.assertEqual(vetting.resolve_scope_appointment_review(review.name,'Clear',
            'Renewed synthetic credential was approved.'),{'status':'Cleared','idempotent':False})
        frappe.db.set_value('Tele Tena Vetting Scope Application',renewal['name'],
            'credential_expiry',frappe.utils.add_days(frappe.utils.today(),-1),update_modified=False)
        self.assertFalse(journey.service_scope_is_current(email,service))
        self.assertEqual(vetting.flag_scope_appointments_for_review(email,service)['flagged'],1,
            'a distinct later expiry event must be reviewable for the same appointment')
        self.assertEqual(journey.one('''SELECT COUNT(*) AS n FROM `tabTele Tena Scope Appointment Review`
            WHERE appointment=%s''',(existing_booking['id'],)).n,2)
        frappe.db.set_value('Tele Tena Vetting Scope Application',renewal['name'],
            'credential_expiry',renewed_values['credential_expiry'],update_modified=False)
        self.assertEqual(frappe.db.get_value('Tele Tena Vetting Scope Application',renewal['name'],
            'reverification_of'),base['name'])
        self.assertEqual(frappe.db.get_value('Tele Tena Vetting Scope Application',base['name'],
            'status'),'Expired')

        # Rejecting a later renewal must not revoke a still-current previous
        # credential; the failed renewal remains an auditable separate record.
        second_values = {**renewed_values,
            'credential_expiry':frappe.utils.add_days(frappe.utils.today(),730),
            'applicant_statement':'Synthetic next renewal for rejection test.'}
        fixtures.login('renewal')
        second_draft = vetting.save_scope_application(service,second_values,
            reverification_of=renewal['name'])
        vetting.upload_scope_evidence(second_draft['name'],'License or registration',
            'license-next-renewal.pdf',pdf)
        second_renewal = vetting.save_scope_application(service,second_values,submit=True,
            reverification_of=renewal['name'])
        fixtures.login('admin')
        vetting.review_scope_application(second_renewal['name'],'Rejected',
            findings='Synthetic renewal evidence rejected; previous approval is still current.')
        self.assertTrue(journey.service_scope_is_current(email,service))
        self.assertEqual(frappe.db.get_value('Tele Tena Service Scope',
            {'clinician':email,'service':service},'status'),'Approved')

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

    def test_mutual_reschedule_keeps_original_hold_until_counterparty_accepts(self):
        savepoint = 'tt_reschedule_' + uuid.uuid4().hex[:16]
        frappe.db.sql('SAVEPOINT ' + savepoint)
        try:
            offering = fixtures.Integration.offers['c1']
            day = day_offset(18)
            fixtures.login('c1')
            payload = schedule_payload(offering, day, mode='automatic')
            payload['minimum_notice_minutes'] = 0
            scheduling.save_schedule(**payload)
            fixtures.login('p1')
            journey.simulated_deposit(10000, 'reschedule-test-' + secrets.token_hex(10))
            available = self.slots(offering, day)
            self.assertGreaterEqual(len(available), 6)
            original = self.book_slot(offering, available[0])
            before = journey.one('SELECT start,price,state FROM tt_appointment WHERE id=%s', (original['id'],))
            wallet_before = journey.one('SELECT available,reserved FROM tt_wallet WHERE patient=%s',
                                        (fixtures.USERS['p1'],))
            replacement = available[4]
            retry_key = 'reschedule-' + secrets.token_hex(8)
            proposed = presentation.propose_reschedule(original['id'], replacement['start'], retry_key)
            retried = presentation.propose_reschedule(original['id'], replacement['start'], retry_key)
            self.assertEqual(proposed['id'], retried['id'])
            self.assertTrue(retried['idempotent'])
            self.assertEqual(journey.one('SELECT start FROM tt_appointment WHERE id=%s',
                                         (original['id'],)).start, before.start)
            self.assertEqual(journey.one('SELECT reserved FROM tt_wallet WHERE patient=%s',
                                         (fixtures.USERS['p1'],)).reserved, wallet_before.reserved)
            with self.assertRaises(frappe.ValidationError):
                presentation.propose_reschedule(original['id'], available[5]['start'], retry_key)
            with self.assertRaises(frappe.PermissionError):
                presentation.respond_to_reschedule(original['id'], proposed['id'], 'accept')
            fixtures.login('c2')
            with self.assertRaises(frappe.PermissionError):
                presentation.appointment_detail(original['id'])
            fixtures.login('c1')
            result = presentation.respond_to_reschedule(original['id'], proposed['id'], 'accept')
            self.assertEqual(result['state'], 'Accepted')
            self.assertEqual(result['start'], replacement['start'])
            repeated = presentation.respond_to_reschedule(original['id'], proposed['id'], 'accept')
            self.assertTrue(repeated['idempotent'])
            fixtures.login('p1')
            timeline = presentation.appointment_detail(original['id'])['timeline']
            self.assertIn('New time accepted', [event['event'] for event in timeline])
            self.assertNotIn('RescheduleAccepted', str(timeline))
            after = journey.one('SELECT start,end,price,state FROM tt_appointment WHERE id=%s',
                                (original['id'],))
            moved_start = datetime.fromisoformat(replacement['start'].replace('Z', '+00:00')).replace(tzinfo=None)
            self.assertEqual((after.start, after.price, after.state),
                             (moved_start, before.price, before.state))
            wallet_after = journey.one('SELECT available,reserved FROM tt_wallet WHERE patient=%s',
                                       (fixtures.USERS['p1'],))
            self.assertEqual((wallet_after.available, wallet_after.reserved),
                             (wallet_before.available, wallet_before.reserved))
            self.assertEqual(journey.one('SELECT COUNT(*) n FROM tt_journal WHERE event_ref=%s',
                                         ('booking:' + original['id'],)).n, 1)
        finally:
            frappe.db.sql('ROLLBACK TO SAVEPOINT ' + savepoint)
            frappe.db.sql('RELEASE SAVEPOINT ' + savepoint)

    def test_mutual_reschedule_revalidates_target_slot_at_acceptance(self):
        savepoint = 'tt_reschedule_conflict_' + uuid.uuid4().hex[:12]
        frappe.db.sql('SAVEPOINT ' + savepoint)
        try:
            offering = fixtures.Integration.offers['c1']
            day = day_offset(20)
            fixtures.login('c1')
            payload = schedule_payload(offering, day, mode='automatic')
            payload['minimum_notice_minutes'] = 0
            scheduling.save_schedule(**payload)
            fixtures.login('p1')
            journey.simulated_deposit(10000, 'reschedule-conflict-p1-' + secrets.token_hex(8))
            slots = self.slots(offering, day)
            original = self.book_slot(offering, slots[0])
            alternate = slots[8]
            proposal = presentation.propose_reschedule(original['id'], alternate['start'],
                                                        'reschedule-conflict-' + secrets.token_hex(8))
            fixtures.login('p2')
            journey.simulated_deposit(10000, 'reschedule-conflict-p2-' + secrets.token_hex(8))
            competing = self.book_slot(offering, alternate, who='p2')
            self.assertNotEqual(competing['id'], original['id'])
            fixtures.login('c1')
            result = presentation.respond_to_reschedule(original['id'], proposal['id'], 'accept')
            self.assertEqual(result['state'], 'Unavailable')
            persisted = journey.one('SELECT start,state FROM tt_appointment WHERE id=%s', (original['id'],))
            self.assertEqual(persisted.start, datetime.fromisoformat(slots[0]['start'].replace('Z','+00:00')).replace(tzinfo=None))
            self.assertEqual(persisted.state, 'Booked')
            proposal_state = journey.one('SELECT state FROM tt_reschedule_proposal WHERE id=%s', (proposal['id'],))
            self.assertEqual(proposal_state.state, 'Unavailable')
        finally:
            frappe.db.sql('ROLLBACK TO SAVEPOINT ' + savepoint)
            frappe.db.sql('RELEASE SAVEPOINT ' + savepoint)

    def test_patient_request_detail_is_owner_scoped_and_returns_persisted_snapshot(self):
        fixtures.login('p1')
        key = 'request-detail-' + secrets.token_hex(8)
        start = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        published = open_requests.publish_request(
            service=fixtures.PREFIX, request_text='Synthetic request detail only.',
            urgency='scheduled', language='en', consultation_format='audio',
            sharing={'name': False, 'history': False}, retry_key=key,
            timezone_name='Africa/Addis_Ababa', earliest_start=start, latest_start=start)
        detail = open_requests.my_request_detail(published['id'])
        self.assertEqual(detail.id, published['id'])
        self.assertEqual(detail.request_text, 'Synthetic request detail only.')
        self.assertEqual(detail.disclosure_snapshot, {'request': 'Synthetic request detail only.'})
        self.assertEqual(detail.offers, [])
        fixtures.login('p2')
        with self.assertRaises(frappe.ValidationError):
            open_requests.my_request_detail(published['id'])
        with self.assertRaises(frappe.ValidationError):
            open_requests.my_request_detail('00000000-0000-0000-0000-000000000000')
        fixtures.login('c1')
        with self.assertRaises(frappe.PermissionError):
            open_requests.my_request_detail(published['id'])

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
        self.assertEqual(journey.one('SELECT acquisition_source FROM tt_appointment WHERE id=%s',
                                     (match['appointment'],)).acquisition_source, 'open_request')
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

    def test_progressive_request_waves_are_due_bounded_and_deduplicated(self):
        """The scheduler widens to new eligible clinicians without repeat notices."""
        from zoneinfo import ZoneInfo

        savepoint = 'tt_request_waves_' + uuid.uuid4().hex[:14]
        frappe.db.sql('SAVEPOINT ' + savepoint)
        try:
            service = fixtures.PREFIX
            day = day_offset(21)
            offering_by_clinician = dict(fixtures.Integration.offers)

            # c3 begins as an unapproved synthetic applicant. Approval is an
            # explicit fixture action; no scope is inferred from profile data.
            fixtures.login('admin')
            journey.review(fixtures.USERS['c3'], 'Approved')
            journey.review_service_scope(fixtures.USERS['c3'], service, 'Approved')
            fixtures.login('c3')
            created = journey.publish(service, 600, 30, 'Wave test consultation',
                'Synthetic offer for progressive routing coverage.', retry_key='wave-test-' + secrets.token_hex(8))
            offering_by_clinician['c3'] = created['offering']

            for kind, offering in offering_by_clinician.items():
                fixtures.login(kind)
                journey.save_profile('clinician', 'Synthetic clinician ' + kind, True,
                                     languages=['en'])
                payload = schedule_payload(offering, day, mode='automatic')
                payload['minimum_notice_minutes'] = 0
                payload['buffer_before'] = 0
                payload['buffer_after'] = 0
                scheduling.save_schedule(**payload)

            fixtures.login('p1')
            common_slots = None
            for offering in offering_by_clinician.values():
                starts = {slot['start'] for slot in self.slots(offering, day)}
                common_slots = starts if common_slots is None else common_slots.intersection(starts)
            self.assertTrue(common_slots, 'Synthetic clinicians must share at least one conflict-free slot')
            start = sorted(common_slots)[0]
            with patch.dict(frappe.conf, {
                'tele_tena_request_wave_1_size': 1,
                'tele_tena_request_wave_2_size': 1,
                'tele_tena_request_wave_3_size': 1,
                'tele_tena_request_wave_2_seconds': 10,
                'tele_tena_request_wave_3_seconds': 20,
            }):
                published = open_requests.publish_request(
                    service=service,
                    request_text='Synthetic scheduled request for bounded wave delivery.',
                    urgency='scheduled', language='en', consultation_format='video',
                    sharing={'name': False, 'history': False},
                    retry_key='routing-waves-' + secrets.token_hex(8),
                    timezone_name='Africa/Addis_Ababa',
                    earliest_start=start,
                    latest_start=start)
                self.assertEqual(published['eligible_supply'], 3)
                self.assertEqual(published['notified'], 1)
                self.assertEqual(published['wave'], 1)

                request = journey.one('SELECT * FROM tt_open_request WHERE id=%s',
                                      (published['id'],))
                first = journey.rows('SELECT clinician,wave FROM tt_request_recipient WHERE request_id=%s',
                                     (published['id'],))
                self.assertEqual(len(first), 1)
                self.assertEqual(first[0].wave, 1)

                for expected_wave, delay_seconds in ((2, 11), (3, 21)):
                    request = journey.one('SELECT last_routed_at FROM tt_open_request WHERE id=%s',
                                          (published['id'],))
                    due_at = request.last_routed_at + timedelta(seconds=delay_seconds)
                    with patch.object(open_requests, 'now', return_value=due_at):
                        open_requests.dispatch_open_requests()
                    recipients = journey.rows(
                        'SELECT clinician,wave FROM tt_request_recipient WHERE request_id=%s ORDER BY wave',
                        (published['id'],))
                    self.assertEqual(len(recipients), expected_wave)
                    self.assertEqual([int(row.wave) for row in recipients],
                                     list(range(1, expected_wave + 1)))
                    self.assertEqual(len({row.clinician for row in recipients}), expected_wave)
                    self.assertEqual(int(journey.one(
                        "SELECT COUNT(*) n FROM tt_request_route_log WHERE request_id=%s "
                        "AND event='NotificationEnqueued' AND wave=%s",
                        (published['id'], expected_wave)).n), 1)

                # Re-running the due reconciler after the last wave cannot
                # create duplicate recipients or repeat the terminal wave.
                with patch.object(open_requests, 'now', return_value=due_at + timedelta(seconds=1)):
                    open_requests.dispatch_open_requests()
                self.assertEqual(int(journey.one(
                    'SELECT COUNT(*) n FROM tt_request_recipient WHERE request_id=%s',
                    (published['id'],)).n), 3)
                self.assertEqual(int(journey.one(
                    "SELECT COUNT(*) n FROM tt_request_route_log WHERE request_id=%s "
                    "AND event='NotificationEnqueued'",
                    (published['id'],)).n), 3)
        finally:
            frappe.db.sql('ROLLBACK TO SAVEPOINT ' + savepoint)
            frappe.db.sql('RELEASE SAVEPOINT ' + savepoint)

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
        # Enqueued delivery is not a durable privacy/eligibility grant. A
        # clinician who loses the matching language or whose ready lease goes
        # stale must no longer receive the request disclosure from inbox reads.
        profile_row = journey.one('SELECT languages FROM tt_profile WHERE user=%s',
                                  (fixtures.USERS['c1'],))
        frappe.db.sql("UPDATE tt_profile SET languages='[]' WHERE user=%s", (fixtures.USERS['c1'],))
        self.assertFalse(any(item.id == immediate['id'] for item in open_requests.clinician_requests()))
        frappe.db.sql('UPDATE tt_profile SET languages=%s WHERE user=%s',
                      (profile_row.languages, fixtures.USERS['c1']))
        frappe.db.sql("UPDATE tt_clinician_request_presence SET expires_at='2000-01-01 00:00:00' WHERE clinician=%s",
                      (fixtures.USERS['c1'],))
        self.assertFalse(any(item.id == immediate['id'] for item in open_requests.clinician_requests()))
        frappe.db.sql('UPDATE tt_clinician_request_presence SET expires_at=%s WHERE clinician=%s',
                      (current + timedelta(seconds=90), fixtures.USERS['c1']))
        self.assertTrue(any(item.id == immediate['id'] for item in open_requests.clinician_requests()))
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

    def test_live_request_presence_is_paused_when_schedule_no_longer_fits_window(self):
        """A retained lease must not claim Available after hours move outside its start window."""
        from zoneinfo import ZoneInfo
        offering = fixtures.Integration.offers['c1']
        service = fixtures.PREFIX
        local_day = day_offset(40, zone='Africa/Addis_Ababa')
        local_now = datetime.combine(local_day, datetime.min.time().replace(hour=10, minute=5),
                                     ZoneInfo('Africa/Addis_Ababa'))
        current = local_now.astimezone(timezone.utc).replace(tzinfo=None)
        savepoint = 'tt_presence_window_' + uuid.uuid4().hex[:14]
        frappe.db.sql('SAVEPOINT ' + savepoint)
        try:
            fixtures.login('c1')
            journey.save_profile('clinician', 'Synthetic window clinician', True, languages=['en'])
            payload = dict(offering=offering, schedule_name='Synthetic immediate window',
                timezone_name='Africa/Addis_Ababa', consultation_format='video',
                confirmation_mode='automatic', minimum_notice_minutes=60, horizon_days=60,
                buffer_before=0, buffer_after=0,
                intervals=[{'weekday':local_day.weekday(),'start':'10:00','end':'12:00'}],
                exceptions=[],status='Published')
            scheduling.save_schedule(**payload)
            with patch.object(open_requests, 'now', return_value=current), \
                    patch.object(open_requests, 'dispatch_open_requests', return_value=0):
                self.assertTrue(open_requests.set_request_presence(True)['ready'])
                payload['intervals'] = [{'weekday':local_day.weekday(),'start':'11:00','end':'12:00'}]
                scheduling.save_schedule(**payload)
                readiness = open_requests.request_presence()
                self.assertFalse(readiness['ready'])
                self.assertFalse(readiness['configured'])
                self.assertEqual(readiness['immediate_window_minutes'], 30)
                self.assertIn('no_immediate_capacity', readiness['reasons'])

                fixtures.login('p1')
                request = open_requests.publish_request(service=service,
                    request_text='Synthetic request for schedule-window regression.',
                    urgency='immediate',language='en',consultation_format='video',
                    sharing={'name':False,'history':False},
                    retry_key='presence-window-' + secrets.token_hex(8),
                    timezone_name='Africa/Addis_Ababa')
                self.assertEqual(request['eligible_supply'], 0)
                self.assertEqual(request['notified'], 0)
                row = journey.one('SELECT state FROM tt_open_request WHERE id=%s',(request['id'],))
                self.assertEqual(row.state, 'Open')
                self.assertEqual(int(journey.one('SELECT COUNT(*) n FROM tt_request_recipient WHERE request_id=%s',
                                                  (request['id'],)).n), 0)
                fixtures.login('c1')
                self.assertFalse(any(item.id == request['id'] for item in open_requests.clinician_requests()))
        finally:
            frappe.db.sql('ROLLBACK TO SAVEPOINT ' + savepoint)
            frappe.db.sql('RELEASE SAVEPOINT ' + savepoint)

    def test_immediate_request_policy_is_explicit_and_site_scoped(self):
        offering = fixtures.Integration.offers['c1']
        self.make_schedule(offering=offering)
        fixtures.login('c1')
        with patch.dict(frappe.conf, tele_tena_demo_immediate_care_enabled=False):
            with patch.object(open_requests, 'clinician_languages', return_value=set()):
                presence = open_requests.request_presence()
                self.assertFalse(presence['configured'])
                self.assertIn('language_required', presence['reasons'])
                self.assertIn('immediate_policy_required', presence['reasons'])
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

    def test_immediate_service_policy_requires_reviewer_and_is_audited_idempotently(self):
        service = fixtures.PREFIX + '-immediate-policy-' + secrets.token_hex(3)
        fixtures.login('admin')
        journey.save_service(service, 'Synthetic immediate policy')
        reason = 'Synthetic reviewer approved the bounded immediate-care workflow.'
        key = 'policy-' + secrets.token_hex(12)
        try:
            with patch('tele_tena.review.enabled', return_value=True):
                self.assertTrue(any(row.id == service for row in service_policy.immediate_services()))
                changed = service_policy.set_immediate_policy(service, True, reason, key)
                self.assertTrue(changed['changed'])
                replay = service_policy.set_immediate_policy(service, True, reason, key)
                self.assertTrue(replay['replayed'])
                self.assertEqual(changed['event'], replay['event'])
                with self.assertRaises(frappe.ValidationError):
                    service_policy.set_immediate_policy(service, False, reason, key)
                self.assertTrue(frappe.db.get_value('Tele Tena Service', service,
                                                    'immediate_care_enabled'))
                events = service_policy.immediate_policy_history(service)
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0].reviewer, fixtures.USERS['admin'])
                self.assertEqual(events[0].reason, reason)
                request_id = str(uuid.uuid4())
                frappe.db.sql('''INSERT INTO tt_open_request
                    (id,patient,state,urgency,service,language,consultation_format,request_text,
                     disclosure_snapshot,max_price_minor,earliest_start,latest_start,timezone,
                     retry_key,payload_hash,sharing_choices,published_at,expires_at)
                    VALUES (%s,%s,'Open','immediate',%s,'en','video','Synthetic active request',
                     '{}',NULL,NULL,DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 20 MINUTE),
                     'Africa/Addis_Ababa',%s,REPEAT('a',64),'{}',UTC_TIMESTAMP(6),
                     DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 15 MINUTE))''',
                    (request_id, fixtures.USERS['p1'], service, 'policy-request-' + secrets.token_hex(6)))
                with self.assertRaises(frappe.ValidationError):
                    service_policy.set_immediate_policy(service, False, reason,
                                                        'policy-disable-' + secrets.token_hex(12))
                frappe.db.sql('DELETE FROM tt_open_request WHERE id=%s', (request_id,))
                with self.assertRaises(frappe.PermissionError):
                    fixtures.login('c1')
                    service_policy.immediate_services()
                fixtures.login('admin')
                frappe.local.tele_tena_service_policy_action = False
                doc = frappe.get_doc('Tele Tena Service', service)
                doc.immediate_care_enabled = 0
                with self.assertRaises(frappe.PermissionError):
                    doc.save()
                disabled = service_policy.set_immediate_policy(
                    service, False, reason, 'policy-disable-' + secrets.token_hex(12))
                self.assertTrue(disabled['changed'])
                doc = frappe.get_doc('Tele Tena Service', service)
                doc.immediate_care_enabled = 1
                with self.assertRaises(frappe.PermissionError):
                    doc.save()
        finally:
            fixtures.login('admin')
            if 'request_id' in locals():
                frappe.db.sql('DELETE FROM tt_open_request WHERE id=%s', (request_id,))
            frappe.db.sql('DELETE FROM tt_immediate_service_policy_event WHERE service=%s', (service,))
            frappe.db.sql('DELETE FROM `tabTele Tena Service` WHERE name=%s', (service,))

    def test_two_patients_cannot_claim_one_offer_slot_concurrently(self):
        offering = fixtures.Integration.offers['c1']
        service = fixtures.PREFIX
        # Avoid colliding with an intentionally retained appointment from a
        # prior interrupted run of this suite on the same disposable site.
        day = day_offset(28 + secrets.randbelow(20))
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
        # Another clinician may legitimately have a different appointment at
        # the same instant; the conflict invariant is global across offerings
        # owned by this clinician, not global across the entire service.
        booked_rows = journey.rows("SELECT start,end,state FROM tt_appointment WHERE clinician=%s AND start=%s AND state='Booked'",
                                   (fixtures.USERS['c1'], slot['start']))
        self.assertEqual(len(booked_rows), 1,
                         msg='Expected one globally reserved start; found ' + repr([(str(r.start), str(r.end), r.state) for r in booked_rows]))
        self.assertEqual(journey.one("SELECT COUNT(*) n FROM tt_request_offer WHERE id IN %s AND state='Accepted'",
                                     (tuple(offers),)).n, 1)

    def test_booking_link_is_opaque_owner_scoped_and_revocable(self):
        offering = fixtures.Integration.offers['c1']
        day, _, _ = self.make_schedule(day_offset(55), offering=offering)
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
        self.fund_patient('p1', 100000)
        sharing = {'name': False, 'history': False}
        request_text = 'Synthetic clinician-share acquisition test.'
        disclosure = journey.preview(request_text, sharing)['disclosure']
        offering_row = journey.one('SELECT price,minutes FROM tt_offering WHERE id=%s', (offering,))
        slot = self.slots(offering, day, who='p1')[0]
        direct_payload = dict(offering=offering, start=slot['start'], request_text=request_text,
            sharing=sharing, expected_price=offering_row.price, expected_minutes=offering_row.minutes,
            expected_disclosure=disclosure, booked_timezone='Africa/Addis_Ababa')
        with self.assertRaises(frappe.ValidationError):
            journey.book(**direct_payload, retry_key='invalid-share-' + secrets.token_hex(5),
                         booking_link_token='0' * 64)
        share_retry = 'valid-share-' + secrets.token_hex(5)
        linked = journey.book(**direct_payload, retry_key=share_retry, booking_link_token=token)
        self.assertEqual(journey.one('SELECT acquisition_source FROM tt_appointment WHERE id=%s',
                                     (linked['id'],)).acquisition_source, 'clinician_share')
        self.assertEqual(journey.book(**direct_payload, retry_key=share_retry,
                                      booking_link_token=token)['id'], linked['id'])
        with self.assertRaises(frappe.ValidationError):
            journey.book(**direct_payload, retry_key=share_retry, booking_link_token='0' * 64)
        self.assertFalse(frappe.db.sql("SHOW COLUMNS FROM tt_profile LIKE 'acquisition_source'"))
        next_slot = self.slots(offering, day, who='p1')[0]
        direct = self.book_slot(offering, next_slot, 'direct-acquisition-' + secrets.token_hex(5))
        self.assertEqual(journey.one('SELECT acquisition_source FROM tt_appointment WHERE id=%s',
                                     (direct['id'],)).acquisition_source, 'direct_booking')
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

    def test_appointment_acquisition_migration_is_repeatable_and_preserves_history(self):
        before = journey.rows('SELECT id,state,patient,clinician,price FROM tt_appointment ORDER BY id')
        v1_26_appointment_acquisition_source.execute()
        after_first = journey.rows('''SELECT id,state,patient,clinician,price,acquisition_source
            FROM tt_appointment ORDER BY id''')
        v1_26_appointment_acquisition_source.execute()
        after_second = journey.rows('''SELECT id,state,patient,clinician,price,acquisition_source
            FROM tt_appointment ORDER BY id''')
        self.assertEqual([(r.id, r.state, r.patient, r.clinician, r.price) for r in after_first],
                         [(r.id, r.state, r.patient, r.clinician, r.price) for r in before])
        self.assertEqual(after_first, after_second)
        # Migrated history is explicitly unknown; no source is inferred.
        self.assertTrue(all(r.acquisition_source in ('unknown', 'direct_booking', 'clinician_share', 'open_request')
                            for r in after_first))

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

    def test_prefunded_extension_requires_consent_and_settles_once(self):
        from tele_tena import accounting
        offering = fixtures.Integration.offers['c1']
        day, _, _ = self.make_schedule(mode='automatic', offering=offering)
        slot = self.slots(offering, day)[0]
        self.fund_patient(kind='p1', amount=10000)
        booked = self.book_slot(offering, slot, 'extension-flow-' + secrets.token_hex(6))
        appointment = booked['id']
        patient = fixtures.USERS['p1']
        clinician = fixtures.USERS['c1']
        wallet_before = journey.one('SELECT available,reserved FROM tt_wallet WHERE patient=%s', (patient,))
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        frappe.db.sql('''INSERT INTO tt_consultation
            (appointment,id,room_name,patient_identity,clinician_identity,state,created)
            VALUES (%s,%s,%s,%s,%s,'Open',%s)''',
            (appointment, str(uuid.uuid4()), uuid.uuid4().hex, uuid.uuid4().hex, uuid.uuid4().hex, now))
        fixtures.login('c1')
        proposal = extensions.propose_extension(appointment, 'extension-retry-' + secrets.token_hex(6))
        self.assertEqual(proposal['duration_minutes'], 15)
        self.assertEqual(proposal['amount_minor'], 300)
        retry_key = journey.one('SELECT retry_key FROM tt_consultation_extension WHERE id=%s',
                                (proposal['id'],)).retry_key
        idem = extensions.propose_extension(appointment, retry_key)
        self.assertTrue(idem['idempotent'])
        duplicate = extensions.propose_extension(appointment, 'lost-response-retry-' + secrets.token_hex(6))
        self.assertTrue(duplicate['idempotent'])
        self.assertEqual(duplicate['id'], proposal['id'])
        fixtures.login('p1')
        accepted = extensions.respond_extension(appointment, proposal['id'], 'accept')
        self.assertEqual(accepted['state'], 'Accepted')
        self.assertTrue(extensions.respond_extension(appointment, proposal['id'], 'accept')['idempotent'])
        wallet_reserved = journey.one('SELECT available,reserved FROM tt_wallet WHERE patient=%s', (patient,))
        self.assertEqual(int(wallet_reserved.available), int(wallet_before.available) - 300)
        self.assertEqual(int(wallet_reserved.reserved), int(wallet_before.reserved) + 300)
        self.assertEqual(journey.one('SELECT COUNT(*) n FROM tt_journal WHERE event_ref=%s',
                                     ('extension-reserve:' + proposal['id'],)).n, 1)
        with self.assertRaises(frappe.ValidationError):
            presentation.cancel_appointment(appointment, 'Synthetic attempt during open call')
        self.assertEqual(frappe.local.response.get('tele_tena_error'), 'cancellation_call_active')
        self.assertEqual(int(journey.one('SELECT reserved FROM tt_wallet WHERE patient=%s', (patient,)).reserved),
                         int(wallet_reserved.reserved))
        # The clinician explicitly starts the accepted block; elapsed call time
        # alone is not used as consent or billing evidence.
        pending_before = accounting.balance('clinician', clinician, 'pending')
        frappe.set_user('Administrator')
        frappe.db.sql('UPDATE tt_consultation_extension SET start_after=UTC_TIMESTAMP(6)-INTERVAL 1 SECOND WHERE id=%s',
                      (proposal['id'],))
        fixtures.login('c1')
        self.assertEqual(extensions.start_extension(appointment, proposal['id'])['state'], 'Started')
        frappe.db.sql("UPDATE tt_consultation SET state='Ended',ended=UTC_TIMESTAMP(6) WHERE appointment=%s", (appointment,))
        presentation.save_note_draft(appointment, 'Synthetic private note', 'Synthetic patient summary')
        with patch.dict(frappe.conf, {'tele_tena_demo_platform_fee_bps': 0,
                                     'tele_tena_demo_dispute_window_minutes': 30}):
            presentation.finalize_consultation(appointment, 1)
            presentation.finalize_consultation(appointment, 1)
        earning = journey.one('SELECT gross_minor,net_minor,policy_snapshot FROM tt_earning WHERE appointment=%s',
                              (appointment,))
        self.assertEqual(int(earning.gross_minor), 900)
        self.assertEqual(int(earning.net_minor), 900)
        self.assertEqual(len(json.loads(earning.policy_snapshot)['extension_blocks']), 1)
        self.assertEqual(journey.one('SELECT state FROM tt_consultation_extension WHERE id=%s',
                                     (proposal['id'],)).state, 'Settled')
        self.assertEqual(accounting.balance('clinician', clinician, 'pending'), pending_before + 900)

    def test_ending_releases_unstarted_extension_once_and_expiry_is_scheduled(self):
        offering = fixtures.Integration.offers['c1']
        day, _, _ = self.make_schedule(mode='automatic', offering=offering)
        slot = self.slots(offering, day)[0]
        self.fund_patient(kind='p2', amount=10000)
        booked = self.book_slot(offering, slot, 'extension-release-' + secrets.token_hex(6), who='p2')
        patient = fixtures.USERS['p2']
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        frappe.db.sql('''INSERT INTO tt_consultation
            (appointment,id,room_name,patient_identity,clinician_identity,state,created)
            VALUES (%s,%s,%s,%s,%s,'Open',%s)''',
            (booked['id'], str(uuid.uuid4()), uuid.uuid4().hex, uuid.uuid4().hex, uuid.uuid4().hex, now))
        fixtures.login('c1')
        proposal = extensions.propose_extension(booked['id'], 'extension-release-key-' + secrets.token_hex(6))
        fixtures.login('p2')
        extensions.respond_extension(booked['id'], proposal['id'], 'accept')
        reserved_before_end = int(journey.one('SELECT reserved FROM tt_wallet WHERE patient=%s', (patient,)).reserved)
        fixtures.login('c1')
        extensions.close_unstarted_extensions(booked['id'], fixtures.USERS['c1'])
        extensions.close_unstarted_extensions(booked['id'], fixtures.USERS['c1'])
        wallet = journey.one('SELECT reserved FROM tt_wallet WHERE patient=%s', (patient,))
        self.assertEqual(int(wallet.reserved), reserved_before_end - proposal['amount_minor'])
        self.assertEqual(journey.one('SELECT state FROM tt_consultation_extension WHERE id=%s',
                                     (proposal['id'],)).state, 'Released')
        # Expiry is durable via the scheduled worker; a second run is a no-op.
        expiry_proposal = extensions.propose_extension(booked['id'], 'extension-expire-key-' + secrets.token_hex(6))
        frappe.db.sql('UPDATE tt_consultation_extension SET expires_at=UTC_TIMESTAMP(6)-INTERVAL 1 SECOND WHERE id=%s',
                      (expiry_proposal['id'],))
        extensions.expire_extensions()
        extensions.expire_extensions()
        self.assertEqual(journey.one('SELECT state FROM tt_consultation_extension WHERE id=%s',
                                     (expiry_proposal['id'],)).state, 'Expired')
        self.assertEqual(journey.one('''SELECT COUNT(*) n FROM tt_appointment_event
            WHERE appointment=%s AND event_type='ExtensionExpired' ''', (booked['id'],)).n, 1)

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
            self.assertEqual(int(journey.one('''SELECT COUNT(*) n FROM tt_ledger
                WHERE patient=%s AND reference=%s AND kind='Consumption' ''',
                (fixtures.USERS['p2'], 'completion:' + booked['id'])).n), 1)
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
            earning = journey.one('SELECT id,state FROM tt_earning WHERE appointment=%s', (booked['id'],))
            self.assertEqual(earning.state, 'Disputed')
            fixtures.login('admin')
            self.assertEqual(accounting.resolve_earning_dispute(booked['id'], 'refund', 'Synthetic resolution')['resolution'], 'refund')
            self.assertEqual(accounting.resolve_earning_dispute(booked['id'], 'refund', 'Synthetic resolution')['idempotent'], True)
            self.assertEqual(int(journey.one('''SELECT COUNT(*) n FROM tt_ledger
                WHERE patient=%s AND reference=%s AND kind='Refund' ''',
                (fixtures.USERS['p2'], 'earning-refund:' + earning.id)).n), 1)
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
        self.assertFalse(patient_detail['can_submit_feedback'])
        with self.assertRaises(frappe.ValidationError):
            trust.submit_session_feedback(appointment, 5)
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
        self.assertTrue(shared['can_submit_feedback'])
        previous = journey.previous_clinicians()
        self.assertEqual(len(previous), 1)
        self.assertEqual(previous[0].display_name, 'Synthetic Test')
        self.assertEqual(previous[0].completed_sessions, 1)
        self.assertNotEqual(previous[0].clinician_id, fixtures.USERS['c1'])
        self.assertNotIn(fixtures.USERS['c1'], json.dumps(previous, default=str))
        fixtures.login('p2')
        self.assertEqual(journey.previous_clinicians(), [])
        fixtures.login('c2')
        with self.assertRaises(frappe.PermissionError):
            journey.previous_clinicians()
        fixtures.login('p1')
        frappe.db.commit()
        feedback_barrier = threading.Barrier(2)
        def submit_feedback():
            fixtures.connect()
            try:
                fixtures.login('p1')
                feedback_barrier.wait(timeout=10)
                result = trust.submit_session_feedback(appointment, 5)
                frappe.db.commit()
                return result
            finally:
                frappe.destroy()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            feedback_results = list(pool.map(lambda _index: submit_feedback(), range(2)))
        frappe.db.rollback()
        self.assertEqual(sum(not result['idempotent'] for result in feedback_results), 1)
        self.assertTrue(all(result['submitted'] for result in feedback_results))
        self.assertTrue(trust.submit_session_feedback(appointment, 5)['idempotent'])
        self.assertEqual(journey.one("SELECT COUNT(*) n FROM tt_appointment_event WHERE appointment=%s AND event_type='SessionFeedbackSubmitted'", (appointment,)).n, 1)
        with self.assertRaises(frappe.ValidationError):
            trust.submit_session_feedback(appointment, 4)
        with self.assertRaises(frappe.ValidationError):
            trust.submit_session_feedback(appointment, 6)
        fixtures.login('p2')
        with self.assertRaises(frappe.PermissionError):
            trust.submit_session_feedback(appointment, 5)
        fixtures.login('c1')
        with self.assertRaises(frappe.PermissionError):
            trust.submit_session_feedback(appointment, 5)
        fixtures.login('p1')
        clinician_id = journey.one('SELECT public_id FROM tt_profile WHERE user=%s',
                                   (fixtures.USERS['c1'],)).public_id
        public_profile = open_requests.clinician_profile(clinician_id)
        metric = public_profile['trust_indicators']['session_experience']
        self.assertEqual(metric['sample_count'], 1)
        self.assertIsNone(metric['average'])
        self.assertEqual(metric['status'], 'more_feedback_needed')
        response_metric = public_profile['trust_indicators']['responsiveness']
        self.assertEqual(response_metric['sample_count'], 0)
        self.assertIsNone(response_metric['rate_percent'])
        reliability_metric = public_profile['trust_indicators']['reliability']
        self.assertEqual(reliability_metric['sample_count'], 1)
        self.assertIsNone(reliability_metric['rate_percent'])
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

    def test_07_legacy_wallet_mismatch_is_held_until_audited_decision(self):
        from tele_tena import accounting
        from tele_tena.patches.v1_13_financial_reconciliation_audit import audit_wallet
        savepoint = 'tt_fin_audit_' + uuid.uuid4().hex[:16]
        frappe.db.sql('SAVEPOINT ' + savepoint)
        patient = fixtures.USERS['p1']
        try:
            wallet = journey.one('SELECT available,reserved FROM tt_wallet WHERE patient=%s', (patient,))
            journey.simulation_log(patient, 'Deposit', 1000, 'deposit:mismatch-test-' + uuid.uuid4().hex)
            result = audit_wallet(patient)
            self.assertFalse(result['matches'])
            self.assertEqual(result['legacy']['available'], int(wallet.available) + 1000)
            self.assertEqual(result['wallet']['available'], int(wallet.available))
            self.assertEqual(accounting.balance('patient', patient, 'available'), int(wallet.available))
            fixtures.login('p1')
            with self.assertRaises(frappe.ValidationError):
                journey.simulated_deposit(250, 'held-wallet-test-' + uuid.uuid4().hex)
            after = journey.one('SELECT available,reserved FROM tt_wallet WHERE patient=%s', (patient,))
            self.assertEqual((after.available, after.reserved), (wallet.available, wallet.reserved))
            with self.assertRaises(frappe.PermissionError):
                accounting.financial_reconciliation_queue()
            with self.assertRaises(frappe.PermissionError):
                accounting.accept_reconciliation_case('unknown-case', 'Unauthorized test')
            fixtures.login('admin')
            queue = accounting.financial_reconciliation_queue()
            audit_id = journey.one('SELECT id FROM tt_financial_reconciliation WHERE patient=%s', (patient,)).id
            case = next(row for row in queue if row.status == 'ReviewRequired' and
                        row.case_ref == accounting._reconciliation_case_ref(audit_id))
            self.assertNotIn('id', case.keys())
            self.assertNotIn('@', json.dumps(dict(case), default=str))
            accepted = accounting.accept_reconciliation_case(case.case_ref, 'Synthetic review accepted current opening snapshot')
            self.assertTrue(accepted['historical_difference_preserved'])
            retried = accounting.accept_reconciliation_case(case.case_ref, 'Synthetic review accepted current opening snapshot')
            self.assertTrue(retried['idempotent'])
            accounting.check_wallet_projection(patient, after)
            audit = journey.one('''SELECT status,decision,reason FROM tt_financial_reconciliation
                WHERE patient=%s''', (patient,))
            self.assertEqual(audit.status, 'SnapshotAccepted')
            self.assertIn('legacy_diff', audit.reason)

            boundary_owner = 'boundary-' + uuid.uuid4().hex[:16] + '@example.invalid'
            frappe.db.sql('INSERT INTO tt_wallet (patient,available,reserved) VALUES (%s,100,0)',
                          (boundary_owner,))
            account = accounting.account_id('patient', boundary_owner, 'available')
            opening_ref = 'opening:' + boundary_owner
            accounting.post(opening_ref, 'Opening', opening_ref,
                            [(account, 0, 100), ('demo:opening-control', 100, 0)],
                            {'source': 'synthetic exact-boundary test'})
            journey.simulation_log(boundary_owner, 'Deposit', 100, 'deposit:boundary-test-' + uuid.uuid4().hex)
            frappe.db.sql('''UPDATE tt_ledger SET created=(SELECT created FROM tt_journal WHERE event_ref=%s)
                WHERE patient=%s ORDER BY id DESC LIMIT 1''', (opening_ref, boundary_owner))
            boundary_result = audit_wallet(boundary_owner)
            self.assertFalse(boundary_result['matches'])
            boundary_case = journey.one('''SELECT status,boundary_event_count FROM tt_financial_reconciliation
                WHERE patient=%s''', (boundary_owner,))
            self.assertEqual(boundary_case.status, 'ReviewRequired')
            self.assertEqual(int(boundary_case.boundary_event_count), 1)
        finally:
            frappe.db.sql('ROLLBACK TO SAVEPOINT ' + savepoint)
            frappe.db.sql('RELEASE SAVEPOINT ' + savepoint)

    def test_08_legacy_completion_activity_backfill_requires_matching_journal(self):
        from tele_tena import accounting
        from tele_tena.patches.v1_13_financial_reconciliation_audit import audit_wallet
        savepoint = 'tt_fin_completion_' + uuid.uuid4().hex[:16]
        frappe.db.sql('SAVEPOINT ' + savepoint)
        patient = 'completion-audit-' + uuid.uuid4().hex[:12] + '@example.invalid'
        appointment = str(uuid.uuid4())
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        try:
            frappe.db.sql('INSERT INTO tt_wallet (patient,available,reserved) VALUES (%s,0,0)', (patient,))
            reserved = accounting.account_id('patient', patient, 'reserved')
            accounting.post('opening:' + patient, 'Opening', 'opening:' + patient,
                [(reserved, 0, 500), ('demo:opening-control', 500, 0)], {'synthetic': True})
            journey.simulation_log(patient, 'Deposit', 500, 'deposit:' + appointment)
            journey.simulation_log(patient, 'Reservation', 500, 'booking:' + appointment)
            # Model the historical state transition: journal and wallet are
            # authoritative, but the old code omitted a completion log event.
            accounting.post('completion:' + appointment, 'ConsultationFinalized',
                'completion:' + appointment,
                [(reserved, 500, 0), (accounting.account_id('clinician', fixtures.USERS['c1'], 'pending'), 0, 500)],
                {'synthetic': True})
            frappe.db.sql('UPDATE tt_wallet SET reserved=0 WHERE patient=%s', (patient,))
            earning_id = str(uuid.uuid4())
            frappe.db.sql('''INSERT INTO tt_earning
                (id,appointment,patient,clinician,gross_minor,fee_minor,net_minor,policy_snapshot,
                 state,completed_at,release_at,created,modified)
                VALUES (%s,%s,%s,%s,500,0,500,'{}','Pending',%s,%s,%s,%s)''',
                (earning_id, appointment, patient, fixtures.USERS['c1'], now,
                 now + timedelta(hours=1), now, now))
            self.assertFalse(audit_wallet(patient)['matches'])
            self.assertEqual(v1_24_legacy_completion_activity.backfill_completion_activity(patient), 1)
            self.assertEqual(v1_24_legacy_completion_activity.backfill_completion_activity(patient), 0)
            activity = journey.one('''SELECT patient,kind,amount,reference,created FROM tt_ledger
                WHERE reference=%s''', ('completion:' + appointment,))
            self.assertEqual((activity.patient, activity.kind, int(activity.amount)),
                             (patient, 'Consumption', 500))
            journal = journey.one('SELECT created FROM tt_journal WHERE event_ref=%s',
                                  ('completion:' + appointment,))
            self.assertEqual(activity.created, journal.created)
            result = audit_wallet(patient)
            self.assertTrue(result['matches'], result)
            wallet = journey.one('SELECT available,reserved FROM tt_wallet WHERE patient=%s', (patient,))
            self.assertEqual((int(wallet.available), int(wallet.reserved)), (0, 0))
            refund_ref = 'earning-refund:' + earning_id
            accounting.post(refund_ref, 'EarningRefunded', refund_ref,
                [(accounting.account_id('clinician', fixtures.USERS['c1'], 'pending'), 500, 0),
                 (accounting.account_id('patient', patient, 'available'), 0, 500)], {'synthetic': True})
            frappe.db.sql("UPDATE tt_earning SET state='Refunded' WHERE id=%s", (earning_id,))
            frappe.db.sql('UPDATE tt_wallet SET available=available+500 WHERE patient=%s', (patient,))
            self.assertEqual(v1_25_legacy_refund_activity.backfill_refund_activity(patient), 1)
            self.assertEqual(v1_25_legacy_refund_activity.backfill_refund_activity(patient), 0)
            refund = journey.one('''SELECT patient,kind,amount,reference,created FROM tt_ledger
                WHERE reference=%s''', (refund_ref,))
            self.assertEqual((refund.patient, refund.kind, int(refund.amount)), (patient, 'Refund', 500))
            refund_journal = journey.one('SELECT created FROM tt_journal WHERE event_ref=%s', (refund_ref,))
            self.assertEqual(refund.created, refund_journal.created)
            self.assertTrue(audit_wallet(patient)['matches'])
            wallet = journey.one('SELECT available,reserved FROM tt_wallet WHERE patient=%s', (patient,))
            self.assertEqual((int(wallet.available), int(wallet.reserved)), (500, 0))
            case = journey.one('''SELECT status,legacy_available,legacy_reserved,wallet_available,
                wallet_reserved,reason FROM tt_financial_reconciliation WHERE patient=%s''', (patient,))
            self.assertEqual(case.status, 'ReviewRequired')
            self.assertEqual((int(case.legacy_available), int(case.legacy_reserved),
                              int(case.wallet_available), int(case.wallet_reserved)), (500, 0, 500, 0))
            self.assertGreaterEqual(len(json.loads(case.reason)['audit_history']), 1)
            fixtures.login('admin')
            accounting.accept_wallet_snapshot(patient, 'Synthetic reconciliation after evidence-backed activity backfill')
            accounting.check_wallet_projection(patient, wallet)
        finally:
            frappe.db.sql('ROLLBACK TO SAVEPOINT ' + savepoint)
            frappe.db.sql('RELEASE SAVEPOINT ' + savepoint)

    def test_service_catalog_edits_are_typed_draft_only_and_reviewer_scoped(self):
        key = 'synthetic-catalog-' + secrets.token_hex(5)
        attribute_names = []
        fixtures.login('admin')
        payload = {
            'service_key': key, 'service_label': 'Synthetic counseling definition',
            'category': 'counseling', 'description': 'Synthetic test only.',
            'participant_structure': 'individual', 'supported_formats': 'audio\nvideo',
            'booking_rules': 'scheduled',
            'required_workflows': 'individual-consultation\nprivate-notes',
            'population_restriction': 'Adults only', 'definition_version': 'test-1',
            'catalog_source': 'Synthetic source for regression testing.',
            'min_duration_minutes': '20', 'max_duration_minutes': '60',
        }
        try:
            created = service_catalog.save_draft_definition(payload)
            self.assertEqual(created, {'id': key, 'status': 'Draft', 'bookable': False,
                                       'definition_version': 'test-1'})
            self.assertEqual(frappe.db.get_value('Tele Tena Service', key,
                                                 ['active', 'catalog_status', 'vetting_required']),
                             (0, 'Draft', 1))
            changed = dict(payload, service_label='Synthetic edited definition')
            service_catalog.save_draft_definition(changed)
            self.assertEqual(frappe.db.get_value('Tele Tena Service', key, 'service_label'),
                             'Synthetic edited definition')
            with self.assertRaises(frappe.ValidationError):
                service_catalog.save_draft_definition(dict(payload, min_duration_minutes='61',
                                                            max_duration_minutes='20'))

            attribute = {'field_key':'synthetic_private_need','label_en':'Private need',
                         'data_type':'Text','visibility':'Patient private','sensitivity':'Clinical',
                         'matching_field':True,'filterable':False,'active':True}
            with self.assertRaises(frappe.ValidationError):
                service_catalog.save_attribute_definition(key, attribute)
            attribute.update(matching_field=False, visibility='Public metadata', sensitivity='Ordinary')
            result = service_catalog.save_attribute_definition(key, attribute)
            self.assertEqual(result['definition_version'], 'test-1')
            attribute_names = frappe.db.sql('''SELECT name FROM `tabTele Tena Service Attribute Definition`
                WHERE service=%s''', (key,), pluck=True)
            self.assertEqual(len(attribute_names), 1)

            service_catalog.submit_for_clinical_review(key)
            self.assertEqual(frappe.db.get_value('Tele Tena Service', key,
                                                 ['clinical_review_status', 'active']),
                             ('In review', 0))
            with self.assertRaises(frappe.ValidationError):
                service_catalog.save_draft_definition(changed)
            with self.assertRaises(frappe.ValidationError):
                service_catalog.save_attribute_definition(key, attribute)

            fixtures.login('p1')
            with self.assertRaises(frappe.PermissionError):
                service_catalog.definitions()
            with self.assertRaises(frappe.PermissionError):
                service_catalog.save_draft_definition(payload)
        finally:
            fixtures.login('admin')
            if attribute_names:
                frappe.db.sql('DELETE FROM `tabTele Tena Service Attribute Definition` WHERE name IN %s',
                              (tuple(attribute_names),))
            frappe.db.sql('DELETE FROM `tabTele Tena Service` WHERE name=%s', (key,))


if __name__ == '__main__':
    unittest.main(verbosity=2)
