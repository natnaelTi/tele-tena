"""Local read-only, private hash checkpoint for an app-only site migration.
Never outputs row contents, credentials or file contents. Run while writers stop.
"""
import argparse
import hashlib,json,os
from pathlib import Path


def row_hash(row):
    def encode(value):
        return bytes(value).hex() if isinstance(value,(bytes,bytearray,memoryview)) else str(value)
    return hashlib.sha256(json.dumps(tuple(row),default=encode,separators=(',',':')).encode()).hexdigest()


def capture(frappe,site,columns=None):
    tables={};semantic={}
    chosen=columns or {name:[r[0] for r in frappe.db.sql('SHOW COLUMNS FROM `'+name+'`')] for name in frappe.db.get_tables(cached=False) if name.startswith(('tt_','tabTele Tena ')) or name in ('__Auth','tabUser','tabHas Role','tabFile','tabTele Tena Service','tabTele Tena Service Scope')}
    for name,fields in chosen.items():
        # Snapshot input is locally owned but SQL identifiers still require validation.
        assert name.startswith(('tt_','tabTele Tena ')) or name in ('__Auth','tabUser','tabHas Role','tabFile','tabTele Tena Service','tabTele Tena Service Scope')
        assert all(c.isalnum() or c in ' _-' for c in name),'Unsafe table identifier'
        assert all(field.replace('_','').isalnum() for field in fields)
        values=frappe.db.sql('SELECT '+','.join('`'+f+'`' for f in fields)+' FROM `'+name+'`')
        tables[name]={'columns':fields,'rows':sorted(row_hash(r) for r in values)}
        records=[dict(zip(fields,row)) for row in values]
        identity=lambda value:hashlib.sha256(str(value).encode()).hexdigest()
        if name=='tabUser':semantic['users']={identity(r['name']):{'full':row_hash(tuple(r[f] for f in fields)),'stable':row_hash(tuple(r[f] for f in fields if f not in ('modified','modified_by')))} for r in records}
        if name=='tabHas Role':semantic['roles']={identity(r['name']):{'full':row_hash(tuple(r[f] for f in fields)),'stable':row_hash(tuple(r[f] for f in fields if f not in ('modified','modified_by','idx'))),'parent':identity(r['parent']),'role':r['role']} for r in records}
        if name=='tt_audit':
            eligible={}
            for r in records:
                try:evidence=json.loads(r['evidence'] or '{}')
                except (ValueError,TypeError):continue
                if r['actor']=='Administrator' and r['action']=='ReviewerFinancialDefaultGranted' and evidence=={'role':'Tele Tena Financial Configuration','policy':'reviewer-default-2026-10-28','source':'v1.48 owner-approved default'}:
                    eligible[row_hash(tuple(r[f] for f in fields))]=identity(r['subject'])
            semantic['reviewer_default_audits']=eligible

    files={}
    for path in [site/'site_config.json',*(site/'private').rglob('*')]:
        if path.is_file() and 'backups' not in path.relative_to(site).parts:
            assert not path.is_symlink(),'Private file symlink needs separate review'
            files[str(path.relative_to(site))]=hashlib.sha256(path.read_bytes()).hexdigest()
    return {'site':site.name,'tables':tables,'files':files,'reviewer_default_v148':semantic}


def verify_snapshot(saved,actual,allow_reviewer_default=False):
    if all(saved.get(key)==actual.get(key) for key in ('site','tables','files')):return 0
    assert allow_reviewer_default,'Original data/config/private-file hash mismatch; keep writers stopped and inspect privately'
    assert saved['site']==actual['site'] and saved['files']==actual['files'],'Site/private/configuration changed'
    assert saved['tables'].keys()==actual['tables'].keys(),'Protected table set changed'
    special={'tabUser','tabHas Role','tt_audit'}
    for table in saved['tables']:
        assert saved['tables'][table]['columns']==actual['tables'][table]['columns'],'Protected columns changed'
        if table not in special:assert saved['tables'][table]==actual['tables'][table],'Unrelated protected records changed'
    assert 'reviewer_default_v148' in saved and 'reviewer_default_v148' in actual,'Expected-role verification requires a snapshot from this helper version'
    before=saved['reviewer_default_v148'];after=actual['reviewer_default_v148']
    roles=before['roles'];new_roles=after['roles'];assert roles.keys()<=new_roles.keys(),'An existing role record was removed'
    additions=[v for k,v in new_roles.items() if k not in roles]
    assert additions and all(r['role']=='Tele Tena Financial Configuration' for r in additions),'Unexpected new role'
    parents={r['parent'] for r in additions};assert len(parents)==len(additions),'Duplicate role grant'
    for parent in parents:
        old={r['role'] for r in roles.values() if r['parent']==parent}
        assert 'Tele Tena Approver' in old and 'Tele Tena Financial Configuration' not in old,'Grant not an existing reviewer default'
    for key,row in roles.items():assert row==new_roles[key] if row['parent'] not in parents else row['stable']==new_roles[key]['stable'],'Existing role changed beyond expected ordering/audit metadata'
    assert before['users'].keys()==after['users'].keys(),'User set changed'
    for key,row in before['users'].items():assert row==after['users'][key] if key not in parents else row['stable']==after['users'][key]['stable'],'User credentials/settings changed'
    old_audit=saved['tables']['tt_audit']['rows'];new_audit=actual['tables']['tt_audit']['rows'];assert set(old_audit)<=set(new_audit),'Historical audit changed'
    extra=[h for h in new_audit if h not in set(old_audit)]
    assert len(extra)==len(parents) and {after['reviewer_default_audits'].get(h) for h in extra}==parents,'Missing or unrelated reviewer-default audit'
    return len(parents)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('snapshot','verify'));p.add_argument('--bench',type=Path,required=True);p.add_argument('--site',required=True);p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--expect-reviewer-default-v148',action='store_true',help='Verify only the previously owner-approved reviewer financial-role backfill; every other record/credential/file remains strict');a=p.parse_args()
    bench=a.bench.resolve();site=(bench/'sites'/a.site).resolve();assert site.parent==bench/'sites' and site.is_dir()
    assert os.geteuid()!=0,'Use the normal Bench user';os.chdir(bench/'sites')
    import frappe
    try:
        frappe.init(site=a.site,sites_path=str(bench/'sites'));frappe.connect()
        if a.action=='snapshot':
            saved=capture(frappe,site)
            fd=os.open(a.snapshot,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            with os.fdopen(fd,'w') as out:json.dump(saved,out)
        else:
            assert not a.snapshot.is_symlink() and a.snapshot.stat().st_uid==os.getuid() and not a.snapshot.stat().st_mode&0o077,'Private owned checkpoint required'
            saved=json.loads(a.snapshot.read_text());assert saved['site']==a.site
            actual=capture(frappe,site,{n:v['columns'] for n,v in saved['tables'].items()})
            expected=verify_snapshot(saved,actual,a.expect_reviewer_default_v148)
            if expected:print('PASS: audited owner-approved v1.48 reviewer defaults:',expected,'all other protected values unchanged')
        print('PASS:',a.action,'protected tables',len(saved['tables']),'rows',sum(len(t['rows']) for t in saved['tables'].values()),'private/config files',len(saved['files']))
    finally:frappe.db.rollback();frappe.destroy()

if __name__=='__main__':main()
