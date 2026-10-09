"""Explicit local owned-fixture browser check. No migration or retained-record edits.
Sets an owned synthetic call to Ended for documentation-state testing only.
Does not prove hosted media, End, token revocation, or scheduled release.
Run with TELE_TENA_TEST_SITE=tele-tena-pr12-fresh.localhost using bench Python.
"""
import importlib.util,json,os,secrets,subprocess,tempfile
from datetime import datetime,timezone
from pathlib import Path
app=Path(__file__).resolve().parents[1]
assert os.environ.get('TELE_TENA_TEST_SITE') == 'tele-tena-pr12-fresh.localhost', 'Explicit isolated review site required'
spec=importlib.util.spec_from_file_location('note_browser_fixtures', app/'tests/presentation.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
cls=m.Presentation
cls.setUpClass()
f=None
try:
    test=cls();test.setUp();test.fund_patient('p1',3000)
    day,_,_=test.make_schedule(mode='automatic')
    offering=m.fixtures.Integration.offers['c1']
    booked=test.book_slot(offering,test.slots(offering,day)[0],'owned-note-browser')
    now=datetime.now(timezone.utc).replace(tzinfo=None)
    m.frappe.db.sql('''INSERT INTO tt_consultation
        (appointment,id,room_name,patient_identity,clinician_identity,state,created,ended_by,ended,room_closed)
        VALUES (%s,%s,%s,%s,%s,'Ended',%s,%s,%s,1)''',
        (booked['id'],secrets.token_hex(16),secrets.token_hex(32),secrets.token_hex(24),secrets.token_hex(24),now,m.fixtures.USERS['c1'],now))
    m.frappe.db.commit()
    fd,file=tempfile.mkstemp(prefix='tt-owned-notes-',suffix='.json');f=Path(file)
    with os.fdopen(fd,'w') as stream:json.dump({'site':m.fixtures.SITE,'users':m.fixtures.USERS,'password':m.fixtures.PASSWORD,'appointment':booked['id']},stream)
    env={**os.environ,'NODE_PATH':'/tmp/tele-tena-browser/node_modules','TELE_TENA_NOTES_FIXTURE':str(f)}
    result=subprocess.run(['node',str(app/'scripts/browser-mvp-notes.cjs')],env=env,timeout=180)
    m.frappe.db.rollback()
    if result.returncode:raise RuntimeError('Owned note browser check failed; no private detail printed')
    journal=m.frappe.db.sql('SELECT COUNT(*) FROM tt_journal WHERE event_ref=%s',('completion:'+booked['id'],))[0][0]
    earning=m.frappe.db.sql('SELECT COUNT(*) FROM tt_earning WHERE appointment=%s',(booked['id'],))[0][0]
    assert journal==1 and earning==1, 'Amendment must not duplicate financial completion'
    print('PASS: one completion journal and one earning after amendment; owned fixtures removed by harness.')
finally:
    if f:f.unlink(missing_ok=True)
    cls.tearDownClass()
