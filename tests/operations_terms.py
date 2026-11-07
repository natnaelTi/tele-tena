"""Rollback-only policy/guest consent boundaries; no recorder/provider calls."""
from operations import *
from tele_tena.api import policies
from tele_tena.operations import disclosure,capture
class Terms(Operations):
 def test_current_disclosure_has_versioned_terms_and_privacy_without_mutating_sources(self):
  from tele_tena.api.public_content import public
  source=public();before=json.dumps(source,sort_keys=True,default=str);value=policies.current()
  self.assertEqual(value['documents'],source['documents']);self.assertEqual(json.dumps(public(),sort_keys=True,default=str),before)
  self.assertEqual(value['terms_version'],disclosure.version(value['terms_source_version'],'terms'))
  self.assertIn('PostHog',' '.join(value['replay_disclosure']['privacy']));self.assertFalse(value['replay_disclosure']['guest_acceptance_available']);self.assertTrue(value['review_only'])
 def test_disclosure_wording_changes_effective_policy_version(self):
  before=policies.current()['terms_version']
  with patch.object(disclosure,'TERMS',[*disclosure.TERMS,'Synthetic wording revision.']):self.assertNotEqual(policies.current()['terms_version'],before)
 def test_old_policy_version_cannot_be_recorded_as_current(self):
  value=policies.current();before=j.one('SELECT COUNT(*) n FROM tt_policy_acceptance').n
  with self.assertRaises(frappe.ValidationError):policies.record(users['patient'],{'terms_accepted':True,'privacy_acknowledged':True,'terms_version':value['terms_source_version'],'privacy_version':value['privacy_source_version']})
  self.assertEqual(j.one('SELECT COUNT(*) n FROM tt_policy_acceptance').n,before)
 def test_terms_acceptance_never_enables_optional_replay(self):
  value=policies.current();ops.preference(False,False)
  policies.record(users['patient'],dict(terms_accepted=True,privacy_acknowledged=True,terms_version=value['terms_version'],privacy_version=value['privacy_version']))
  self.assertFalse(ops.collection()['preference']['replay'])
 def test_guest_no_choice_cookie_or_old_acceptance_can_enable_capture(self):
  before=j.one('SELECT COUNT(*) n FROM tt_ops_capture').n
  frappe.set_user('Guest')
  for _ in ('not accepted','declined','withdrawn','older Terms accepted'):
   self.assertFalse(ops.collection()['preference']['replay']);self.assertIsNone(ops.collection()['subject']);self.assertFalse(capture.eligible())
   with self.assertRaises(frappe.PermissionError):ops.preference(False,True)
   with self.assertRaises(frappe.PermissionError):ops.replay_admit(str(uuid.uuid4()),str(uuid.uuid4()))
  self.assertEqual(j.one('SELECT COUNT(*) n FROM tt_ops_capture').n,before)
 def test_sign_in_out_account_change_and_withdrawal_do_not_transfer_choice(self):
  frappe.set_user(users['patient']);ops.preference(False,True);self.assertTrue(ops.collection()['preference']['replay'])
  frappe.set_user('Guest');self.assertFalse(ops.collection()['preference']['replay'])
  frappe.set_user(users['counselor']);ops.preference(False,False);self.assertFalse(ops.collection()['preference']['replay'])
  frappe.set_user(users['patient']);ops.preference(False,False);self.assertFalse(ops.collection()['preference']['replay']);self.assertFalse(capture.eligible())
if __name__=='__main__':
 try:
  result=unittest.TextTestRunner().run(unittest.TestSuite(Terms(n) for n in Terms.__dict__ if n.startswith('test_')));sys.exit(not result.wasSuccessful())
 finally:frappe.db.rollback();frappe.destroy()
