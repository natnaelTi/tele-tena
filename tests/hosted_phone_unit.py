"""Hosted access rules that need no site database or live SMS."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tele_tena import review, sms
from tele_tena.api import phone_auth


class Permission(Exception):
    pass


class HostedPhoneUnit(unittest.TestCase):
    def setUp(self):
        def deny(*args):
            raise Permission()
        self.fake = SimpleNamespace(local=SimpleNamespace(site='review.test', request=None, response={}),
            conf={'tele_tena_review_site':'review.test', 'tele_tena_review_enabled':True},
            session=SimpleNamespace(user='Administrator'), PermissionError=Permission, throw=deny,
            clear_cache=Mock())
        patcher = patch.object(review, 'frappe', self.fake)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_local_helper_changes_only_explicit_site_flags(self):
        updates = []
        with patch('builtins.input', side_effect=['review.test','yes','yes','no','7']), \
             patch('frappe.installer.update_site_config', side_effect=lambda key, value: updates.append((key,value))), \
             patch.object(sms, '_config', return_value={'api_key':'synthetic'}):
            result = review.configure_contact_access()
        self.assertEqual(result['sms_24h_cap'], 7)
        self.assertEqual(updates, [('tele_tena_phone_otp_enabled',True),
            ('tele_tena_patient_registration_enabled',True),
            ('tele_tena_clinician_registration_enabled',False),
            ('tele_tena_sms_24h_cap',7)])
        self.assertNotIn('tele_tena_review_enabled', dict(updates))
        self.assertNotIn('tele_tena_simulation_enabled', dict(updates))

    def test_helper_rejects_wrong_site_and_missing_key_without_change(self):
        with patch('builtins.input', return_value='other.test'), \
             patch('frappe.installer.update_site_config') as change:
            with self.assertRaises(ValueError):
                review.configure_contact_access()
            change.assert_not_called()
        with patch('builtins.input', side_effect=['review.test','yes','yes','yes','5']), \
             patch.object(sms, '_config', side_effect=sms.SMSRejected('not_configured')), \
             patch('frappe.installer.update_site_config') as change:
            with self.assertRaises(sms.SMSRejected):
                review.configure_contact_access()
            change.assert_not_called()

    def test_one_explicit_provider_header_no_fallback(self):
        response = Mock(status_code=200)
        response.json.return_value = {'status':'success','message':'Accepted Successfully'}
        config = {'api_key':'synthetic','auth_header':'Authorization','auth_scheme':'bearer'}
        with patch.object(sms, '_config', return_value=config), \
             patch.object(sms.requests, 'post', return_value=response) as send:
            self.assertEqual(sms.send_otp('+251911234567','123456'), 'accepted')
        headers = send.call_args.kwargs['headers']
        self.assertEqual(headers['Authorization'], 'Bearer synthetic')
        self.assertNotIn('KEY', headers)
        response.status_code = 401
        with patch.object(sms, '_config', return_value=config), \
             patch.object(sms.requests, 'post', return_value=response) as send:
            with self.assertRaises(sms.SMSRejected):
                sms.send_otp('+251911234567','123456')
            self.assertEqual(send.call_count, 1)

    def test_peer_ignores_untrusted_forwarded_header(self):
        self.fake.local.request = SimpleNamespace(remote_addr='127.0.0.1',
                                                  headers={'X-Forwarded-For':'1.2.3.4'})
        with patch.object(phone_auth, 'frappe', self.fake):
            self.assertEqual(phone_auth._peer_ip(), '127.0.0.1')


if __name__ == '__main__':
    unittest.main(verbosity=2)
