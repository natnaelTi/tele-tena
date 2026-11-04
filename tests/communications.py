"""Real Frappe16 transactional event coverage; all outbound transports mocked."""
from direct_payments import *
from unittest.mock import patch
from datetime import datetime,timezone,timedelta
from tele_tena import communications as comm,booking_notifications as notices,notifications,email_delivery
from tele_tena.api import contact_auth,care_languages,vetting

class Communications(DirectPayment):
 def setUp(self):
  super().setUp();self.enqueue=patch('tele_tena.communications._enqueue');self.enqueue.start();self.addCleanup(self.enqueue.stop)
 def contacts(self,user):
  for channel,contact in [('email','notice-'+uuid.uuid4().hex+'@offline-test.invalid'),('phone','+251900000'+str(uuid.uuid4().int)[:3])]:
   frappe.db.sql('INSERT INTO tt_contact_identity VALUES (%s,%s,%s,UTC_TIMESTAMP(6))',(channel,contact,user))
 def deliveries(self,key):return j.rows('SELECT * FROM tt_booking_notice WHERE event_key=%s',(key,))
 def test_application_ack_three_channels_and_owner_only_status(self):
  user=users['applicant'];frappe.db.sql('UPDATE tt_application SET submitted_at=UTC_TIMESTAMP(6),status=\'Pending\' WHERE user=%s',(user,))
  comm.application_submitted(user);comm.application_submitted(user)
  found=j.rows("SELECT * FROM tt_booking_notice WHERE user=%s AND event='ApplicationSubmitted'",(user,));self.assertEqual(len(found),3)
  self.assertIn('24 hours',comm.describe(found[0])['body'])
  frappe.set_user(user);feed=notifications.feed();item=next(n for n in feed if n['kind']=='ApplicationSubmitted');self.assertEqual(item['href'],'/clinician/account');self.assertNotIn('@',json.dumps(item))
  notifications.mark_read(item['id'],'booking');self.assertTrue(next(n for n in notifications.feed() if n['id']==item['id'])['read'])
  frappe.set_user(users['patient']);self.assertFalse(any(n['id']==item['id'] for n in notifications.feed()))
  with self.assertRaises(frappe.PermissionError):notifications.mark_read(item['id'],'booking')
 def test_human_general_decision_ack_is_idempotent(self):
  user=users['applicant'];frappe.set_user(users['reviewer']);j.review(user,'Approved');j.review(user,'Approved')
  self.assertEqual(len(j.rows("SELECT id FROM tt_booking_notice WHERE user=%s AND event='ApplicationApproved'",(user,))),3)
 def test_application_24_hour_update_is_once_and_only_for_notified_submissions(self):
  user=users['applicant'];frappe.db.sql("UPDATE tt_application SET status='Pending',submitted_at=UTC_TIMESTAMP(6)-INTERVAL 25 HOUR WHERE user=%s",(user,))
  comm.application_submitted(user);comm.application_updates();comm.application_updates()
  self.assertEqual(len(j.rows("SELECT id FROM tt_booking_notice WHERE user=%s AND event='ApplicationReviewUpdate'",(user,))),3)
 def test_nonappointment_delivery_and_failure_claims(self):
  user=users['applicant'];self.contacts(user);frappe.set_user(user);notices.save_preferences(True,True)
  ref=j.one('SELECT public_id FROM tt_profile WHERE user=%s',(user,)).public_id
  comm.queue(user,'ApplicationSubmitted','application',ref,'notification-transport-test')
  selected=self.deliveries('notification-transport-test');ids={n.id for n in selected};original=notices.rows
  def scoped(query,args=()):
   value=original(query,args);return [n for n in value if n.id in ids] if query.startswith('SELECT id FROM tt_booking_notice WHERE state=') else value
  from tele_tena.sms import SMSUncertain
  with patch.object(notices,'rows',side_effect=scoped),patch.object(frappe.db,'commit'),patch('tele_tena.email_delivery.send_notice') as email,patch('tele_tena.sms.send_notice',side_effect=SMSUncertain('provider_outcome_unknown')) as sms,patch('tele_tena.review.phone_enabled',return_value=True),patch('tele_tena.api.phone_auth.reserve_sms_budget',return_value=True):
   notices.dispatch();notices.dispatch();self.assertEqual(email.call_count,1);self.assertEqual(sms.call_count,1)
   text=email.call_args.args[1];self.assertNotIn('@',text);self.assertIn('/teletena/clinician/account',text)
  status={n.channel:n.state for n in self.deliveries('notification-transport-test')};self.assertEqual(status,{'in_app':'Available','email':'ProviderAccepted','sms':'Unknown'})
  unknown=next(n for n in self.deliveries('notification-transport-test') if n.channel=='sms')
  with self.assertRaises(frappe.PermissionError):notices.retry(unknown.id)
 def test_utc_send_gate_ignores_site_clock_offset(self):
  result,_=self.book();id=result['payment'];self.receipt(id);frappe.set_user(users['counselor']);pay.review(id,'confirm','utc-send-gate')
  app=result['id']
  for who in (users['patient'],users['counselor']):
   frappe.set_user(who);notices.save_preferences(True,True)
   frappe.db.sql('DELETE FROM tt_contact_identity WHERE user=%s',(who,));self.contacts(who)
  frappe.db.sql('UPDATE tt_appointment SET start=UTC_TIMESTAMP(6)+INTERVAL 4 MINUTE,end=UTC_TIMESTAMP(6)+INTERVAL 34 MINUTE WHERE id=%s',(app,));notices.process_reminders()
  ids={n.id for n in j.rows("SELECT id FROM tt_booking_notice WHERE appointment=%s AND event='FiveMinuteReminder'",(app,))};original=notices.rows
  def scoped(query,args=()):
   value=original(query,args);return [n for n in value if n.id in ids] if query.startswith('SELECT id FROM tt_booking_notice WHERE state=') else value
  with patch.object(notices,'rows',side_effect=scoped),patch.object(frappe.db,'commit'),patch('frappe.utils.now_datetime',return_value=datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(hours=9)),patch('tele_tena.email_delivery.send_notice') as email,patch('tele_tena.sms.send_notice'),patch('tele_tena.review.phone_enabled',return_value=True),patch('tele_tena.api.phone_auth.reserve_sms_budget',return_value=True):
   notices.dispatch();self.assertEqual(email.call_count,2)
  self.assertEqual(len(j.rows("SELECT id FROM tt_booking_notice WHERE appointment=%s AND event='FiveMinuteReminder' AND state='ProviderAccepted'",(app,))),4)
 def test_five_minute_reminder_occurrence_and_retry_safety(self):
  result,_=self.book();id=result['payment'];self.receipt(id);frappe.set_user(users['counselor']);pay.review(id,'confirm','five-minute-test')
  app=result['id'];frappe.db.sql('UPDATE tt_appointment SET start=UTC_TIMESTAMP(6)+INTERVAL 10 MINUTE,end=UTC_TIMESTAMP(6)+INTERVAL 40 MINUTE WHERE id=%s',(app,));notices.process_reminders()
  self.assertFalse(j.rows("SELECT id FROM tt_booking_notice WHERE appointment=%s AND event='FiveMinuteReminder'",(app,)))
  frappe.db.sql('UPDATE tt_appointment SET start=UTC_TIMESTAMP(6)+INTERVAL 4 MINUTE,end=UTC_TIMESTAMP(6)+INTERVAL 34 MINUTE WHERE id=%s',(app,));notices.process_reminders();notices.process_reminders()
  found=j.rows("SELECT channel,user FROM tt_booking_notice WHERE appointment=%s AND event='FiveMinuteReminder'",(app,));self.assertEqual(len(found),4)
  self.assertEqual({x.user for x in found},{users['patient'],users['counselor']})
  self.assertEqual(len(j.rows("SELECT id FROM tt_user_notification WHERE appointment=%s AND kind='FiveMinuteReminder'",(app,))),2)
 def test_branded_multipart_email_escapes_and_keeps_plaintext(self):
  from tele_tena.email_templates import NoticeText,secure_link
  body=NoticeText('Neutral update <script>alert(1)</script>',title='Application Received',link=secure_link('/clinician/account'))
  with patch.object(email_delivery,'configuration',return_value={'sender':'review@offline-test.invalid'}),patch.object(email_delivery,'_send') as send:
   email_delivery.send_notice('recipient@offline-test.invalid',body)
  message=send.call_args.args[0];self.assertEqual(message.get_content_type(),'multipart/alternative')
  self.assertIn('Neutral update',message.get_body(preferencelist=('plain',)).get_content())
  html=message.get_body(preferencelist=('html',)).get_content();self.assertIn('TeleTena',html);self.assertIn('ቴሌ ጤና',html);self.assertNotIn('<script>',html);self.assertIn('&lt;script&gt;',html);self.assertNotIn('https://fonts.',html)
 def test_request_offer_notifications_are_private_and_retry_safe(self):
  from tele_tena.api import open_requests as requests
  result,args=self.book();first_offer=j.one('SELECT * FROM tt_offering WHERE clinician=%s AND service=%s AND active=1',(users['counselor'],'tt-demo-mvp-v2-counseling'))
  second=users['therapist'];frappe.set_user(second);care_languages.save_claims([{'code':'en','proficiency':3,'explanation':'Fictional request-notification self-assessment.'}]);pay.save_payee('+251900000002',pay.payee()['revision'],'Fictional rollback-only receiving number.')
  frappe.set_user(users['reviewer']);care_languages.decide(second,'en','Approved','Fictional request notification review only.')
  other=j.one('SELECT id FROM tt_offering WHERE clinician=%s AND service=%s AND active=1',(second,first_offer.service))
  from datetime import datetime,timezone
  start_date=(datetime.now(timezone.utc)+timedelta(days=7)).date().isoformat()
  frappe.set_user(users['patient'])
  a={x['start'] for d in scheduling.calendar(first_offer.id,start_date,days=14)['days'] for x in d['slots']}
  b={x['start'] for d in scheduling.calendar(other.id,start_date,days=14)['days'] for x in d['slots']}
  common=sorted(a&b);self.assertTrue(common);slot=common[0]
  frappe.set_user(users['patient']);request=requests.publish_request(first_offer.service,'PRIVATE REQUEST SENTINEL','scheduled','en','video',{'name':False,'history':False},uuid.uuid4().hex,earliest_start=slot,latest_start=slot)
  rid=request['id'];new=self.deliveries('new-request:'+rid);self.assertTrue({users['counselor'],second}<={r.user for r in new});self.assertTrue(all(len([n for n in new if n.user==who])==3 for who in (users['counselor'],second)))
  offers=[]
  for who,offering in [(users['counselor'],first_offer.id),(second,other.id)]:
   frappe.set_user(who);offer=requests.submit_offer(rid,offering,slot);self.assertTrue(requests.submit_offer(rid,offering,slot)['idempotent']);offers.append(offer['id']);self.assertEqual(len(self.deliveries('offer-received:'+offer['id'])),3)
  frappe.set_user(users['patient']);requests.respond_offer(rid,offers[0],'decline');self.assertEqual(len(self.deliveries('offer-declined:'+offers[0])),3)
  frappe.set_user(users['counselor']);replacement=requests.submit_offer(rid,first_offer.id,slot)['id'];frappe.set_user(users['patient'])
  values={'expected_disclosure':json.loads(j.one('SELECT disclosure_snapshot FROM tt_open_request WHERE id=%s',(rid,)).disclosure_snapshot),'expected_payment_mode':'Offline','payment_mode_revision':pay.config().revision}
  chosen=requests.respond_offer(rid,offers[1],'accept',**values);self.assertTrue(requests.respond_offer(rid,offers[1],'accept',**values)['idempotent'])
  self.assertEqual(len(self.deliveries('offer-accepted:'+offers[1])),2);self.assertEqual(len(self.deliveries('offer-declined:'+replacement)),3)
  for record in j.rows('SELECT * FROM tt_booking_notice WHERE event_key IS NOT NULL'):
   message=comm.describe(record)
   if message:self.assertNotIn('PRIVATE REQUEST SENTINEL',json.dumps(message))
 def test_demo_catalog_ready_twice_and_no_bulk_delivery_or_password_changes(self):
  from tele_tena import demo_readiness as ready,demo_dataset
  import tempfile
  import importlib.util
  spec=importlib.util.spec_from_file_location('release_preservation_tool',ROOT/'scripts/release_preservation.py');tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool);capture=tool.capture
  original=json.loads(demo_dataset.paths()[0].read_text());original['site']=SITE
  before={table:j.rows('SELECT * FROM `'+table+'`') for table in ('__Auth','tt_wallet','tt_journal','tt_journal_line','tt_earning','tt_payout')}
  with tempfile.TemporaryDirectory() as temp:
   marker=Path(temp)/'records.json';marker.write_text(json.dumps(original));accounts=demo_dataset.paths()[1]
   with patch.object(demo_dataset,'paths',return_value=(marker,accounts)),patch.object(frappe.db,'commit'),patch('tele_tena.demo_readiness.write_private'):
    first=ready.setup(False);snapshot=capture(frappe,BENCH/'sites'/SITE);second=ready.setup(False);after=capture(frappe,BENCH/'sites'/SITE)
   self.assertEqual(first,second)
   for table in snapshot['tables']:
    self.assertEqual(snapshot['tables'][table],after['tables'][table],table+' changed on second readiness run')
  self.assertEqual(first['ready_service_count'],10)
  for key,role,price,minutes in ready.SERVICES:
   self.assertTrue(j.service_scope_is_current(users[role],key));self.assertTrue(j.rows('SELECT o.id FROM tt_offering o JOIN tt_schedule s ON s.offering=o.id WHERE o.clinician=%s AND o.service=%s AND o.active=1 AND s.status=\'Published\'',(users[role],key)))
  for table,values in before.items():self.assertEqual(values,j.rows('SELECT * FROM `'+table+'`'),table+' changed')
  self.assertFalse(j.rows("SELECT id FROM tt_booking_notice WHERE state='Pending' AND event_key LIKE 'scope-decision:%%'"))

if __name__=='__main__':
 try:unittest.main(defaultTest='Communications')
 finally:frappe.db.rollback();frappe.destroy()
