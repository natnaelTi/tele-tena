"""Real MariaDB auth regression; all external delivery mocked, synthetic contacts."""
import concurrent.futures
import threading
import importlib.util
import json
from pathlib import Path
import secrets
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('baseline', Path(__file__).with_name('integration.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
import frappe
from tele_tena.api import contact_auth as auth
from tele_tena.api import phone_auth


def acknowledged(answers):
    from tele_tena.api.policies import TERMS, PRIVACY
    return {**answers, 'terms_accepted': True, 'privacy_acknowledged': True,
            'terms_version': TERMS, 'privacy_version': PRIVACY}


class ContactAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base.connect()
        cls.users = []
        cls.contacts = []
        cls.challenges = []
        cls.services = []

    @classmethod
    def tearDownClass(cls):
        frappe.db.rollback()
        frappe.set_user('Administrator')
        for service in cls.services:
            frappe.db.sql('DELETE FROM `tabTele Tena Service` WHERE name=%s', (service,))
        for user in cls.users:
            for table, field in [('contact_identity', 'user'), ('onboarding', 'user'), ('profile', 'user'), ('application', 'user'), ('wallet', 'patient')]:
                frappe.db.sql(f'DELETE FROM tt_{table} WHERE {field}=%s', (user,))
            frappe.db.sql('DELETE FROM tt_resume_evidence WHERE clinician=%s', (user,))
            if frappe.db.exists('User', user):
                frappe.delete_doc('User', user)
        for challenge in cls.challenges:
            frappe.db.sql('DELETE FROM tt_otp_challenge WHERE id=%s', (challenge,))
        for contact in cls.contacts:
            digest = phone_auth._keyed('contact:email', contact)
            for kind in ('contact-window', 'contact-day', 'contact-verify'):
                frappe.db.sql('DELETE FROM tt_otp_rate_limit WHERE bucket_key=%s', (phone_auth._keyed('limit:' + kind, digest),))
        frappe.db.commit()
        frappe.destroy()

    def setUp(self):
        frappe.set_user('Guest')
        self.contact = 'tt-contact-' + secrets.token_hex(8) + '@example.invalid'
        self.contacts.append(self.contact)
        # The site intentionally has no live email provider. Authentication
        # tests exercise the mocked delivery path, so satisfy the separate
        # configuration gate without creating a credential file or sending mail.
        self.email_configuration = patch(
            'tele_tena.email_delivery.configuration',
            return_value={'host': 'mock.invalid', 'sender': 'noreply@example.invalid',
                          'username': 'mock', 'password': 'mock', 'port': 587},
        )
        self.email_configuration.start()
        self.addCleanup(self.email_configuration.stop)
        # These OTP state-machine tests exercise the enabled-registration
        # configuration. The retained review site remains invitation-only;
        # site-policy enforcement is covered by its separate disabled-mode
        # integration checks.
        self.registration_policy = patch(
            'tele_tena.review.registration_enabled', return_value=True,
        )
        self.registration_policy.start()
        self.addCleanup(self.registration_policy.stop)
        self.peer = patch.object(phone_auth, '_peer_ip', return_value='synthetic-' + secrets.token_hex(8))
        self.peer.start()
        self.addCleanup(self.peer.stop)

    def challenge(self):
        with patch('tele_tena.email_delivery.send_code') as delivery:
            result = auth.request_code('email', self.contact, secrets.token_hex(20))
            code = delivery.call_args.args[1]
        self.challenges.append(result['challenge_id'])
        return result, code

    def verify(self, result, code):
        with patch.object(phone_auth, '_establish_login') as login:
            auth.verify_code('email', self.contact, result['challenge_id'], code)
            user = login.call_args.args[0]
            if user not in self.users:
                self.users.append(user)
            return user

    def test_contact_is_not_completed_registration_and_resume_is_owned(self):
        result, code = self.challenge()
        user = self.verify(result, code)
        self.assertFalse(frappe.db.sql('SELECT user FROM tt_profile WHERE user=%s', (user,)))
        self.assertNotIn('Tele Tena Patient', frappe.get_roles(user))
        self.assertNotIn('Tele Tena Clinician', frappe.get_roles(user))
        frappe.set_user(user)
        auth.save_onboarding('patient', 1, {'name': 'Synthetic alias'})
        self.assertEqual(auth.onboarding()['answers']['name'], 'Synthetic alias')
        frappe.db.commit()
        frappe.set_user('Guest')
        with self.assertRaises(frappe.PermissionError):
            auth.onboarding()
        frappe.set_user(user)
        auth.save_onboarding('patient', 3, acknowledged({'name': 'Synthetic alias', 'adult': True, 'consent': True, 'language': 'am'}), 1)
        from tele_tena.api.presentation import preferences
        self.assertEqual(preferences()['locale'],'am')
        self.assertIn('Tele Tena Patient', frappe.get_roles(user))
        self.assertNotIn('Tele Tena Clinician', frappe.get_roles(user))
        frappe.db.commit()

    def test_optional_patient_background_preserves_owned_draft_and_private_defaults(self):
        result, code = self.challenge()
        user = self.verify(result, code)
        frappe.set_user(user)
        answers = {'name': 'Fictional alias', 'adult': True, 'consent': True,
                   'history': 'Fictional optional care background', 'language': 'en'}
        auth.save_onboarding('patient', 4, answers)
        draft = auth.onboarding()
        self.assertEqual(draft['step'], 4)
        self.assertEqual(draft['answers']['history'], answers['history'])
        self.assertFalse(draft['answers']['share_history'])
        with self.assertRaises(frappe.ValidationError):
            auth.save_onboarding('clinician', 4, answers)
        with self.assertRaises(frappe.ValidationError):
            auth.save_onboarding('patient', 4, {**answers, 'history': 'x' * 4001})
        self.assertEqual(auth.onboarding()['answers']['history'], answers['history'])
        frappe.set_user('Guest')
        with self.assertRaises(frappe.PermissionError):
            auth.onboarding()
        frappe.set_user(user)
        auth.save_onboarding('patient', 3, acknowledged(answers), 1)
        profile = frappe.db.sql('SELECT history,share_history FROM tt_profile WHERE user=%s', (user,), as_dict=True)[0]
        self.assertEqual(profile.history, answers['history'])
        self.assertFalse(profile.share_history)
        with self.assertRaises(frappe.ValidationError):
            auth.save_onboarding('patient', 3, acknowledged(answers), 1)
        self.assertEqual(frappe.db.sql('SELECT COUNT(*) FROM tt_profile WHERE user=%s', (user,))[0][0], 1)
        frappe.db.commit()

    def test_request_response_does_not_reveal_contact_lookup_or_delivery(self):
        first_contact = self.contact
        second_contact = 'another-' + secrets.token_hex(8) + '@example.invalid'
        self.contacts.append(second_contact)
        with patch('tele_tena.email_delivery.send_code', side_effect=[None, TimeoutError]):
            first = auth.request_code('email', first_contact, secrets.token_hex(20))
            second = auth.request_code('email', second_contact, secrets.token_hex(20))
        self.challenges.extend([first['challenge_id'], second['challenge_id']])
        self.assertEqual(set(first) - {'challenge_id', 'message'}, set(second) - {'challenge_id', 'message'})
        self.assertEqual(first['delivery_state'], 'accepted')
        self.assertEqual(second['delivery_state'], 'uncertain')
        self.assertNotIn('account', first['message'].lower())
        self.assertNotIn('account', second['message'].lower())
        self.assertEqual(first['resend_after'], second['resend_after'])

    def test_single_use_attempts_and_role_injection(self):
        result, code = self.challenge()
        with self.assertRaises(frappe.ValidationError):
            auth.verify_code('email', self.contact, result['challenge_id'], 'xxxxxx')
        self.assertEqual(frappe.db.sql('SELECT attempts FROM tt_otp_challenge WHERE id=%s', (result['challenge_id'],))[0][0], 1)
        user = self.verify(result, code)
        with self.assertRaises(frappe.ValidationError):
            self.verify(result, code)
        frappe.set_user(user)
        with self.assertRaises(frappe.ValidationError):
            auth.save_onboarding('clinician', 2, {'roles': ['System Manager']})
        service = 'otp-test-' + secrets.token_hex(5)
        frappe.set_user('Administrator')
        frappe.get_doc(dict(doctype='Tele Tena Service', service_key=service,
                            service_label='Synthetic application service', active=1)).insert()
        self.services.append(service)
        frappe.db.commit()
        frappe.set_user(user)
        answers = {'name': 'Synthetic applicant', 'statement': 'Synthetic credentials and scope',
                   'adult': True, 'consent': True, 'requested_services': [service]}
        structured = {'professional_category': 'Counselor', 'qualification': 'Fictional qualification',
                      'issuing_institution': 'Fictional institution', 'registration_number': 'PRIVATE-CREDENTIAL',
                      'experience_years': 8, 'credential_expiry': '2027-06-30'}
        for values in ({'professional': {'roles': ['System Manager']}},
                       {'professional': {'experience_years': -1}},
                       {'professional': {'credential_expiry': 'not-a-date'}},
                       {'care_languages': ['en', 'en']}, {'care_languages': ['unsupported']}):
            with self.assertRaises(frappe.ValidationError):
                auth.save_onboarding('clinician', 0, {**answers, **values})
        with self.assertRaises(frappe.ValidationError):
            auth.save_onboarding('patient', 0, {**answers, 'professional': structured})
        answers.update(professional=structured, care_languages=['en', 'am'], introduction='Public fictional introduction')
        auth.save_onboarding('clinician', 2, answers)
        auth.save_onboarding('clinician', 5, answers)
        self.assertEqual(auth.onboarding()['step'], 5)
        self.assertEqual(auth.onboarding()['answers']['professional'], structured)
        self.assertEqual(auth.onboarding()['answers']['requested_services'], [service])
        with self.assertRaises(frappe.ValidationError):
            auth.save_onboarding('patient', 5, answers)
        self.assertEqual(auth.onboarding()['kind'], 'clinician')
        from tele_tena.api import presentation
        import base64
        pdf = b'%PDF-1.7\n1 0 obj<</Type/Catalog>>endobj\n%%EOF\n'
        presentation.upload_resume('synthetic.pdf', base64.b64encode(pdf).decode())
        with self.assertRaises(frappe.ValidationError):
            auth.save_onboarding('clinician', 3, acknowledged({**answers, 'professional': {'professional_category': 'Counselor'}}), 1)
        self.assertFalse(frappe.db.sql('SELECT user FROM tt_profile WHERE user=%s', (user,)))
        auth.save_onboarding('clinician', 3, acknowledged({**answers, 'statement': ''}), 1)
        self.assertIn('Tele Tena Applicant', frappe.get_roles(user))
        self.assertNotIn('Tele Tena Clinician', frappe.get_roles(user))
        self.assertEqual(frappe.db.sql('SELECT status FROM tt_application WHERE user=%s', (user,))[0][0], 'Pending')
        from tele_tena.api import journey
        self.assertEqual(journey.applications()[0].application_profile, structured)
        profile = frappe.db.sql('SELECT languages,introduction,history FROM tt_profile WHERE user=%s', (user,), as_dict=True)[0]
        self.assertEqual(json.loads(profile.languages), ['am', 'en'])
        self.assertEqual(profile.introduction, 'Public fictional introduction')
        self.assertNotIn('PRIVATE-CREDENTIAL', json.dumps(profile))
        frappe.set_user('Administrator')
        reviewed = [item for item in journey.applications() if item.user == user]
        self.assertEqual(reviewed[0].application_profile['registration_number'], 'PRIVATE-CREDENTIAL')
        self.assertTrue(reviewed[0].evidence_complete)
        self.assertEqual(reviewed[0].statement, '')
        frappe.set_user('Guest')
        with self.assertRaises(frappe.PermissionError):
            journey.applications()
        with self.assertRaises(frappe.PermissionError):
            auth.onboarding()
        frappe.set_user(user)
        with self.assertRaises(frappe.ValidationError):
            auth.save_onboarding('clinician', 3, acknowledged(answers), 1)
        self.assertEqual(frappe.db.sql('SELECT COUNT(*) FROM tt_application WHERE user=%s', (user,))[0][0], 1)
        frappe.db.commit()

    def test_delivery_send_once_uncertain_and_no_plaintext_storage(self):
        request = secrets.token_hex(20)
        with patch('tele_tena.email_delivery.send_code', side_effect=TimeoutError) as delivery:
            result = auth.request_code('email', self.contact, request)
            again = auth.request_code('email', self.contact, request)
            self.assertEqual(delivery.call_count, 1)
            self.assertEqual(result['challenge_id'], again['challenge_id'])
            self.assertEqual(result['delivery_state'], 'uncertain')
            code = delivery.call_args.args[1]
        self.challenges.append(result['challenge_id'])
        row = frappe.db.sql('SELECT otp_digest,dispatch_state FROM tt_otp_challenge WHERE id=%s', (result['challenge_id'],))[0]
        self.assertNotEqual(row[0], code)
        self.assertEqual(len(row[0]), 64)
        with self.assertRaises(frappe.ValidationError):
            auth.request_code('email', self.contact, secrets.token_hex(20))

    def test_concurrent_verification_consumes_once(self):
        result, code = self.challenge()
        barrier = threading.Barrier(2)
        def worker():
            base.connect()
            frappe.set_user('Guest')
            try:
                barrier.wait()
                auth.verify_code('email', self.contact, result['challenge_id'], code)
                return 'success'
            except frappe.ValidationError:
                frappe.db.rollback()
                return 'rejected'
            finally:
                frappe.destroy()
        with patch.object(phone_auth, '_establish_login'):
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: worker(), range(2)))
        self.users.append(self.contact)
        self.assertCountEqual(results, ['success', 'rejected'])

    def test_expiry_attempt_limit_and_other_owner_draft(self):
        result, code = self.challenge()
        for _ in range(5):
            with self.assertRaises(frappe.ValidationError):
                auth.verify_code('email', self.contact, result['challenge_id'], 'wrong')
        with self.assertRaises(frappe.ValidationError):
            self.verify(result, code)
        frappe.db.sql('UPDATE tt_otp_challenge SET attempts=0,expires=UTC_TIMESTAMP()-INTERVAL 1 SECOND WHERE id=%s', (result['challenge_id'],))
        frappe.db.commit()
        with self.assertRaises(frappe.ValidationError):
            self.verify(result, code)
        # Arbitrary user claims are not accepted by any owner-only draft endpoint.
        with self.assertRaises(TypeError):
            auth.onboarding(user='another@example.invalid')

    def test_verified_existing_email_only_and_guest_session(self):
        self.assertEqual(auth.session(), {'authenticated': False})
        result, code = self.challenge()
        user = self.verify(result, code)
        frappe.db.sql('UPDATE tt_otp_challenge SET created=UTC_TIMESTAMP()-INTERVAL 2 MINUTE WHERE id=%s', (result['challenge_id'],))
        frappe.db.commit()
        next_result, next_code = self.challenge()
        self.assertEqual(self.verify(next_result, next_code), user)
        self.assertEqual(frappe.db.sql('SELECT COUNT(*) FROM tt_contact_identity WHERE contact=%s', (self.contact,))[0][0], 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
