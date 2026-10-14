"""Pause only the isolated worker; observe native queued jobs and restart recovery."""
import json
import os
from pathlib import Path
import signal
import sys
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

BENCH=Path(__file__).resolve().parents[3];SITE='teletena-mvp-presentation.localhost';RUNTIME=Path('/home/frappe/teletena-mvp-runtime')
assert os.environ.get('TELE_TENA_TEST_SITE')==SITE
os.chdir(BENCH/'sites');sys.path.insert(0,str(BENCH/'apps/frappe'))
import frappe
from tele_tena.api import journey, couples, scheduling
from frappe.utils.background_jobs import get_queue

frappe.init(site=SITE);frappe.connect()
root=BENCH/'sites'/SITE/'private'
seed=json.loads((root/'tele_tena_presentation_seed.json').read_text());setup=json.loads((root/'tele_tena_couples_presentation.json').read_text())
frappe.set_user(seed['users']['clinician'])
current=next(s for s in scheduling.schedules() if s['offering']==setup['offering'])
payload={k:current[k] for k in ('offering','schedule_name','consultation_format','confirmation_mode','minimum_notice_minutes','horizon_days','buffer_before','buffer_after','status')}
payload.update(timezone_name=current['timezone'],intervals=[dict(weekday=i['weekday'],start=i['start_local'],end=i['end_local']) for i in current['intervals']],exceptions=[dict(date=str(e['date']),kind=e['kind'],start=e.get('start_local'),end=e.get('end_local')) for e in current['exceptions']])
local=datetime.now(ZoneInfo(current['timezone']))+timedelta(minutes=2)
assert local.hour<21,'Run daytime fixture only; no clock changes'
replacement=[e for e in payload['exceptions'] if str(e['date'])!=local.date().isoformat()]+[dict(date=local.date().isoformat(),kind='replace',start=local.strftime('%H:%M'),end='22:00')]
scheduling.save_schedule(**dict(payload,exceptions=replacement));frappe.db.commit()
frappe.set_user(seed['users']['patient'])
calendar=scheduling.calendar(setup['offering'],local.date().isoformat(),1,current['timezone'])
slot=calendar['days'][0]['slots'][0]
text='We are considering a shared conversation.'
invitation=couples.invite(setup['offering'],slot['start'],text,{'name':False,'history':False},{'request':text},True,'worker-recovery:'+str(int(time.time())))
frappe.db.commit()
frappe.set_user(seed['users']['clinician']);scheduling.save_schedule(**payload);frappe.db.commit()
expiry=journey.one('SELECT expires_at FROM tt_couple_plan WHERE id=%s',(invitation['id'],)).expires_at
pid=int((RUNTIME/'worker.pid').read_text());cmd=Path(f'/proc/{pid}/cmdline').read_bytes();assert b'frappe' in cmd and b'worker' in cmd
assert Path(f'/proc/{pid}/cwd').resolve()==RUNTIME/'sites'
os.kill(pid,signal.SIGTERM)
print('Stopped only isolated worker; awaiting native scheduler enqueue with an expiring uncharged invitation.',flush=True)
for _ in range(12):
    time.sleep(10);frappe.db.rollback()
    queue=get_queue('default')
    jobs=queue.get_jobs()
    assert all(job.kwargs.get('site')==SITE for job in jobs),'Unrelated site job in isolated queue'
    if any(job.kwargs.get('kwargs',{}).get('job_type')=='tele_tena.api.couples.expire_invitations' for job in jobs):break
else:raise RuntimeError('Native scheduler did not enqueue expiry while worker was stopped')
# Retain the native queued job until its real, server-enforced expiry passes.
while datetime.now(timezone.utc).replace(tzinfo=None)<=expiry:time.sleep(5)
frappe.destroy()
sys.path.insert(0,str(BENCH/'apps/tele_tena/scripts'))
import start_presentation_processing
start_presentation_processing.run()
frappe.init(site=SITE);frappe.connect()
for _ in range(18):
    time.sleep(5);frappe.db.rollback()
    if journey.one('SELECT state FROM tt_couple_plan WHERE id=%s',(invitation['id'],)).state=='Expired':break
else:raise RuntimeError('Queued expiry did not recover after worker restart')
report=json.loads(Path('/tmp/tt-continuous-processing-result.json').read_text())
report.update(worker_restart_recovery=True,automatically_enqueued_expiry=True,persisted_invitation_expired=True)
Path('/tmp/tt-continuous-processing-result.json').write_text(json.dumps(report,indent=2))
print('PASS: native scheduler queued while worker was stopped; restarted worker expired the persisted invitation. No financial mutation for invitation.',flush=True)
frappe.destroy()
