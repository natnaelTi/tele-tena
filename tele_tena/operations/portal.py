"""Reviewer projections: no provider I/O, raw event IDs, credentials or business writes."""
import json,re
from datetime import timedelta,timezone
from zoneinfo import ZoneInfo
from pathlib import Path
import frappe
from . import runtime as rt,providers
from tele_tena.api.journey import fail

FAMILIES={'application','booking','request','consultation'}

def integrations():
 c=providers.settings();saved=rt.config()
 history=json.loads((Path(__file__).resolve().parents[2]/'docs/operations/provider-verification-summary.json').read_text())
 bound=bool(frappe.conf.get('tele_tena_operations_config_file') or frappe.conf.get('tele_tena_operations'))
 configured={'posthog':bool(c.get('posthog_token') and c.get('posthog_host') in ('https://eu.i.posthog.com','https://us.i.posthog.com')),'bugsink':bool(c.get('bugsink_dsn')),'mobile':bool(c.get('telegram_token') and c.get('telegram_chat')),'archive':bool(c and providers.archive_capability()),'source_maps':bool(c.get('bugsink_source_map_token'))}
 flags={'posthog':'analytics','bugsink':'errors','mobile':'alerts','archive':'archive'}
 result=[]
 for key in ('posthog','bugsink','mobile','archive','source_maps'):
  enabled=bool(saved.get(flags.get(key,''))) if key!='source_maps' else False
  observed=[]
  if key=='posthog':observed=frappe.db.sql('SELECT delivery state,COUNT(*) n,MAX(created) at FROM tt_ops_event GROUP BY delivery',as_dict=True)
  if key=='bugsink':observed=frappe.db.sql('SELECT state,COUNT(*) n,MAX(created) at FROM tt_ops_error GROUP BY state',as_dict=True)
  if key=='mobile':observed=frappe.db.sql("SELECT state,COUNT(*) n,MAX(modified) at FROM tt_ops_alert WHERE channel='telegram' GROUP BY state",as_dict=True)
  result.append({'key':key,'site_configured':configured[key],'enabled':enabled,'effective':bool(configured[key] and enabled),'configuration_state':('Configured' if configured[key] else 'Unconfigured'),'health':'Not Observed' if not observed else 'Recorded Outcomes Only','observed':observed,'last_verified':history[key],'next_action':('Before binding private configuration, review and disable saved external analytics, errors, alerts, replay and export switches. Binding credentials while switches are enabled can activate delivery; obtain separate activation approval.' if not bound else 'Review prerequisites and effective settings before explicitly enabling this capability.'),'current_build_verified':False})
 return {'site_binding_present':bound,'private_configuration_loaded':bool(c),'observed_at':rt.now(),'environment':saved['environment'],'release':rt.release(),'scenario':bool(frappe.conf.get('tele_tena_ops_review_scenario')),'items':result}

def journeys(family='application',days=7,locale='all',device='all',payment_mode='all',source='all',include_synthetic=0):
 rt.reviewer()
 if family not in FAMILIES or str(days) not in ('1','7','30','90') or locale not in ('all','en','am','om') or device not in ('all','mobile','tablet','desktop','unknown') or payment_mode not in ('all','Wallet','Offline') or source not in ('all','server','browser'):fail('Choose supported journey filters.','operations_filter_invalid')
 synthetic=str(include_synthetic)=='1';clock=rt.now();since=clock-timedelta(days=int(days));clauses=[];args=[]
 for key,value in [('locale',locale),('device',device),('payment_mode',payment_mode),('source',source)]:
  if value!='all':clauses.append("JSON_UNQUOTE(JSON_EXTRACT(dimensions,'$."+key+"'))=%s");args.append(value)
 if not synthetic:clauses.append("JSON_UNQUOTE(JSON_EXTRACT(dimensions,'$.synthetic'))='no'")
 tail=(' AND '+' AND '.join(clauses)) if clauses else ''
 attempts=frappe.db.sql("SELECT state,COUNT(*) n,SUM(completed IS NOT NULL AND TIMESTAMPDIFF(SECOND,started,completed) BETWEEN 0 AND 86400) within_window,SUM(completed IS NOT NULL AND TIMESTAMPDIFF(SECOND,started,completed)>86400) later,SUM(completed IS NULL AND last_seen<%s) interrupted FROM tt_ops_attempt WHERE family=%s AND started>=%s AND started<=%s"+tail+' GROUP BY state',(clock-timedelta(hours=24),family,since,clock,*args),as_dict=True)
 # Daily aggregate resolution is explicit: local calendar dates, not exact rolling-hour events.
 first_day=since.replace(tzinfo=timezone.utc).astimezone(ZoneInfo('Africa/Nairobi')).date();last_day=clock.replace(tzinfo=timezone.utc).astimezone(ZoneInfo('Africa/Nairobi')).date()
 events=frappe.db.sql("SELECT name,JSON_UNQUOTE(JSON_EXTRACT(dimensions,'$.source')) source,SUM(n) n FROM tt_ops_daily WHERE day>=%s AND day<=%s AND name LIKE %s"+tail+' GROUP BY name,source ORDER BY name,source',(first_day,last_day,family+'.%',*args),as_dict=True)
 total=sum(x.n for x in attempts);completed=sum(int(x.within_window or 0) for x in attempts)
 coverage=frappe.db.sql('SELECT kind,SUM(n) n FROM tt_ops_counter WHERE day>=%s AND day<=%s AND day<>%s GROUP BY kind',(first_day,last_day,'1970-01-01'),as_dict=True)
 return {'family':family,'days':int(days),'since':since,'through':clock,'attempts':attempts,'observed_attempts':total,'completed_in_window':completed,'completed_later':sum(int(x.later or 0) for x in attempts),'interrupted':sum(int(x.interrupted or 0) for x in attempts),'completion_percent':round(completed*100/total,1) if total else None,'sample_state':'No Eligible Data' if not total else 'Insufficient Sample' if total<20 else 'Observed','events':events,'coverage':coverage,'coverage_scope':'Site-wide counters; not filtered journey denominators.','daily_start':str(first_day),'daily_end':str(last_day),'include_synthetic':synthetic,'completion_window_hours':24,'native_collection_enabled':rt.config()['native_events'],'heatmap_state':'Unavailable — No Approved Public Interaction Coordinates','correlation_note':'Bounded correlation groups, not unique people. Stage counts are independent events, not a conversion funnel. Saved or interrupted does not mean abandoned. Attempt cohorts use first observed dimensions; daily stages use Nairobi calendar dates.'}

def support_queue(state='all',priority='all',ownership='all',offset=0):
 user=rt.reviewer();clauses=[];args=[]
 from .support import STATES,reviewers
 if state!='all':
  if state not in STATES:fail('Choose a supported report status.')
  clauses.append('s.state=%s');args.append(state)
 if priority!='all':
  if priority not in ('Low','Normal','High','Critical'):fail('Choose a supported priority.')
  clauses.append('s.priority=%s');args.append(priority)
 if ownership not in ('all','mine','unassigned'):fail('Choose a supported ownership filter.')
 if ownership=='mine':clauses.append('s.assignee=%s');args.append(user)
 if ownership=='unassigned':clauses.append("(s.assignee IS NULL OR s.assignee='')")
 try:offset=int(offset)
 except (ValueError,TypeError):fail('Choose a valid queue page.')
 if offset<0 or offset>100000:fail('Choose a valid queue page.')
 where=' WHERE '+' AND '.join(clauses) if clauses else ''
 total=frappe.db.sql('SELECT COUNT(*) FROM tt_ops_support s'+where,args)[0][0]
 items=frappe.db.sql("SELECT s.id,s.category,s.state,s.priority,s.assignee,COALESCE(u.full_name,s.assignee) assignee_name,s.created,s.modified FROM tt_ops_support s LEFT JOIN tabUser u ON u.name=s.assignee"+where+" ORDER BY FIELD(s.priority,'Critical','High','Normal','Low'),s.created,s.id LIMIT 30 OFFSET %s",(*args,offset),as_dict=True)
 return {'items':items,'total':total,'offset':offset,'page_size':30,'reviewers':frappe.db.sql("SELECT name id,full_name label FROM tabUser WHERE name IN %s ORDER BY full_name,name",(reviewers() or ['Administrator'],),as_dict=True),'observed_at':rt.now()}

def assign(id,state,priority,assignee=None):
 user=rt.reviewer()
 from .support import allowed,STATES,reviewers
 from tele_tena.api.journey import audit
 allowed(id)
 if state not in STATES or priority not in ('Low','Normal','High','Critical') or assignee and assignee!='Administrator' and assignee not in reviewers():fail('Choose an authorized reviewer, status and priority.')
 frappe.db.sql('SELECT id FROM tt_ops_support WHERE id=%s FOR UPDATE',(id,))
 frappe.db.sql('UPDATE tt_ops_support SET state=%s,priority=%s,assignee=%s,modified=%s,resolved_at=IF(%s=\'Resolved\',COALESCE(resolved_at,%s),resolved_at) WHERE id=%s',(state,priority,assignee or None,rt.now(),state,rt.now(),id))
 audit(id,'SupportAssigned',{'state':state,'priority':priority,'assigned':bool(assignee),'assignee':assignee or None})
 rt.safe_record('support.resolved' if state=='Resolved' else 'support.triaged',id+':'+state)
 return {'saved':True}

def worker_observation():
 """Operator-enqueued read-only probe; not a whitelisted API or provider test."""
 import os
 c=providers.settings();v=rt.config()
 return {'pid':os.getpid(),'site_bound':bool(frappe.conf.get('tele_tena_operations_config_file') or frappe.conf.get('tele_tena_operations')),'private_configuration_loaded':bool(c),'flags':{k:v[k] for k in ('analytics','errors','replay','archive','alerts')},'release':rt.release(),'observed_at':str(rt.now())}

def archive_records(state='all',reference='',offset=0):
 rt.reviewer()
 if state not in ('all','Capturing','Pending','Exporting','Verified','Failed','Incomplete','Expired'):fail('Choose a supported recording state.')
 if not isinstance(reference,str) or reference and not re.fullmatch('[a-f0-9]{1,64}',reference):fail('Use a recording reference containing hexadecimal characters only.')
 try:offset=int(offset)
 except (TypeError,ValueError):fail('Choose a valid archive page.')
 if offset<0 or offset>1000000:fail('Choose a valid archive page.')
 clauses=[];args=[]
 if state!='all':clauses.append('state=%s');args.append(state)
 if reference:clauses.append('id LIKE %s');args.append(reference+'%')
 where=' WHERE '+' AND '.join(clauses) if clauses else ''
 total=frappe.db.sql('SELECT COUNT(*) FROM tt_ops_archive'+where,args)[0][0]
 items=frappe.db.sql('SELECT id,captured,expires,state,size_bytes,failure_code,tries FROM tt_ops_archive'+where+' ORDER BY captured DESC,id LIMIT 30 OFFSET %s',(*args,offset),as_dict=True)
 return {'items':items,'total':total,'offset':offset,'page_size':30}
