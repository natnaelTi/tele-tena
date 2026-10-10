"""Representative financial-schema upgrade on the empty named disposable site.
Never runs against a retained site. Reconstructs absent pre-v1.7 financial tables,
keeps all legacy fixture records, and checks opening/retry/boundary owner by owner.
This is not a checkout/test of every historical application version.
"""
import hashlib, json, os, sys, uuid
from pathlib import Path
BENCH=Path(__file__).resolve().parents[3]
SITE='teletena-mvp-v133-fresh.localhost'
assert os.environ.get('TELE_TENA_TEST_SITE')==SITE
os.chdir(BENCH/'sites');sys.path.insert(0,str(BENCH/'apps/frappe'))
import frappe
frappe.init(site=SITE,sites_path=str(BENCH/'sites'));frappe.connect()
from tele_tena import accounting
from tele_tena.api import journey
from tele_tena.patches import v1_7_demo_subledger as opening, v1_8_legacy_event_reconciliation as import_events, v1_13_financial_reconciliation_audit as audit
try:
    if os.environ.get('TELE_TENA_VERIFY_RETAINED_UPGRADE') == '1':
        # Read-only diagnosis of this harness's retained fixture after failure.
        owners=['upgrade-p1@example.invalid','upgrade-p2@example.invalid','upgrade-boundary@example.invalid','upgrade-unknown@example.invalid']
        assert set(frappe.db.sql('SELECT patient FROM tt_wallet',pluck=True)) == set(owners)
        for owner,expected in zip(owners,((70000,30000),(65000,20000),(100,0),(100,0))):
            wallet=journey.one('SELECT available,reserved FROM tt_wallet WHERE patient=%s',(owner,))
            assert (int(wallet.available),int(wallet.reserved))==expected
            assert (accounting.balance('patient',owner,'available'),accounting.balance('patient',owner,'reserved'))==expected
        assert frappe.db.sql("SELECT COUNT(*) FROM tt_journal WHERE event_type='Opening'")[0][0]==4
        assert frappe.db.sql("SELECT COUNT(*) FROM tt_journal WHERE event_ref='deposit:post-opening'")[0][0]==1
        assert frappe.db.sql("SELECT COUNT(*) FROM tt_ledger WHERE reference='unknown:legacy-kind'")[0][0]==1
        assert frappe.db.sql("SELECT COUNT(*) FROM tt_appointment")[0][0]==2
        holds=frappe.db.sql('SELECT clinician,state,release_at FROM tt_earning')
        assert len(holds)==1 and holds[0][1]=='LegacyHold' and holds[0][2] is None
        for owner in owners[2:]:
            assert journey.one('SELECT status FROM tt_financial_reconciliation WHERE patient=%s',(owner,)).status=='ReviewRequired'
            try:
                accounting.check_wallet_projection(owner,journey.one('SELECT available,reserved FROM tt_wallet WHERE patient=%s',(owner,)))
                raise AssertionError('Held owner allowed to transact')
            except frappe.ValidationError:
                pass
        assert not frappe.db.sql('SELECT journal_id FROM tt_journal_line GROUP BY journal_id HAVING SUM(debit_minor)<>SUM(credit_minor)')
        report={'site':SITE,'legacy_patient_owners':4,'legacy_clinician_owners':2,'legacy_completed_holds':1,'opening_journals':4,'known_post_opening_import_once':True,'boundary_held_without_duplicate':True,'unknown_event_retained_and_held':True,'original_wallets_and_appointments_preserved':True,'automatic_historical_settlement':False,'scope':'representative financial-schema upgrade; not whole historical app checkout','retained_failure_diagnosis':'held-wallet command rejection was expected; projections verified by owner without clearing holds'}
        Path('/tmp/tt-legacy-financial-upgrade.json').write_text(json.dumps(report,indent=2))
        print('PASS: retained upgrade fixture reconciles per owner; boundary/unknown holds and all original records preserved.')
        raise SystemExit(0)
    # These guards refuse rerunning on a populated verification site; fixtures
    # and any financial discrepancy remain for diagnosis instead of being erased.
    for table in ('wallet','ledger','appointment','journal','earning','payout','dispute','financial_reconciliation'):
        assert frappe.db.sql('SELECT COUNT(*) FROM tt_'+table)[0][0]==0, 'Fresh disposable site is not empty'
    for table in reversed(tuple(opening.TABLES)):
        frappe.db.sql_ddl('DROP TABLE tt_'+table)
    owners=['upgrade-p1@example.invalid','upgrade-p2@example.invalid','upgrade-boundary@example.invalid','upgrade-unknown@example.invalid']
    for owner,available,reserved in zip(owners,(70000,60000,100,100),(30000,20000,0,0)):
        frappe.db.sql('INSERT INTO tt_wallet (patient,available,reserved) VALUES (%s,%s,%s)',(owner,available,reserved))
        deposit=available+reserved
        frappe.db.sql("INSERT INTO tt_ledger (id,patient,kind,amount,reference,created) VALUES (%s,%s,'Deposit',%s,%s,DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 2 DAY))",(str(uuid.uuid4()),owner,deposit,'deposit:legacy:'+owner))
        if reserved:
            appointment=str(uuid.uuid4())
            frappe.db.sql('''INSERT INTO tt_appointment (id,patient,clinician,offering,start,end,state,price,minutes,service_label,disclosure,choices,retry_key,payload_hash)
                VALUES (%s,%s,%s,'legacy-offering',DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 1 DAY),DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 23 HOUR),%s,%s,60,'Legacy counseling','{}','{}','legacy-book',%s)''',
                (appointment,owner,'upgrade-c'+str(owners.index(owner)+1)+'@example.invalid','Completed' if owner==owners[0] else 'Booked',reserved,hashlib.sha256(owner.encode()).hexdigest()))
            frappe.db.sql("INSERT INTO tt_ledger (id,patient,kind,amount,reference,created) VALUES (%s,%s,'Reservation',%s,%s,DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 1 DAY))",(str(uuid.uuid4()),owner,reserved,'booking:'+appointment))
    frappe.db.commit()
    old_wallets=frappe.db.sql('SELECT * FROM tt_wallet ORDER BY patient')
    old_events=frappe.db.sql('SELECT * FROM tt_ledger ORDER BY id')
    old_appointments=frappe.db.sql('SELECT * FROM tt_appointment ORDER BY id')
    opening.execute();opening.execute()
    assert old_wallets==frappe.db.sql('SELECT * FROM tt_wallet ORDER BY patient')
    assert old_events==frappe.db.sql('SELECT * FROM tt_ledger ORDER BY id')
    assert old_appointments==frappe.db.sql('SELECT * FROM tt_appointment ORDER BY id')
    assert frappe.db.sql("SELECT COUNT(*) FROM tt_journal WHERE event_type='Opening'")[0][0]==4
    holds=frappe.db.sql('SELECT clinician,state,release_at FROM tt_earning')
    assert len(holds)==1 and holds[0][1]=='LegacyHold' and holds[0][2] is None
    for owner in owners:
        wallet=journey.one('SELECT available,reserved FROM tt_wallet WHERE patient=%s',(owner,))
        accounting.check_wallet_projection(owner,wallet)
        assert audit.audit_wallet(owner)['matches']
    # Simulate known post-opening legacy writes only inside this isolated fixture.
    journey.simulation_log(owners[1],'Deposit',5000,'deposit:post-opening')
    frappe.db.sql('UPDATE tt_wallet SET available=available+5000 WHERE patient=%s',(owners[1],))
    assert import_events.reconcile_wallet_events(owners[1])==1
    assert import_events.reconcile_wallet_events(owners[1])==0
    accounting.check_wallet_projection(owners[1],journey.one('SELECT available,reserved FROM tt_wallet WHERE patient=%s',(owners[1],)))
    # Exact boundary is held, never silently excluded or posted twice.
    frappe.db.sql('UPDATE tt_ledger SET created=(SELECT created FROM tt_journal WHERE event_ref=%s) WHERE patient=%s',('opening:'+owners[2],owners[2]))
    assert import_events.reconcile_wallet_events(owners[2])==0
    assert not audit.audit_wallet(owners[2])['matches']
    assert journey.one('SELECT boundary_event_count,status FROM tt_financial_reconciliation WHERE patient=%s',(owners[2],)).boundary_event_count==1
    journey.simulation_log(owners[3],'UnsupportedKind',20,'unknown:legacy-kind')
    for retry in range(2):
        try:
            import_events.reconcile_wallet_events(owners[3])
            raise AssertionError('Unknown event accepted')
        except frappe.ValidationError:
            pass
        assert audit.audit_wallet(owners[3])['unknown_event_count']==1
    opening.execute()
    for owner in owners[:2]:
        accounting.check_wallet_projection(owner,journey.one('SELECT available,reserved FROM tt_wallet WHERE patient=%s',(owner,)))
    for owner in owners[2:]:
        try:
            accounting.check_wallet_projection(owner,journey.one('SELECT available,reserved FROM tt_wallet WHERE patient=%s',(owner,)))
            raise AssertionError('Held owner allowed to transact')
        except frappe.ValidationError:
            pass
    assert holds==frappe.db.sql('SELECT clinician,state,release_at FROM tt_earning')
    assert not frappe.db.sql('SELECT journal_id FROM tt_journal_line GROUP BY journal_id HAVING SUM(debit_minor)<>SUM(credit_minor)')
    frappe.db.commit()
    report={'site':SITE,'legacy_patient_owners':4,'legacy_clinician_owners':2,'legacy_completed_holds':1,'opening_journals':4,'known_post_opening_import_once':True,'boundary_held_without_duplicate':True,'unknown_event_retained_and_held':True,'original_wallets_and_appointments_preserved':True,'automatic_historical_settlement':False,'scope':'representative financial-schema upgrade; not whole historical app checkout'}
    Path('/tmp/tt-legacy-financial-upgrade.json').write_text(json.dumps(report,indent=2))
    print('PASS: four legacy owners, preserved records, one LegacyHold, repeat opening/import, boundary and unknown-event holds; no automatic settlement.')
finally:
    frappe.db.rollback();frappe.destroy()
