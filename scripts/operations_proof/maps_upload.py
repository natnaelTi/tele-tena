"""One checksum-pinned synthetic pair through a quota-enforcing loopback proxy.
No provider credential enters the CLI process, argv or logs. Only standard source
map paths for the approved project are forwarded; raw responses stay in memory.
"""
import argparse,hashlib,json,os,subprocess,sys,threading,uuid
from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tele_tena.operations.proof import ProofRun,ProofBlocked

def rewrite(value,hostname):
 if isinstance(value,dict):return {k:rewrite(v,hostname) for k,v in value.items()}
 if isinstance(value,list):return [rewrite(v,hostname) for v in value]
 if isinstance(value,str) and value.startswith(('https://','http://')):
  u=urlsplit(value)
  if u.hostname!=hostname:raise ProofBlocked('upload_destination_changed')
  return urlunsplit(('http','127.0.0.1:8130',u.path,u.query,''))
 return value

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args();run=ProofRun(a.root);m,c=run.checked();directory=a.output/'source-map';tool=a.output/'tools/sentry-cli-Linux-x86_64'
 if hashlib.sha256(tool.read_bytes()).hexdigest()!='c958865f9d4000183509ea21b1f04925d5390de6d8d87386b9e69f2b305070c3':raise ProofBlocked('tool_checksum_mismatch')
 files=[directory/'index-ProofV1.js',directory/'index-ProofV1.js.map'];size=sum(x.stat().st_size for x in files);pair=hashlib.sha256(b''.join(x.read_bytes() for x in files)).hexdigest()
 if size>5*1024**2:raise ProofBlocked('pair_size_limit')
 if 'source-map-pair-v1' not in m['actions']:run.reserve('source-map-pair-v1',{'map_pair_upload_bytes':size});run.outcome('source-map-pair-v1','Prepared',checksum=pair)
 else:
  if m['actions']['source-map-pair-v1'].get('checksum')!=pair:raise ProofBlocked('source_map_pair_changed')
 hostname=urlsplit(c['bugsink_dsn']).hostname
 slug=c.get('bugsink_project_slug')
 if not isinstance(slug,str) or not __import__('re').fullmatch('[A-Za-z0-9_-]{1,100}',slug):raise ProofBlocked('project_slug_required')
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def do_GET(self):self.forward()
  def do_POST(self):self.forward()
  def forward(self):
   try:
    _,current=run.checked();project=current['bugsink_project_slug'];prefixes=('/api/0/organizations/bugsinkhasnoorgs/chunk-upload/','/api/0/organizations/bugsinkhasnoorgs/artifactbundle/assemble/','/api/0/projects/bugsinkhasnoorgs/'+project+'/files/difs/assemble/','/api/0/projects/bugsinkhasnoorgs/'+project+'/files/','/api/0/projects/bugsinkhasnoorgs/'+project+'/')
    if not self.path.startswith(prefixes):raise ProofBlocked('upload_path_unapproved')
    length=int(self.headers.get('Content-Length','0'))
    if length>5*1024**2:raise ProofBlocked('upload_size_limit')
    body=self.rfile.read(length) if length else None;key='map-upload-'+str(uuid.uuid4());status,raw=run.request(key,'bugsink_api',self.path,method=self.command,payload=body,costs={'map_upload_requests':1},maximum=1024**2,content_type=self.headers.get('Content-Type'))
    if raw:
     try:raw=json.dumps(rewrite(json.loads(raw),hostname)).encode()
     except ValueError:raise ProofBlocked('upload_response_not_json') from None
    self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    print('Source-map protocol request HTTP status:',status,flush=True)
   except Exception:
    raw=b'{"detail":"Bounded source-map proxy stopped"}';self.send_response(400);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 server=HTTPServer(('127.0.0.1',8130),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();home=a.output/'tools/cli-home';home.mkdir(mode=0o700,exist_ok=True)
 env={'PATH':os.environ['PATH'],'HOME':str(home),'SENTRY_URL':'http://127.0.0.1:8130/','SENTRY_AUTH_TOKEN':'isolated-proxy-only','SENTRY_DISABLE_UPDATE_CHECK':'1','SENTRY_LOG_LEVEL':'error','SENTRY_HTTP_MAX_RETRIES':'0','CI':'true'}
 try:
  result=subprocess.run([str(tool),'sourcemaps','upload','--org','bugsinkhasnoorgs','--project',slug,'--url-prefix','app:///assets',str(directory)],env=env,cwd=directory,capture_output=True,timeout=120)
  code='upload_client_failed'
  if result.returncode==0:state='UploadClientSucceeded';code='upload_readback_pending'
  else:state='UploadUnverified'
  run.outcome('source-map-pair-v1',state,error_code=code,checksum=pair);print('Pinned source-map upload client exit status:',result.returncode,'; actual mapped event readback still required.')
 finally:server.shutdown();server.server_close()
if __name__=='__main__':
 try:main()
 except Exception as e:print('Source-map phase stopped:',str(e) if isinstance(e,ProofBlocked) else 'local_client_unavailable');raise SystemExit(1)
