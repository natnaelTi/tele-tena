"""Repeat the additive subledger migration and verify preserved demo balances."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

BENCH = Path(__file__).resolve().parents[3]
SITE = os.environ.get('TELE_TENA_TEST_SITE', 'tele-tena-pr2-test.localhost')
os.chdir(BENCH / 'sites')
sys.path.insert(0, str(BENCH / 'apps/frappe'))
import frappe


def snapshot():
    wallets = frappe.db.sql('SELECT patient,available,reserved FROM tt_wallet ORDER BY patient', as_dict=True)
    legacy = frappe.db.sql('SELECT COUNT(*) n,COALESCE(SUM(amount),0) total FROM tt_ledger', as_dict=True)[0]
    earnings = frappe.db.sql('SELECT appointment,state,gross_minor,fee_minor,net_minor FROM tt_earning ORDER BY appointment', as_dict=True)
    balances = []
    for wallet in wallets:
        accounts = frappe.db.sql('''SELECT bucket,balance_minor FROM tt_financial_account
            WHERE owner=%s AND bucket IN ('available','reserved')''', (wallet.patient,), as_dict=True)
        account_balance = {item.bucket: int(item.balance_minor) for item in accounts}
        projection = {'available': int(wallet.available), 'reserved': int(wallet.reserved)}
        assert account_balance.get('available', 0) == projection['available']
        assert account_balance.get('reserved', 0) == projection['reserved']
        balances.append([wallet.patient, projection])
    unbalanced = frappe.db.sql('''SELECT COUNT(*) FROM (
        SELECT journal_id FROM tt_journal_line GROUP BY journal_id
        HAVING SUM(debit_minor)<>SUM(credit_minor) OR SUM(debit_minor)=0
    ) invalid''')[0][0]
    assert unbalanced == 0
    payload = {'wallets': balances, 'legacy_count': int(legacy.n), 'legacy_total': int(legacy.total),
               'earnings': [[r.appointment,r.state,int(r.gross_minor),int(r.fee_minor),int(r.net_minor)] for r in earnings],
               'journals': int(frappe.db.sql('SELECT COUNT(*) FROM tt_journal')[0][0]),
               'journal_lines': int(frappe.db.sql('SELECT COUNT(*) FROM tt_journal_line')[0][0])}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


if __name__ == '__main__':
    frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
    frappe.connect()
    before = snapshot()
    frappe.destroy()
    subprocess.run([shutil.which('bench'), '--site', SITE, 'migrate', '--skip-search-index'],
                   cwd=BENCH, check=True, stdout=subprocess.DEVNULL)
    frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
    frappe.connect()
    try:
        after = snapshot()
        assert before == after, 'Balances or historical financial records changed during repeated migration'
        print('PASS: repeat migration preserved wallet balances, legacy simulation log, earnings and balanced journals')
    finally:
        frappe.destroy()
