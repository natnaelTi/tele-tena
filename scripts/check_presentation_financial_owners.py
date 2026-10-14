"""Read-only, consistent-snapshot reconciliation; never repairs projections.
Reports counts only, never account identities, records or clinical content.
"""
import json, os, sys
from pathlib import Path
BENCH=Path(__file__).resolve().parents[3]
SITE='teletena-mvp-presentation.localhost'
assert os.environ.get('TELE_TENA_TEST_SITE')==SITE
os.chdir(BENCH/'sites');sys.path.insert(0,str(BENCH/'apps/frappe'))
import frappe
frappe.init(site=SITE,sites_path=str(BENCH/'sites'));frappe.connect()
try:
    frappe.db.rollback()
    # Frappe rollback immediately begins another transaction; end that empty
    # transaction before setting this read-only audit's snapshot semantics.
    frappe.db.sql('ROLLBACK')
    frappe.db.sql('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
    frappe.db.sql('START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY')
    accounts=frappe.db.sql('''SELECT a.id,a.owner,a.bucket,a.normal_side,a.balance_minor,
        COALESCE(SUM(l.debit_minor),0) debits,COALESCE(SUM(l.credit_minor),0) credits
        FROM tt_financial_account a LEFT JOIN tt_journal_line l ON l.account_id=a.id
        GROUP BY a.id''',as_dict=True)
    projected={a.id:int(a.balance_minor) for a in accounts}
    account_errors=sum(int(a.balance_minor)!=(int(a.credits)-int(a.debits) if a.normal_side=='C' else int(a.debits)-int(a.credits)) for a in accounts)
    wallets=frappe.db.sql('SELECT patient,available,reserved FROM tt_wallet',as_dict=True)
    patient_errors=sum(any(projected.get('patient:'+w.patient+':'+bucket,0)!=int(w[bucket]) for bucket in ('available','reserved')) for w in wallets)
    owners={a.owner for a in accounts if a.id.startswith('clinician:')}
    clinician_errors=0
    for owner in owners:
        pending=int(frappe.db.sql("SELECT COALESCE(SUM(net_minor),0) FROM tt_earning WHERE clinician=%s AND state IN ('Pending','Disputed')",(owner,))[0][0])
        payout=int(frappe.db.sql("SELECT COALESCE(SUM(amount_minor),0) FROM tt_payout WHERE clinician=%s AND state IN ('Requested','Processing')",(owner,))[0][0])
        released=int(frappe.db.sql("SELECT COALESCE(SUM(net_minor),0) FROM tt_earning WHERE clinician=%s AND state='Released'",(owner,))[0][0])
        clinician_errors+=any(projected.get('clinician:'+owner+':'+bucket,0)!=expected for bucket,expected in [('pending',pending),('payout_reserved',payout),('earnings_available',released-payout)])
    journal_errors=len(frappe.db.sql('''SELECT journal_id FROM tt_journal_line GROUP BY journal_id
        HAVING SUM(debit_minor)<>SUM(credit_minor)'''))
    report={'site':SITE,'read_only':True,'patient_owners_checked':len(wallets),'clinician_owners_checked':len(owners),'accounts_checked':len(accounts),'patient_projection_mismatches':patient_errors,'clinician_obligation_mismatches':clinician_errors,'account_journal_mismatches':account_errors,'unbalanced_journals':journal_errors}
    Path('/tmp/tt-presentation-financial-owners.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))
    assert not any((patient_errors,clinician_errors,account_errors,journal_errors)), 'Financial discrepancy preserved; no repair attempted'
finally:
    frappe.db.rollback();frappe.destroy()
