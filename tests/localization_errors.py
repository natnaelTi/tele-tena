"""Synthetic reviewed messages only; authorization and HTTP exception types unchanged."""
import os,sys,unittest,hashlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.chdir('/home/frappe/teletena-compat/bench/sites')
import frappe
frappe.init(site='teletena-guest-first-test.localhost');frappe.connect();frappe.set_user('Guest')
from tele_tena import localization
from tele_tena.api.journey import fail,actor
class Errors(unittest.TestCase):
 def setUp(self):self.old=getattr(frappe.local,'request',None);frappe.local.request=SimpleNamespace(headers={'X-TeleTena-Locale':'am'})
 def tearDown(self):frappe.local.request=self.old
 def test_template_is_translated_before_private_value_interpolation(self):
  source='Amount {amount}';entry={'english':source,'source_hash':hashlib.sha256(source.encode()).hexdigest(),'amharic':'መጠን {amount}'}
  with patch.object(localization,'entries',return_value={'fixture':entry}):
   with self.assertRaises(frappe.ValidationError) as caught:fail(source,'fixture_error',template_values={'amount':'12.34'})
  self.assertEqual(str(caught.exception),'መጠን 12.34');self.assertEqual(frappe.local.response['tele_tena_error'],'fixture_error')
 def test_localized_permission_failure_never_grants_access(self):
  source='Authentication required';entry={'english':source,'source_hash':hashlib.sha256(source.encode()).hexdigest(),'amharic':'ማረጋገጫ ያስፈልጋል'}
  with patch.object(localization,'entries',return_value={'fixture':entry}):
   with self.assertRaises(frappe.PermissionError) as caught:actor('Tele Tena Approver')
  self.assertEqual(str(caught.exception),'ማረጋገጫ ያስፈልጋል');self.assertEqual(frappe.session.user,'Guest')
 def test_care_language_or_role_header_is_not_an_interface_locale(self):
  frappe.local.lang='en'
  for value in ['fr','Tele Tena Approver','xx']:
   frappe.local.request=SimpleNamespace(headers={'X-TeleTena-Locale':value});self.assertEqual(localization.request_locale(),'en')
 def test_unapproved_other_locale_still_falls_back(self):
  frappe.local.request=SimpleNamespace(headers={'X-TeleTena-Locale':'om'})
  source='Authentication required';entry={'english':source,'source_hash':hashlib.sha256(source.encode()).hexdigest(),'amharic':'ማረጋገጫ'}
  with patch.object(localization,'entries',return_value={'fixture':entry}):
   with self.assertRaises(frappe.PermissionError) as caught:actor()
  self.assertEqual(str(caught.exception),source)
if __name__=='__main__':
 try:unittest.main()
 finally:frappe.db.rollback();frappe.destroy()
