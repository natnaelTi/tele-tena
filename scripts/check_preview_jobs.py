"""Observe native scheduler/worker evidence without invoking business jobs."""
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BENCH = Path(__file__).resolve().parents[3]
SITE = 'teletena-mvp-presentation.localhost'
RUNTIME = Path('/home/frappe/teletena-mvp-runtime')
assert os.environ.get('TELE_TENA_TEST_SITE') == SITE
os.chdir(BENCH / 'sites')
sys.path.insert(0, str(BENCH / 'apps/frappe'))
import frappe
from frappe.utils.background_jobs import get_queue
frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
frappe.connect()
try:
    since = datetime.fromtimestamp((RUNTIME / 'scheduler.pid').stat().st_mtime, timezone.utc).astimezone(ZoneInfo(frappe.utils.get_system_timezone())).replace(tzinfo=None)
    methods = ('tele_tena.accounting.release_eligible_earnings',
               'tele_tena.api.couples.expire_invitations',
               'tele_tena.api.open_requests.expire_requests',
               'tele_tena.api.extensions.expire_extensions')
    logs = frappe.db.sql('''SELECT t.method,l.status,MAX(l.creation) latest,COUNT(*) executions
        FROM `tabScheduled Job Log` l JOIN `tabScheduled Job Type` t ON t.name=l.scheduled_job_type
        WHERE t.method IN %s AND l.creation>=%s GROUP BY t.method,l.status''',
        (methods, since), as_dict=True)
    jobs = get_queue('default').get_jobs()
    assert all(job.kwargs.get('site') == SITE for job in jobs), 'Unexpected site in isolated queue'
    data = {'site': SITE, 'since_scheduler_start': str(since), 'native_logs': logs,
            'queued_jobs': len(jobs), 'all_queued_jobs_site_scoped': True,
            'complete_methods': sorted({l.method for l in logs if l.status == 'Complete'})}
    Path('/tmp/tt-preview-native-jobs.json').write_text(json.dumps(data, default=str, indent=2))
    print(json.dumps(data, default=str))
finally:
    frappe.destroy()
