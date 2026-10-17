"""Persisted guest-first checks on an explicitly disposable copy;no provider I/O."""
import base64,json,os,secrets,sys,unittest,uuid
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
BENCH=Path(os.environ['TELE_TENA_TEST_BENCH']);SITE=os.environ['TELE_TENA_TEST_SITE']
assert SITE=='teletena-guest-first-test.localhost'
os.chdir(BENCH/'sites');sys.path.insert(0,str(BENCH/'apps/tele_tena'))
import frappe
frappe.init(site=SITE);frappe.connect();frappe.local.lang='en'
from tele_tena.api import directory,journey,scheduling,history_documents,encounter_files,policies,contact_auth
from tele_tena import accounting,booking_notifications
state=json.loads(Path(frappe.get_site_path('private','tt-demo-mvp-v2-records.json')).read_text());users=state['users']

class GuestFirst(unittest.TestCase):
 def setUp(self):
  frappe.db.savepoint('guest_first');frappe.set_user(users['patient']);self.guard=patch('frappe.sendmail',side_effect=AssertionError('Unexpected external mail'));self.guard.start()
 def tearDown(self):
  frappe.db.rollback(save_point='guest_first');self.guard.stop();frappe.set_user('Administrator')
 def offer(self):
  values=journey.discover()
  for offer in values:
   if offer.participant_structure in (None,'','individual') and scheduling.calendar(offer.id)['days']:return offer
  self.fail('Existing presentation dataset has no usable offering;do not fabricate one')
 def book(self,files=None):
  offer=self.offer();slot=scheduling.calendar(offer.id)['days'][0]['slots'][0]
  sharing={'name':False,'history':True,'files':files or [],'alias':'Fictional care alias'}
  preview=journey.preview('Fictional consent test',sharing)['disclosure']
  wallet=journey.wallet()
  if wallet['available']<offer.price:journey.simulated_deposit(offer.price-wallet['available'],str(uuid.uuid4()))
  key=str(uuid.uuid4());args=(offer.id,slot['start'],'Fictional consent test',sharing,key,offer.price,offer.minutes,preview)
  result=journey.book(*args);return result,args,offer
 def test_public_projection_and_composable_filters(self):
  frappe.set_user('Guest');response=directory.offerings();self.assertTrue(response['items'])
  for item in response['items']:
   self.assertEqual(set(item),set(directory.PUBLIC_FIELDS)|{'availability','photo_url'})
   self.assertNotIn('@',item['clinician_id']);self.assertNotIn('clinician',item);self.assertNotIn('patient',item)
  item=response['items'][0];filtered=directory.offerings(service=item['service_category'],language=item['care_languages'][0],consultation_format=item['consultation_format'])
  self.assertTrue(any(row['id']==item['id'] for row in filtered['items']))
  self.assertFalse(directory.offerings(language='om',consultation_format='audio',service='not-a-service')['items'])
  with self.assertRaises(frappe.PermissionError):journey.wallet()
  with self.assertRaises(frappe.ValidationError):directory.offerings(availability_filter='invented')
 def test_public_withdrawal_and_private_photo_denial(self):
  offer=self.offer();frappe.db.sql('UPDATE tt_offering SET active=0 WHERE id=%s',(offer.id,));frappe.set_user('Guest')
  self.assertFalse(directory.offerings(offering=offer.id)['items'])
  with self.assertRaises(frappe.PermissionError):directory.photo(str(uuid.uuid4()))
 def test_no_calendar_is_not_available_now(self):
  offer=self.offer();frappe.db.sql("UPDATE tt_schedule SET status='Draft' WHERE offering=%s",(offer.id,))
  self.assertEqual(directory.availability(offer.id)['state'],'unpublished')
  self.assertFalse(directory.availability(offer.id)['available_now'])
 def test_owner_only_before_explicit_grant_and_revoke(self):
  from tele_tena.demo_dataset import document
  uploaded=history_documents.upload('fictional-encounter.pdf',document('Fictional history'))
  for key in ('private_patient','counselor','reviewer','couple_partner'):
   frappe.set_user(users[key])
   with self.assertRaises(frappe.PermissionError):history_documents.download(uploaded['id'])
  frappe.set_user(users['patient']);result,args,offer=self.book([uploaded['id']]);id=result['id']
  grants=encounter_files.grants(id);self.assertEqual(len(grants),1);grant=grants[0]
  clinician=frappe.db.sql('SELECT clinician FROM tt_appointment WHERE id=%s',(id,))[0][0]
  frappe.set_user(clinician);self.assertEqual(encounter_files.download(grant.id).status_code,200)
  for key in ('private_patient','reviewer','couple_partner'):
   frappe.set_user(users[key])
   with self.assertRaises(frappe.PermissionError):encounter_files.download(grant.id)
  frappe.set_user(users['patient']);again=journey.book(*args);self.assertEqual(again['id'],id);self.assertEqual(len(encounter_files.grants(id)),1)
  encounter_files.revoke(grant.id);encounter_files.revoke(grant.id)
  self.assertEqual(frappe.db.sql("SELECT COUNT(*) FROM tt_history_grant_event WHERE grant_id=%s AND event='Revoked'",(grant.id,))[0][0],1)
  frappe.set_user(clinician)
  with self.assertRaises(frappe.PermissionError):encounter_files.download(grant.id)
  frappe.set_user(users['patient']);self.assertEqual(encounter_files.download(grant.id).status_code,200)
  self.assertTrue(frappe.db.sql('SELECT content FROM tt_history_grant WHERE id=%s',(grant.id,))[0][0])
 def test_file_removal_preserves_snapshot(self):
  from tele_tena.demo_dataset import document
  uploaded=history_documents.upload('fictional-retention.pdf',document('Fictional retained snapshot'))
  result,args,offer=self.book([uploaded['id']]);grant=encounter_files.grants(result['id'])[0]
  history_documents.remove(uploaded['id']);self.assertTrue(encounter_files.grants(result['id'])[0].revoked_at)
  self.assertEqual(encounter_files.download(grant.id).status_code,200)
 def test_notice_is_idempotent_and_not_a_payment(self):
  result,args,offer=self.book();id=result['id'];app=frappe.db.sql('SELECT * FROM tt_appointment WHERE id=%s',(id,),as_dict=True)[0]
  booking_notifications.create(id,app.state);booking_notifications.create(id,app.state)
  self.assertEqual(frappe.db.sql('SELECT COUNT(*) FROM tt_booking_notice WHERE appointment=%s',(id,))[0][0],2)
  self.assertEqual(frappe.db.sql("SELECT COUNT(*) FROM tt_journal WHERE event_ref=%s",('booking:'+id,))[0][0],1)
  self.assertEqual(booking_notifications.preferences(),{'email_enabled':False,'sms_enabled':False})
  self.assertEqual(len(booking_notifications.notices()),1)
 def test_policy_versions_and_no_implicit_privilege(self):
  with patch('tele_tena.review.registration_enabled',return_value=True):user=contact_auth._identity('email','guest-first-'+secrets.token_hex(6)+'@example.invalid')
  frappe.set_user(user)
  answers={'name':'Fictional patient','adult':True,'consent':True,'care_alias':'River','share_name':False,'share_history':True}
  with patch('tele_tena.review.registration_enabled',return_value=True):
   with self.assertRaises(frappe.ValidationError):contact_auth.save_onboarding('patient',3,answers,1)
   answers.update(terms_accepted=True,privacy_acknowledged=True,terms_version=policies.TERMS,privacy_version=policies.PRIVACY)
   contact_auth.save_onboarding('patient',3,answers,1)
  self.assertNotIn('Tele Tena Clinician',frappe.get_roles(user));self.assertNotIn('Tele Tena Approver',frappe.get_roles(user))
  self.assertEqual(journey.profile('patient').care_alias,'River')
  self.assertEqual(frappe.db.sql('SELECT COUNT(*) FROM tt_policy_acceptance WHERE user=%s',(user,))[0][0],1)
  self.assertTrue(journey.profile('patient').share_history)
 def test_invalid_files_and_cross_owner_selection_denied(self):
  with self.assertRaises(frappe.ValidationError):journey.preview('',{'name':False,'history':False,'files':[str(uuid.uuid4())]})
  with self.assertRaises(frappe.ValidationError):history_documents.upload('bad.exe',base64.b64encode(b'bad').decode())
  with self.assertRaises(frappe.PermissionError):encounter_files.grants() if frappe.set_user('Guest') else encounter_files.grants()

if __name__=='__main__':
 try:
  result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(GuestFirst));sys.exit(0 if result.wasSuccessful() else 1)
 finally:frappe.db.rollback();frappe.destroy()
