"""Owned TeleTena operations processes only; no Supervisor/Nginx generation.
Start is explicit, integrations remain controlled by their site flags. Re-run start
following a host reboot, or use an operator-approved persistent launcher. Shared
Bench web/default/short/long workers are never signalled by this helper.
"""
import argparse,fcntl,json,os,signal,subprocess,time,sys
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('start','status','stop'));p.add_argument('--bench',type=Path,required=True);p.add_argument('--site',required=True);a=p.parse_args()
bench=a.bench.resolve();site=bench/'sites'/a.site
assert site.resolve().parent==bench/'sites' and site.is_dir(),'Existing target site required'
assert os.geteuid()!=0,'Use the Bench user'
root=site/'private/teletena-operations-processes';root.mkdir(mode=0o700,exist_ok=True);assert not root.is_symlink();root.chmod(0o700)
repo=Path(__file__).resolve().parents[1]
commands={'worker':[str(bench/'env/bin/python'),'-m','frappe.utils.bench_helper','frappe','worker','--queue','teletena_ops'],'watch':[str(bench/'env/bin/python'),str(repo/'scripts/operations_watch.py'),'--bench',str(bench),'--site',a.site]}
def owned(name):
 file=root/(name+'.pid')
 if not file.exists():return None
 pid=int(file.read_text());proc=Path('/proc')/str(pid)
 if not proc.exists():return None
 assert proc.stat().st_uid==os.getuid(),'PID owner differs; no process changed'
 assert (proc/'cwd').resolve()==bench/'sites','PID working directory differs; no process changed'
 actual=(proc/'cmdline').read_bytes().split(b'\0');expected=[v.encode() for v in commands[name]]
 assert actual[:len(expected)]==expected,'PID command differs; no process changed'
 return pid
with (root/'control.lock').open('a') as lock:
 os.chmod(lock.name,0o600);fcntl.flock(lock,fcntl.LOCK_EX)
 if a.action=='start':
  config=json.loads((bench/'sites/common_site_config.json').read_text())
  assert config.get('workers',{}).get('teletena_ops',{}).get('timeout')==120,'Register reviewed teletena_ops queue first'
 for name,cmd in commands.items():
  pid=owned(name)
  if a.action=='start' and not pid:
   if name=='worker':
    os.chdir(bench/'sites');sys.path.insert(0,str(repo));sys.path.insert(1,str(bench/'apps/frappe'))
    import tele_tena,frappe
    frappe.init(site=a.site,sites_path=str(bench/'sites'));frappe.connect()
    try:
     from frappe.utils.background_jobs import get_workers
     assert not get_workers('teletena_ops'),'Operations queue already has a worker; inspect it rather than creating a duplicate'
    finally:frappe.destroy()
   file=root/(name+'.log');fd=os.open(file,os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
   with os.fdopen(fd,'ab') as log:
    env=dict(os.environ,PYTHONPATH=str(repo)+os.pathsep+str(bench/'apps/frappe'))
    proc=subprocess.Popen(cmd,cwd=bench/'sites',env=env,stdout=log,stderr=log,start_new_session=True)
   f=root/(name+'.pid');f.write_text(str(proc.pid));f.chmod(0o600);time.sleep(.5)
   assert proc.poll() is None,'Owned operations process failed; inspect private log';pid=proc.pid
  if a.action=='stop' and pid:
   os.kill(pid,signal.SIGTERM)
   for _ in range(60):
    if not Path('/proc',str(pid)).exists():break
    # Reaped children may remain zombies briefly. Never escalate to broad kill.
    if ') Z ' in Path('/proc',str(pid),'stat').read_text():break
    time.sleep(.25)
   else:raise RuntimeError('Process still stopping; inspect it, do not start a duplicate')
   (root/(name+'.pid')).unlink(missing_ok=True);pid=None
  print(name+': '+('running PID '+str(pid) if pid else 'stopped'))
