"""Immediate provisional export or the same authorized25hour resume checkpoint."""
import argparse,gzip,hashlib,json,os,sys
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tele_tena.operations.proof import ProofRun,ProofBlocked
from tele_tena.operations.posthog_export import export_recording,ExportError
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--settled',action='store_true');args=p.parse_args();run=ProofRun(args.root);m,c=run.checked()
for recording in m['recordings']:
 id=recording['id'];phase='settled' if args.settled else 'provisional';due=recording.get('recheck_due_at')
 if args.settled and (not due or datetime.now(timezone.utc)<datetime.fromisoformat(due)):
  print('25hour recheck pending; due UTC:',due);continue
 with run.locked():
  m,c=run.checked();item=next(x for x in m['recordings'] if x['id']==id)
  if item.get(phase+'_export')=='Complete':print('Existing completed export retained; no repeated provider calls.');continue
  attempt=item.get(phase+'_attempts',0)+1;item[phase+'_attempts']=attempt;run._write(run.manifest,m)
 index=0
 def fetch(path,maximum):
  global index
  index+=1;return run.request('export-'+phase+'-'+id+'-'+str(attempt)+'-'+str(index),'posthog_api',path,costs={'posthog_admin_gets':1},maximum=maximum)
 try:
  result=export_recording(c['posthog_project_id'],id,fetch);content=json.dumps(result).encode();compressed=gzip.compress(content,mtime=0)
  if len(compressed)>10*1024**2:raise ExportError('compressed_size_limit')
  # The output is an owned private recording, never a public URL/database blob.
  key=hashlib.sha256(id.encode()).hexdigest();target=args.output/('replay-'+key+'-'+phase+'.json.gz')
  if sum(x.stat().st_size for x in args.output.glob('replay-*.json.gz'))+len(compressed)>30*1024**2:raise ExportError('private_proof_storage_limit')
  fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
  with os.fdopen(fd,'wb') as f:f.write(compressed)
  normalized=args.output/'normalized-recording.json';normalized.write_bytes(content);normalized.chmod(0o600)
  with run.locked():
   m,c=run.checked();item=next(x for x in m['recordings'] if x['id']==id);item[phase+'_export']='Complete';item[phase+'_sha256']=result['sha256'];item[phase+'_bytes']=len(compressed);item[phase+'_source_count']=len(result['source_keys']);item['format']=result['format'];item['archive_path']=target.name;item['state']='ProvisionalExport' if not args.settled else 'SettledExport';run._write(run.manifest,m)
  print('Complete',phase,'export:',len(result['source_keys']),'sources,',len(result['events']),'events,',len(compressed),'compressed bytes; playback still requires verification.')
 except (ProofBlocked,ValueError,KeyError,OSError) as e:
  code=str(e) if isinstance(e,(ProofBlocked,ExportError)) else 'format_or_storage_unavailable'
  with run.locked():
   m,c=run.checked();item=next(x for x in m['recordings'] if x['id']==id);item[phase+'_export']='Incomplete';item['failure_code']=code;run._write(run.manifest,m)
  print('Export stopped:',code)
