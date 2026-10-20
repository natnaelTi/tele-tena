"""Persisted opt-in schedule/pause/lease regressions; disposable site only."""
from guest_first import *
from datetime import timedelta
from tele_tena.api import open_requests as requests

class SchedulePresence(GuestFirst):
 def setUp(self):
  super().setUp()
  self.item=self.offer();self.clinician=frappe.db.sql('SELECT clinician FROM tt_offering WHERE id=%s',(self.item.id,))[0][0]
  frappe.set_user(self.clinician)
  self.schedule=next(s for s in scheduling.schedules() if s.offering==self.item.id)
  self.args=dict(offering=self.item.id,schedule_name=self.schedule.schedule_name,timezone_name='UTC',consultation_format=self.schedule.consultation_format,confirmation_mode=self.schedule.confirmation_mode,minimum_notice_minutes=60,horizon_days=60,buffer_before=0,buffer_after=0,intervals=[{'weekday':i,'start_local':'00:00','end_local':'23:59'} for i in range(7)],exceptions=[],status='Published',auto_requests=True)
  # Only this isolated transaction is changed; no existing bookings removed.
  scheduling.save_schedule(**self.args)
  frappe.db.sql("UPDATE `tabTele Tena Service` SET immediate_care_enabled=1 WHERE name=%s",(self.item.service,))
  frappe.db.sql('DELETE FROM tt_clinician_request_presence WHERE clinician=%s',(self.clinician,))
 def test_persisted_opt_in_and_manual_pause(self):
  self.assertEqual(next(s for s in scheduling.schedules() if s.offering==self.item.id).auto_requests,1)
  with patch.object(requests,'_has_immediate_capacity',return_value=True),patch.object(requests,'dispatch_open_requests'):
   self.assertTrue(requests.heartbeat_request_presence()['ready'])
   requests.set_request_presence(False)
   for _ in range(2):self.assertFalse(requests.heartbeat_request_presence()['ready'])
   self.assertEqual(requests.request_presence()['control_mode'],'paused')
   self.assertTrue(requests.heartbeat_request_presence(True)['ready'])
   frappe.db.sql('UPDATE tt_clinician_request_presence SET expires_at=DATE_SUB(UTC_TIMESTAMP(),INTERVAL 1 SECOND) WHERE clinician=%s',(self.clinician,))
   self.assertFalse(requests.request_presence()['ready'])
   self.assertTrue(requests.heartbeat_request_presence()['ready'])
 def test_unavailable_date_break_and_outside_hours(self):
  with patch.object(requests,'_has_immediate_capacity',return_value=True),patch.object(requests,'dispatch_open_requests'):
   self.assertTrue(requests.heartbeat_request_presence()['ready'])
   day=requests.now().date().isoformat()
   scheduling.save_schedule(**{**self.args,'exceptions':[{'date':day,'kind':'unavailable'}]})
   self.assertFalse(requests.heartbeat_request_presence()['ready'])
   scheduling.save_schedule(**{**self.args,'exceptions':[{'date':day,'kind':'break','start_local':'00:00','end_local':'23:59'}]})
   self.assertFalse(requests.heartbeat_request_presence()['ready'])
   scheduling.save_schedule(**{**self.args,'auto_requests':False})
   self.assertFalse(requests.heartbeat_request_presence()['ready'])
 def test_capacity_failure_and_recovery_without_setup_error(self):
  with patch.object(requests,'_has_immediate_capacity',return_value=False):
   result=requests.heartbeat_request_presence();self.assertFalse(result['ready']);self.assertIn('no_immediate_capacity',result['reasons'])
  with patch.object(requests,'_has_immediate_capacity',return_value=True),patch.object(requests,'dispatch_open_requests'):
   self.assertTrue(requests.heartbeat_request_presence()['ready'])
 def test_booked_occupancy_and_opened_consultation(self):
  from tele_tena.api import consultations
  frappe.set_user(users['patient']);result,_,_=self.book()
  appointment=frappe.db.sql('SELECT * FROM tt_appointment WHERE id=%s',(result['id'],),as_dict=True)[0]
  frappe.set_user(appointment.clinician)
  with patch.object(requests,'now',return_value=appointment.start+timedelta(minutes=1)):
   self.assertEqual(requests.request_presence()['occupancy'],'occupied')
   # Controlled future join window/token transport; authorization and persisted
   # join command are real. This is not hosted-media evidence.
   with patch.object(consultations,'_window',return_value=True),patch('tele_tena.livekit._credentials',return_value=('wss://local.invalid','test','test')),patch('tele_tena.livekit.participant_token',return_value='local-test-token'):
    consultations.join(appointment.id)
   self.assertEqual(requests.request_presence()['occupancy'],'in_consultation')
  with patch.object(requests,'now',return_value=appointment.end+timedelta(days=1)):
   self.assertIsNone(requests.request_presence()['occupancy'])
 def test_manual_start_remains_available_outside_automatic_hours(self):
  with patch.object(requests,'_automatic_hours',return_value=False),patch.object(requests,'_has_immediate_capacity',return_value=True),patch.object(requests,'dispatch_open_requests'):
   self.assertFalse(requests.heartbeat_request_presence()['ready'])
   self.assertTrue(requests.set_request_presence(True)['ready'])
   self.assertTrue(requests.heartbeat_request_presence()['ready'])
   requests.set_request_presence(False)
   self.assertFalse(requests.heartbeat_request_presence()['ready'])
 def test_real_capacity_and_opt_out(self):
  expected=requests._has_immediate_capacity(self.clinician,[frappe._dict(id=self.item.id)])
  with patch.object(requests,'dispatch_open_requests'):
   result=requests.heartbeat_request_presence()
   self.assertEqual(result['ready'],expected)
   self.assertTrue(result['within_hours'])
   scheduling.save_schedule(**{**self.args,'auto_requests':False})
   self.assertFalse(requests.heartbeat_request_presence()['ready'])
 def test_unauthorized_setting_and_presence(self):
  frappe.set_user(users['patient'])
  with self.assertRaises(frappe.PermissionError):scheduling.save_schedule(**self.args)
  with self.assertRaises(frappe.PermissionError):requests.heartbeat_request_presence(True)
 def test_invalid_schedule_does_not_change_preference(self):
  with self.assertRaises(frappe.ValidationError):scheduling.save_schedule(**{**self.args,'intervals':[{'weekday':0,'start_local':'17:00','end_local':'09:00'}],'auto_requests':False})
  self.assertEqual(next(s for s in scheduling.schedules() if s.offering==self.item.id).auto_requests,1)

if __name__=='__main__':
 try:
  # Inherited guest-first tests retain capacity/conflict/private-data assertions.
  result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(SchedulePresence(name) for name in SchedulePresence.__dict__ if name.startswith('test_')));sys.exit(not result.wasSuccessful())
 finally:frappe.db.rollback();frappe.destroy()
