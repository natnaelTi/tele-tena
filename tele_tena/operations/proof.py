"""One-run proof ledger. No web endpoints, recorder activation or business mutations.
Counters reserve before I/O and unknown outcomes cannot be automatically resent.
Only the immutable, owner-approved private PlanV1 authorizes this runner.
"""
import fcntl,hashlib,http.client,json,os,uuid
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit

class ProofBlocked(Exception):pass
class ProofRun:
 def __init__(self,root):self.root=Path(root);self.manifest=self.root/'live-verification-plan-v1.json';self.config=self.root/'providers.json'
 def _read(self,path):
  if path.is_symlink() or path.stat().st_uid!=os.geteuid() or path.stat().st_mode&0o077:raise ProofBlocked('private_file_required')
  return json.loads(path.read_text())
 def _write(self,path,data):
  tmp=path.with_name('.'+path.name+'.'+str(uuid.uuid4())+'.tmp');fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  try:
   with os.fdopen(fd,'w') as f:json.dump(data,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
   tmp.replace(path)
  finally:tmp.unlink(missing_ok=True)
 @contextmanager
 def locked(self):
  fd=os.open(self.root/'proof-execution.lock',os.O_RDWR|os.O_CREAT,0o600)
  with os.fdopen(fd,'a') as f:
   fcntl.flock(f,fcntl.LOCK_EX);yield
 def checked(self):
  m=self._read(self.manifest);c=self._read(self.config)
  plan=Path(__file__).resolve().parents[2]/'docs/operations/live-verification-plan-v1.md'
  if not m.get('approved') or not m.get('authorization') or m.get('public_plan_sha256')!=hashlib.sha256(plan.read_bytes()).hexdigest():raise ProofBlocked('approval_required')
  authorization=m['authorization']
  if authorization.get('status') in ('Completed','Revoked') or authorization.get('expires_at') and datetime.now(timezone.utc)>=datetime.fromisoformat(authorization['expires_at']):raise ProofBlocked('one_run_authorization_expired')
  d=urlsplit(c['bugsink_dsn']);expected={'posthog_ingest':c['posthog_host'],'posthog_api':c['posthog_api_host'],'posthog_project_id':str(c['posthog_project_id']),'bugsink_host':d.hostname,'bugsink_project_id':d.path.strip('/'),'email_recipient':c['owner_alert_email']}
  if 'telegram_chat' in m['destinations'] and m['destinations']['telegram_chat']!=c.get('telegram_chat'):raise ProofBlocked('destination_changed')
  amendment=m.get('amendments',{}).get('email_recipient',{})
  if amendment.get('approved') and amendment.get('recipient')==c['owner_alert_email']:expected['email_recipient']=m['destinations']['email_recipient']
  if c.get('owner_account')!='' or any(m['destinations'].get(k)!=v for k,v in expected.items()):raise ProofBlocked('destination_changed')
  return m,c
 def reserve(self,key,costs):
  with self.locked():
   m,c=self.checked()
   if m.get('phase')=='AwaitingSettledRecheck':
    allowed=key.startswith('export-settled-') or key.startswith('provider-delete-')
    if not allowed or set(costs)-{'posthog_admin_gets','recording_deletes','deletion_confirmation_gets','deletion_readback_amendment'}:raise ProofBlocked('immediate_phase_closed')
   if key in m['actions']:raise ProofBlocked('action_already_reserved')
   limits={**m['caps']}
   amendment=m.get('amendments',{}).get('email_recipient',{})
   if amendment.get('approved'):limits['email_amendment_messages']=amendment['limit']
   line_amendment=m.get('amendments',{}).get('source_map_line_readback',{})
   if line_amendment.get('approved'):limits['source_map_line_readback']=line_amendment['limit']
   deletion_amendment=m.get('amendments',{}).get('deletion_readback',{})
   if deletion_amendment.get('approved'):limits['deletion_readback_amendment']=deletion_amendment['limit']
   for kind,n in costs.items():
    if type(n) is not int or n<0 or kind not in limits or m['usage'].get(kind,0)+n>limits[kind]:raise ProofBlocked('approved_limit_reached')
   for kind,n in costs.items():m['usage'][kind]=m['usage'].get(kind,0)+n
   m['actions'][key]={'state':'Reserved','at_utc':datetime.now(timezone.utc).isoformat(),'costs':costs};self._write(self.manifest,m)
 def outcome(self,key,state,**safe):
  if set(safe)-{'http_status','bytes','checksum','error_code','stored_count','event_id','recording_id','captured_at','due_at'}:raise ProofBlocked('unsafe_result_fields')
  with self.locked():
   m,_=self.checked();m['actions'][key].update(state=state,**safe);self._write(self.manifest,m)
 @contextmanager
 def live(self):
  # Holds a separate lock through network I/O; ledger reservations use their own lock.
  fd=os.open(self.root/'proof-live.lock',os.O_RDWR|os.O_CREAT,0o600)
  with os.fdopen(fd,'a') as f:
   fcntl.flock(f,fcntl.LOCK_EX);_,c=self.checked()
   if c.get('live_test_authorized') is not False:raise ProofBlocked('unexpected_live_flag')
   self._write(self.config,{**c,'live_test_authorized':True})
   try:yield c
   finally:
    current=self._read(self.config);self._write(self.config,{**current,'live_test_authorized':False})
 def request(self,key,kind,path,method='GET',payload=None,costs=None,maximum=10*1024**2,content_type=None):
  # No caller-supplied hosts, credentials or redirect following.
  m,c=self.checked();d=urlsplit(c['bugsink_dsn']);headers={'Accept':'application/json'}
  if m.get('phase')=='AwaitingSettledRecheck':
   allowed=False
   for recording in m.get('recordings',[]):
    prefixes=tuple('/api/'+family+'/'+str(c['posthog_project_id'])+'/session_recordings/'+recording['id']+'/' for family in ('projects','environments'))
    if kind=='posthog_api' and path.startswith(prefixes) and method in ('GET','DELETE'):
     due=recording.get('recheck_due_at')
     allowed=bool(due and datetime.now(timezone.utc)>=datetime.fromisoformat(due))
   if not allowed:raise ProofBlocked('settled_checkpoint_only')
  if kind=='posthog_api':
   host=urlsplit(c['posthog_api_host']).hostname;headers['Authorization']='Bearer '+c['posthog_read_key']
   if not path.startswith(('/api/projects/'+str(c['posthog_project_id'])+'/','/api/environments/'+str(c['posthog_project_id'])+'/')):raise ProofBlocked('path_not_allowed')
   if method=='DELETE':
    match=__import__('re').fullmatch('/api/projects/'+str(c['posthog_project_id'])+'/session_recordings/([a-f0-9-]{36})/',path)
    record=next((x for x in m.get('recordings',[]) if match and x['id']==match[1]),None)
    if not record or record.get('settled_export')!='Complete' or record.get('settled_playback')!='VerifiedOffline':raise ProofBlocked('new_settled_test_recording_required')
    headers['Authorization']='Bearer '+c['posthog_delete_key']
  elif kind=='posthog_ingest':
   host=urlsplit(c['posthog_host']).hostname
   if path not in ('/capture/','/s/','/i/v0/e/'):raise ProofBlocked('path_not_allowed')
  elif kind=='bugsink_api':
   host=d.hostname;headers['Authorization']='Bearer '+c['bugsink_source_map_token']
   if not path.startswith(('/api/canonical/0/','/api/0/')):raise ProofBlocked('path_not_allowed')
  elif kind=='bugsink_ingest':
   host=d.hostname
   if path not in ('/api/'+d.path.strip('/')+'/envelope/','/api/'+d.path.strip('/')+'/store/'):raise ProofBlocked('path_not_allowed')
   headers['X-Sentry-Auth']='Sentry sentry_version=7,sentry_client=teletena-proof-v1,sentry_key='+d.username
  else:raise ProofBlocked('destination_not_allowed')
  if not path.startswith('/') or '\r' in path or '\n' in path:raise ProofBlocked('path_not_allowed')
  self.reserve(key,costs or {})
  body=payload if isinstance(payload,bytes) else json.dumps(payload).encode() if payload is not None else None
  if body:
   if content_type and (len(content_type)>200 or '\r' in content_type or '\n' in content_type):raise ProofBlocked('content_type_invalid')
   headers['Content-Type']=content_type or 'application/json'
  connection=http.client.HTTPSConnection(host,timeout=15)
  try:
   with self.live():
    connection.request(method,path,body=body,headers=headers);response=connection.getresponse();raw=response.read(maximum+1)
    if len(raw)>maximum:raise ProofBlocked('response_limit')
    self.outcome(key,'HTTPResponse',http_status=response.status,bytes=len(raw),checksum=hashlib.sha256(raw).hexdigest())
    return response.status,raw
  except Exception:
   self.outcome(key,'Unknown',error_code='transport_or_response_unavailable');raise ProofBlocked('transport_or_response_unavailable') from None
  finally:connection.close()
