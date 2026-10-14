"""Run only on an isolated review site; no external delivery or existing file removal."""
import base64,importlib.util,json,os,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
BENCH=Path(os.environ['TELE_TENA_TEST_BENCH']);SITE=os.environ['TELE_TENA_TEST_SITE'];assert SITE.endswith('.localhost') and SITE.startswith('teletena-')
os.chdir(BENCH/'sites');sys.path.insert(0,str(BENCH/'apps/tele_tena'))
import frappe
frappe.init(site=SITE);frappe.connect()
from tele_tena.api import history_documents as documents,country,journey
from tele_tena.demo_dataset import document
state=json.loads(Path(frappe.get_site_path('private','tt-demo-mvp-v2-records.json')).read_text());patient=state['users']['patient']
class Uploads(unittest.TestCase):
 def setUp(self):frappe.set_user(patient)
 def test_owner_retry_and_privacy(self):
  before=journey.profile('patient');result=documents.upload('fictional-permission-check.pdf',document('medical history fixture'))
  try:
   self.assertEqual(documents.upload('fictional-permission-check.pdf',document('medical history fixture'))['id'],result['id'])
   self.assertEqual(documents.download(result['id']).headers['Cache-Control'],'private, no-store')
   self.assertEqual(journey.profile('patient').history,before.history)
   self.assertEqual(journey.profile('patient').share_history,before.share_history)
   for role in ['private_patient','counselor','reviewer']:
    frappe.set_user(state['users'][role])
    with self.assertRaises(frappe.PermissionError):documents.download(result['id'])
   frappe.set_user('Guest')
   with self.assertRaises(frappe.PermissionError):documents.list_documents()
  finally:frappe.set_user(patient);documents.remove(result['id'])
 def test_invalid_and_quota_are_atomic(self):
  before=len(documents.list_documents()['documents'])
  for name,data in [('bad.pdf',base64.b64encode(b'%PDF-broken').decode()),('bad.exe',document('invalid extension'))]:
   with self.assertRaises(frappe.ValidationError):documents.upload(name,data)
  old=frappe.conf.get('tele_tena_history_storage_mb');frappe.conf.tele_tena_history_storage_mb=0
  try:
   with self.assertRaises(frappe.ValidationError):documents.upload('quota.pdf',document('quota'))
  finally:frappe.conf.tele_tena_history_storage_mb=old
  self.assertEqual(len(documents.list_documents()['documents']),before)
 def test_verified_onboarding_gate(self):
  from tele_tena.api.contact_auth import _identity,save_onboarding
  import uuid
  keys=('tele_tena_review_site','tele_tena_review_enabled','tele_tena_patient_registration_enabled')
  old={key:frappe.conf.get(key) for key in keys};frappe.db.savepoint('history_onboarding')
  try:
   frappe.conf.update(dict(tele_tena_review_site=SITE,tele_tena_review_enabled=True,tele_tena_patient_registration_enabled=True))
   # Internal post-verification identity helper; no SMS/email or fixed public OTP.
   user=_identity('email','history-'+uuid.uuid4().hex+'@example.invalid');frappe.set_user(user)
   with self.assertRaises(frappe.PermissionError):documents.list_documents()
   frappe.db.sql("UPDATE tt_onboarding SET answers=%s WHERE user=%s",(json.dumps({'adult':True,'consent':True}),user))
   result=documents.upload('onboarding.pdf',document('fictional onboarding history'))
   self.assertEqual(documents.list_documents()['documents'][0].id,result['id'])
   frappe.conf.tele_tena_patient_registration_enabled=False
   with self.assertRaises(frappe.PermissionError):documents.download(result['id'])
  finally:
   frappe.db.rollback(save_point='history_onboarding');frappe.conf.update(old);frappe.set_user(patient)
 def test_proxy_chain_and_database(self):
  old=frappe.conf.get('tele_tena_country_trusted_proxies');frappe.conf.tele_tena_country_trusted_proxies=['127.0.0.1/32']
  try:
   with patch.object(frappe.local,'request',SimpleNamespace(remote_addr='4.4.4.4',headers={'X-Forwarded-For':'8.8.8.8'}),create=True):self.assertEqual(country.client_ip(),'4.4.4.4')
   with patch.object(frappe.local,'request',SimpleNamespace(remote_addr='127.0.0.1',headers={'X-Forwarded-For':'11.22.33.44, 8.8.8.8'}),create=True):self.assertEqual(country.client_ip(),'8.8.8.8')
   with patch.object(frappe.local,'request',SimpleNamespace(remote_addr='127.0.0.1',headers={}),create=True):self.assertIsNone(country.suggestion()['country'])
  finally:frappe.conf.tele_tena_country_trusted_proxies=old
if __name__=='__main__':
 try:
  result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Uploads));frappe.db.commit();sys.exit(0 if result.wasSuccessful() else 1)
 finally:frappe.destroy()
