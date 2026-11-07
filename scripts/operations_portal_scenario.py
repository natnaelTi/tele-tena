"""Explicit loopback-only Operations review fixture; no business or provider records.
Run using compatible Bench Python with PYTHONPATH set to this app. Credentials are
written only to a private local manifest. Repeats preserve the original scenario.
"""
import os,json,uuid,secrets,hashlib
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
SITE='teletena-ops-v154-release.localhost';BENCH=Path('/home/frappe/teletena-compat/bench')
assert os.environ.get('TELE_TENA_LOCAL_OPERATIONS_SCENARIO')=='1'
assert (BENCH/'sites'/SITE/'site_config.json').is_file()
os.chdir(BENCH/'sites')
import frappe
frappe.init(site=SITE,sites_path=str(BENCH/'sites'));frappe.connect();frappe.set_user('Administrator')
from tele_tena.operations import runtime as rt,reports,support,jobs,storage,archive
from tele_tena.api import operations as ops
manifest=BENCH/'sites'/SITE/'private/operations-portal-review.json'
if manifest.exists():
 print('Existing isolated scenario retained; no accounts, dates or events refreshed.');frappe.destroy();raise SystemExit(0)
assert not frappe.conf.get('tele_tena_operations_config_file') and not frappe.conf.get('tele_tena_operations')
assert not any(rt.config()[k] for k in ('analytics','errors','alerts','replay','archive'))
assert not frappe.db.sql("SELECT id FROM tt_ops_event LIMIT 1"),'Use an empty disposable operations site; existing metrics are not overwritten.'
sitefile=BENCH/'sites'/SITE/'site_config.json';conf=json.loads(sitefile.read_text());conf['tele_tena_ops_review_scenario']='operations-portal-review-v1';sitefile.write_text(json.dumps(conf,indent=2)+'\n');sitefile.chmod(0o600);frappe.conf.tele_tena_ops_review_scenario=conf['tele_tena_ops_review_scenario']
accounts={};owned=[]
from frappe.utils.password import update_password
for role,frappe_role in [('reviewer','Tele Tena Approver'),('patient','Tele Tena Patient'),('clinician','Tele Tena Clinician')]:
 email='portal-'+role+'@ops-review.invalid';assert not frappe.db.exists('User',email),'Never overwrite an existing account'
 user=frappe.get_doc({'doctype':'User','email':email,'first_name':{'reviewer':'Mekdes','patient':'Saron','clinician':'Hana'}[role],'last_name':'Review Scenario','enabled':1,'user_type':'Website User','send_welcome_email':0,'roles':[{'role':frappe_role}]});user.insert();password=secrets.token_urlsafe(24);update_password(email,password);accounts[role]={'user':email,'password':password}
clock=rt.now();context={'route':'/onboarding','locale':'en','device':'desktop'}
for family,count,complete_event in [('application',8,'application.submitted'),('booking',5,'booking.confirmed'),('request',4,'request.appointment_created'),('consultation',3,'consultation.documentation_completed')]:
 for i in range(count):
  attempt=str(uuid.uuid4());t=clock-timedelta(days=2,hours=i)
  user=accounts['clinician' if family=='application' else 'patient']['user']
  first={'application':'application.started','booking':'booking.offering_selected','request':'request.draft_progressed','consultation':'consultation.join_attempted'}[family]
  with patch.object(rt,'now',return_value=t):rt.record(first,'portal-scenario-'+attempt,{},'browser',attempt,user,{**context,'attempt':attempt,'locale':['en','am','om'][i%3],'device':['desktop','mobile','tablet'][i%3]})
  ending=complete_event if i<count-3 else 'application.saved' if family=='application' and i==count-3 else 'application.resumed' if family=='application' and i==count-2 else None
  if ending:
   with patch.object(rt,'now',return_value=t+timedelta(hours=1)):rt.record(ending,'portal-scenario-end-'+attempt,{'step':'review'} if family=='application' else {},'browser' if ending.endswith('resumed') else 'server',attempt,user,{**context,'attempt':attempt,'locale':['en','am','om'][i%3],'device':['desktop','mobile','tablet'][i%3]})
reports.aggregate(500)
with patch('tele_tena.communications.wake_dispatch'):
 for i,(category,state,priority) in enumerate([('Technical','New','High'),('Application','In Progress','Normal'),('Accessibility','Waiting for User','Normal'),('Booking','Resolved','Low')]):
  frappe.set_user(accounts['patient']['user']);r=ops.support_submit(category,['The navigation labels wrap on my small screen.','I need help finding the application feedback.','Please explain the keyboard shortcuts for navigation.','I found the appointment time after checking my timezone.'][i],False,'portal-review-'+str(i),{'route':'/support'});owned.append(r['id']);frappe.set_user(accounts['reviewer']['user']);ops.support_assign(r['id'],state,priority,accounts['reviewer']['user'] if i else None)
  if i:ops.support_reply(r['id'],'Review the navigation guidance before replying.','Internal','portal-note-'+str(i),state,priority,accounts['reviewer']['user'])
  if i==3:ops.support_reply(r['id'],'The displayed time uses your chosen timezone. Thank you for confirming.','User','portal-visible-'+str(i),state,priority,accounts['reviewer']['user'])
frappe.set_user('Administrator')
with patch.object(rt,'now',return_value=clock-timedelta(hours=4)):
 jobs.beat('scheduler');jobs.beat('worker_completed')
for _ in range(3):rt.count('events_dropped',100)
period=str(clock.year)+'-Q'+str((clock.month-1)//3+1);report=reports.compile_report(period,include_synthetic=True)
# Safe, entirely generated local recording. No browser recorder/provider recording.
from tele_tena.operations.replay_format import normalize
source=[{'source':'blob_v2','blob_key':'0'}];events=[{'type':4,'timestamp':1000,'data':{'width':700,'height':400,'href':'http://proof.invalid/ops-proof-v1/'}},{'type':2,'timestamp':1001,'data':{'node':{'type':0,'id':0,'childNodes':[{'type':2,'id':1,'tagName':'html','attributes':{},'childNodes':[{'type':2,'id':2,'tagName':'body','attributes':{},'childNodes':[{'type':2,'id':3,'tagName':'h1','attributes':{},'childNodes':[{'type':3,'id':4,'textContent':'Masked review scenario'}]}]}]}]}}}]
normalized=normalize(source,{'0':b'\n'.join(json.dumps(['review',e]).encode() for e in events)})
import gzip
content=gzip.compress(json.dumps(normalized).encode());key=storage.put(content,rt.config()['recording_bytes'],rt.config()['archive_bytes'],kind='replay');id=hashlib.sha256(b'operations-portal-review-local-replay-v1').hexdigest()
frappe.db.sql("INSERT INTO tt_ops_archive (id,provider_id,captured,expires,state,size_bytes,sha256,format_version,player_version,object_key,verified,modified) VALUES (%s,'local-review-only',%s,%s,'Verified',%s,%s,%s,%s,%s,%s,%s)",(id,clock,clock+timedelta(days=90),len(content),normalized['sha256'],normalized['format'],'local-review-only',key,clock,clock))
# This local fixture is only playable through the explicitly isolated WSGI harness.
frappe.db.commit();manifest.write_text(json.dumps({'dataset':'operations-portal-review-v1','site':SITE,'accounts':accounts,'support':owned,'report':report['id'],'local_replay':id,'created':str(clock)},indent=2));manifest.chmod(0o600);frappe.destroy()
print('Isolated Operations scenario created; private account manifest written. No provider I/O or business/financial scenarios created.')
