"""Site-bound native telemetry. No provider I/O in a business transaction."""
import hashlib,hmac,json,re,uuid,inspect,traceback
from datetime import datetime,timezone
from pathlib import Path
import frappe
from .contract import EVENTS,VERSION,properties,route_template

def now():return datetime.now(timezone.utc).replace(tzinfo=None)
def available():
 return bool(getattr(frappe.local,'site',None)) and bool(frappe.db.sql("SHOW TABLES LIKE 'tt_ops_config'"))
def config():
 from tele_tena.patches.v1_53_operations import DEFAULTS
 row=frappe.db.sql('SELECT revision,payload FROM tt_ops_config WHERE id=1',as_dict=True)
 return {**DEFAULTS,**json.loads(row[0].payload),'revision':row[0].revision}
def reviewer():
 from tele_tena.api.journey import actor
 user=actor()
 if user!='Administrator' and 'Tele Tena Approver' not in frappe.get_roles(user):raise frappe.PermissionError('Operational reviewer access required')
 return user
def pseudonym(value):
 # Fresh sites may not yet have a framework encryption key. Keep a separate
 # private stable HMAC key rather than modifying framework/provider credentials.
 from .storage import root,locked
 import os,secrets
 file=root()/'actor-hmac.key'
 with locked():
  if file.exists():
   if file.is_symlink() or file.stat().st_uid!=os.geteuid() or file.stat().st_mode&0o077 or file.stat().st_size!=64:raise ValueError('site_key_unavailable')
   key=file.read_text()
  else:
   key=frappe.conf.get('encryption_key')
   if not key:
    fd=os.open(file,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as stream:stream.write(secrets.token_hex(32))
    key=file.read_text()
 return hmac.new(str(key).encode(),('teletena-ops-v1:'+str(value)).encode(),hashlib.sha256).hexdigest()
def role(user=None):
 user=user or frappe.session.user
 if user=='Guest':return 'guest'
 roles=frappe.get_roles(user)
 return 'reviewer' if user=='Administrator' or 'Tele Tena Approver' in roles else 'clinician' if 'Tele Tena Clinician' in roles or 'Tele Tena Applicant' in roles else 'patient' if 'Tele Tena Patient' in roles else 'other'
def release():
 try:
  d=json.loads((Path(__file__).resolve().parents[1]/'public/review/release.json').read_text());return d['source_commit'][:40]
 except Exception:return 'unknown'
def request_context():
 request=getattr(frappe.local,'request',None);headers=request.headers if request else {}
 return {'route':route_template(headers.get('X-TeleTena-Route','/unknown')),'locale':headers.get('X-TeleTena-Locale','en') if headers.get('X-TeleTena-Locale','en') in ('en','am','om') else 'en','device':headers.get('X-TeleTena-Device','unknown') if headers.get('X-TeleTena-Device','unknown') in ('mobile','tablet','desktop') else 'unknown','attempt':headers.get('X-TeleTena-Attempt','')}
def count(kind,limit,day=None):
 day=day or now().date();frappe.db.sql('INSERT IGNORE INTO tt_ops_counter VALUES (%s,%s,0)',(day,kind))
 frappe.db.sql('UPDATE tt_ops_counter SET n=n+1 WHERE day=%s AND kind=%s AND n<%s',(day,kind,limit))
 return bool(frappe.db._cursor.rowcount)
def record(name,key,props=None,source='server',attempt=None,user=None,context=None):
 """Caller supplies stable outcome key; raw key never leaves this function."""
 if name not in EVENTS or EVENTS[name]!=source:raise ValueError('event_source_invalid')
 c=config()
 if not c['native_events']:return False
 props=properties(props or {});context=context or request_context();user=user or frappe.session.user
 event_id=pseudonym(name+':'+str(key))
 if frappe.db.sql('SELECT id FROM tt_ops_event WHERE id=%s',(event_id,)):return False
 if not count('events',c['events_per_day']):
  frappe.db.sql('INSERT INTO tt_ops_counter VALUES (%s,%s,1) ON DUPLICATE KEY UPDATE n=n+1',(now().date(),'events_dropped'));return False
 if not count('events_stored',c['event_total_limit'],__import__('datetime').date(1970,1,1)):
  frappe.db.sql('INSERT INTO tt_ops_counter VALUES (%s,%s,1) ON DUPLICATE KEY UPDATE n=n+1',(now().date(),'capacity_dropped'));return False
 from .contract import uuid as valid_uuid
 attempt=attempt or context.get('attempt');attempt=pseudonym('attempt:'+attempt) if valid_uuid(attempt) else pseudonym('attempt:'+name.split('.')[0]+':'+str(key))
 actor=pseudonym(user) if user!='Guest' else pseudonym('guest:'+attempt)
 roles=role(user);synthetic='yes' if c['environment']!='production' or roles=='reviewer' or frappe.conf.get('tele_tena_ops_synthetic_users') and user in frappe.conf.tele_tena_ops_synthetic_users else 'no'
 if name.startswith('operations.') and c['environment']=='production' and not getattr(frappe.flags,'tele_tena_ops_test',False):synthetic='no'
 if '@' in user and (user.endswith('.invalid') or user.startswith('tt-demo-')):synthetic='yes'
 props['synthetic']=synthetic
 mode=context.get('payment_mode') if context.get('payment_mode') in ('Wallet','Offline') else frappe.db.sql('SELECT mode FROM tt_payment_config WHERE id=1')[0][0]
 pref=frappe.db.sql('SELECT analytics FROM tt_ops_preference WHERE actor=%s',(actor,))
 delivery='Pending' if c['analytics'] and user!='Guest' and pref and pref[0][0] else 'Disabled'
 frappe.db.sql('INSERT IGNORE INTO tt_ops_event (id,name,attempt,actor,source,role,locale,device,environment,release_id,payment_mode,route,properties,created,delivery) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(event_id,name,attempt,actor,source,roles,context.get('locale','en'),context.get('device','unknown'),c['environment'],release(),mode,route_template(context.get('route','/unknown')),json.dumps(props),now(),delivery))
 return True

def safe_record(*args,**kwargs):
 if getattr(frappe.flags,'tele_tena_ops_active',False):return
 try:
  frappe.flags.tele_tena_ops_active=True
  if not available():return
  sp='ops_'+uuid.uuid4().hex;frappe.db.savepoint(sp)
  try:return record(*args,**kwargs)
  except Exception:frappe.db.rollback(save_point=sp)
 except Exception:pass
 finally:frappe.flags.tele_tena_ops_active=False

# Only application-owned methods, never arbitrary request bodies.
METHODS={
 'vetting.save_scope_application':('application.scope_created','application'),
 'professional.save':('application.saved','application'), 'contact_auth.save_onboarding':('application.step_completed','application'),
 'application_flow.request_assistance':('application.assistance_requested','application'), 'application_flow.assisted_save':('application.saved','application'), 'application_flow.assisted_submit':('application.submitted','application'), 'application_flow.respond':('application.resubmitted','application'),
 'professional.upload':('upload.succeeded','application'),'application_flow.assisted_upload':('upload.succeeded','application'),'history_documents.upload':('upload.succeeded','booking'),'vetting.upload_scope_evidence':('upload.succeeded','application'),
 'journey.book':('booking.created','booking'),'open_requests.publish_request':('request.published','request'),'open_requests.create_request':('request.published','request'),'open_requests.respond_offer':('request.offer_accepted','request'),
 'direct_payments.submit':('payment.submitted','booking'),'direct_payments.review':('payment.verified','booking'),'direct_payments.raise_issue':('payment.followup','booking'), 'consultations.join':('consultation.join_authorized','consultation'),
}
def outcome(fn,args,kwargs,result):
 method=fn.__module__.removeprefix('tele_tena.api.')+'.'+fn.__name__
 if method not in METHODS or not isinstance(result,dict) or result.get('idempotent'):return
 values=inspect.signature(fn).bind_partial(*args,**kwargs).arguments;name,family=METHODS[method];props={}
 if method=='contact_auth.save_onboarding':
  if values.get('kind')!='clinician':return
  name='application.submitted' if result.get('completed') else 'application.saved';props['step']=str(values.get('step',0))
 if method=='open_requests.respond_offer':name='request.offer_declined' if values.get('decision')=='decline' else 'request.offer_accepted'
 if method=='vetting.save_scope_application' and result.get('status') not in ('Submitted','Resubmitted'):return
 if method=='direct_payments.review':
  if values.get('decision')!='confirm':return
  if not result.get('verified_at'):return
 if method.endswith('upload') and values.get('purpose') in ('CV','License','Identification','Certification','Authorization'):props['document']=values['purpose']
 # Keys are minimized identifiers/revisions, never full payloads, proof or credentials.
 key=result.get('id') or result.get('name') or result.get('appointment') or result.get('response') or result.get('application') or result.get('case') or values.get('id') or values.get('case') or values.get('application') or values.get('appointment') or values.get('offer_id') or values.get('retry_key')
 if method.endswith('save') or method.endswith('save_onboarding'):key=str(frappe.session.user)+':'+str(result.get('revision') or values.get('revision') or values.get('step'))
 if not key:return
 context=request_context()
 if method.startswith('direct_payments.'):context['payment_mode']='Offline'
 elif result.get('payment_mode') in ('Wallet','Offline'):context['payment_mode']=result['payment_mode']
 safe_record(name,method+':'+str(key),props,context=context)
 if method=='open_requests.respond_offer' and values.get('decision')=='accept' and result.get('appointment'):safe_record('request.appointment_created',result['appointment'])
 if method=='journey.book' and result.get('state')=='Booked':safe_record('booking.confirmed',result['id'])

def unexpected(error,origin='backend'):
 """No exception message/locals/request. Private bounded spool survives rollback."""
 try:
  if not available() or not config()['errors']:return
  frames=[]
  for f in traceback.extract_tb(error.__traceback__):
   name=Path(f.filename).name
   if '/tele_tena/' in f.filename and re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',name):frames.append({'filename':'tele_tena/'+name,'lineno':f.lineno})
  payload={'exception':{'values':[{'type':type(error).__name__ if re.fullmatch('[A-Za-z0-9_]{1,80}',type(error).__name__) else 'UnexpectedError','value':'Unexpected TeleTena failure','stacktrace':{'frames':frames[-15:]}}]},'tags':{'origin':origin,'release':release(),'route':request_context()['route'],'attempt':pseudonym('attempt:'+request_context()['attempt']) if __import__('tele_tena.operations.contract',fromlist=['uuid']).uuid(request_context()['attempt']) else ''}}
  from .storage import write_spool
  write_spool(payload)
 except Exception:pass

def incident(code,severity='Warning',recovery=False):
 if not re.fullmatch('[a-z0-9_]{1,80}',code):raise ValueError('unsafe_incident_code')
 id=pseudonym('incident:'+code);t=now();old=frappe.db.sql('SELECT state FROM tt_ops_incident WHERE id=%s FOR UPDATE',(id,))
 if recovery:
  if old and old[0][0]=='Open':frappe.db.sql("UPDATE tt_ops_incident SET state='Recovered',recovered=%s,last_seen=%s WHERE id=%s",(t,t,id));safe_record('operations.recovery',id+str(t))
  return
 frappe.db.sql("INSERT INTO tt_ops_incident (id,code,severity,state,n,first_seen,last_seen) VALUES (%s,%s,%s,'Open',1,%s,%s) ON DUPLICATE KEY UPDATE acknowledged_by=IF(state='Recovered',NULL,acknowledged_by),acknowledged_at=IF(state='Recovered',NULL,acknowledged_at),last_alert=IF(state='Recovered',NULL,last_alert),first_seen=IF(state='Recovered',VALUES(last_seen),first_seen),recovered=IF(state='Recovered',NULL,recovered),state='Open',severity=VALUES(severity),n=n+1,last_seen=VALUES(last_seen)",(id,code,severity,t,t));safe_record('operations.failure',id+':'+str(t.date()),{'error_code':'unexpected'})
