"""Real Frappe 16 site/transaction tests; provider mocked, synthetic contacts only."""
import base64
import concurrent.futures
import json
import os
from pathlib import Path
import secrets
import unittest
from unittest.mock import patch

BENCH = Path(__file__).resolve().parents[3]
SITE = 'tele-tena-pr2-test.localhost'
assert BENCH.parent.name == 'teletena-compat' and os.geteuid() != 0
os.chdir(BENCH / 'sites')
import frappe
from tele_tena import review, sms
from tele_tena.api import contact_auth as auth, phone_auth as otp, presentation


def connect():
    frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
    frappe.connect()


def phone():
    return '+2519' + str(secrets.randbelow(100_000_000)).zfill(8)


class HostedPhone(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        connect()
        frappe.set_user('Administrator')
        with patch('builtins.input', side_effect=[SITE, 'https://review.example.invalid']):
            review.configure()
        frappe.conf.update(tele_tena_review_site=SITE, tele_tena_review_enabled=True)
        assert frappe.db.get_single_value('Website Settings', 'disable_signup')
        cls.seed = json.loads((BENCH/'sites'/SITE/'private'/'tele_tena_review_seed.json').read_text())
        # A synthetic key only; every actual send_otp call below is mocked.
        review.write_private(Path(frappe.get_site_path('private','tele_tena_sms.json')),
                             {'api_key':'synthetic-do-not-send','auth_header':'KEY','auth_scheme':'raw'})
        with patch.dict(frappe.conf, {'tele_tena_phone_otp_enabled':False}):
            assert not review.phone_enabled()
        with patch('builtins.input', side_effect=[SITE,'yes','yes','yes','100']):
            review.configure_contact_access()
        frappe.conf.update(tele_tena_phone_otp_enabled=True,
                           tele_tena_patient_registration_enabled=True,
                           tele_tena_clinician_registration_enabled=True,
                           tele_tena_sms_24h_cap=100)
        cls.users = []

    @classmethod
    def tearDownClass(cls):
        frappe.destroy()

    def setUp(self):
        frappe.set_user('Guest')
        peer = patch.object(otp, '_peer_ip', return_value='synthetic-peer-' + secrets.token_hex(8))
        peer.start()
        self.addCleanup(peer.stop)

    def send(self, number, failure=None):
        captured = []
        def deliver(destination, code):
            captured.append((destination, code))
            if failure:
                raise failure
            return 'accepted'
        request_id=secrets.token_hex(20)
        self.last_request_id=request_id
        with patch.object(sms, 'send_otp', side_effect=deliver):
            result = auth.request_code('phone', number, request_id)
        self.assertEqual(len(captured), 1)
        return result, captured[0][1]

    def verify(self, number, result, code):
        with patch.object(otp, '_establish_login', side_effect=frappe.set_user):
            auth.verify_code('phone', number, result['challenge_id'], code)
        return frappe.session.user

    def existing_patient(self):
        """An administrator-created synthetic account with a prior verified phone."""
        from tele_tena.account_context import authorized_user_change
        from tele_tena.api import journey
        user='hosted-existing-' + secrets.token_hex(8) + '@example.invalid'
        number=phone()
        frappe.set_user('Administrator')
        with authorized_user_change():
            doc=frappe.get_doc(dict(doctype='User',email=user,first_name='Synthetic patient',
                                    user_type='Website User',send_welcome_email=0))
            doc.insert()
            doc.add_roles('Tele Tena Patient')
        frappe.set_user(user)
        journey.save_profile('patient','Synthetic alias',True)
        frappe.set_user('Administrator')
        frappe.db.sql('INSERT INTO tt_phone_identity (user,phone,verified_at,created) VALUES (%s,%s,UTC_TIMESTAMP(6),UTC_TIMESTAMP(6))',
                      (user,number))
        frappe.db.commit()
        frappe.set_user('Guest')
        return user,number

    def test_01_site_flags_and_existing_verified_user(self):
        self.assertTrue(review.phone_enabled())
        self.assertTrue(review.registration_enabled('patient'))
        self.assertTrue(review.registration_enabled('clinician'))
        self.assertFalse(bool(frappe.db.get_single_value('Website Settings', 'disable_signup') == 0))
        with patch.dict(frappe.conf, {'tele_tena_phone_otp_enabled':False}):
            with self.assertRaises(frappe.PermissionError):
                auth.request_code('phone', phone(), secrets.token_hex(20))
        existing,number=self.existing_patient()
        result, code = self.send(number)
        self.assertEqual(result['delivery_state'], 'accepted')
        self.__class__.existing_result = result
        self.assertEqual(self.verify(number,result,code),existing)
        with self.assertRaises(frappe.ValidationError):
            self.verify(number,result,code)
        frappe.db.commit()

    def test_02_new_patient_requires_adult_consent(self):
        number=phone()
        result, code=self.send(number)
        self.assertEqual({key:value for key,value in result.items() if key!='challenge_id'},
                         {key:value for key,value in self.existing_result.items() if key!='challenge_id'})
        with patch.object(sms,'send_otp') as delivery:
            replay=auth.request_code('phone',number,self.last_request_id)
            self.assertEqual(replay['challenge_id'],result['challenge_id'])
            delivery.assert_not_called()
        user=self.verify(number,result,code)
        self.users.append(user)
        self.assertFalse(frappe.db.exists('tt_profile',user))
        self.assertNotIn('Tele Tena Patient',frappe.get_roles(user))
        with self.assertRaises(frappe.ValidationError):
            auth.save_onboarding('patient',3,{'name':'Synthetic alias','adult':True,'consent':False},1)
        auth.save_onboarding('patient',1,{'name':'Synthetic alias'},0)
        self.assertEqual(auth.onboarding()['answers']['name'],'Synthetic alias')
        auth.save_onboarding('patient',3,{'name':'Synthetic alias','adult':True,'consent':True},1)
        self.assertIn('Tele Tena Patient',frappe.get_roles(user))
        self.assertNotIn('Tele Tena Approver',frappe.get_roles(user))
        frappe.db.commit()

    def test_03_new_clinician_stays_unapproved(self):
        number=phone()
        result, code=self.send(number)
        user=self.verify(number,result,code)
        self.users.append(user)
        service=frappe.db.sql('SELECT name FROM `tabTele Tena Service` WHERE active=1 LIMIT 1')
        if not service:
            frappe.set_user('Administrator')
            from tele_tena.api import journey
            service_id='hosted-' + secrets.token_hex(5)
            journey.save_service(service_id,'Synthetic review service')
            frappe.set_user(user)
        else:
            service_id=service[0][0]
        self.assertNotIn('Tele Tena Clinician',frappe.get_roles(user))
        auth.save_onboarding('clinician',1,{'name':'Synthetic applicant','statement':'Synthetic claim',
            'requested_services':[service_id],'adult':True,'consent':True},0)
        presentation.upload_resume('synthetic-resume.pdf',base64.b64encode(b'%PDF-1.4\nSynthetic evidence\n%%EOF').decode())
        auth.save_onboarding('clinician',3,{'name':'Synthetic applicant','statement':'Synthetic claim',
            'requested_services':[service_id],'adult':True,'consent':True},1)
        self.assertIn('Tele Tena Applicant',frappe.get_roles(user))
        self.assertNotIn('Tele Tena Clinician',frappe.get_roles(user))
        self.assertEqual(frappe.db.sql('SELECT status FROM tt_application WHERE user=%s',(user,))[0][0],'Pending')
        frappe.db.commit()

    def test_04_rejected_uncertain_and_budget(self):
        rejected_phone=phone()
        rejected, code=self.send(rejected_phone,sms.SMSRejected('provider_rejected'))
        self.assertEqual(rejected['delivery_state'],'rejected')
        with self.assertRaises(frappe.ValidationError):
            self.verify(rejected_phone,rejected,code)
        uncertain, code=self.send(phone(),sms.SMSUncertain('provider_outcome_unknown'))
        self.assertEqual(uncertain['delivery_state'],'uncertain')
        used=frappe.db.sql("SELECT COUNT(*) FROM tt_otp_challenge WHERE dispatch_state IN ('Sending','Accepted','Rejected','Uncertain') AND created>UTC_TIMESTAMP(6)-INTERVAL 24 HOUR")[0][0]
        with patch.dict(frappe.conf,{'tele_tena_sms_24h_cap':used}):
            with patch.object(sms,'send_otp') as deliver:
                with self.assertRaises(frappe.ValidationError):
                    auth.request_code('phone',phone(),secrets.token_hex(20))
                deliver.assert_not_called()
        frappe.db.commit()

    def test_05_registration_switch_blocks_new_completion_not_existing_login(self):
        number=phone()
        result, code=self.send(number)
        user=self.verify(number,result,code)
        self.users.append(user)
        with patch.dict(frappe.conf,{'tele_tena_clinician_registration_enabled':False}):
            with self.assertRaises(frappe.ValidationError):
                auth.save_onboarding('clinician',0,{'name':'Blocked'},0)
            existing_user,number=self.existing_patient()
            existing, proof=self.send(number)
            self.assertEqual(self.verify(number,existing,proof),existing_user)
        frappe.db.commit()

    def test_06_concurrent_code_consume_creates_one_account(self):
        number=phone()
        result, code=self.send(number)
        frappe.db.commit()
        def worker():
            connect()
            try:
                frappe.set_user('Guest')
                auth.verify_code('phone',number,result['challenge_id'],code)
                return True
            except frappe.ValidationError:
                frappe.db.rollback()
                return False
            finally:
                frappe.destroy()
        with patch.object(otp,'_establish_login'), concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:worker(), range(2)))
        self.assertEqual(results.count(True),1)
        self.assertEqual(frappe.db.sql('SELECT COUNT(*) FROM tt_contact_identity WHERE channel=%s AND contact=%s',('phone',number))[0][0],1)

    def test_07_conflicting_verified_phone_mappings_fail_closed(self):
        number=phone()
        result, code=self.send(number)
        user=self.verify(number,result,code)
        self.users.append(user)
        conflicting_user,_=self.existing_patient()
        frappe.db.sql('DELETE FROM tt_phone_identity WHERE user=%s',(conflicting_user,))
        frappe.db.sql('INSERT INTO tt_phone_identity (user,phone,verified_at,created) VALUES (%s,%s,UTC_TIMESTAMP(6),UTC_TIMESTAMP(6))',
                      (conflicting_user,number))
        frappe.db.sql('UPDATE tt_otp_challenge SET created=created-INTERVAL 61 SECOND WHERE phone_digest=%s',
                      (otp._keyed('contact:phone',number),))
        frappe.db.commit()
        frappe.set_user('Guest')
        next_result,next_code=self.send(number)
        with self.assertRaises(frappe.ValidationError):
            self.verify(number,next_result,next_code)
        frappe.db.rollback()
        self.assertEqual(frappe.db.sql('SELECT COUNT(*) FROM tt_contact_identity WHERE channel=%s AND contact=%s AND user=%s',
                         ('phone',number,user))[0][0],1)


if __name__=='__main__':
    unittest.main(verbosity=2)
