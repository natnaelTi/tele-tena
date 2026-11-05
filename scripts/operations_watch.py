"""Operator-owned health/alert runner, independent of application/RQ workers.
Use the target Bench Python. Never run from a public web route. No live test alerts
are sent unless the reviewer explicitly enables them and configures a recipient.
"""
import argparse,fcntl,os,sys,time
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--bench',type=Path,required=True);parser.add_argument('--site',required=True);parser.add_argument('--once',action='store_true');args=parser.parse_args()
bench=args.bench.resolve();assert (bench/'sites'/args.site/'site_config.json').is_file()
os.chdir(bench/'sites');sys.path.insert(0,str(Path(__file__).resolve().parents[1]));import tele_tena,frappe
lock=bench/'sites'/args.site/'private/teletena-operations-watch.lock'
with lock.open('a') as handle:
 os.chmod(lock,0o600);fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while True:
  try:
   frappe.init(site=args.site,sites_path=str(bench/'sites'));frappe.connect();frappe.set_user('Administrator')
   from tele_tena.operations.jobs import watch
   watch();print('TeleTena operational health/alert tick completed',flush=True)
  except Exception:print('TeleTena operational tick unavailable; inspect authenticated health and external monitor',flush=True)
  finally:frappe.destroy()
  if args.once:break
  time.sleep(30)
