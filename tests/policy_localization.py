"""Read-only synthetic approved-source fixtures; no policy publication or consent writes."""
import os,sys,unittest,hashlib,copy
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.chdir('/home/frappe/teletena-compat/bench/sites')
import frappe
frappe.init(site='teletena-guest-first-test.localhost');frappe.connect();frappe.set_user('Guest')
from tele_tena.api import policies
from tele_tena import localization
from tele_tena.public_content_defaults import DOCUMENTS
class Policy(unittest.TestCase):
 def data(self):
  title,audience,body=DOCUMENTS['terms'];return {'documents':[{'key':'terms','version':'immutable-fixture-v1','title':title,'body':body,'audience':audience,'review_only':True}]}
 def test_only_reviewed_locale_default_is_presented_without_new_versions(self):
  source=self.data();title=source['documents'][0]['title'];reviewed={'fixture':{'english':title,'source_hash':hashlib.sha256(title.encode()).hexdigest(),'amharic':'የሙከራ ሰነድ'}}
  with patch('tele_tena.api.public_content.public',return_value=source),patch.object(localization,'entries',return_value=reviewed):
   am=policies.current('am');om=policies.current('om')
  self.assertEqual(am['documents'][0]['title'],'የሙከራ ሰነድ');self.assertEqual(om['documents'][0]['title'],title);self.assertEqual(am['terms_version'],'immutable-fixture-v1');self.assertTrue(am['review_only']);self.assertEqual(am['documents'][0]['body'],source['documents'][0]['body']);self.assertEqual(source,self.data())
 def test_custom_document_text_is_not_translated_or_modified(self):
  source=self.data();source['documents'][0].update(title='Owner-authored title',body='Owner-authored policy content');original=copy.deepcopy(source)
  with patch('tele_tena.api.public_content.public',return_value=source),patch.object(localization,'translate',side_effect=AssertionError('Custom content must not enter source translation')):
   result=policies.current('am')
  self.assertEqual(result['documents'],original['documents']);self.assertEqual(source,original)
 def test_care_language_is_not_an_interface_locale(self):
  with self.assertRaises(frappe.ValidationError):policies.current('fr')
if __name__=='__main__':
 try:unittest.main()
 finally:frappe.db.rollback();frappe.destroy()
