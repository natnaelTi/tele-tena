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
 def book(self,mode='Offline',key=None,expensive=False):
  c=pay.config()
  if c.mode!=mode:pay.configure(mode,c.revision,'Isolated rollback test only',transition_plan='Preserve all historical wallets and original transaction rules; this rollback fixture does not change existing financial data.')
  frappe.set_user(users['counselor']);pay.save_payee('+251911234567',pay.payee()['revision'],'Synthetic payee for rollback test')
  from tele_tena.api import care_languages
  care_languages.save_claims([{'code':'en','proficiency':3,'explanation':'Explicit synthetic self-assessment for rollback-only test'}])
  frappe.set_user('Administrator');care_languages.decide(users['counselor'],'en','Approved','Synthetic language decision for rollback-only acceptance test')
  frappe.set_user(users['patient']);ids={r.id for r in j.rows('SELECT id FROM tt_offering WHERE clinician=%s AND active=1',(users['counselor'],))};offer=next(x for x in j.discover() if x.id in ids)
  if expensive:
   amount=j.one('SELECT available FROM tt_wallet WHERE patient=%s',(users['patient'],)).available+1
   current=j.one('SELECT * FROM tt_offering WHERE id=%s',(offer.id,));frappe.set_user(users['counselor']);j.publish(current.service,amount,current.minutes,title=current.title,description=current.description,offering_id=current.id,care_languages=['en']);frappe.set_user(users['patient']);offer=next(x for x in j.discover() if x.id==current.id)
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
  self.assertIsNone(j.one('SELECT confirmed_at FROM tt_appointment WHERE id=%s',(result['id'],)).confirmed_at)
  self.assertEqual(j.one("SELECT COUNT(*) n FROM tt_appointment_event WHERE appointment=%s AND event_type IN ('Booked','Confirmed')",(result['id'],)).n,0)
  first=self.receipt(id);self.assertEqual(first['state'],'Submitted');self.assertEqual(self.receipt(id)['history'],first['history']);self.assertEqual(self.receipt(id,'another-tab')['history'],first['history'])
  frappe.set_user(users['therapist'])
  with self.assertRaises(frappe.PermissionError):pay.detail(id)
  with self.assertRaises(frappe.PermissionError):pay.for_appointment(result['id'])
  with self.assertRaises(frappe.PermissionError):pay.detail(str(uuid.uuid4()))
  frappe.set_user(users['counselor']);verified=pay.review(id,'confirm','verify');self.assertEqual(verified['state'],'Verified');pay.review(id,'confirm','verify');pay.review(id,'confirm','other-tab')
  self.assertEqual(j.one("SELECT COUNT(*) n FROM tt_direct_payment_event WHERE payment=%s AND event='ReceiptVerified'",(id,)).n,1)
  with self.assertRaises(frappe.ValidationError):pay.review(id,'confirm','verify','Changed retry details')
  self.assertEqual(frappe.db.sql('SELECT COUNT(*) FROM tt_journal')[0][0],before)
  self.assertEqual(frappe.db.sql('SELECT COUNT(*) FROM tt_direct_payment WHERE id=%s',(id,))[0][0],1)
 def test_late_claim_is_retained_for_reconciliation(self):
  result,_=self.book();id=result['payment'];frappe.db.sql('UPDATE tt_direct_payment SET hold_until=DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 1 MINUTE) WHERE id=%s',(id,));frappe.db.sql("UPDATE tt_appointment SET state='Expired' WHERE id=%s",(result['id'],))
  self.assertEqual(self.receipt(id)['state'],'ReconciliationRequired');frappe.set_user(users['counselor']);self.assertEqual(pay.review(id,'confirm','late')['state'],'RefundRequired')
  pay.refund(id,'reported','reported','External refund claimed by synthetic clinician');frappe.set_user(users['patient']);self.assertEqual(pay.refund(id,'received','received','Synthetic payer confirms receipt')['state'],'RefundConfirmed')
 def test_payment_notifications_and_pending_queue_are_party_scoped(self):
  from tele_tena import notifications
  result,_=self.book();self.receipt(result['payment']);frappe.set_user(users['counselor'])
  self.assertIn(result['payment'],[p.id for p in pay.pending_reviews()['items']])
  links=[n for n in notifications.feed() if n['kind']=='PaymentSubmitted' and n['appointment']==result['id']]
  self.assertEqual(len(links),1);self.assertEqual(links[0]['href'],'/clinician/direct-payments/'+result['payment'])
  from tele_tena.api.presentation import appointment_detail
  self.assertEqual(appointment_detail(result['id'])['direct_payment_id'],result['payment'])
  frappe.set_user(users['therapist']);self.assertNotIn(result['payment'],[p.id for p in pay.pending_reviews()['items']])
  self.assertIsNone(pay.notice_path(result['id'],users['therapist']))
  frappe.set_user(users['patient'])
  with self.assertRaises(frappe.PermissionError):pay.pending_reviews()
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
  self.receipt(accepted['payment'],'extension-proof','SYNTHETICEXT1234');frappe.set_user(users['counselor'])
  from tele_tena import notifications
  self.assertTrue(any(n['kind']=='PaymentSubmitted' and n['href']=='/clinician/direct-payments/'+accepted['payment'] for n in notifications.feed()))
  pay.review(accepted['payment'],'confirm','extension-verify')
  self.assertEqual(j.one('SELECT state FROM tt_appointment WHERE id=%s',(app.id,)).state,'Booked')
  self.assertEqual(j.one('SELECT state FROM tt_consultation_extension WHERE id=%s',(extension['id'],)).state,'Accepted')
  self.assertEqual(frappe.db.sql('SELECT COUNT(*) FROM tt_journal')[0][0],before)
 def test_wrong_amount_retained_without_false_verification(self):
  result,_=self.book();id=result['payment'];self.assertEqual(self.receipt(id,amount=1)['state'],'ReconciliationRequired')
  self.assertEqual(pay.ledger()['totals_minor']['ReconciliationRequired'],1)
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
 def test_configuration_rejections_explain_fields_without_mutation(self):
  before=dict(pay.config());events=j.one("SELECT COUNT(*) n FROM tt_audit WHERE action='PaymentModeChanged'").n
  cases=[({'hold_minutes':0},'payment_hold_invalid'),({'verification_hours':0},'payment_verification_window_invalid'),({'verification_hours':'1.5'},'payment_verification_window_invalid'),({'reason':''},'payment_change_reason_required'),({'transition_plan':'x'*2001},'payment_transition_plan_invalid')]
  for values,code in cases:
   args={'mode':before['mode'],'revision':before['revision'],'reason':'Isolated configuration validation regression',**values}
   with self.assertRaises(frappe.ValidationError):pay.configure(**args)
   self.assertEqual(frappe.local.response['tele_tena_error'],code)
   self.assertEqual(dict(pay.config()),before)
  self.assertEqual(j.one("SELECT COUNT(*) n FROM tt_audit WHERE action='PaymentModeChanged'").n,events)
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
 def test_retained_wallet_shortfall_does_not_create_direct_payment(self):
  before=j.one('SELECT COUNT(*) n FROM tt_direct_payment').n
  with self.assertRaises(frappe.ValidationError):self.book('Wallet',expensive=True)
  self.assertEqual(j.one('SELECT COUNT(*) n FROM tt_direct_payment').n,before)
 def test_reference_priority_is_stable_and_never_pins_nonmatching_entries(self):
  from tele_tena.api import professional_directory as directory
  frappe.set_user(users['counselor']);items=directory.search('issuer')['items'];priorities=[x for x in items if x.priority_et]
  self.assertTrue(priorities);self.assertEqual([x.id for x in items], [x.id for x in directory.search('issuer')['items']]);self.assertEqual(items[:len(priorities)],priorities)
  self.assertFalse(any(x.priority_et for x in directory.search('issuer',search='Harvard')['items']))
  with self.assertRaises(frappe.PermissionError):directory.set_priority(priorities[0].id,False,'https://ror.org/','Not an authorized navigation reviewer')
 def test_finalization_does_not_credit_direct_payment_again(self):
  from tele_tena.api import consultations,presentation
  from unittest.mock import patch
  result,_=self.book();id=result['payment'];self.receipt(id);frappe.set_user(users['counselor']);pay.review(id,'confirm','verify-before-call')
  if j.one('SELECT state FROM tt_appointment WHERE id=%s',(result['id'],)).state=='PendingConfirmation':presentation.respond_to_request(result['id'],'confirm')
  with patch('tele_tena.api.consultations._window',return_value=True),patch('tele_tena.livekit._credentials',return_value=('wss://test.invalid','test','test')),patch('tele_tena.livekit.participant_token',return_value='private-fake-provider-token'):
   consultations.join(result['id'])
  # Preserve this test's outer rollback while exercising unchanged End logic;
  # room I/O and commit durability are inherited hosted-call evidence, not claimed here.
  with patch.object(frappe.db,'commit'),patch('tele_tena.livekit.close_room'):
   consultations.end(result['id'])
  before=j.one('SELECT COUNT(*) n FROM tt_journal').n
  presentation.save_note_draft(result['id'],'Private synthetic note for isolation assertion','Shared synthetic follow-up',False)
  first=presentation.finalize_consultation(result['id'],True,False);again=presentation.finalize_consultation(result['id'],True,False)
  self.assertEqual(first['revision'],again['revision']);self.assertTrue(again['idempotent']);self.assertEqual(again['earning_state'],'DirectReceiptRecorded')
  self.assertEqual(j.one('SELECT COUNT(*) n FROM tt_earning WHERE appointment=%s',(result['id'],)).n,0)
  self.assertEqual(j.one('SELECT COUNT(*) n FROM tt_journal').n,before)
  frappe.set_user(users['patient']);view=presentation.appointment_detail(result['id']);self.assertNotIn('Private synthetic note for isolation assertion',json.dumps(view,default=str));self.assertEqual(view['status'],'Completed')
 def test_history_requires_a_transition_plan_without_converting_wallets(self):
  self.assertGreater(pay.transition_obligations()['legacy_wallet_holds'],0,'Retained compatibility fixture must include historical holds')
  before=frappe.db.sql('SELECT * FROM tt_wallet ORDER BY patient');count=j.one('SELECT COUNT(*) n FROM tt_journal').n;c=pay.config()
  with self.assertRaises(frappe.ValidationError):pay.configure('Offline',c.revision,'No transition plan supplied',transition_plan='None')
  self.assertEqual(frappe.local.response['tele_tena_error'],'payment_transition_plan_required')
  pay.configure('Offline',c.revision,'Explicit isolated cutover test',transition_plan='Keep every historical wallet transaction under its original rules and retain authorized history, cancellation, dispute and release processing. No money is converted.')
  self.assertEqual(before,frappe.db.sql('SELECT * FROM tt_wallet ORDER BY patient'));self.assertEqual(count,j.one('SELECT COUNT(*) n FROM tt_journal').n)
 def test_couples_payment_keeps_payer_consent_and_language_separate(self):
  from tele_tena.api import couples,care_languages,presentation
  pay.configure('Offline',pay.config().revision,'Isolated couples payment test',transition_plan='Preserve every historical wallet and original booking policy. Only new synthetic bookings use direct payment in this rollback.')
  offer=j.one("SELECT o.* FROM tt_offering o JOIN `tabTele Tena Service` s ON s.name=o.service WHERE s.participant_structure='couple' AND o.active=1 LIMIT 1")
  frappe.set_user(offer.clinician);care_languages.save_claims([{'code':'en','proficiency':3,'explanation':'Synthetic explicit couples language claim'}]);pay.save_payee('+251911234567',pay.payee()['revision'],'Synthetic receiving number for rollback couples test')
  frappe.set_user('Administrator');care_languages.decide(offer.clinician,'en','Approved','Synthetic individual language decision, not clinical verification')
  payer=users['couple_payer'];partner=users['couple_partner'];frappe.set_user(payer)
  from datetime import datetime,timedelta,timezone
  cal=scheduling.calendar(offer.id,(datetime.now(timezone.utc)+timedelta(days=2)).date().isoformat(),days=7,display_timezone='Africa/Addis_Ababa');start=next(slot['start'] for day in cal['days'] for slot in day['slots']);sharing={'name':False,'history':False};disclosure=j.disclosure(j.profile('patient'),'',sharing)
  invitation=couples.invite(offer.id,start,'',sharing,disclosure,True,'couples-payment-language',care_language='en')
  frappe.set_user(partner);other_disclosure=j.disclosure(j.profile('patient'),'',sharing);couples.consent(invitation['token'],'',sharing,other_disclosure,True)
  with self.assertRaises((frappe.PermissionError,frappe.ValidationError)):couples.confirm(invitation['id'],expected_payment_mode='Offline',payment_mode_revision=pay.config().revision)
  frappe.set_user(payer);before=j.one('SELECT COUNT(*) n FROM tt_journal').n;booking=couples.confirm(invitation['id'],expected_payment_mode='Offline',payment_mode_revision=pay.config().revision);self.assertEqual(couples.confirm(invitation['id'])['payment'],booking['payment'])
  self.assertEqual(json.loads(j.one('SELECT policy_snapshot FROM tt_appointment WHERE id=%s',(booking['id'],)).policy_snapshot)['care_language'],'en')
  self.receipt(booking['payment']);receipt_id=next(x.evidence for x in pay.detail(booking['payment'])['history'] if x.evidence)
  frappe.set_user(partner)
  with self.assertRaises(frappe.PermissionError):pay.detail(booking['payment'])
  with self.assertRaises(frappe.PermissionError):pay.receipt(receipt_id)
  frappe.set_user(offer.clinician);pay.review(booking['payment'],'confirm','couples-payment-review')
  if j.one('SELECT state FROM tt_appointment WHERE id=%s',(booking['id'],)).state=='PendingConfirmation':presentation.respond_to_request(booking['id'],'confirm')
  self.assertEqual(j.one("SELECT COUNT(*) n FROM tt_direct_payment WHERE appointment=%s AND reference_type='Appointment'",(booking['id'],)).n,1)
  self.assertEqual(j.one('SELECT COUNT(*) n FROM tt_journal').n,before)
  frappe.set_user(partner);self.assertTrue(any(x.id==booking['id'] for x in j.appointments()))
 def test_mode_configuration_is_privileged(self):
  frappe.set_user(users['reviewer'])
  if 'Tele Tena Financial Configuration' not in frappe.get_roles():
   with self.assertRaises(frappe.PermissionError):pay.configure('Offline',pay.config().revision,'Denied reviewer change')
  frappe.set_user(users['patient'])
  with self.assertRaises(frappe.PermissionError):pay.configure('Offline',pay.config().revision,'Denied patient change')
if __name__=='__main__':
 try:unittest.main()
 finally:frappe.db.rollback();frappe.destroy()
