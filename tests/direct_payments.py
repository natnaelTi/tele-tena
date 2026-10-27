"""Rollback-isolated direct-payment state/ownership tests on retained synthetic accounts."""
import os,sys,json,unittest,uuid,base64,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BENCH=Path('/home/frappe/teletena-compat/bench');SITE='teletena-guest-first-test.localhost'
os.chdir(BENCH/'sites');sys.path.insert(0,str(ROOT));import frappe
frappe.init(site=SITE);frappe.connect();frappe.set_user('Administrator');frappe.conf.update(tele_tena_review_enabled=True,tele_tena_review_site=SITE)
from tele_tena.patches.v1_45_direct_payments import execute
from tele_tena.patches.v1_46_reference_navigation import execute as refs
execute();refs();from tele_tena.patches.v1_47_care_languages import execute as langs
langs();frappe.db.commit()
from tele_tena.api import direct_payments as pay,journey as j,scheduling
users=json.loads((BENCH/'sites'/SITE/'private/tt-demo-mvp-v2-records.json').read_text())['users']
class DirectPayment(unittest.TestCase):
 def setUp(self):
  frappe.db.savepoint('payment_test');frappe.set_user('Administrator');frappe.local.lang='en'
 def tearDown(self):frappe.db.rollback(save_point='payment_test');frappe.set_user('Administrator')
 def book(self,mode='Offline',key=None):
  c=pay.config()
  if c.mode!=mode:pay.configure(mode,c.revision,'Isolated rollback test only')
  frappe.set_user(users['counselor']);pay.save_payee('+251911234567',pay.payee()['revision'],'Synthetic payee for rollback test')
  from tele_tena.api import care_languages
  care_languages.save_claims([{'code':'en','proficiency':3,'explanation':'Explicit synthetic self-assessment for rollback-only test'}])
  frappe.set_user('Administrator');care_languages.decide(users['counselor'],'en','Approved','Synthetic language decision for rollback-only acceptance test')
  frappe.set_user(users['patient']);ids={r.id for r in j.rows('SELECT id FROM tt_offering WHERE clinician=%s AND active=1',(users['counselor'],))};offer=next(x for x in j.discover() if x.id in ids)
  from datetime import datetime,timedelta,timezone
  start=None
  for n in range(1,15):
   day=(datetime.now(timezone.utc)+timedelta(days=n)).date().isoformat();cal=scheduling.calendar(offer.id,day,days=7,display_timezone='Africa/Addis_Ababa')
   slots=[x for d in cal['days'] for x in d['slots']]
   if slots:start=slots[0]['start'];break
  self.assertTrue(start,'Fixture needs an actual future generated slot')
  sharing={'name':False,'history':False};disclosure=j.disclosure(j.profile('patient'),'Synthetic payment workflow test',sharing)
  args=dict(offering=offer.id,start=start,request_text='Synthetic payment workflow test',sharing=sharing,retry_key=key or str(uuid.uuid4()),expected_price=offer.price,expected_minutes=offer.minutes,expected_disclosure=disclosure,care_language=offer.care_languages[0],expected_payment_mode=mode,payment_mode_revision=pay.config().revision)
  return j.book(**args),args
 def receipt(self,id,key='proof',ref='SYNTHETIC123456',amount=None):
  from PIL import Image
  image=io.BytesIO();Image.new('RGB',(64,64),'blue').save(image,format='PNG')
  return pay.submit(id,ref,pay.detail(id)['amount'] if amount is None else amount,'fictional-receipt.png',base64.b64encode(image.getvalue()).decode(),key)
 def test_direct_confirmation_no_wallet_postings(self):
  before=frappe.db.sql('SELECT COUNT(*) FROM tt_journal')[0][0];result,args=self.book();self.assertEqual(result['state'],'AwaitingPayment')
  id=result['payment'];self.assertEqual(j.book(**args)['payment'],id)
  first=self.receipt(id);self.assertEqual(first['state'],'Submitted');self.assertEqual(self.receipt(id)['history'],first['history'])
  frappe.set_user(users['therapist'])
  with self.assertRaises(frappe.PermissionError):pay.detail(id)
  frappe.set_user(users['counselor']);verified=pay.review(id,'confirm','verify');self.assertEqual(verified['state'],'Verified');pay.review(id,'confirm','verify')
  self.assertEqual(frappe.db.sql('SELECT COUNT(*) FROM tt_journal')[0][0],before)
  self.assertEqual(frappe.db.sql('SELECT COUNT(*) FROM tt_direct_payment WHERE id=%s',(id,))[0][0],1)
 def test_late_claim_is_retained_for_reconciliation(self):
  result,_=self.book();id=result['payment'];frappe.db.sql('UPDATE tt_direct_payment SET hold_until=DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 1 MINUTE) WHERE id=%s',(id,));frappe.db.sql("UPDATE tt_appointment SET state='Expired' WHERE id=%s",(result['id'],))
  self.assertEqual(self.receipt(id)['state'],'ReconciliationRequired');frappe.set_user(users['counselor']);self.assertEqual(pay.review(id,'confirm','late')['state'],'RefundRequired')
  pay.refund(id,'reported','reported','External refund claimed by synthetic clinician');frappe.set_user(users['patient']);self.assertEqual(pay.refund(id,'received','received','Synthetic payer confirms receipt')['state'],'RefundConfirmed')
 def test_correction_history_and_receipt_denial(self):
  result,_=self.book();id=result['payment'];self.receipt(id)
  frappe.set_user(users['counselor']);pay.review(id,'correct','correction','Please provide a readable complete screenshot')
  frappe.set_user(users['patient']);self.receipt(id,'second-proof');history=pay.detail(id)['history'];self.assertEqual(sum(e.event=='PaymentSubmitted' for e in history),2)
  receipt=next(e.evidence for e in history if e.evidence);self.assertEqual(pay.receipt(receipt).status_code,200)
  frappe.set_user(users['therapist'])
  with self.assertRaises(frappe.PermissionError):pay.receipt(receipt)
 def test_duplicate_reference_does_not_pay_two_bookings(self):
  first,_=self.book();self.receipt(first['payment']);second,_=self.book()
  with self.assertRaises(frappe.ValidationError):self.receipt(second['payment'],'different-booking')
  self.assertEqual(pay.detail(second['payment'])['state'],'AwaitingPayment')
 def test_offline_extension_uses_additional_payment_not_wallet(self):
  from tele_tena.api import consultations,extensions
  from unittest.mock import patch
  result,_=self.book();id=result['payment'];self.receipt(id);frappe.set_user(users['counselor']);pay.review(id,'confirm','base-verify')
  from tele_tena.api.presentation import respond_to_request
  app=j.one('SELECT * FROM tt_appointment WHERE id=%s',(result['id'],))
  if app.state=='PendingConfirmation':respond_to_request(app.id,'confirm')
  with patch('tele_tena.api.consultations._window',return_value=True),patch('tele_tena.livekit._credentials',return_value=('wss://test.invalid','test','test')),patch('tele_tena.livekit.participant_token',return_value='private-fake-provider-token'):
   consultations.join(app.id)
  before=frappe.db.sql('SELECT COUNT(*) FROM tt_journal')[0][0]
  extension=extensions.propose_extension(app.id,'extension-quote');frappe.set_user(users['patient']);accepted=extensions.respond_extension(app.id,extension['id'],'accept')
  self.assertEqual(accepted['state'],'PaymentPending');self.assertEqual(extensions.respond_extension(app.id,extension['id'],'accept')['payment'],accepted['payment'])
  self.receipt(accepted['payment'],'extension-proof','SYNTHETICEXT1234');frappe.set_user(users['counselor']);pay.review(accepted['payment'],'confirm','extension-verify')
  self.assertEqual(j.one('SELECT state FROM tt_appointment WHERE id=%s',(app.id,)).state,'Booked')
  self.assertEqual(j.one('SELECT state FROM tt_consultation_extension WHERE id=%s',(extension['id'],)).state,'Accepted')
  self.assertEqual(frappe.db.sql('SELECT COUNT(*) FROM tt_journal')[0][0],before)
 def test_wrong_amount_retained_without_false_verification(self):
  result,_=self.book();id=result['payment'];self.assertEqual(self.receipt(id,amount=1)['state'],'ReconciliationRequired')
  frappe.set_user(users['counselor']);self.assertEqual(pay.review(id,'confirm','wrong-amount')['state'],'RefundRequired')
  self.assertNotEqual(j.one('SELECT state FROM tt_appointment WHERE id=%s',(result['id'],)).state,'Booked')
 def test_manual_acceptance_is_distinct_from_receipt(self):
  result,_=self.book();id=result['payment']
  # A deliberate fixture policy, separate from a payment verification fact.
  frappe.db.sql("UPDATE tt_appointment SET confirmation_mode='manual' WHERE id=%s",(result['id'],))
  frappe.set_user(users['counselor']);from tele_tena.api.presentation import respond_to_request
  with self.assertRaises(frappe.ValidationError):respond_to_request(result['id'],'confirm')
  frappe.set_user(users['patient']);self.receipt(id);frappe.set_user(users['counselor']);pay.review(id,'confirm','manual-payment')
  self.assertEqual(j.one('SELECT state FROM tt_appointment WHERE id=%s',(result['id'],)).state,'PendingConfirmation')
  respond_to_request(result['id'],'confirm');self.assertEqual(j.one('SELECT state FROM tt_appointment WHERE id=%s',(result['id'],)).state,'Booked')
 def test_mode_change_blocks_live_holds_and_stale_booking(self):
  result,args=self.book();frappe.set_user('Administrator');c=pay.config()
  with self.assertRaises(frappe.ValidationError):pay.configure('Wallet',c.revision,'Must reject live direct hold')
  frappe.set_user(users['patient']);args=dict(args,retry_key=str(uuid.uuid4()),payment_mode_revision=c.revision-1)
  with self.assertRaises(frappe.ValidationError):j.book(**args)
  self.assertEqual(j.one('SELECT COUNT(*) n FROM tt_direct_payment WHERE appointment=%s',(result['id'],)).n,1)
 def test_cancellation_retains_verified_receipt_and_needs_external_refund(self):
  result,_=self.book();self.receipt(result['payment']);frappe.set_user(users['counselor']);pay.review(result['payment'],'confirm','verified-before-cancel')
  from tele_tena.api.presentation import cancel_appointment
  frappe.set_user(users['patient']);cancel_appointment(result['id'],'Synthetic cancellation, no external transfer')
  self.assertEqual(pay.detail(result['payment'])['state'],'RefundRequired')
  self.assertIsNotNone(pay.detail(result['payment'])['verified_at'])
 def test_payment_reminder_is_idempotent_and_not_confirmation_score(self):
  result,_=self.book();id=result['payment'];frappe.db.sql('UPDATE tt_direct_payment SET created=DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 2 HOUR) WHERE id=%s',(id,))
  pay.process_reminders();pay.process_reminders()
  self.assertEqual(j.one("SELECT COUNT(*) n FROM tt_direct_payment_event WHERE payment=%s AND event='PaymentReminder'",(id,)).n,1)
  self.assertEqual(j.one('SELECT COUNT(*) n FROM tt_confirmation_observation WHERE appointment=%s',(result['id'],)).n,0)
 def test_care_language_claim_is_not_approval(self):
  from tele_tena.api import care_languages as language
  result,args=self.book();frappe.set_user(users['counselor']);language.save_claims([{'code':'en','proficiency':3,'explanation':'Changed claim requires a fresh human decision'}])
  self.assertEqual(language.approved_for(users['counselor']),[])
  self.assertEqual(language.offering_languages(args['offering']),[])
  self.assertEqual(j.one('SELECT state FROM tt_appointment WHERE id=%s',(result['id'],)).state,'PendingConfirmation')
  self.assertTrue(j.rows('SELECT appointment FROM tt_language_appointment_review WHERE appointment=%s',(result['id'],)))
 def test_mode_configuration_is_privileged(self):
  frappe.set_user(users['reviewer'])
  if 'Tele Tena Financial Configuration' not in frappe.get_roles():
   with self.assertRaises(frappe.PermissionError):pay.configure('Offline',pay.config().revision,'Denied reviewer change')
  frappe.set_user(users['patient'])
  with self.assertRaises(frappe.PermissionError):pay.configure('Offline',pay.config().revision,'Denied patient change')
if __name__=='__main__':
 try:unittest.main()
 finally:frappe.db.rollback();frappe.destroy()
