"""Read-only release/runtime/site/queue inspection; never emits configuration secrets."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

p=argparse.ArgumentParser();p.add_argument('--bench',type=Path,required=True);p.add_argument('--site',required=True);a=p.parse_args()
bench=a.bench.resolve();site=a.site
assert site and Path(site).name==site and (bench/'sites'/site/'site_config.json').is_file()
os.chdir(bench/'sites');sys.path.insert(0,str(bench/'apps/frappe'))
import frappe
try:
 frappe.init(site=site,sites_path=str(bench/'sites'));frappe.connect()
 from frappe.utils.background_jobs import get_workers,generate_qname,get_redis_conn
 workers=list(get_workers());default=generate_qname('default')
 queue_names=sorted({q.name for worker in workers for q in worker.queues})
 logs=frappe.db.sql('''SELECT t.method,l.status,l.creation FROM `tabScheduled Job Log` l
   JOIN `tabScheduled Job Type` t ON t.name=l.scheduled_job_type
   WHERE t.method LIKE 'tele_tena.%%' ORDER BY l.creation DESC LIMIT 12''',as_dict=True)
 result={'site':site,'bench':str(bench),'python':platform.python_version(),
  'node':subprocess.check_output(['node','--version'],text=True).strip(),
  'installed_apps':frappe.get_installed_apps(),
  'app_commits':{app:subprocess.check_output(['git','-C',str(bench/'apps'/app),'rev-parse','HEAD'],text=True).strip() for app in ('frappe','erpnext','tele_tena')},
  'versions':{app:importlib.metadata.version(app) for app in ('frappe','erpnext','tele_tena')},
  'dirty_apps':{app:bool(subprocess.check_output(['git','-C',str(bench/'apps'/app),'status','--porcelain'],text=True).strip()) for app in ('frappe','erpnext','tele_tena')},
  'database_version':frappe.db.sql('SELECT VERSION()')[0][0],
  'redis_queue_version':get_redis_conn().info('server').get('redis_version'),
  'worker_count':len(workers),'subscribed_queues':queue_names,'default_queue_subscribed':default in queue_names,
  'scheduler_disabled':bool(frappe.conf.get('disable_scheduler')),'scheduler_paused':bool(frappe.conf.get('pause_scheduler')),
  'review_site_bound':frappe.conf.get('tele_tena_review_site')==site and frappe.conf.get('tele_tena_review_enabled') is True,
  'developer_mode':bool(frappe.conf.get('developer_mode')),'csrf_bypass':bool(frappe.conf.get('ignore_csrf')),
  'sql_body_logging':frappe.conf.get('logging')==2,'scheduled_execution_metadata':logs}
 print(json.dumps(result,default=str,indent=2))
finally:
 frappe.db.rollback();frappe.destroy()
