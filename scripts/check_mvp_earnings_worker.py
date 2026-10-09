"""Native scheduled-job dispatch and RQ execution on owned local fixtures.

This verifies a forced native scheduler dispatch, not a continuously running
scheduler daemon or a production cron tick. Shared queues/services/site config
are untouched. Only the zero/one-minute policies snapshotted on owned fixture
bookings are shortened; retained policy settings and records are preserved.
"""
import importlib.util
import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
BENCH = APP.parents[1]
assert os.environ.get('TELE_TENA_TEST_SITE') == 'tele-tena-pr12-fresh.localhost'
spec = importlib.util.spec_from_file_location('worker_acceptance_fixtures', APP / 'tests/presentation.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
cls = m.Presentation


def financial_record_fingerprints():
    """Keep private row contents in memory; reports contain only equality/counts."""
    tables = ('financial_account', 'journal', 'journal_line', 'wallet', 'ledger',
              'earning', 'payout', 'dispute', 'financial_reconciliation',
              'appointment', 'consultation_note', 'note_revision')
    result = {}
    for table in tables:
        rows = m.frappe.db.sql(f'SELECT * FROM tt_{table}')
        encoded = sorted(json.dumps(row, default=str, separators=(',', ':')) for row in rows)
        result[table] = (len(rows), hashlib.sha256('\n'.join(encoded).encode()).hexdigest())
    return result


m.fixtures.connect()
before = financial_record_fingerprints()
m.frappe.destroy()
cls.setUpClass()
queue = None
owned_job = None
try:
    from tele_tena import accounting
    from frappe.utils import background_jobs as jobs
    from frappe.core.doctype.scheduled_job_type.scheduled_job_type import ScheduledJobType
    method = 'tele_tena.accounting.release_eligible_earnings'
    name = m.frappe.db.get_value('Scheduled Job Type', {'method': method}, 'name')
    assert name, 'Native scheduled job must already be installed'
    retained_due = m.frappe.db.sql("SELECT COUNT(*) FROM tt_earning WHERE state='Pending' AND release_at<=UTC_TIMESTAMP(6)")[0][0]
    assert retained_due == 0, 'Refusing to release retained earnings during owned-fixture verification'
    job = m.frappe.get_doc('Scheduled Job Type', name)
    assert not job.is_job_in_queue(), 'Existing site job must not be replaced or drained'
    test = cls()
    test.setUp()
    test.fund_patient('p1', 3000)
    day, _, _ = test.make_schedule(mode='automatic')
    offering = m.fixtures.Integration.offers['c1']
    appointments = []
    for minutes in (0, 1):
        with patch.dict(m.frappe.conf, {'tele_tena_demo_platform_fee_bps': 0,
                                     'tele_tena_demo_dispute_window_minutes': minutes}):
            booked = test.book_slot(offering, test.slots(offering, day)[0], 'worker-' + secrets.token_hex(10))
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        m.frappe.db.sql('''INSERT INTO tt_consultation
            (appointment,id,room_name,patient_identity,clinician_identity,state,created,ended_by,ended,room_closed)
            VALUES (%s,%s,%s,%s,%s,'Ended',%s,%s,%s,1)''',
            (booked['id'], secrets.token_hex(16), secrets.token_hex(32), secrets.token_hex(24),
             secrets.token_hex(24), now, m.fixtures.USERS['c1'], now))
        m.fixtures.login('c1')
        m.presentation.save_note_draft(booked['id'], 'Fictional worker acceptance note', '')
        m.presentation.finalize_consultation(booked['id'])
        earning = m.journey.one('SELECT id,policy_snapshot,release_at FROM tt_earning WHERE appointment=%s', (booked['id'],))
        assert json.loads(earning.policy_snapshot)['dispute_window_minutes'] == minutes
        appointments.append((booked['id'], earning.id, earning.release_at))
    m.fixtures.login('p1')
    accounting.open_earning_dispute(appointments[1][0], 'Fictional dispute for isolated worker acceptance')
    m.frappe.db.commit()
    wait = max(0, (appointments[1][2] - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds()) + 1
    print('Waiting for the owned one-minute policy release boundary; server clock and retained policies unchanged.', flush=True)
    assert wait <= 70, "Only owned one-minute policy waiting is permitted"
    while wait > 0:
        step = min(wait, 30)
        time.sleep(step)
        wait -= step
        print("Owned policy boundary wait progressing.", flush=True)
    assert datetime.now(timezone.utc).replace(tzinfo=None) >= appointments[1][2]
    queue_name = 'teletena-mvp-check-' + secrets.token_hex(8)
    timeouts = jobs.get_queues_timeout()
    # Test-process memory only. Never writes common_site_config or site_config.
    with patch.dict(timeouts, {queue_name: 300}):
        queue = jobs.get_queue(queue_name)
        assert queue.count == 0
        for attempt in (1, 2):
            m.fixtures.login('admin')
            m.frappe.db.commit()
            with patch.object(ScheduledJobType, 'get_queue_name', return_value=queue_name):
                assert job.enqueue(force=True), 'Native scheduler dispatch must queue the installed hook'
            owned_job = jobs.get_job(job.rq_job_id)
            assert owned_job and owned_job.kwargs.get('site') == m.fixtures.SITE
            worker_source = '''import os,frappe
from rq import Queue,Worker
from frappe.utils.background_jobs import get_redis_conn
frappe.init(site=os.environ['TELE_TENA_TEST_SITE'])
connection=get_redis_conn()
queue=Queue(os.environ['TELE_TENA_OWNED_QUEUE'],connection=connection)
frappe.destroy()
Worker([queue],connection=connection).work(burst=True,logging_level='WARNING')
'''
            result = subprocess.run([sys.executable, '-c', worker_source],
                cwd=BENCH / 'sites', env={**os.environ, 'TELE_TENA_OWNED_QUEUE': queue.name},
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
            assert result.returncode == 0, 'Native worker failed; private output withheld'
            m.frappe.db.rollback()
            released = m.journey.one('SELECT state FROM tt_earning WHERE id=%s', (appointments[0][1],))
            held = m.journey.one('SELECT state FROM tt_earning WHERE id=%s', (appointments[1][1],))
            assert released.state == 'Released' and held.state == 'Disputed'
            assert m.frappe.db.sql('SELECT COUNT(*) FROM tt_journal WHERE event_ref=%s', ('earning-release:' + appointments[0][1],))[0][0] == 1
            assert m.frappe.db.sql('SELECT COUNT(*) FROM tt_journal WHERE event_ref=%s', ('earning-release:' + appointments[1][1],))[0][0] == 0
            print('PASS: native installed job through owned RQ worker; release once, expired-window dispute held; attempt', attempt, flush=True)
    m.fixtures.login('c1')
    payout = accounting.request_payout(200, 'owned-worker-payout')
    assert accounting.request_payout(200, 'owned-worker-payout')['id'] == payout['id']
    balances = m.frappe.db.sql('SELECT bucket,balance_minor FROM tt_financial_account WHERE owner=%s', (m.fixtures.USERS['c1'],), as_dict=True)
    projection = {row.bucket: int(row.balance_minor) for row in balances}
    assert projection['earnings_available'] == 400 and projection['payout_reserved'] == 200 and projection['pending'] == 600
    m.frappe.db.commit()
    print('PASS: booking → finalization → native queued release/retry → private hold → payout reservation; no external transfer or media claim.')
finally:
    try:
        if owned_job:
            owned_job.delete()
        if queue:
            assert queue.count == 0, 'Owned verification queue unexpectedly contains unfinished jobs'
    finally:
        cls.tearDownClass()
        m.fixtures.connect()
        try:
            after = financial_record_fingerprints()
            changed = [table for table in before if before[table] != after[table]]
            assert not changed, 'Retained financial/encounter records changed: ' + ', '.join(changed)
            print('PASS: exact before/after row fingerprints match for all 12 retained financial/encounter tables.')
        finally:
            m.frappe.destroy()
