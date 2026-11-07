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
 from .contract import properties,VERSION
 props={**properties(json.loads(event.properties)),**{k:event[k] for k in ('source','role','locale','device','environment','release_id','payment_mode','route')},'distinct_id':event.actor,'$insert_id':event.id,'attempt':event.attempt,'schema':VERSION,'$geoip_disable':True}
 import requests
 try:
  response=requests.post(host+'/capture/',json={'api_key':token,'event':event.name,'properties':props,'timestamp':event.created.isoformat()+'Z'},timeout=(2,3),allow_redirects=False)
  if response.status_code==429:raise ProviderUnavailable('rate_limited')
  if response.status_code not in (200,201,202):raise ProviderUnavailable('provider_rejected')
 except requests.RequestException:raise ProviderUnavailable('provider_unavailable') from None
 return 'ProviderAccepted'
def javascript_assets():
 from pathlib import Path
 try:
  manifest=json.loads((Path(__file__).resolve().parents[1]/'public/review/release.json').read_text());ids=manifest.get('debug_ids',{})
  return {'app:///'+name:ids.get(name) for name in manifest['files'] if name.startswith('assets/') and name.endswith('.js')}
 except (OSError,ValueError,KeyError):return {}
def sanitized_error(payload):
 # Reconstruct from trusted release assets, never raw stack messages/URLs/locals.
 origin=payload.get('tags',{}).get('origin');browser=origin=='browser';assets=javascript_assets() if browser else {};values=payload.get('exception',{}).get('values',[])[:1];out=[];images=[]
 for item in values:
  type_=item.get('type','UnexpectedError');type_=type_ if re.fullmatch('[A-Za-z0-9_]{1,80}',type_) else 'UnexpectedError';frames=[]
  for frame in item.get('stacktrace',{}).get('frames',[])[:12]:
   name=frame.get('filename','');line=frame.get('lineno')
   if not isinstance(name,str):continue
   if type(line) is not int or not 0<line<=1000000:continue
   if browser and name in assets:
    clean={'filename':name,'abs_path':name,'lineno':line};column=frame.get('colno')
    if type(column) is int and 0<column<=10000000:clean['colno']=column
    frames.append(clean);debug_id=assets[name]
    if isinstance(debug_id,str) and re.fullmatch('[a-f0-9-]{36}',debug_id):images.append({'type':'sourcemap','code_file':name,'debug_id':debug_id})
   elif not browser and re.fullmatch(r'tele_tena/[A-Za-z0-9_.-]{1,100}',name):frames.append({'filename':name,'lineno':line})
  out.append({'type':type_,'value':'Unexpected TeleTena failure','stacktrace':{'frames':frames}})
 result={**({'event_id':payload['event_id']} if re.fullmatch('[a-f0-9]{32}',str(payload.get('event_id',''))) else {}),'exception':{'values':out},'platform':'javascript' if browser else 'python','level':'error','tags':{**({'attempt':payload['tags']['attempt']} if re.fullmatch('[a-f0-9]{64}',str(payload.get('tags',{}).get('attempt',''))) else {}),'route':__import__('tele_tena.operations.contract',fromlist=['route_template']).route_template(payload.get('tags',{}).get('route','/unknown')),'release':__import__('tele_tena.operations.runtime',fromlist=['release']).release(),'origin':origin if origin in ('backend','browser','job') else 'backend'}}
 if images:result['debug_meta']={'images':list({i['code_file']:i for i in images}.values())}
 return result
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
def archive_capability():
 from pathlib import Path
 import os
 c=settings();value=c.get('archive_proof_file')
 if not value:return False
 try:
  file=Path(value)
  if not file.is_absolute() or file.is_symlink() or file.stat().st_uid!=os.geteuid() or file.stat().st_mode&0o077 or file.stat().st_size>16384:return False
  proof=json.loads(file.read_text())
  return proof.get('project_id')==str(c.get('posthog_project_id')) and proof.get('format')=='teletena-web-replay-v1' and proof.get('settled_export') is True and proof.get('independent_playback') is True and proof.get('provider_deletion_verified') is True and proof.get('player_sha256')==__import__('hashlib').sha256((Path(__file__).parent/'player.js').read_bytes()).hexdigest()
 except (OSError,ValueError):return False

def archive_export(recording):
 if not archive_capability():raise ArchiveUnverified('selected_project_export_and_player_proof_required')
 c=settings();project=str(c.get('posthog_project_id'));host=c.get('posthog_api_host')
 if host!='https://eu.posthog.com' or not c.get('posthog_read_key'):raise Unconfigured('archive_project_unconfigured')
 import requests
 from .posthog_export import export_recording
 import time
 deadline=time.monotonic()+40
 def fetch(path,maximum):
  try:
   if time.monotonic()>=deadline:raise ProviderUnavailable('archive_wall_budget')
   response=requests.get(host+path,headers={'Authorization':'Bearer '+c['posthog_read_key']},timeout=(2,10),allow_redirects=False,stream=True)
   if response.status_code==429:raise ProviderUnavailable('archive_rate_limited')
   raw=b''
   for block in response.iter_content(65536):
    raw+=block
    if len(raw)>maximum:raise ProviderUnavailable('archive_response_limit')
   return response.status_code,raw
  except requests.RequestException:raise ProviderUnavailable('archive_provider_unavailable') from None
 return export_recording(project,recording['provider_id'],fetch)

def archive_delete_provider(recording_id):
 if not archive_capability():raise ArchiveUnverified('archive_project_proof_required')
 if not re.fullmatch('[a-f0-9-]{36}',recording_id):raise ProviderUnavailable('archive_identifier_invalid')
 c=settings()
 if c.get('posthog_api_host')!='https://eu.posthog.com' or not c.get('posthog_delete_key'):raise Unconfigured('archive_delete_unconfigured')
 import requests
 try:
  response=requests.delete(c['posthog_api_host']+'/api/projects/'+str(c['posthog_project_id'])+'/session_recordings/'+recording_id+'/',headers={'Authorization':'Bearer '+c['posthog_delete_key']},timeout=(2,10),allow_redirects=False)
  if response.status_code not in (200,202,204,404):raise ProviderUnavailable('archive_delete_unconfirmed')
 except requests.RequestException:raise ProviderUnavailable('archive_delete_unknown') from None
 return 'ProviderAccepted'
def archive_provider_absent(recording_id):
 if not archive_capability():raise ArchiveUnverified('archive_project_proof_required')
 if not re.fullmatch('[a-f0-9-]{36}',recording_id):raise ProviderUnavailable('archive_identifier_invalid')
 c=settings();import requests
 try:
  response=requests.get(c['posthog_api_host']+'/api/projects/'+str(c['posthog_project_id'])+'/session_recordings/'+recording_id+'/',headers={'Authorization':'Bearer '+c['posthog_read_key']},timeout=(2,10),allow_redirects=False)
  if response.status_code==404:return True
  if response.status_code==200:return False
  raise ProviderUnavailable('archive_delete_confirmation_unavailable')
 except requests.RequestException:raise ProviderUnavailable('archive_delete_confirmation_unknown') from None
def telegram(message):
 c=settings()
 if not c.get('telegram_token') or not c.get('telegram_chat'):raise Unconfigured('mobile_unconfigured')
 import requests
 try:
  r=requests.post('https://api.telegram.org/bot'+c['telegram_token']+'/sendMessage',json={'chat_id':c['telegram_chat'],'text':message,'disable_web_page_preview':True},timeout=(2,3),allow_redirects=False)
  if r.status_code!=200 or not r.json().get('ok'):raise ProviderUnavailable('mobile_rejected')
 except requests.RequestException:raise ProviderUnavailable('mobile_unknown') from None
 return 'ProviderAccepted'

def replay_snapshot(session, chunk, events):
 """Only gateway-projected snapshots. Stable UUID and timestamps make retries safe."""
 c=settings();host=c.get('posthog_host');token=c.get('posthog_token')
 if host not in ('https://eu.i.posthog.com','https://us.i.posthog.com') or not token:raise Unconfigured('replay_unconfigured')
 import requests,uuid
 payload={'event':'$snapshot','uuid':str(uuid.UUID(chunk['id'][:32])),'timestamp':session['captured'].isoformat()+'Z','properties':{'token':token,'distinct_id':session['owner_actor'],'$session_id':session['provider_id'],'$window_id':session['window_id'],'$snapshot_data':events,'$lib':'web','$lib_version':'1.446.0','$snapshot_host':'replay.invalid','$geoip_disable':True,'schema':'teletena-masked-web-v2','role':session['role'],'locale':session['locale'],'device':session['device'],'release':session['release_id'],'environment':session['environment'],'payment_mode':session['payment_mode'],'synthetic':'yes' if session['synthetic'] else 'no'}}
 try:
  response=requests.post(host+'/s/',json=[payload],timeout=(2,3),allow_redirects=False)
  if response.status_code not in (200,201,202):raise ProviderUnavailable('snapshot_rate_limited' if response.status_code==429 else 'snapshot_rejected')
 except requests.RequestException:raise ProviderUnavailable('snapshot_unknown') from None
 return 'ProviderAccepted'
