"""Resume existing V2: actual native archive worker, offline proof, approved cleanup.
No new capture; no scheduling. Stops before I/O until the saved25hour due time.
"""
import argparse,os,sys,subprocess,json
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.operations_proof.native_v2 import NativeRun

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--delete-verified-tests',action='store_true');a=p.parse_args();run=NativeRun(a.root);m,c=run.checked();row=m['recordings'][0]
 if datetime.now(timezone.utc)<datetime.fromisoformat(row['recheck_due_at']):
  print('PENDING native V2 settled checkpoint UTC:',row['recheck_due_at']);return
 repo=Path(__file__).resolve().parents[2];sites=Path('/home/frappe/teletena-communications-release/jobs/sites');site='teletena-payments-v147-fresh.localhost';bench=Path('/home/frappe/teletena-compat/bench');os.chdir(sites)
 env=dict(os.environ,PYTHONPATH=str(repo),TELE_TENA_NATIVE_V2='1',TELE_TENA_NATIVE_PROOF_ROOT=str(a.root),TELE_TENA_TEST_SITE=site,TELE_TENA_LOCAL_JOB_TEST='1',TELE_TENA_LOCAL_REPLAY_TEST='1',TELE_TENA_TEST_SITES_PATH=str(sites))
 import frappe
 def connect():frappe.init(site=site,sites_path=str(sites));frappe.connect();frappe.set_user('Administrator')
 # Old isolated pending records may precede this one; their adapters reject egress.
 # Never change their timestamps to bypass selection. Only this recording can use budget.
 for attempt in range(32):
  connect();state=frappe.db.sql('SELECT state,tries FROM tt_ops_archive WHERE id=%s',(row['native_id'],))[0]
  if state[0]=='Verified':frappe.destroy();break
  if state[1]>0:frappe.destroy();raise RuntimeError('Native archive attempt failed; inspect safe code before retry')
  frappe.enqueue('tele_tena.operations.jobs.process',queue='teletena_ops',timeout=120,job_id='native-v2-settled-'+str(attempt),deduplicate=True);frappe.db.commit();frappe.destroy()
  with (a.output/'settled-worker.log').open('ab') as log:
   subprocess.run([str(bench/'env/bin/python'),str(repo/'scripts/operations_proof/native_worker.py')],cwd=sites,env=env,stdout=log,stderr=log,check=True)
 else:raise RuntimeError('Native archive queue did not reach exact recording; no timestamp changes made')
 connect()
 from tele_tena.operations import storage
 record=frappe.db.sql('SELECT object_key,sha256 FROM tt_ops_archive WHERE id=%s',(row['native_id'],),as_dict=True)[0]
 import gzip
 data=json.loads(gzip.decompress(storage.read(record.object_key,'replay')));assert data['sha256']==record.sha256
 # Test the actual stored archive independently before deleting its provider copy.
 run._write(a.output/'normalized-recording.json',data);frappe.destroy()
 player_env=dict(env,TELE_TENA_PROOF_ROOT=str(a.output),NODE_PATH='/home/frappe/teletena-browser-tools/node_modules')
 subprocess.run(['node',str(repo/'scripts/operations_proof/playback.cjs')],env=player_env,check=True)
 with run.locked():
  m,c=run.checked();m['recordings'][0]['native_archive_playback']='VerifiedOffline';run._write(run.manifest,m)
 subprocess.run([str(bench/'env/bin/python'),str(repo/'scripts/operations_proof/recheck.py'),'--native-v2','--root',str(a.root),'--output',str(a.output)]+(['--delete-verified-tests'] if a.delete_verified_tests else []),env=env,check=True)
 final=run._read(run.manifest)
 if final['authorization'].get('status')=='Completed':
  connect()
  from tele_tena.operations import archive
  archive.tombstone(row['native_id'],'UserDeleted');frappe.db.sql("UPDATE tt_ops_deleted SET provider_state='ConfirmedAbsent' WHERE id=%s",(row['native_id'],));frappe.db.commit();frappe.destroy()
  print('Exact synthetic native archive removed after verified provider cleanup; audit retained. No site activation.')

if __name__=='__main__':main()
