"""Isolated existing-site preservation check; stores hashes, never record bodies.

No data writes, fixtures or seeding. Private snapshot must stay outside Git.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('action',choices=('snapshot','verify'))
parser.add_argument('--bench',type=Path,required=True)
parser.add_argument('--site',required=True)
parser.add_argument('--snapshot',type=Path,required=True)
parser.add_argument('--baseline-commit',choices=('800a591ac6af9c6c3b4afd61ed4353be4ff0826e','5efe78527309f8dab9e2a5bb391114cba153a862'),default='800a591ac6af9c6c3b4afd61ed4353be4ff0826e')
args=parser.parse_args()
assert args.site.startswith('teletena-') and args.site.endswith('.localhost'), 'Isolated site only'
bench=args.bench.resolve();site=bench/'sites'/args.site
assert site.resolve().parent==bench/'sites'
os.chdir(bench/'sites');sys.path.insert(0,str(bench/'apps/tele_tena'))
import frappe
frappe.init(site=args.site);frappe.connect();frappe.set_user('Administrator')

def digest(value):
    if isinstance(value,(bytes,bytearray,memoryview)):
        return {'binary_sha256':hashlib.sha256(bytes(value)).hexdigest()}
    return str(value)

def capture():
    names=[row[0] for row in frappe.db.sql('SHOW TABLES')]
    selected=[name for name in names if name.startswith(('tt_','tabTele Tena ')) or name in ('tabUser','tabHas Role','tabFile','__Auth')]
    tables={}
    for table in sorted(selected):
        assert '`' not in table
        columns=[row[0] for row in frappe.db.sql('SHOW COLUMNS FROM `'+table+'`')]
        records=frappe.db.sql('SELECT * FROM `'+table+'`')
        tables[table]={'columns':columns,'rows':sorted(hashlib.sha256(json.dumps(row,default=digest,separators=(',',':')).encode()).hexdigest() for row in records)}
    files={}
    for kind in ('public/files','private'):
        directory=site/kind
        if directory.exists():
            for path in directory.rglob('*'):
                relative=path.relative_to(site)
                if path.is_file() and not path.is_symlink() and 'backups' not in relative.parts:
                    files[str(relative)]=hashlib.sha256(path.read_bytes()).hexdigest()
    config={key:hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest() for key,value in json.loads((site/'site_config.json').read_text()).items()}
    return {'tables':tables,'files':files,'config':config}

try:
    if args.action=='snapshot':
        assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=bench/'apps/tele_tena',text=True).strip()==args.baseline_commit
        before=capture();before['source_commit']=args.baseline_commit;fd=os.open(args.snapshot,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'w') as stream:json.dump(before,stream)
        print('PASS: private hash-only baseline snapshot; no record writes')
    else:
        assert not args.snapshot.is_symlink() and not args.snapshot.stat().st_mode & 0o077
        before=json.loads(args.snapshot.read_text());after=capture()
        for table,expected in before['tables'].items():
            assert after['tables'].get(table)==expected,'Existing table/rows changed: '+table
        for name,expected in before['files'].items():assert after['files'].get(name)==expected,'Existing private/public file changed'
        assert after['config']==before['config'],'Existing configuration changed'
        extra=set(after['tables'])-set(before['tables'])
        assert extra==({'tt_history_document'} if before.get('source_commit','800a591').startswith('800a591') else set()),'Unexpected schema change'
        assert after['tables']['tt_history_document']['rows']==[],'Migration manufactured history documents'
        from tele_tena.accounting import check_wallet_projection
        wallets=frappe.db.sql('SELECT patient,available,reserved FROM tt_wallet',as_dict=True)
        for row in wallets:check_wallet_projection(row.patient,row)
        from tele_tena.accounting import balance
        # All clinician earnings owners, including existing zero-balance owners.
        users=frappe.db.sql("SELECT user FROM tt_profile WHERE kind='clinician'",pluck=True)
        for user in users:
            pending=int(frappe.db.sql("SELECT COALESCE(SUM(net_minor),0) FROM tt_earning WHERE clinician=%s AND state IN ('Pending','Disputed')",(user,))[0][0])
            released=int(frappe.db.sql("SELECT COALESCE(SUM(net_minor),0) FROM tt_earning WHERE clinician=%s AND state='Released'",(user,))[0][0])
            reserved=int(frappe.db.sql("SELECT COALESCE(SUM(amount_minor),0) FROM tt_payout WHERE clinician=%s AND state IN ('Requested','Processing')",(user,))[0][0])
            for bucket,expected in [('pending',pending),('earnings_available',released-reserved),('payout_reserved',reserved)]:
                assert expected>=0 and balance('clinician',user,bucket)==expected,'Clinician owner reconciliation mismatch'
        assert not frappe.db.sql('SELECT j.id FROM tt_journal j JOIN tt_journal_line l ON j.id=l.journal_id GROUP BY j.id HAVING SUM(l.debit_minor)<>SUM(l.credit_minor)'),'Unbalanced journal'
        from frappe.utils.password import check_password
        credentials=0
        for filename in ('tt-demo-mvp-v2-accounts.json','tele_tena_review_accounts.json'):
            for user,password in json.loads((site/'private'/filename).read_text()).items():check_password(user,password);credentials+=1
        print(json.dumps({'result':'PASS','existing_tables_unchanged':len(before['tables']),'existing_rows_unchanged':sum(len(x['rows']) for x in before['tables'].values()),'existing_file_hashes_unchanged':len(before['files']),'config_unchanged':True,'existing_passwords_accepted':credentials,'patient_owners_reconciled':len(wallets),'clinician_owners_reconciled':len(users),'additive_empty_table':list(extra)}))
finally:frappe.destroy()
