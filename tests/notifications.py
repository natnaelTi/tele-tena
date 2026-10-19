"""Notification policy, privacy, delivery-claim and response regressions; no live I/O."""
from guest_first import *
from tele_tena import notifications
from tele_tena.api import presentation
from datetime import timedelta
from tele_tena.sms import SMSUncertain

class Notifications(GuestFirst):
 def manual(self):
  offer=self.offer();clinician=frappe.db.sql('SELECT clinician FROM tt_offering WHERE id=%s',(offer.id,))[0][0]
  frappe.set_user(clinician);schedule=next(s for s in scheduling.schedules() if s.offering==offer.id)
  scheduling.save_schedule(offer.id,schedule.schedule_name,schedule.timezone,schedule.consultation_format,'manual',schedule.minimum_notice_minutes,schedule.horizon_days,schedule.buffer_before,schedule.buffer_after,schedule.intervals,schedule.exceptions,'Published')
  frappe.set_user(users['patient']);result,_,_=self.book()
  app=frappe.db.sql('SELECT * FROM tt_appointment WHERE id=%s',(result['id'],),as_dict=True)[0]
  self.assertEqual(app.state,'PendingConfirmation');return app
 def test_manual_policy_snapshot_and_reminder_once(self):
  app=self.manual();policy=json.loads(app.policy_snapshot)
  self.assertEqual(policy['notifications']['confirmation_reminder_seconds'],180)
  self.assertLessEqual(app.expires_at,app.start)
  self.assertEqual(frappe.db.sql('SELECT COUNT(*) FROM tt_confirmation_observation WHERE appointment=%s',(app.id,))[0][0],1)
  frappe.db.sql('UPDATE tt_confirmation_observation SET requested_at=UTC_TIMESTAMP(6)-INTERVAL 181 SECOND WHERE appointment=%s',(app.id,))
  booking_notifications.process_reminders();booking_notifications.process_reminders()
  reminders=frappe.db.sql("SELECT user,channel FROM tt_booking_notice WHERE appointment=%s AND event='ConfirmationReminder'",(app.id,),as_dict=True)
  self.assertEqual([(r.user,r.channel) for r in reminders],[(app.clinician,'email')])
  frappe.set_user(app.clinician);self.assertEqual(len([n for n in notifications.feed() if n['kind']=='ConfirmationReminder']),1)
 def test_response_stops_reminder_and_is_idempotent(self):
  app=self.manual();frappe.set_user(app.clinician);notifications.confirmation_presented(app.id)
  presentation.respond_to_request(app.id,'confirm');presentation.respond_to_request(app.id,'confirm')
  frappe.db.sql('UPDATE tt_confirmation_observation SET requested_at=UTC_TIMESTAMP(6)-INTERVAL 181 SECOND WHERE appointment=%s',(app.id,))
  booking_notifications.process_reminders()
  self.assertFalse(frappe.db.sql("SELECT id FROM tt_booking_notice WHERE appointment=%s AND event='ConfirmationReminder'",(app.id,)))
  observation=frappe.db.sql('SELECT response FROM tt_confirmation_observation WHERE appointment=%s',(app.id,))[0][0]
  self.assertEqual(observation,'Confirmed');self.assertEqual(notifications.confirmation_metric(app.clinician)['sample_count'],1)
  self.assertEqual(frappe.db.sql("SELECT COUNT(*) FROM tt_journal WHERE event_ref=%s",('booking:'+app.id,))[0][0],1)
 def test_expiry_releases_once_and_records_observed_nonresponse(self):
  app=self.manual();frappe.set_user(app.clinician);notifications.confirmation_presented(app.id)
  frappe.db.sql('UPDATE tt_appointment SET expires_at=UTC_TIMESTAMP(6)-INTERVAL 1 SECOND WHERE id=%s',(app.id,))
  with patch.object(frappe.db,'commit'):
   presentation.expire_pending_appointments();presentation.expire_pending_appointments()
  self.assertEqual(frappe.db.sql('SELECT state FROM tt_appointment WHERE id=%s',(app.id,))[0][0],'Expired')
  self.assertEqual(frappe.db.sql('SELECT COUNT(*) FROM tt_journal WHERE event_ref=%s',('release:'+app.id,))[0][0],1)
  self.assertEqual(notifications.confirmation_metric(app.clinician)['expired_count'],1)
  frappe.set_user(app.patient);self.assertEqual(len([n for n in notifications.feed() if n['kind']=='Expired' and n['appointment']==app.id]),1)
 def test_unseen_expiry_is_not_a_clinician_penalty(self):
  app=self.manual();frappe.db.sql('UPDATE tt_appointment SET expires_at=UTC_TIMESTAMP(6)-INTERVAL 1 SECOND WHERE id=%s',(app.id,))
  with patch.object(frappe.db,'commit'):presentation.expire_pending_appointments()
  self.assertEqual(notifications.confirmation_metric(app.clinician)['sample_count'],0)
 def test_owner_read_privacy_and_system_deduplication(self):
  app=self.manual();notifications.emit(app.patient,'private-system-test','SystemUpdate');notifications.emit(app.patient,'private-system-test','SystemUpdate')
  feed=notifications.feed();notice=next(n for n in feed if n['kind']=='SystemUpdate');self.assertEqual(len([n for n in feed if n['kind']=='SystemUpdate']),1)
  self.assertEqual(set(notice),{'id','source','kind','title','category','appointment','created','read'})
  notifications.mark_read(notice['id'],notice['source']);self.assertTrue(next(n for n in notifications.feed() if n['id']==notice['id'])['read'])
  frappe.set_user(users['reviewer']);self.assertFalse(any(n['id']==notice['id'] for n in notifications.feed()))
  with self.assertRaises(frappe.PermissionError):notifications.mark_read(notice['id'],notice['source'])
  with self.assertRaises(frappe.PermissionError):notifications.confirmation_presented(app.id)
  frappe.set_user('Guest')
  with self.assertRaises(frappe.PermissionError):notifications.feed()
 def test_confirmation_email_sms_and_uncertain_outcome(self):
  # Isolate the transport queue inside this rolled-back fixture transaction.
  frappe.db.sql("DELETE FROM tt_booking_notice WHERE channel<>'in_app'")
  result,_,_=self.book();app=frappe.db.sql('SELECT * FROM tt_appointment WHERE id=%s',(result['id'],),as_dict=True)[0]
  frappe.db.sql("DELETE FROM tt_booking_notice WHERE channel<>'in_app'")
  booking_notifications.save_preferences(True,True)
  for channel,contact in [('email','fictional-receipt@example.invalid'),('phone','+251900000123')]:
   frappe.db.sql('INSERT INTO tt_contact_identity (channel,contact,user,verified_at) VALUES (%s,%s,%s,UTC_TIMESTAMP(6))',(channel,contact,app.patient))
  booking_notifications.queue_external(app.id,'Confirmed',[app.patient])
  with patch.object(frappe.db,'commit'),patch('tele_tena.review.phone_enabled',return_value=True),patch('tele_tena.api.phone_auth.reserve_sms_budget',return_value=True),patch('tele_tena.email_delivery.send_notice') as email,patch('tele_tena.sms.send_notice',side_effect=SMSUncertain('provider_outcome_unknown')) as sms:
   booking_notifications.dispatch();booking_notifications.dispatch()
   self.assertEqual(email.call_count,1);self.assertEqual(sms.call_count,1)
   body=email.call_args.args[1];self.assertIn('reserved',body);self.assertIn('No external payment collected',body);self.assertNotIn('Fictional consent test',body)
  states=dict(frappe.db.sql('SELECT channel,state FROM tt_booking_notice WHERE appointment=%s AND user=%s AND channel<>%s',(app.id,app.patient,'in_app')))
  self.assertEqual(states,{'email':'ProviderAccepted','sms':'Unknown'})
  uncertain=frappe.db.sql("SELECT id FROM tt_booking_notice WHERE appointment=%s AND user=%s AND channel='sms'",(app.id,app.patient))[0][0]
  with self.assertRaises(frappe.PermissionError):booking_notifications.retry(uncertain)
 def test_optout_is_preserved(self):
  app=self.manual();booking_notifications.queue_external(app.id,'ConfirmationReminder',[app.patient],('email',))
  self.assertEqual(frappe.db.sql("SELECT state FROM tt_booking_notice WHERE appointment=%s AND user=%s AND event='ConfirmationReminder'",(app.id,app.patient))[0][0],'Suppressed')
 def test_post_consultation_notices_have_no_clinical_text(self):
  from tele_tena.api import consultations
  result,_,_=self.book();id=result['id'];app=frappe.db.sql('SELECT * FROM tt_appointment WHERE id=%s',(id,),as_dict=True)[0]
  frappe.set_user(app.clinician)
  with patch.object(consultations,'_window',return_value=True),patch('tele_tena.livekit._credentials',return_value=('wss://local.invalid','test','test')),patch('tele_tena.livekit.participant_token',return_value='test-token'):
   consultations.join(id)
  with patch('tele_tena.livekit.close_room'),patch.object(frappe.db,'commit'):consultations.end(id)
  presentation.save_note_draft(id,'Fictional private sentinel','Fictional shared sentinel')
  presentation.finalize_consultation(id,True);presentation.finalize_consultation(id,True)
  frappe.set_user(app.patient);feed=[n for n in notifications.feed() if n['appointment']==id]
  self.assertEqual(len([n for n in feed if n['kind']=='SummaryReady']),1)
  self.assertNotIn('sentinel',json.dumps(feed));self.assertEqual(frappe.db.sql('SELECT COUNT(*) FROM tt_earning WHERE appointment=%s',(id,))[0][0],1)

if __name__=='__main__':
 try:
  result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(Notifications(name) for name in Notifications.__dict__ if name.startswith('test_')));sys.exit(not result.wasSuccessful())
 finally:frappe.db.rollback();frappe.destroy()
