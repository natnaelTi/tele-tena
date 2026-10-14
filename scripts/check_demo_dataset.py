"""Real persisted seed acceptance on a named disposable site, not production."""
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

BENCH=Path(os.environ.get('TELE_TENA_TEST_BENCH',Path(__file__).resolve().parents[3]))
SITE=os.environ['TELE_TENA_TEST_SITE']
assert SITE.startswith(('tele-tena-','teletena-')) and SITE.endswith('.localhost')
os.chdir(BENCH/'sites')
sys.path.insert(0,str(BENCH/'apps/frappe'))
import frappe
frappe.init(site=SITE);frappe.connect();frappe.set_user('Administrator')
from tele_tena import demo_dataset as demo
from tele_tena.api import journey,presentation,vetting,open_requests,couples


def snapshot(exclude_demo=False):
    users=tuple(demo.DATASET+'-'+key+'@example.invalid' for key in demo.NAMES)
    query=' WHERE name NOT IN %s' if exclude_demo else ''
    result={'users':frappe.db.sql('SELECT name,enabled,full_name FROM tabUser'+query+' ORDER BY name',(users,) if exclude_demo else ())}
    for table,column in [('tt_profile','user'),('tt_wallet','patient'),('tt_application','user'),('tt_ledger','patient'),('tt_appointment','patient')]:
        result[table]=frappe.db.sql('SELECT * FROM '+table+(' WHERE '+column+' NOT IN %s' if exclude_demo else '')+' ORDER BY 1',(users,) if exclude_demo else ())
    for table,column in [('tt_financial_account','owner'),('tt_earning','clinician'),('tt_payout','clinician')]:
        where=(' WHERE '+column+' NOT IN %s' + (" AND owner<>''" if table=='tt_financial_account' else '')) if exclude_demo else ''
        result[table]=frappe.db.sql('SELECT * FROM '+table+where+' ORDER BY 1',(users,) if exclude_demo else ())
    journal_filter=" WHERE NOT EXISTS (SELECT 1 FROM tt_journal_line jl JOIN tt_financial_account a ON a.id=jl.account_id WHERE jl.journal_id=j.id AND a.owner IN %s)" if exclude_demo else ''
    result['journals']=frappe.db.sql('SELECT j.* FROM tt_journal j'+journal_filter+' ORDER BY j.id',(users,) if exclude_demo else ())
    result['journal_lines']=frappe.db.sql('SELECT l.* FROM tt_journal_line l JOIN tt_journal j ON j.id=l.journal_id'+journal_filter+' ORDER BY l.id',(users,) if exclude_demo else ())
    return hashlib.sha256(json.dumps(result,default=str,sort_keys=True).encode()).hexdigest()


try:
    before=snapshot(True)
    preflight=demo.setup()
    assert preflight['dry_run'] and not preflight['changes']
    # No frontend capability mocks: the actual seed backend performs commands.
    with patch('requests.sessions.Session.request',side_effect=AssertionError('Outbound HTTP forbidden')),patch.object(frappe,'sendmail',side_effect=AssertionError('Email forbidden')):
        first=demo.setup(False)
    assert before==snapshot(True),'Unrelated records changed; retained for diagnosis'
    after=snapshot()
    with patch('requests.sessions.Session.request',side_effect=AssertionError('Outbound HTTP forbidden')),patch.object(frappe,'sendmail',side_effect=AssertionError('Email forbidden')):
        second=demo.setup(False)
    assert second['already_present'] and after==snapshot(),'Repeat seed changed records'
    # Fresh comparison generation adds only requests/offers, and preserves money.
    money_before=frappe.db.sql('SELECT patient,available,reserved FROM tt_wallet ORDER BY patient')
    with patch('requests.sessions.Session.request',side_effect=AssertionError('Outbound HTTP forbidden')),patch.object(frappe,'sendmail',side_effect=AssertionError('Email forbidden')):
        demo.refresh('verification',False)
    refreshed=snapshot()
    demo.refresh('verification',False)
    assert refreshed==snapshot(),'Repeat refresh changed records'
    assert money_before==frappe.db.sql('SELECT patient,available,reserved FROM tt_wallet ORDER BY patient'),'Refresh changed funds'
    state=json.loads(demo.paths()[0].read_text());users=state['users'];steps=state['steps']
    def result(key):return steps[key]['result']
    frappe.set_user(users['patient'])
    try:vetting.download_scope_evidence(result('scope-counselor-counseling')['evidence']);raise AssertionError('Private evidence leaked')
    except frappe.PermissionError:pass
    try:open_requests.clinician_offers();raise AssertionError('Offer history role denied incorrectly')
    except frappe.PermissionError:pass
    completed=result('booking-released')['id']
    try:presentation.appointment_detail(completed);raise AssertionError('Another patient record leaked')
    except frappe.PermissionError:pass
    frappe.set_user(users['private_patient'])
    detail=presentation.appointment_detail(completed)
    assert 'Fictional private working note' not in json.dumps(detail,default=str)
    assert 'Fictional next steps' in json.dumps(detail,default=str)
    own_req=result('request-cancelled')['id']
    try:open_requests.my_request_detail(result('request')['id']);raise AssertionError('Another private request leaked')
    except frappe.ValidationError:
        assert frappe.local.response.get('tele_tena_error')=='request_unavailable'
    frappe.set_user(users['counselor']);history=open_requests.clinician_offers()
    assert 'offers' in history or 'items' in history
    frappe.set_user(users['couple_partner']);plan=couples.get_plan(result('couple-invitation')['id']);assert plan
    frappe.set_user('Administrator');reconciliation=demo.reconcile(state)
    saved=frappe.conf.get('tele_tena_real_money_enabled')
    frappe.conf.tele_tena_real_money_enabled=True
    try:demo.setup();raise AssertionError('Real-money guard failed')
    except ValueError:pass
    finally:frappe.conf.tele_tena_real_money_enabled=saved
    print(json.dumps({'site':SITE,'checks':'seed twice, dry-run, unrelated preservation, no outbound delivery, private notes/evidence/request/offer denial, couples consent, real-money guard, owner reconciliation','result':'PASS','reconciliation':reconciliation,'initial_seed':first.get('created',False)}))
finally:
    frappe.db.rollback();frappe.destroy()
