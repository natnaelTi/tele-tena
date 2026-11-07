"""Real Frappe16, rollback-only native operations acceptance. No live providers."""
from direct_payments import *
import tempfile
from unittest.mock import patch
from datetime import datetime,timedelta
from tele_tena.api import operations as ops
from tele_tena.operations import runtime as rt,contract,support,reports,archive,storage,providers,jobs
from tele_tena.patches.v1_53_operations import execute
execute();frappe.db.commit()
class Operations(unittest.TestCase):
 def setUp(self):
  frappe.set_user(users['patient']);frappe.local.lang='en';frappe.db.savepoint('operations')
  self.tmp=tempfile.TemporaryDirectory();self.storage=patch('tele_tena.operations.storage.root',return_value=Path(self.tmp.name));self.storage.start();self.wake=patch('tele_tena.communications.wake_dispatch');self.wake.start()
 def tearDown(self):
  frappe.db.rollback(save_point='operations');self.storage.stop();self.wake.stop();self.tmp.cleanup();frappe.set_user('Administrator')
 def submit(self,key='support-test',attachment=None):return ops.support_submit('Technical','PRIVATE SUPPORT CANARY: please help with layout.',False,key,{'route':'/patient/consultations/private-id?secret=CANARY'},attachment)
 def test_fresh_site_private_pseudonym_key_without_framework_mutation(self):
  before=frappe.conf.get('encryption_key')
  with patch.dict(frappe.conf,{'encryption_key':None}):
   first=rt.pseudonym('synthetic-owner');self.assertEqual(first,rt.pseudonym('synthetic-owner'));self.assertNotEqual(first,rt.pseudonym('other-owner'))
   key=Path(self.tmp.name)/'actor-hmac.key';self.assertEqual(key.stat().st_mode&0o777,0o600);self.assertEqual(len(key.read_text()),64);self.assertIsNone(frappe.conf.get('encryption_key'))
  self.assertEqual(frappe.conf.get('encryption_key'),before)
 def test_reviewer_super_admin_and_other_role_denial(self):
  for u in ('Guest',users['patient'],users['counselor']):
   frappe.set_user(u)
   for fn in (ops.overview,ops.configuration,ops.health,ops.archive_list,ops.reports_list):
    with self.assertRaises(frappe.PermissionError):fn()
  frappe.set_user(users['reviewer']);self.assertIn('support_open',ops.overview());self.assertIn('config',ops.configuration())
 def test_event_allowlist_source_dedupe_and_no_private_properties(self):
  self.assertTrue(rt.record('booking.created','opaque-outcome',{'outcome':'pending'}));self.assertFalse(rt.record('booking.created','opaque-outcome',{'outcome':'pending'}))
  for props in ({'clinical':'SECRET'},{'error_code':'PRIVATE NOTE'},{'step':'password=secret'}):
   with self.assertRaises(ValueError):rt.record('booking.created','unsafe',props)
  with self.assertRaises(ValueError):rt.record('booking.created','fake-click',{},'browser')
  self.assertEqual(contract.route_template('/teletena/patient/consultations/private?token=SECRET'),'/patient/consultations/:ref')
 def test_support_retry_owner_internal_reply_isolation_and_no_sensitive_telemetry(self):
  r=self.submit();self.assertEqual(self.submit()['id'],r['id']);self.assertEqual(r['context']['route'],'/patient/consultations/:ref')
  frappe.set_user(users['counselor'])
  with self.assertRaises(frappe.PermissionError):ops.support_detail(r['id'])
  frappe.set_user(users['reviewer']);ops.support_reply(r['id'],'INTERNAL CANARY','Internal','internal-key','Triaged');ops.support_reply(r['id'],'We are investigating.','User','reply-key','In Progress')
  frappe.set_user(users['patient']);d=ops.support_detail(r['id']);self.assertEqual(len(d['replies']),1);self.assertNotIn('INTERNAL CANARY',json.dumps(d,default=str))
  telemetry=frappe.db.sql('SELECT properties FROM tt_ops_event');self.assertNotIn('PRIVATE SUPPORT CANARY',str(telemetry));self.assertFalse(j.rows("SELECT id FROM tt_booking_notice WHERE context_ref=%s AND channel IN ('email','sms')",(r['id'],)))
 def test_support_screenshot_authorization_and_size_validation(self):
  from PIL import Image
  stream=io.BytesIO();Image.new('RGB',(8,8),'blue').save(stream,format='PNG');r=self.submit(attachment={'filename':'private-canary.png','content_base64':base64.b64encode(stream.getvalue()).decode()});f=r['attachments'][0]
  self.assertEqual(support.download(f.id).mimetype,'image/png');frappe.set_user(users['reviewer']);self.assertIn('no-store',support.download(f.id).headers['Cache-Control'])
  for who in (users['counselor'],'Guest'):
   frappe.set_user(who)
   with self.assertRaises(frappe.PermissionError):support.download(f.id)
 def test_reports_quarter_boundaries_repeat_and_no_synthetic_production_claim(self):
  start,end=reports.quarter_bounds('2026-Q4');self.assertEqual(start.isoformat(),'2026-09-30T21:00:00');self.assertEqual(end.isoformat(),'2026-12-31T21:00:00')
  rt.record('application.saved','saved-case');reports.aggregate();reports.aggregate();frappe.set_user(users['reviewer'])
  first=reports.compile_report('2026-Q4',clock=datetime(2026,11,5));second=reports.compile_report('2026-Q4',clock=datetime(2026,11,6));self.assertEqual(first['id'],second['id'])
  result=ops.report_detail(first['id']);self.assertTrue(result['data']['incomplete_period']);self.assertEqual(result['data']['sample_size'],0);self.assertGreaterEqual(result['data']['excluded_synthetic_events'],1)
 def test_raw_archive_retention_and_restore_tombstone(self):
  clock=datetime(2026,11,5);key=storage.put(b'COMPRESSED SYNTHETIC MASKED REPLAY',1024,10000,'replay');id='a'*64
  frappe.db.sql("INSERT INTO tt_ops_archive (id,provider_id,captured,expires,state,size_bytes,object_key,modified) VALUES (%s,'synthetic',%s,%s,'Verified',10,%s,%s)",(id,clock-timedelta(days=91),clock-timedelta(days=1),key,clock))
  archive.retention(clock);self.assertEqual(j.one('SELECT state FROM tt_ops_archive WHERE id=%s',(id,)).state,'Expired');self.assertFalse((Path(self.tmp.name)/('replay-'+key)).exists())
  frappe.db.sql('DELETE FROM tt_ops_deleted WHERE id=%s',(id,));self.assertTrue(archive.deleted(id));self.assertFalse(archive.status()['available'])
 def test_configuration_limits_no_provider_switch_and_permission_audit(self):
  frappe.set_user(users['reviewer']);before=rt.config();ops.configure({'sample_percent':50},before['revision']);self.assertEqual(rt.config()['sample_percent'],50)
  with self.assertRaises(frappe.ValidationError):ops.configure({'archive':True},rt.config()['revision'])
  with self.assertRaises(frappe.ValidationError):ops.configure({'replay_days':91},rt.config()['revision'])
  self.assertTrue(j.rows("SELECT id FROM tt_audit WHERE action='OperationsConfigured'"))
 def test_safe_error_payload_and_provider_timeout(self):
  data=providers.sanitized_error({'request':{'password':'SECRET'},'extra':{'notes':'SECRET'},'exception':{'values':[{'type':'TypeError','value':'SECRET','stacktrace':{'frames':[{'filename':'tele_tena/example.py','lineno':7,'vars':{'secret':'SECRET'}}]}}]}})
  self.assertNotIn('SECRET',json.dumps(data));self.assertNotIn('request',data)
  with patch('tele_tena.operations.providers.settings',return_value={'posthog_host':'https://us.i.posthog.com','posthog_token':'private-test'}),patch('requests.post',side_effect=__import__('requests').Timeout()):
   e=frappe._dict(properties='{}',source='server',role='patient',locale='en',device='desktop',environment='review',release_id='safe',payment_mode='Offline',route='/patient/book/:ref',actor='a'*64,id='b'*64,attempt='c'*64,name='booking.created',created=datetime(2026,11,5))
   with self.assertRaises(providers.ProviderUnavailable):providers.posthog_event(e)
 def test_actual_bugsink_sdk_uses_only_sanitized_memory_transport(self):
  from sentry_sdk import Client as ActualClient
  from sentry_sdk.transport import Transport
  captured=[]
  class Memory(Transport):
   def capture_event(self,event):captured.append(event)
   def capture_envelope(self,envelope):
    for item in envelope.items:
     if item.headers.get('type')=='event':captured.append(item.payload.json)
  def client(**options):return ActualClient(transport=Memory,**options)
  with patch('tele_tena.operations.providers.settings',return_value={'bugsink_dsn':'https://synthetic-key@synthetic.bugsink.com/1'}),patch('sentry_sdk.Client',side_effect=client):
   self.assertEqual(providers.bugsink_error({'request':{'password':'SDK-CANARY'},'exception':{'values':[{'type':'TypeError','value':'SDK-CANARY'}]},'tags':{'origin':'backend','route':'/patient/book/PRIVATE-CANARY?token=SDK-CANARY'}}),'TransportAttempted')
  self.assertTrue(captured);self.assertNotIn('SDK-CANARY',json.dumps(captured));self.assertNotIn('PRIVATE-CANARY',json.dumps(captured));self.assertNotIn('request',captured[0])
 def test_storage_and_event_quota_preserve_business_operations(self):
  with self.assertRaises(ValueError):storage.put(b'x'*20,10,100)
  c=rt.config();frappe.db.sql('INSERT INTO tt_ops_counter VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE n=VALUES(n)',(rt.now().date(),'events',c['events_per_day']))
  before=j.one('SELECT COUNT(*) n FROM tt_appointment').n;self.assertFalse(rt.record('booking.created','quota-noop'));self.assertEqual(j.one('SELECT COUNT(*) n FROM tt_appointment').n,before)
 def test_guest_cannot_spoof_confirmed_outcomes_or_access_reports(self):
  frappe.set_user('Guest');self.assertEqual(ops.events([])['accepted'],0)
  with self.assertRaises(frappe.PermissionError):ops.report_compile('2026-Q4')

 def test_alert_acknowledgement_cooldown_single_recovery_and_no_live_transport(self):
  c=rt.config();c.update(alerts=True,owner='',alert_email='owner@offline-test.invalid',mobile_channel='Telegram')
  with patch('tele_tena.operations.runtime.config',return_value=c),patch('tele_tena.email_delivery.send_notice') as email,patch('tele_tena.operations.providers.telegram',return_value='ProviderAccepted') as mobile,patch.object(frappe.db,'commit'):
   rt.incident('synthetic_outage','Critical');jobs.send_alerts();jobs.send_alerts();self.assertEqual(email.call_count,1);self.assertEqual(mobile.call_count,1)
   rt.incident('synthetic_outage',recovery=True);jobs.send_alerts();jobs.send_alerts();self.assertEqual(email.call_count,2);self.assertEqual(mobile.call_count,2)
   self.assertEqual(j.one("SELECT escalation FROM tt_ops_incident WHERE code='synthetic_outage'").escalation,2)
 def test_collection_preference_schema_and_quarantined_replay(self):
  ops.preference(True,False);c=ops.collection();self.assertTrue(c['preference']['analytics']);self.assertFalse(c['replay_configured'])
  item={'name':'application.started','id':str(uuid.uuid4()),'attempt':str(uuid.uuid4()),'route':'/patient/consultations/PRIVATE-CANARY?token=SECRET','properties':{},'locale':'en','device':'desktop'}
  self.assertEqual(ops.events([item])['accepted'],1);self.assertEqual(ops.events([item])['accepted'],0)
  item['id']=str(uuid.uuid4());item['name']='booking.confirmed'
  with self.assertRaises(frappe.ValidationError):ops.events([item])
  self.assertNotIn('PRIVATE-CANARY',str(frappe.db.sql('SELECT route,properties FROM tt_ops_event')))
 def test_health_marks_missing_or_stale_execution_and_disabled_provider_honestly(self):
  frappe.db.sql('DELETE FROM tt_ops_heartbeat');h=jobs.health();self.assertEqual(h['freshness'],'Not Observed');self.assertEqual(h['providers']['posthog'],'Unconfigured')
  jobs.beat('scheduler');self.assertEqual(jobs.health()['freshness'],'Not Observed');jobs.beat('worker_completed');self.assertEqual(jobs.health()['freshness'],'Current')
  frappe.db.sql("UPDATE tt_ops_heartbeat SET at=DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 1 HOUR) WHERE name='worker_completed'");self.assertEqual(jobs.health()['freshness'],'Stale')
 def test_verified_archive_payload_private_player_headers_and_withdrawal(self):
  import gzip,hashlib
  from tele_tena.operations.replay_format import FORMAT
  frappe.set_user(users['reviewer']);id='f'*64;now=rt.now();payload={'format':FORMAT,'events':[{'type':4,'timestamp':1,'data':{}},{'type':2,'timestamp':2,'data':{'node':{'type':0,'id':1,'childNodes':[]}}}]};raw=gzip.compress(json.dumps(payload).encode());key=storage.put(raw,1048576,10485760,'replay')
  frappe.db.sql("INSERT INTO tt_ops_archive (id,provider_id,captured,expires,state,size_bytes,sha256,format_version,player_version,object_key,modified) VALUES (%s,%s,%s,%s,'Verified',%s,%s,%s,'teletena-sandbox-web-v1',%s,%s)",(id,str(uuid.uuid4()),now,now+timedelta(days=90),len(raw),hashlib.sha256(raw).hexdigest(),FORMAT,key,now))
  with patch('tele_tena.operations.providers.archive_capability',return_value=True):
   self.assertTrue(ops.archive_playback(id)['available'])
   with patch.object(frappe.db,'commit') as commit:response=ops.archive_player();self.assertEqual(commit.call_count,1)
   self.assertIn("connect-src 'none'",response.headers['Content-Security-Policy']);self.assertIn('sandbox allow-scripts',response.headers['Content-Security-Policy']);self.assertIn('no-store',response.headers['Cache-Control']);archive.tombstone(id);self.assertFalse(ops.archive_playback(id)['available'])
  frappe.set_user(users['patient'])
  for fn in (ops.archive_player,lambda:ops.archive_playback(id)):
   with self.assertRaises(frappe.PermissionError):fn()
 def test_export_preserves_original_capture_clock_and_private_integrity(self):
  from tele_tena.operations.replay_format import FORMAT
  id='e'*64;now=rt.now();captured=now-timedelta(days=2);result={'format':FORMAT,'captured_at':captured.isoformat()+'Z','events':[{'type':4,'timestamp':1,'data':{}},{'type':2,'timestamp':2,'data':{'node':{'type':0,'id':1,'childNodes':[]}}}]};frappe.db.sql("INSERT INTO tt_ops_archive (id,provider_id,captured,expires,state,size_bytes,modified) VALUES (%s,%s,%s,%s,'Pending',0,%s)",(id,str(uuid.uuid4()),captured,captured+timedelta(days=90),now));c=rt.config();c['archive']=True
  with patch('tele_tena.operations.runtime.config',return_value=c),patch('tele_tena.operations.providers.archive_export',return_value=result):archive.export_tick()
  row=j.one('SELECT * FROM tt_ops_archive WHERE id=%s',(id,));self.assertEqual(row.state,'Verified');self.assertEqual(row.captured,captured);self.assertEqual(row.expires,captured+timedelta(days=90));self.assertEqual(row.player_version,'teletena-sandbox-web-v1')
  frappe.set_user(users['reviewer'])
  with patch('tele_tena.operations.providers.archive_capability',return_value=True):self.assertTrue(archive.playback_payload(id)['available'])
 def test_player_translation_cannot_close_trusted_script(self):
  frappe.set_user(users['reviewer'])
  with patch('tele_tena.localization.translate',return_value='</script><script>PRIVATE-CANARY</script>'):
   response=archive.player_response('am')
  body=response.get_data(as_text=True);self.assertNotIn('</script><script>',body);self.assertIn(chr(92)+'u003c/script>',body)
 def test_archive_adapter_does_not_promote_partial_or_metadata_to_verified(self):
  with self.assertRaises(providers.ArchiveUnverified):providers.archive_export({'metadata_only':True})
  self.assertFalse(archive.status()['available']);self.assertIsNone(archive.status()['capacity_estimate'])

if __name__=='__main__':
 try:unittest.main(defaultTest='Operations')
 finally:frappe.db.rollback();frappe.destroy()
