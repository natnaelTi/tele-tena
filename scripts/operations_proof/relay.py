"""Loopback-only synthetic replay relay; validates before provider egress."""
import argparse,hashlib,json,os,re,secrets,sys,uuid
from datetime import datetime,timezone,timedelta
from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tele_tena.operations.proof import ProofRun,ProofBlocked
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run=ProofRun(a.root);auth=secrets.token_hex(32);file=a.output/'relay-auth';fd=os.open(file,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
with os.fdopen(fd,'w') as f:f.write(auth)
ALLOWED={'token','distinct_id','$session_id','$window_id','$snapshot_data','$snapshot_bytes','$lib','$lib_version','$snapshot_host','environment','synthetic','$geoip_disable'}
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def reply(self,value,status=200):
  raw=json.dumps(value).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  if self.headers.get('Authorization')!='Bearer '+auth:return self.reply({'state':'Denied'},403)
  if self.path!='/config':return self.reply({'state':'Denied'},404)
  m,c=run.checked();return self.reply({'token':c['posthog_token'],'actor':hashlib.sha256((m['authorization']['run_id']+':replay').encode()).hexdigest()})
 def do_POST(self):
  try:
   if self.headers.get('Authorization')!='Bearer '+auth:raise ProofBlocked('local_authorization_required')
   n=int(self.headers.get('Content-Length','0'))
   if n<=0 or n>10*1024**2:raise ProofBlocked('request_limit')
   body=json.loads(self.rfile.read(n));m,c=run.checked()
   if self.path=='/register':
    id=body.get('id','')
    if not re.fullmatch('[a-f0-9-]{36}',id):raise ProofBlocked('recording_identifier_invalid')
    run.reserve('recording-'+id,{'replays':1})
    with run.locked():
     m,c=run.checked();m['recordings'].append({'id':id,'registered_at':datetime.now(timezone.utc).isoformat(),'state':'Capturing','source':'new isolated SDK session','wire_accepted':0});run._write(run.manifest,m)
    return self.reply({'state':'Registered'})
   if self.path=='/snapshot':
    events=body['events']
    if not isinstance(events,list) or not events or len(events)>100:raise ProofBlocked('invalid_snapshot_batch')
    id=events[0].get('properties',{}).get('$session_id');known=next((r for r in m['recordings'] if r['id']==id),None)
    if not known or known['state']!='Capturing' or (datetime.now(timezone.utc)-datetime.fromisoformat(known['registered_at'])).total_seconds()>90:raise ProofBlocked('recording_window_closed')
    text=json.dumps(events)
    if re.search(r'TT_SECRET_|/private/|OTP-CANARY|medical_history',text):raise ProofBlocked('sensitive_canary')
    for e in events:
     props=e.get('properties',{})
     if e.get('event')!='$snapshot' or set(props)-ALLOWED or props.get('$session_id')!=id or props.get('token')!=c['posthog_token'] or props.get('synthetic')!='yes':raise ProofBlocked('snapshot_schema_invalid')
     if not isinstance(props.get('$snapshot_data'),list):raise ProofBlocked('snapshot_format_invalid')
    size=len(text.encode());key='snapshot-'+str(uuid.uuid4());status,raw=run.request(key,'posthog_ingest','/s/',method='POST',payload=events,costs={'snapshot_upload_requests':1,'recording_bytes':size},maximum=8192)
    if status not in (200,201,202):raise ProofBlocked('snapshot_provider_rejected')
    with run.locked():
     m,c=run.checked();recording=next(r for r in m['recordings'] if r['id']==id);recording['wire_accepted']+=1;frames=[e for event in events for e in event['properties']['$snapshot_data']];times=[e.get('timestamp') for e in frames if type(e.get('timestamp')) in (int,float)]
     if times:recording['first_snapshot_ms']=min(times+[recording.get('first_snapshot_ms',min(times))]);recording['last_snapshot_ms']=max(times+[recording.get('last_snapshot_ms',max(times))])
     run._write(run.manifest,m)
    return self.reply({'status':1})
   if self.path=='/complete':
    with run.locked():
     m,c=run.checked();recording=next(r for r in m['recordings'] if r['id']==body.get('id'));recording['state']='Captured';recording['duration_ms']=body.get('duration_ms');stamp=recording.get('first_snapshot_ms')
     if stamp:recording['captured_at']=datetime.fromtimestamp(stamp/1000,timezone.utc).isoformat();recording['recheck_due_at']=(datetime.fromtimestamp(stamp/1000,timezone.utc)+timedelta(hours=25,seconds=1)).isoformat()
     run._write(run.manifest,m)
    return self.reply({'state':'CaptureComplete'})
   raise ProofBlocked('local_route_not_allowed')
  except Exception as e:self.reply({'state':'Stopped','error_code':str(e) if isinstance(e,ProofBlocked) else 'local_relay_unavailable'},400)
try:HTTPServer(('127.0.0.1',8128),Handler).serve_forever()
finally:file.unlink(missing_ok=True)
