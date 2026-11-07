"""One separately authorized native-gateway proof. Original PlanV1 stays closed."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
from tele_tena.operations.proof import ProofRun,ProofBlocked

class NativeRun(ProofRun):
 def __init__(self,root):
  super().__init__(root);self.manifest=self.root/'live-verification-native-v2.json'
 def checked(self):
  m,c=super().checked()
  original=self._read(self.root/'live-verification-plan-v1.json')
  plan=Path(__file__).resolve().parents[2]/'docs/operations/live-verification-amendment-v2-proposal.md'
  if (original['authorization']['status']!='Completed' or not original.get('amendments',{}).get('native_gateway',{}).get('approved') or m.get('native_plan_sha256')!=hashlib.sha256(plan.read_bytes()).hexdigest()):raise ProofBlocked('native_amendment_required')
  return m,c
 def reserve(self,key,costs):
  if set(costs)-{'replays','snapshot_upload_requests','recording_bytes','posthog_admin_gets','recording_deletes','deletion_confirmation_gets'}:raise ProofBlocked('native_operation_not_approved')
  super().reserve(key,costs)
  # Separate amendment counters are authoritative; preserve cumulative original usage.
  with self.locked():
   original=self._read(self.root/'live-verification-plan-v1.json')
   for kind,n in costs.items():original['usage'][kind]=original['usage'].get(kind,0)+n
   self._write(self.root/'live-verification-plan-v1.json',original)
 def request(self,key,kind,path,**kwargs):
  if kind not in ('posthog_api','posthog_ingest'):raise ProofBlocked('native_destination_not_approved')
  m,c=self.checked()
  if kind=='posthog_api':
   method=kwargs.get('method','GET');costs=kwargs.get('costs',{})
   if method=='DELETE':
    if costs!={'recording_deletes':1}:raise ProofBlocked('native_delete_cost_required')
   elif method=='GET':
    if costs not in ({'posthog_admin_gets':1},{'deletion_confirmation_gets':1}):raise ProofBlocked('native_read_cost_required')
   else:raise ProofBlocked('native_api_method_not_approved')
   prefixes=tuple('/api/'+family+'/'+str(c['posthog_project_id'])+'/session_recordings/'+r['id']+'/' for family in ('projects','environments') for r in m.get('recordings',[]))
   if not prefixes or not path.startswith(prefixes):raise ProofBlocked('native_recording_only')
  else:
   if kwargs.get('method')!='POST' or path!='/s/':raise ProofBlocked('native_snapshot_only')
   payload=kwargs.get('payload');costs=kwargs.get('costs',{})
   if not isinstance(payload,list) or len(payload)!=1 or set(costs)!={'snapshot_upload_requests','recording_bytes'} or costs['snapshot_upload_requests']!=1:raise ProofBlocked('native_snapshot_schema_required')
   props=payload[0].get('properties',{})
   if payload[0].get('event')!='$snapshot' or props.get('synthetic')!='yes' or props.get('token')!=c['posthog_token'] or props.get('$session_id') not in [r['id'] for r in m['recordings']]:raise ProofBlocked('native_snapshot_identity_required')
   if costs['recording_bytes']!=len(json.dumps(payload).encode()):raise ProofBlocked('native_snapshot_cost_mismatch')
  return super().request(key,kind,path,**kwargs)

def send_native(session,chunk,events,adapter):
 """Actual native adapter constructs wire payload; ledger guards exact transport."""
 import os,re
 from unittest.mock import patch
 from tele_tena.operations import providers
 root=Path(os.environ['TELE_TENA_NATIVE_PROOF_ROOT']);run=NativeRun(root);m,c=run.checked()
 if len(m.get('recordings',[]))!=1 or session['provider_id']!=m['recordings'][0]['id']:raise providers.Unconfigured('not_authorized_native_recording')
 if not session['synthetic'] or m['recordings'][0].get('duration_ms',90001)>90000:raise providers.Unconfigured('native_duration_or_fixture_invalid')
 def post(url,json,**kwargs):
  if url!=c['posthog_host']+'/s/':raise ProofBlocked('native_destination_changed')
  raw=__import__('json').dumps(json).encode()
  if re.search(rb'TT_SECRET_|/private/|native-v2-.*@|Authorization|CANARY_FILENAME',raw):raise ProofBlocked('native_sensitive_canary')
  if any(e.get('event')!='$snapshot' or e.get('properties',{}).get('synthetic')!='yes' or e.get('properties',{}).get('$session_id')!=session['provider_id'] for e in json):raise ProofBlocked('native_payload_invalid')
  status,_=run.request('native-snapshot-'+chunk['id'],'posthog_ingest','/s/',method='POST',payload=json,costs={'snapshot_upload_requests':1,'recording_bytes':len(raw)},maximum=8192)
  return type('Reply',(),{'status_code':status})()
 try:
  with patch.object(providers,'settings',return_value=c),patch('requests.post',side_effect=post):
   result=adapter(session,chunk,events)
  with run.locked():
   m,c=run.checked();row=m['recordings'][0];row['wire_accepted']=row.get('wire_accepted',0)+1;run._write(run.manifest,m)
  return result
 except ProofBlocked:raise providers.Unconfigured('native_proof_stopped') from None

def export_native(recording,adapter):
 """Actual archive adapter, bounded to the same new recording at settled time."""
 import os
 from unittest.mock import patch
 from tele_tena.operations import providers
 run=NativeRun(os.environ['TELE_TENA_NATIVE_PROOF_ROOT']);m,c=run.checked()
 row=m['recordings'][0]
 if recording['provider_id']!=row['id'] or datetime.now(timezone.utc)<datetime.fromisoformat(row['recheck_due_at']):raise providers.Unconfigured('native_export_not_due_or_not_owned')
 with run.locked():
  m,c=run.checked();row=m['recordings'][0];attempt=row.get('native_archive_attempts',0)+1;row['native_archive_attempts']=attempt;run._write(run.manifest,m)
 count=0
 def get(url,**kwargs):
  nonlocal count
  if not url.startswith(c['posthog_api_host']+'/api/'):raise ProofBlocked('native_export_host_invalid')
  count+=1;path=url[len(c['posthog_api_host']):]
  status,raw=run.request('export-settled-native-worker-'+str(attempt)+'-'+str(count),'posthog_api',path,costs={'posthog_admin_gets':1})
  return type('Reply',(),{'status_code':status,'iter_content':lambda self,n:iter([raw])})()
 try:
  with patch.object(providers,'settings',return_value=c),patch.object(providers,'archive_capability',return_value=True),patch('requests.get',side_effect=get):return adapter(recording)
 except ProofBlocked:raise providers.Unconfigured('native_export_budget_stopped') from None
