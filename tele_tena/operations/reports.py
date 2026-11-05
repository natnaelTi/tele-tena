"""Deterministic measured aggregates; calendar quarters in Africa/Nairobi."""
import hashlib,json,re,uuid
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
import frappe
from . import runtime as rt
ZONE=ZoneInfo('Africa/Nairobi')
def quarter_bounds(period):
 if not re.fullmatch(r'20\d{2}-Q[1-4]',period):raise ValueError('invalid_quarter')
 y,q=int(period[:4]),int(period[-1]);month=(q-1)*3+1
 start=datetime(y,month,1,tzinfo=ZONE);end=datetime(y+1,1,1,tzinfo=ZONE) if q==4 else datetime(y,month+3,1,tzinfo=ZONE)
 return start.astimezone(timezone.utc).replace(tzinfo=None),end.astimezone(timezone.utc).replace(tzinfo=None)
def aggregate(limit=500):
 events=frappe.db.sql('SELECT * FROM tt_ops_event WHERE aggregated=0 ORDER BY created,id LIMIT %s FOR UPDATE',(limit,),as_dict=True)
 for e in events:
  props=json.loads(e.properties);dimensions={k:e[k] for k in ('source','role','locale','device','environment','release_id','payment_mode','route')};dimensions['synthetic']=props.get('synthetic','unknown');dimensions.update({k:props[k] for k in ('step','document','outcome','error_code','category') if k in props})
  day=e.created.replace(tzinfo=timezone.utc).astimezone(ZONE).date();encoded=json.dumps(dimensions,sort_keys=True);key=hashlib.sha256((str(day)+e.name+encoded).encode()).hexdigest()
  frappe.db.sql('INSERT INTO tt_ops_daily VALUES (%s,%s,%s,%s,1) ON DUPLICATE KEY UPDATE n=n+1',(key,day,e.name,encoded))
  family=e.name.split('.')[0];state='Completed' if e.name in ('application.submitted','booking.confirmed','request.appointment_created','consultation.documentation_completed') else 'Saved' if e.name=='application.saved' else 'Resumed' if e.name.endswith('resumed') else 'Blocked' if e.name in ('validation.failed','upload.failed','consultation.connection_failed') else 'In Progress'
  if family in ('application','booking','request','consultation'):
   id=hashlib.sha256((e.attempt+family).encode()).hexdigest();frappe.db.sql("INSERT INTO tt_ops_attempt VALUES (%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE last_seen=GREATEST(last_seen,VALUES(last_seen)),state=IF(completed IS NOT NULL,'Completed',VALUES(state)),completed=COALESCE(completed,VALUES(completed))",(id,family,e.created,e.created,state,e.created if state=='Completed' else None,encoded))
  frappe.db.sql('UPDATE tt_ops_event SET aggregated=1 WHERE id=%s',(e.id,))
 return len(events)
def insights(include_synthetic=False):
 items=frappe.db.sql('SELECT day,name,dimensions,n FROM tt_ops_daily WHERE day>=DATE_SUB(CURDATE(),INTERVAL 90 DAY) ORDER BY day DESC LIMIT 5000',as_dict=True)
 result=[]
 for x in items:
  x.dimensions=json.loads(x.dimensions)
  if not include_synthetic and x.dimensions['synthetic']!='no':continue
  result.append(x)
 return {'events':result,'window_days':90,'completion_window_hours':24,'interpretation':'Incomplete and saved attempts are not assumed abandoned. Event counts are not unique people.','coverage':frappe.db.sql('SELECT day,kind,n FROM tt_ops_counter WHERE day>=DATE_SUB(CURDATE(),INTERVAL 7 DAY)',as_dict=True),'first_collected':frappe.db.sql('SELECT MIN(day) day FROM tt_ops_daily',as_dict=True)[0].day,'include_synthetic':include_synthetic}
def compile_report(period,clock=None):
 start,end=quarter_bounds(period);clock=clock or rt.now()
 if clock<start:raise ValueError('future_quarter')
 rows=frappe.db.sql('SELECT day,name,dimensions,n FROM tt_ops_daily WHERE day>=%s AND day<%s ORDER BY day,name,id',(start.replace(tzinfo=timezone.utc).astimezone(ZONE).date(),end.replace(tzinfo=timezone.utc).astimezone(ZONE).date()),as_dict=True)
 events={};excluded=0;segments={};patterns={}
 for r in rows:
  d=json.loads(r.dimensions)
  if d.get('synthetic')!='no':excluded+=r.n;continue
  events[r.name]=events.get(r.name,0)+r.n
  if r.name in ('validation.failed','upload.failed','support.submitted'):
   pattern=json.dumps({k:d[k] for k in ('step','document','error_code','category') if k in d},sort_keys=True);patterns[pattern]=patterns.get(pattern,0)+r.n
  key=json.dumps({k:d[k] for k in ('locale','device','release_id')},sort_keys=True);segments[key]=segments.get(key,0)+r.n
 attempts=frappe.db.sql("SELECT family,state,COUNT(*) n,AVG(TIMESTAMPDIFF(SECOND,started,completed)) seconds FROM tt_ops_attempt WHERE started>=%s AND started<%s AND JSON_UNQUOTE(JSON_EXTRACT(dimensions,'$.synthetic'))='no' GROUP BY family,state",(start,min(end,clock)),as_dict=True)
 # Attempt rows include synthetic activity. Never silently mix them into a production funnel.
 payload={'period':period,'timezone':'Africa/Nairobi','start_utc':str(start),'end_utc_exclusive':str(end),'incomplete_period':clock<end,'events':events,'sample_size':sum(events.values()),'excluded_synthetic_events':excluded,'segments':segments,'validation_upload_support_patterns':patterns,'support_resolution':frappe.db.sql('SELECT category,COUNT(*) n,AVG(TIMESTAMPDIFF(SECOND,created,resolved_at)) seconds FROM tt_ops_support WHERE created>=%s AND created<%s GROUP BY category',(start,min(end,clock)),as_dict=True),'attempts':attempts,'attempt_segmentation_limit':'Attempts are bounded correlation groups, not unique people. Staff/demo are excluded.','coverage':frappe.db.sql('SELECT day,kind,n FROM tt_ops_counter WHERE day>=%s AND day<%s',(start.date(),end.date()),as_dict=True),'recurring_issues_lifetime_snapshot':frappe.db.sql('SELECT code,state,n,first_seen,last_seen FROM tt_ops_incident WHERE first_seen<%s AND last_seen>=%s',(end,start),as_dict=True),'archive':frappe.db.sql('SELECT state,COUNT(*) n,SUM(size_bytes) bytes FROM tt_ops_archive GROUP BY state',as_dict=True),'notes':'Measured events only. Delays do not establish confusion or abandonment. No AI interpretation.','generated_through_utc':str(min(clock,end))}
 canonical=json.dumps(payload,sort_keys=True,default=str);digest=hashlib.sha256(json.dumps({k:v for k,v in payload.items() if k!='generated_through_utc'},sort_keys=True,default=str).encode()).hexdigest();old=frappe.db.sql('SELECT id,version FROM tt_ops_report WHERE period=%s AND digest=%s',(period,digest),as_dict=True)
 if old:return dict(old[0],idempotent=True)
 frappe.db.sql('SELECT id FROM tt_ops_config WHERE id=1 FOR UPDATE')
 version=frappe.db.sql('SELECT COALESCE(MAX(version),0)+1 FROM tt_ops_report WHERE period=%s',(period,))[0][0];id=str(uuid.uuid4())
 frappe.db.sql('INSERT INTO tt_ops_report VALUES (%s,%s,%s,%s,%s,%s,%s)',(id,period,version,digest,canonical,'',rt.now()));return {'id':id,'version':version}
