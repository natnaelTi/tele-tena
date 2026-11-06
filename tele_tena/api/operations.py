"""Native Operations API. Reviewer authority is checked on every command/query."""
import hashlib,json,re,uuid
from pathlib import Path
import frappe
from tele_tena.api.journey import actor,command,query,rows,one,fail,audit
from tele_tena.operations import runtime as rt,support as desk,jobs,reports,archive,providers,capture

@frappe.whitelist(allow_guest=True,methods=['GET'])
def liveness():
 from werkzeug.wrappers import Response
 try:
  if not rt.available() or frappe.conf.get('maintenance_mode'):raise ValueError()
  root=Path(__file__).resolve().parents[1]/'public/review'
  if not (root/'release.json').is_file() or not (root/'index.html').is_file():raise ValueError()
  manifest=json.loads((root/'release.json').read_text())
  if not all((root/name).is_file() for name in manifest.get('files',{}) if name.endswith(('.js','.css'))):raise ValueError()
  frappe.db.sql('SELECT 1');ready=True
 except Exception:ready=False
 return Response('TELETENA_APPLICATION_READY' if ready else 'TELETENA_UNAVAILABLE',status=200 if ready else 503,content_type='text/plain',headers={'Cache-Control':'no-store'})
@query()
def configuration():
 rt.reviewer();return {'config':rt.config(),'providers':providers.status(),'archive':archive.status(),'replay_capability':capture.capability(),'archive_capability':providers.archive_capability()}
@command
def configure(values,revision):
 user=rt.reviewer();old=rt.config()
 if not isinstance(values,dict) or set(values)-set(old) or 'revision' in values:fail('Review the supported operational settings.')
 if int(revision)!=old['revision']:fail('Settings changed. Reload before saving.','operations_conflict')
 for key in ('native_events','analytics','errors','replay','archive','alerts'):
  if key in values and type(values[key]) is not bool:fail('Use an explicit enabled or disabled setting.')
 limits={'events_per_day':(100,100000),'event_total_limit':(1000,1000000),'alert_messages_per_day':(1,1000),'errors_per_day':(10,2000),'replays_per_day':(1,5000),'archive_bytes':(10485760,5*1024**3),'recording_bytes':(1024,50*1024**2),'export_queue':(1,5000),'retry_budget':(1,10),'replay_days':(90,90),'event_days':(7,90),'sample_percent':(1,100),'cooldown_minutes':(5,1440)}
 for k,(low,high) in limits.items():
  if k in values and (type(values[k]) is not int or not low<=values[k]<=high):fail('A storage, retention or collection limit is outside its supported range.','operations_limit_invalid')
 if values.get('alert_email') and (not isinstance(values['alert_email'],str) or len(values['alert_email'])>254 or not re.fullmatch(r'[^@\s,]+@[^@\s,]+\.[^@\s,]+',values['alert_email'])):fail('Enter one valid owner alert email address.')
 if values.get('owner'):
  if not frappe.db.get_value('User',values['owner'],'enabled'):fail('Choose an enabled account for the consenting owner alert subscription.')
 if values.get('mobile_channel',old['mobile_channel']) not in ('Disabled','Telegram') or values.get('environment',old['environment']) not in ('review','staging','production'):fail('Choose a supported environment and alert channel.')
 if values.get('replay') and not capture.capability():fail('Session replay is unavailable until project masking and capture verification pass.','replay_unverified')
 if values.get('archive') and not providers.archive_capability():fail('Archive export is unavailable until the selected project passes complete export and independent playback verification.','archive_unverified')
 data={**old,**values};data.pop('revision',None)
 if data['replay'] and not data['archive']:fail('Enable verified archive exports before enabling replay, or disable replay first.','replay_archive_required')
 frappe.db.sql('SELECT id FROM tt_ops_config WHERE id=1 FOR UPDATE')
 if rt.config()['revision']!=old['revision']:fail('Settings changed. Reload before saving.','operations_conflict')
 frappe.db.sql('UPDATE tt_ops_config SET payload=%s,revision=revision+1,modified=%s WHERE id=1',(json.dumps(data),rt.now()))
 audit(user,'OperationsConfigured',{'changed':sorted(values),'prior_revision':old['revision']});return configuration()
@frappe.whitelist(allow_guest=True,methods=['GET'])
def collection():
 c=rt.config();user=frappe.session.user;pref=rows('SELECT analytics,replay FROM tt_ops_preference WHERE actor=%s',(rt.pseudonym(user),)) if user!='Guest' else []
 return {'schema':'operations-v1.1','subject':rt.pseudonym(user) if user!='Guest' else None,'analytics':c['native_events'],'errors':c['errors'],'csrf_token':(__import__('frappe.sessions',fromlist=['get_csrf_token']).get_csrf_token() if getattr(frappe.local,'request',None) else None),'external_analytics_enabled':c['analytics'],'replay_configured':bool(c['replay'] and c['archive'] and capture.capability()),'role':rt.role(),'revision':c['revision'],'replay_status':'Unavailable until project masking and compatibility verification','notice_version':'operations-notice-draft-v1','preference':{'analytics':bool(pref and pref[0].analytics),'replay':bool(pref and pref[0].replay)},'sample_percent':c['sample_percent']}
@command
def preference(analytics,replay=False):
 user=actor()
 if type(analytics) is not bool or type(replay) is not bool:fail('Review your collection choices.')
 frappe.db.sql('INSERT INTO tt_ops_preference VALUES (%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE analytics=VALUES(analytics),replay=VALUES(replay),version=VALUES(version),modified=VALUES(modified)',(rt.pseudonym(user),int(analytics),int(replay),'operations-notice-draft-v1',rt.now()))
 if not analytics:frappe.db.sql("UPDATE tt_ops_event SET delivery='Disabled' WHERE actor=%s AND delivery IN ('Pending','Unconfigured')",(rt.pseudonym(user),))
 if not replay:capture.revoke_owner()
 audit(user,'CollectionPreferenceChanged',{'analytics':analytics,'replay':replay,'notice_version':'operations-notice-draft-v1'});return collection()
def _capture_call(fn,*args):
 try:return fn(*args)
 except ValueError:fail('Masked replay could not continue. Other care features are unaffected.','replay_unavailable')

@command
def replay_admit(provider_id,window_id):
 return _capture_call(capture.admit,provider_id,window_id)
@command
def replay_chunk(id,chunk_id,events,route):
 return _capture_call(capture.chunk,id,chunk_id,events,route)
@command
def replay_loss(id,reason):
 return _capture_call(capture.loss,id,reason)
@command
def replay_close(id):
 return _capture_call(capture.close,id)
@command
def replay_delete(id):
 row=capture._owned(id,require_scope=False);archive.tombstone(row.id,'UserDeleted');audit(id,'OwnReplayDeleted',{});return {'state':'Expired'}
@frappe.whitelist(allow_guest=True,methods=['POST'])
def events(items):
 # Guest is allowed only allowlisted interaction events, never confirmed outcomes.
 from tele_tena.operations.contract import EVENTS,uuid as valid_uuid
 if not isinstance(items,list) or len(items)>10:fail('Event batch unavailable.')
 user=frappe.session.user;c=rt.config()
 if not c['native_events']:return {'accepted':0,'state':'Disabled'}
 if user=='Guest':return {'accepted':0,'state':'Consent Required — Guest Interaction Collection Disabled'}
 pref=rows('SELECT analytics FROM tt_ops_preference WHERE actor=%s',(rt.pseudonym(user),))
 if not pref or not pref[0].analytics:return {'accepted':0,'state':'Consent Required'}
 accepted=0
 for item in items:
  if not isinstance(item,dict) or set(item)!={'name','id','attempt','route','properties','locale','device'} or EVENTS.get(item.get('name'))!='browser' or not valid_uuid(item.get('id')) or not valid_uuid(item.get('attempt')):fail('Event schema unavailable.','event_invalid')
  if item['locale'] not in ('en','am','om') or item['device'] not in ('mobile','tablet','desktop'):fail('Event context unavailable.')
  if int(hashlib.sha256(item['attempt'].encode()).hexdigest()[:8],16)%100>=c['sample_percent']:continue
  try:accepted+=bool(rt.record(item['name'],item['id'],item['properties'],'browser',item['attempt'],context={'route':item['route'],'locale':item['locale'],'device':item['device']}))
  except ValueError:fail('Event properties unavailable.','event_invalid')
 return {'accepted':accepted,'state':'Recorded Locally'}
@frappe.whitelist(allow_guest=True,methods=['POST'])
def browser_error(kind,route,frames=None):
 # No raw message, stack, URL or arbitrary payload accepted.
 if kind not in ('Error','TypeError','ReferenceError','RangeError','UnhandledRejection','RenderError'):kind='Error'
 if not rt.config()['errors']:return {'recorded':False,'state':'Disabled'}
 key=rt.pseudonym(str(getattr(frappe.local,'request_ip','unknown')));cache=frappe.cache();n=cache.incr('teletena-ops-error:'+key);cache.expire('teletena-ops-error:'+key,60)
 if n>20:return {'recorded':False,'state':'Limited'}
 from tele_tena.operations.storage import write_spool
 if not isinstance(frames,list):frames=[]
 payload={'exception':{'values':[{'type':kind,'value':'Unexpected TeleTena failure','stacktrace':{'frames':[f for f in frames[:12] if isinstance(f,dict)]}}]},'tags':{'origin':'browser','route':rt.route_template(route)}}
 write_spool(providers.sanitized_error(payload))
 return {'recorded':True}
@query()
def overview():
 rt.reviewer()
 return {'applications':one("SELECT COUNT(*) n FROM tt_application WHERE status='Pending'").n,'scope_replies':one("SELECT COUNT(*) n FROM `tabTele Tena Vetting Scope Application` WHERE status='Resubmitted'").n,'payment_reviews':one("SELECT COUNT(*) n FROM tt_direct_payment WHERE state IN ('Submitted','ReconciliationRequired') AND verified_at IS NULL").n,'support_open':one("SELECT COUNT(*) n FROM tt_ops_support WHERE state NOT IN ('Resolved','Closed')").n,'incidents':rows('SELECT id,code,severity,state,n,last_seen,acknowledged_at,escalation FROM tt_ops_incident ORDER BY last_seen DESC LIMIT 50'),'health':jobs.health(),'archive':archive.status(),'collection':rt.config(),'freshness':'Native counts from the current database; provider coverage is reported separately.'}
@query()
def health():rt.reviewer();return jobs.health()
@query()
def insights(include_synthetic=0):rt.reviewer();return reports.insights(str(include_synthetic)=='1')
@query()
def support_list():return desk.listing()
@command
def support_detail(id):return desk.detail(id)
@command
def support_submit(category,description,followup,retry_key,context,attachment=None):return desk.submit(category,description,followup,retry_key,context,attachment)
@command
def support_reply(id,body,audience,retry_key,state=None,priority='Normal',assignee=None):return desk.reply(id,body,audience,retry_key,state,priority,assignee)
@frappe.whitelist(methods=['GET'])
def support_file(id):
 result=desk.download(id);frappe.db.commit() # GET read plus this access audit only; no business writes.
 return result
@query()
def archive_list():rt.reviewer();return archive.status()
@command
def archive_delete(id):
 rt.reviewer();one('SELECT id FROM tt_ops_archive WHERE id=%s',(id,));archive.tombstone(id,'UserDeleted');audit(id,'ReplayDeleted',{});return {'state':'Expired','provider_deletion':'Pending'}
@command
def archive_playback(id):
 rt.reviewer();audit(id,'ReplayAccessAttempted',{})
 return archive.playback_payload(id)
@frappe.whitelist(methods=['GET'])
def archive_player(locale=None):
 rt.reviewer();audit('archive-player','ReplayPlayerAccessed',{});result=archive.player_response(locale);frappe.db.commit();return result
@query()
def reports_list():rt.reviewer();return rows('SELECT id,period,version,created FROM tt_ops_report ORDER BY created DESC LIMIT 40')
@command
def report_compile(period):rt.reviewer();result=reports.compile_report(period);audit(result['id'],'QuarterReportCompiled',{'period':period});return result
@command
def report_detail(id):
 rt.reviewer();row=one('SELECT * FROM tt_ops_report WHERE id=%s',(id,));audit(id,'QuarterReportAccessed',{});return {'id':id,'version':row.version,'data':json.loads(row.payload),'annotation':row.annotation}
@command
def report_annotate(id,note):
 from tele_tena.api.journey import text
 user=rt.reviewer();note=text(note,3000);r=one('SELECT annotation FROM tt_ops_report WHERE id=%s FOR UPDATE',(id,));history=json.loads(r.annotation or '[]')
 if len(history)>=100:fail('This report has reached its annotation limit. Create a follow-up report version.')
 history.append({'note':note,'actor':rt.pseudonym(user),'at':str(rt.now())})
 frappe.db.sql('UPDATE tt_ops_report SET annotation=%s WHERE id=%s',(json.dumps(history),id));audit(id,'QuarterReportAnnotated',{});return {'saved':True}
@command
def report_export(id):
 result=report_detail(id);audit(id,'QuarterReportExported',{})
 return result
@command
def acknowledge(id):
 user=rt.reviewer();frappe.db.sql('UPDATE tt_ops_incident SET acknowledged_by=%s,acknowledged_at=%s WHERE id=%s',(user,rt.now(),id));audit(id,'IncidentAcknowledged',{});return {'acknowledged':True}
