"""Observe native scheduler/worker release on owned, persisted presentation flows.
One-minute dispute policy is snapshotted only for these new fictional encounters.
No server-clock changes, manual releases, balance edits, or queue draining.
"""
import json
import os
from pathlib import Path
import secrets
import sys
import time
from datetime import datetime, timezone
from unittest.mock import patch

BENCH=Path(__file__).resolve().parents[3]
SITE='teletena-mvp-presentation.localhost'
os.chdir(BENCH/'sites');sys.path.insert(0,str(BENCH/'apps/frappe'))
import frappe
from tele_tena.api import journey, couples, consultations, presentation, scheduling
from tele_tena import accounting
from tele_tena.review import write_private

assert os.environ.get('TELE_TENA_TEST_SITE')==SITE
frappe.init(site=SITE,sites_path=str(BENCH/'sites'));frappe.connect()
root=BENCH/'sites'/SITE/'private'
seed=json.loads((root/'tele_tena_presentation_seed.json').read_text())
setup=json.loads((root/'tele_tena_couples_presentation.json').read_text())
marker=root/'tele_tena_scheduler_acceptance.json'
payer=seed['users']['patient'];clinician=seed['users']['clinician'];partner=setup['partner']

if not marker.exists():
    frappe.conf.tele_tena_demo_dispute_window_minutes=1
    frappe.set_user(payer);journey.simulated_deposit(240000,'scheduler-acceptance-v1:funds');frappe.db.commit()
    appointments=[]
    for number in range(2):
        frappe.set_user(payer)
        calendar=scheduling.calendar(setup['offering'],datetime.now(timezone.utc).date().isoformat(),35,'Africa/Addis_Ababa')
        slot=next(s for d in calendar['days'] for s in d['slots'] if datetime.fromisoformat(s['start'].replace('Z','+00:00')).timestamp()>time.time()+60)
        text='A calm conversation about listening and communication.'
        shared={'request':text};choices={'name':False,'history':False}
        invitation=couples.invite(setup['offering'],slot['start'],text,choices,shared,True,'scheduler-acceptance-v1:'+str(number))
        frappe.set_user(partner);couples.consent(invitation['token'],text,choices,shared,True)
        frappe.set_user(payer);booked=couples.confirm(invitation['id']);frappe.db.commit()
        frappe.set_user(clinician)
        with patch.object(consultations,'_window',return_value=True),patch('tele_tena.livekit._credentials',return_value=('wss://example.invalid','key','secret')),patch('tele_tena.livekit.participant_token',return_value='private-fixture-token'):
            consultations.join(booked['id'])
        with patch('tele_tena.livekit.close_room'):consultations.end(booked['id'])
        presentation.save_note_draft(booked['id'],'Private fictional follow-up note.','',summary_recipients=[])
        presentation.finalize_consultation(booked['id'],False);frappe.db.commit()
        if number==1:
            frappe.set_user(payer);accounting.open_earning_dispute(booked['id'],'Demonstration fee review.');frappe.db.commit()
        appointments.append(booked['id'])
    write_private(marker,{'appointments':appointments,'dispute_window_minutes':1,'created':datetime.now(timezone.utc).isoformat(),'media':'No media test; provider mocked only during fixture setup'})
else:
    appointments=json.loads(marker.read_text())['appointments']
frappe.conf.pop('tele_tena_demo_dispute_window_minutes',None)
print('Observing two owned encounters: one eligible release and one dispute hold. No manual business job invocation.',flush=True)
for iteration in range(36):
    frappe.db.rollback()
    earnings=journey.rows('SELECT appointment,state,release_at,id FROM tt_earning WHERE appointment IN %s',(tuple(appointments),))
    states={e.appointment:e.state for e in earnings}
    if states.get(appointments[0])=='Released':
        assert states.get(appointments[1])=='Disputed','Dispute did not block release'
        released=next(e for e in earnings if e.appointment==appointments[0])
        postings=journey.rows('SELECT id,created FROM tt_journal WHERE event_ref=%s',('earning-release:'+released.id,))
        assert len(postings)==1,'Duplicate release posting'
        assert journey.rows('SELECT id FROM tt_journal WHERE event_ref=%s',('earning-release:'+next(e.id for e in earnings if e.appointment==appointments[1]),))==[]
        jobs=frappe.db.sql("SELECT t.method scheduled_job_type,l.status,l.creation FROM `tabScheduled Job Log` l JOIN `tabScheduled Job Type` t ON t.name=l.scheduled_job_type WHERE t.method IN ('tele_tena.accounting.release_eligible_earnings','tele_tena.api.couples.expire_invitations','tele_tena.api.open_requests.expire_requests') ORDER BY l.creation DESC LIMIT 30",as_dict=True)
        assert any(row.scheduled_job_type=='tele_tena.accounting.release_eligible_earnings' and row.status=='Complete' for row in jobs)
        report={'site':SITE,'queue':'127.0.0.1:13917 / home-frappe-frappe-frappe-bench:default','one_minute_new_booking_policy':True,'automatic_release':True,'dispute_blocks_release':True,'release_postings':len(postings),'jobs':jobs,'worker_restart_recovery':'pending','source_commit':os.popen('git -C '+str(BENCH/'apps/tele_tena')+' rev-parse HEAD').read().strip()}
        Path('/tmp/tt-continuous-processing-result.json').write_text(json.dumps(report,default=str,indent=2))
        print('PASS: native scheduled release produced exactly one posting; disputed earnings remained held.',flush=True)
        break
    time.sleep(10)
else:raise SystemExit('FAIL: native release was not observed within six minutes; preserve fixtures and inspect isolated logs')
frappe.destroy()
