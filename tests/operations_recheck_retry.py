"""Network-free settled-cleanup retry authorization checks."""
import hashlib
import unittest
from scripts.operations_proof.recheck import deletion_keys
from tele_tena.operations.proof import ProofBlocked

class RetryTests(unittest.TestCase):
    def setUp(self):
        self.row = {'id': 'synthetic', 'denied_key_observed_sha256': hashlib.sha256(b'old').hexdigest()}
        self.m = {'actions': {'provider-delete-synthetic': {'state': 'HTTPResponse', 'http_status': 403}}, 'recordings': [self.row]}
    def test_requires_confirmation(self):
        with self.assertRaises(ProofBlocked): deletion_keys(self.m, {'posthog_delete_key': 'new'}, 'synthetic')
    def test_requires_changed_key(self):
        self.row['deletion_retry_authorized'] = True
        with self.assertRaises(ProofBlocked): deletion_keys(self.m, {'posthog_delete_key': 'old'}, 'synthetic')
    def test_explicit_same_key_permission_correction(self):
        self.row['deletion_retry_authorized'] = True
        self.row['deletion_permission_change_confirmed'] = True
        self.assertEqual(deletion_keys(self.m, {'posthog_delete_key': 'old'}, 'synthetic')[0], 'provider-delete-retry-1-synthetic')
    def test_one_stable_retry_key(self):
        self.row['deletion_retry_authorized'] = True
        self.assertEqual(deletion_keys(self.m, {'posthog_delete_key': 'new'}, 'synthetic'), ('provider-delete-retry-1-synthetic', 'provider-delete-confirm-retry-1-synthetic'))
    def test_final_pair_requires_explicit_authorization_and_known_denial(self):
        self.row.update(deletion_retry_authorized=True, deletion_permission_change_confirmed=True, deletion_retry_authorized_attempts=2)
        with self.assertRaises(ProofBlocked): deletion_keys(self.m, {'posthog_delete_key':'old'}, 'synthetic')
        self.m['actions']['provider-delete-retry-1-synthetic']={'state':'HTTPResponse','http_status':403}
        self.assertEqual(deletion_keys(self.m, {'posthog_delete_key':'old'}, 'synthetic')[0], 'provider-delete-retry-2-synthetic')
    def test_unknown_not_resent(self):
        self.m['actions']['provider-delete-synthetic'] = {'state': 'Unknown'}
        self.assertEqual(deletion_keys(self.m, {}, 'synthetic')[0], 'provider-delete-synthetic')

if __name__ == '__main__': unittest.main()
