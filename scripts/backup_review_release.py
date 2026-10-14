"""Native complete Frappe backup, private files and no DB password in argv.

Run with the Bench Python. The local command-builder wrapper writes a temporary
client option file; no framework source or site credentials are modified.
"""
import argparse
import os
from pathlib import Path
import tempfile
from unittest.mock import patch


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bench',type=Path,required=True);parser.add_argument('--site',required=True);parser.add_argument('--destination',type=Path,required=True);args=parser.parse_args()
    bench=args.bench.resolve();dest=args.destination.resolve()
    assert os.geteuid()!=0,'Use the normal Bench user'
    assert (bench/'sites'/args.site).resolve().parent==bench/'sites','Invalid site name'
    assert not args.destination.is_symlink() and not dest.exists(),'Use a new backup directory, never overwrite an old bundle'
    dest.mkdir(mode=0o700,parents=False)
    os.chdir(bench/'sites')
    import frappe,frappe.database
    from frappe.utils.backups import BackupGenerator
    frappe.init(site=args.site,sites_path=str(bench/'sites'));frappe.connect();frappe.set_user('Administrator')
    assert 'tele_tena' in frappe.get_installed_apps(),'Expected TeleTena site'
    assert not frappe.get_system_settings('encrypt_backup'),'Encrypted backup policy enabled: stop for a verified encrypted backup procedure; do not disable encryption'
    assert frappe.conf.db_type in (None,'mariadb'),'Only tested MariaDB backup path supported'
    original=frappe.database.get_command
    try:
        with tempfile.TemporaryDirectory(prefix='client-',dir=dest) as tmp:
            def secure_command(*values,**kwargs):
                password=kwargs.pop('password',None)
                binary,arguments,name=original(*values,**kwargs)
                if password:
                    client=Path(tmp)/'client.cnf'
                    escaped=password.replace('\\','\\\\').replace('"','\\"').replace('\n','\\n').replace('\r','\\r')
                    fd=os.open(client,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                    with os.fdopen(fd,'w') as stream:stream.write('[client]\npassword="'+escaped+'"\n')
                    arguments.insert(0,'--defaults-extra-file='+str(client))
                assert not any(str(a).startswith('--password') for a in arguments),'Unsafe native command'
                return binary,arguments,name
            with patch('frappe.database.get_command',secure_command):
                backup=BackupGenerator(db_name=frappe.conf.db_name,user=frappe.conf.db_user or frappe.conf.db_name,password=frappe.conf.db_password,backup_path_db=str(dest/'database.sql.gz'),backup_path_files=str(dest/'public-files.tar'),backup_path_private_files=str(dest/'private-files.tar'),backup_path_conf=str(dest/'site-config.json'),ignore_conf=True,compress_files=False,db_type="mariadb",db_socket=frappe.conf.db_socket,db_host=frappe.conf.db_host,db_port=frappe.conf.db_port)
                backup.get_backup(force=True,ignore_files=False)
        from verify_release_backup import verify
        result=verify(dest)
        import json
        fd=os.open(dest/'verified-manifest.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as stream:json.dump(result,stream,indent=2)
        print('PASS: complete native database/public/private/config backup verified; destination:',dest)
    finally:frappe.destroy()

if __name__=='__main__':main()
