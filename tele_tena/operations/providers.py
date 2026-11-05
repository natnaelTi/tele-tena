"""Versioned adapters. All credentials read server-side, no auto-enablement."""
import json,re
from urllib.parse import urlsplit
import frappe
class Unconfigured(Exception):pass
class ProviderUnavailable(Exception):pass
class ArchiveUnverified(Exception):pass

def settings():
 value=frappe.conf.get('tele_tena_operations') or {}
 path=frappe.conf.get('tele_tena_operations_config_file')
 if path:
  from pathlib import Path
  import os
  try:
   file=Path(path)
   if not file.is_absolute() or file.is_symlink() or file.stat().st_mode&0o077 or file.stat().st_uid!=os.geteuid() or file.stat().st_size>32768:return {}
   value=json.loads(file.read_text())
   if value.get('schema')!='teletena-operations-config-v1':return {}
  except (OSError,ValueError):return {}
 return value if isinstance(value,dict) else {}

def status():
 c=settings()
 return {'posthog':'Configured — Ingestion Unverified' if c.get('posthog_token') and c.get('posthog_host') else 'Unconfigured','bugsink':'Configured — Ingestion Unverified' if c.get('bugsink_dsn') else 'Unconfigured','mobile':'Configured — Receipt Unverified' if c.get('telegram_token') and c.get('telegram_chat') else 'Unconfigured','archive':'Unavailable — Project Export and Independent Playback Not Verified','source_maps':'Unavailable — Private Upload Not Verified'}
def posthog_event(event):
 c=settings();host=c.get('posthog_host');token=c.get('posthog_token')
 if host not in ('https://us.i.posthog.com','https://eu.i.posthog.com') or not isinstance(token,str):raise Unconfigured('posthog_unconfigured')
 # Construct from owned allowlist only; never forward an SDK envelope/raw request.
 from .contract import properties
 props={**properties(json.loads(event.properties)),**{k:event[k] for k in ('source','role','locale','device','environment','release_id','payment_mode','route')},'distinct_id':event.actor,'$insert_id':event.id,'attempt':event.attempt,'schema':'operations-v1','$geoip_disable':True}
 import requests
 try:
  response=requests.post(host+'/capture/',json={'api_key':token,'event':event.name,'properties':props,'timestamp':event.created.isoformat()+'Z'},timeout=(2,3),allow_redirects=False)
  if response.status_code==429:raise ProviderUnavailable('rate_limited')
  if response.status_code not in (200,201,202):raise ProviderUnavailable('provider_rejected')
 except requests.RequestException:raise ProviderUnavailable('provider_unavailable') from None
 return 'ProviderAccepted'
def sanitized_error(payload):
 # Mandatory final egress reconstruction, even if caller passed a crafted envelope.
 values=payload.get('exception',{}).get('values',[])[:1];out=[]
 for item in values:
  type_=item.get('type','UnexpectedError');type_=type_ if re.fullmatch('[A-Za-z0-9_]{1,80}',type_) else 'UnexpectedError';frames=[]
  for frame in item.get('stacktrace',{}).get('frames',[])[:15]:
   name=frame.get('filename','')
   if re.fullmatch(r'tele_tena/[A-Za-z0-9_.-]{1,100}',name) and type(frame.get('lineno')) is int:frames.append({'filename':name,'lineno':max(0,min(100000,frame['lineno']))})
  out.append({'type':type_,'value':'Unexpected TeleTena failure','stacktrace':{'frames':frames}})
 return {**({'event_id':payload['event_id']} if re.fullmatch('[a-f0-9]{32}',str(payload.get('event_id',''))) else {}),'exception':{'values':out},'platform':'python','level':'error','tags':{**({'attempt':payload['tags']['attempt']} if re.fullmatch('[a-f0-9]{64}',str(payload.get('tags',{}).get('attempt',''))) else {}),'route':__import__('tele_tena.operations.contract',fromlist=['route_template']).route_template(payload.get('tags',{}).get('route','/unknown')),'release':__import__('tele_tena.operations.runtime',fromlist=['release']).release(),'origin':payload.get('tags',{}).get('origin') if payload.get('tags',{}).get('origin') in ('backend','browser','job') else 'backend'}}
def bugsink_error(payload):
 c=settings();dsn=c.get('bugsink_dsn')
 if not dsn:raise Unconfigured('bugsink_unconfigured')
 parsed=urlsplit(dsn)
 if parsed.scheme!='https' or not parsed.hostname or not parsed.hostname.endswith('.bugsink.com'):raise Unconfigured('bugsink_host_unverified')
 # Existing Frappe dependency, isolated client; no broad SDK/framework integrations.
 from sentry_sdk import Client
 safe=sanitized_error(payload)
 client=Client(dsn=dsn,default_integrations=False,auto_enabling_integrations=False,debug=False,integrations=[],send_default_pii=False,include_local_variables=False,max_breadcrumbs=0,traces_sample_rate=0,send_client_reports=False,before_send=lambda event,hint:sanitized_error(event))
 client.capture_event(safe);client.flush(timeout=3)
 # SDK flush is not proof of provider ingestion. Do not label this Delivered/Accepted.
 return 'TransportAttempted'
def archive_export(recording):
 # Official snapshot API is mutable, provider/project-specific and not vanilla rrweb.
 # Do not invent completeness or import metadata as playable snapshots.
 raise ArchiveUnverified('selected_project_export_and_player_proof_required')
def telegram(message):
 c=settings()
 if not c.get('telegram_token') or not c.get('telegram_chat'):raise Unconfigured('mobile_unconfigured')
 import requests
 try:
  r=requests.post('https://api.telegram.org/bot'+c['telegram_token']+'/sendMessage',json={'chat_id':c['telegram_chat'],'text':message,'disable_web_page_preview':True},timeout=(2,3),allow_redirects=False)
  if r.status_code!=200 or not r.json().get('ok'):raise ProviderUnavailable('mobile_rejected')
 except requests.RequestException:raise ProviderUnavailable('mobile_unknown') from None
 return 'ProviderAccepted'
