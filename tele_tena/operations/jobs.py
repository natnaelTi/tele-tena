"""Dedicated queue plus independent health/alert runner; bounded work per tick."""
import hashlib,json,sys,uuid
from datetime import timedelta
import frappe
from . import runtime as rt

def beat(name,details=None):
 frappe.db.sql('INSERT INTO tt_ops_heartbeat VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE at=VALUES(at),details=VALUES(details)',(name,rt.now(),json.dumps(details or {})))
def schedule():
 if not rt.available():return
 beat('scheduler')
 try:frappe.enqueue('tele_tena.operations.jobs.process',queue='teletena_ops',job_id='teletena-ops:'+frappe.local.site,deduplicate=True,enqueue_after_commit=True)
 except Exception:rt.incident('operations_enqueue_failed')
def process():
 if not rt.available():return
 from . import reports,archive,storage,providers,capture
 beat('worker_started');reports.aggregate(500)
 for file in list(storage.root().glob('error-*'))[:25]:
  try:
   data=json.loads(file.read_text());safe=providers.sanitized_error(data);group={**safe,'tags':{k:v for k,v in safe.get('tags',{}).items() if k!='attempt'}};group.pop('event_id',None);fingerprint=hashlib.sha256(json.dumps(group,sort_keys=True).encode()).hexdigest()
   if rt.count('errors',rt.config()['errors_per_day']):
    frappe.db.sql('INSERT INTO tt_ops_error VALUES (%s,%s,%s,%s,\'Pending\',0)',(str(uuid.uuid4()),fingerprint,json.dumps(safe),rt.now()));rt.incident('error_'+fingerprint[:12]);rt.safe_record('operations.error_observed',file.name,{'error_code':'unexpected'},context={'route':safe.get('tags',{}).get('route','/unknown'),'locale':'en','device':'unknown'})
   file.unlink()
  except (ValueError,OSError):file.unlink(missing_ok=True)
 c=rt.config()
 if c['analytics']:
  for event in frappe.db.sql("SELECT * FROM tt_ops_event WHERE delivery='Pending' AND tries<%s ORDER BY created LIMIT 20",(c['retry_budget'],),as_dict=True):
   try:state=providers.posthog_event(event)
   except providers.Unconfigured:state='Unconfigured'
   except providers.ProviderUnavailable:state='Pending'
   frappe.db.sql('UPDATE tt_ops_event SET delivery=%s,tries=tries+1 WHERE id=%s',(state,event.id))
 if c['errors']:
  for event in frappe.db.sql("SELECT * FROM tt_ops_error WHERE state='Pending' AND tries<%s ORDER BY created LIMIT 10",(c['retry_budget'],),as_dict=True):
   try:
    payload=json.loads(event.payload);payload['event_id']=event.id.replace('-','');state=providers.bugsink_error(payload)
   except providers.Unconfigured:state='Unconfigured'
   except Exception:state='Unknown'
   frappe.db.sql('UPDATE tt_ops_error SET state=%s,tries=tries+1 WHERE id=%s',(state,event.id))
 archive_failed=False
 for lifecycle in (capture.tick,archive.retention,archive.process_provider_deletions,archive.export_tick):
  try:lifecycle()
  except (ValueError,OSError,providers.Unconfigured,providers.ProviderUnavailable):
   archive_failed=True;rt.incident('archive_lifecycle_unavailable');beat('archive_lifecycle',{'state':'Unavailable'})
 if not archive_failed:rt.incident('archive_lifecycle_unavailable',recovery=True);beat('archive_lifecycle',{'state':'Current'})
 # Aggregate before raw structured-event expiry. Business/support/audit rows are never deleted here.
 frappe.db.sql('DELETE FROM tt_ops_event WHERE aggregated=1 AND created<%s LIMIT 1000',(rt.now()-timedelta(days=c['event_days']),))
 removed=frappe.db._cursor.rowcount
 if removed:frappe.db.sql("UPDATE tt_ops_counter SET n=GREATEST(0,n-%s) WHERE day='1970-01-01' AND kind='events_stored'",(removed,))
 frappe.db.sql('DELETE FROM tt_ops_error WHERE created<%s LIMIT 1000',(rt.now()-timedelta(days=30),))
 frappe.db.sql('DELETE FROM tt_ops_daily WHERE day<%s LIMIT 1000',((rt.now()-timedelta(days=1096)).date(),))
 frappe.db.sql('DELETE FROM tt_ops_attempt WHERE last_seen<%s LIMIT 1000',(rt.now()-timedelta(days=365),))
 beat('worker_completed')
 today=rt.now().date().isoformat()
 if c['owner'] and c['alerts'] and not frappe.db.sql("SELECT name FROM tt_ops_heartbeat WHERE name=%s",('digest:'+today,)):
  from tele_tena.communications import queue
  queue(c['owner'],'OperationsDigest','operations',today,'operations-digest:'+today);beat('digest:'+today)
 last=frappe.db.sql("SELECT at FROM tt_ops_heartbeat WHERE name='quarter_report'",as_dict=True)
 if not last or last[0].at.date()!=rt.now().date():
  from .reports import compile_report
  current=rt.now().date();quarter=(current.month-1)//3+1;compile_report(str(current.year)+'-Q'+str(quarter))
  if current.month in (1,4,7,10) and current.day==1:compile_report(str(current.year-1 if quarter==1 else current.year)+'-Q'+str(4 if quarter==1 else quarter-1))
  beat('quarter_report')

def _after_job(method=None,kwargs=None,result=None):
 if not isinstance(method,str) or not method.startswith('tele_tena.') or not rt.available():return
 error=sys.exc_info()[1]
 if error:rt.unexpected(error,'job');return
 # Background-job transaction has already committed. Never inspect kwargs or results.
 beat('app_job_completed');frappe.db.commit()

def health():
 c=rt.config();beats={x.name:{'at':x.at,'age_seconds':max(0,int((rt.now()-x.at).total_seconds()))} for x in frappe.db.sql('SELECT name,at FROM tt_ops_heartbeat WHERE name IN (\'scheduler\',\'worker_started\',\'worker_completed\',\'retention\',\'app_job_completed\',\'archive_lifecycle\')',as_dict=True)}
 queue={'state':'Unavailable','pending':None,'oldest_age_seconds':None}
 try:
  from frappe.utils.background_jobs import get_queue
  q=get_queue('teletena_ops');queue={'state':'Observed','pending':q.count,'oldest_age_seconds':None}
  ids=q.get_job_ids(0,1)
  if ids:
   from rq.job import Job
   job=Job.fetch(ids[0],connection=q.connection)
   if job.enqueued_at:queue['oldest_age_seconds']=max(0,int((rt.now()-job.enqueued_at.replace(tzinfo=None)).total_seconds()))
 except Exception:pass
 return {'release':rt.release(),'environment':c['environment'],'database':'Ready','beats':beats,'queue':queue,'alert_states':frappe.db.sql('SELECT state,COUNT(*) n FROM tt_ops_alert GROUP BY state',as_dict=True),'notification_states':frappe.db.sql("SELECT state,COUNT(*) n,MIN(created) oldest FROM tt_booking_notice WHERE channel IN ('email','sms') GROUP BY state",as_dict=True),'backup':'Unavailable — No Verified Backup-Freshness Metadata','freshness':'Stale' if any(beats.get(k,{}).get('age_seconds',999999)>240 for k in ('scheduler','worker_completed')) else 'Current','archive':__import__('tele_tena.operations.archive',fromlist=['status']).status(),'providers':__import__('tele_tena.operations.providers',fromlist=['status']).status()}

def watch():
 """CLI operator runner; no RQ dependency for critical technical alert delivery."""
 if not rt.available():return
 status=health();rt.incident('operations_worker_stale','Warning',recovery=status['freshness']=='Current')
 failures=frappe.db.sql("SELECT COUNT(*) n,COUNT(DISTINCT actor) people FROM tt_ops_event WHERE name='validation.failed' AND created>DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 5 MINUTE) AND JSON_UNQUOTE(JSON_EXTRACT(properties,'$.step')) IN ('payment','schedule') AND JSON_UNQUOTE(JSON_EXTRACT(properties,'$.error_code')) IN ('network','timeout','unavailable')",as_dict=True)[0]
 rt.incident('widespread_booking_payment_failure','Critical',recovery=not(failures.n>=10 and failures.people>=3))
 a=__import__('tele_tena.operations.archive',fromlist=['status']).status()
 rt.incident('archive_capacity_near_limit','Warning',recovery=not(a['used_bytes'] is not None and a['used_bytes']*100>=a['limit_bytes']*80))
 rt.incident('replay_index_near_limit','Warning',recovery=not(a['index_entries']*100>=a['index_limit']*80))
 rt.incident('archive_export_delayed','Warning',recovery=not a['export_warning'])
 pending=sum(x.n for x in a['chunks'] if x.state in ('Pending','Retry'))
 waiting=sum(x.n for x in a['states'] if x.state in ('Capturing','Pending','Failed','Incomplete'))
 rt.incident('replay_queue_near_limit','Warning',recovery=not(pending*100>=rt.config()['replay_pending_chunks']*80 or waiting*100>=rt.config()['export_queue']*80))
 send_alerts();send_digest()
 frappe.db.commit()

def send_alerts():
 c=rt.config()
 if not c['alerts']:return
 recipient=c.get('alert_email') or __import__('tele_tena.operations.providers',fromlist=['settings']).settings().get('owner_alert_email')
 if not recipient and not c['owner']:return
 from .providers import telegram,Unconfigured,ProviderUnavailable
 from tele_tena import email_delivery
 for row in frappe.db.sql("SELECT * FROM tt_ops_incident WHERE state IN ('Open','Recovered') ORDER BY last_seen LIMIT 20 FOR UPDATE",as_dict=True):
  if row.state=='Open' and row.acknowledged_at:continue
  if row.state=='Open' and row.last_alert and rt.now()-row.last_alert<timedelta(minutes=c['cooldown_minutes']):continue
  if row.severity!='Critical' and row.n<3:continue
  phase='Recovery' if row.state=='Recovered' else 'Alert';cycle=str(row.first_seen)+(':recovery' if phase=='Recovery' else ':')+( '' if phase=='Recovery' else str(rt.now().timestamp()//(c['cooldown_minutes']*60)))
  channels=['email']+(['telegram'] if c['mobile_channel']=='Telegram' and row.severity=='Critical' else [])
  sent_any=False
  for channel in channels:
   id=rt.pseudonym(row.id+phase+channel+cycle)
   if frappe.db.sql('SELECT id FROM tt_ops_alert WHERE id=%s',(id,)):continue
   if not rt.count('alerts',c['alert_messages_per_day']):continue
   sent_any=True
   frappe.db.sql("INSERT INTO tt_ops_alert VALUES (%s,%s,%s,%s,'Sending',%s,%s)",(id,row.id,channel,phase,rt.now(),rt.now()));frappe.db.commit()
   message='TeleTena '+phase+': '+row.code.replace('_',' ')+'. Open your authenticated Operations Overview.'
   try:
    if channel=='telegram':state=telegram(message)
    else:
     contacts=frappe.db.sql("SELECT contact FROM tt_contact_identity WHERE user=%s AND channel='email' AND verified_at IS NOT NULL",(c['owner'],)) if c['owner'] else []
     destination=recipient or (contacts[0][0] if contacts else None)
     if not destination:raise Unconfigured('owner_email_unverified')
     email_delivery.send_notice(destination,message);state='ProviderAccepted'
   except (Unconfigured,email_delivery.DeliveryUnavailable):state='Unavailable'
   except Exception:state='Unknown'
   frappe.db.sql('UPDATE tt_ops_alert SET state=%s,modified=%s WHERE id=%s',(state,rt.now(),id))
  if sent_any:frappe.db.sql('UPDATE tt_ops_incident SET last_alert=%s,escalation=escalation+1 WHERE id=%s',(rt.now(),row.id))

def after_job(method=None,kwargs=None,result=None):
 try:_after_job(method=method,kwargs=None,result=None)
 except Exception:pass

def after_request(response,request):
 try:
  if response.status_code>=500 and request.path.startswith('/api/method/tele_tena.'):
   rt.unexpected(RuntimeError('Unexpected TeleTena request failure'))
 except Exception:pass

def send_digest():
 c=rt.config()
 if not c['alerts']:return
 from .providers import settings
 address=c.get('alert_email') or settings().get('owner_alert_email')
 if not address:return
 from zoneinfo import ZoneInfo
 from datetime import timezone
 local=rt.now().replace(tzinfo=timezone.utc).astimezone(ZoneInfo('Africa/Nairobi'))
 if local.hour<8:return
 id=rt.pseudonym('daily-digest:'+local.date().isoformat())
 if frappe.db.sql('SELECT id FROM tt_ops_alert WHERE id=%s',(id,)):return
 frappe.db.sql("INSERT INTO tt_ops_alert VALUES (%s,%s,'email','Digest','Sending',%s,%s)",(id,rt.pseudonym('daily-digest'),rt.now(),rt.now()));frappe.db.commit()
 from tele_tena import email_delivery
 try:
  unresolved=frappe.db.sql("SELECT COUNT(*) FROM tt_ops_support WHERE state NOT IN ('Resolved','Closed')")[0][0]
  message='TeleTena Daily Operations Summary. Unresolved support reports: '+str(unresolved)+'. Open /teletena/admin/operations using an authorized reviewer account. Report contents are available only after sign-in.'
  email_delivery.send_notice(address,message);state='ProviderAccepted'
 except email_delivery.DeliveryUnavailable:state='Unavailable'
 except Exception:state='Unknown'
 frappe.db.sql('UPDATE tt_ops_alert SET state=%s,modified=%s WHERE id=%s',(state,rt.now(),id))
