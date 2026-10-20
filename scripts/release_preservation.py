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
    tables={}
    chosen=columns or {name:[r[0] for r in frappe.db.sql('SHOW COLUMNS FROM `'+name+'`')] for name in frappe.db.get_tables(cached=False) if name.startswith('tt_') or name in ('__Auth','tabUser','tabHas Role','tabFile','tabTele Tena Service','tabTele Tena Service Scope')}
    for name,fields in chosen.items():
        # Snapshot input is locally owned but SQL identifiers still require validation.
        assert name.startswith('tt_') or name in ('__Auth','tabUser','tabHas Role','tabFile','tabTele Tena Service','tabTele Tena Service Scope')
        assert all(field.replace('_','').isalnum() for field in fields)
        values=frappe.db.sql('SELECT '+','.join('`'+f+'`' for f in fields)+' FROM `'+name+'`')
        tables[name]={'columns':fields,'rows':sorted(row_hash(r) for r in values)}
    files={}
    for path in [site/'site_config.json',*(site/'private').rglob('*')]:
        if path.is_file() and 'backups' not in path.relative_to(site).parts:
            assert not path.is_symlink(),'Private file symlink needs separate review'
            files[str(path.relative_to(site))]=hashlib.sha256(path.read_bytes()).hexdigest()
    return {'site':site.name,'tables':tables,'files':files}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('snapshot','verify'));p.add_argument('--bench',type=Path,required=True);p.add_argument('--site',required=True);p.add_argument('--snapshot',type=Path,required=True);a=p.parse_args()
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
            assert actual==saved,'Original data/config/private-file hash mismatch; keep writers stopped and inspect privately'
        print('PASS:',a.action,'protected tables',len(saved['tables']),'rows',sum(len(t['rows']) for t in saved['tables'].values()),'private/config files',len(saved['files']))
    finally:frappe.db.rollback();frappe.destroy()

if __name__=='__main__':main()
