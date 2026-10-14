"""Explicit same-site MariaDB rollback using verified native backup components.

Web/workers must already be stopped and matching code checked out. No migration,
credential reset, grant changes or cross-site restore. No password in child argv.
"""
import argparse
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bench', type=Path, required=True)
    parser.add_argument('--site', required=True)
    parser.add_argument('--backup', type=Path, required=True)
    parser.add_argument('--confirm-restore-site', required=True)
    args = parser.parse_args()
    bench, backup = args.bench.resolve(), args.backup.resolve()
    assert os.geteuid() != 0, 'Use the normal Bench user'
    assert args.site == args.confirm_restore_site, 'Explicit same-site confirmation required'
    site = (bench / 'sites' / args.site).resolve()
    assert site.parent == bench / 'sites' and site.is_dir(), 'Existing site required'
    from verify_release_backup import verify
    verified = verify(backup)
    manifest = backup / "verified-manifest.json"
    assert manifest.is_file() and not manifest.is_symlink(), "Protected checksum manifest required"
    assert manifest.stat().st_uid == os.getuid() and not manifest.stat().st_mode & 0o077, "Private owned manifest required"
    assert json.loads(manifest.read_text()) == verified, "Backup checksum mismatch"
    current = json.loads((site / 'site_config.json').read_text())
    saved = json.loads((backup / 'site-config.json').read_text())
    for key in ('db_name', 'db_user', 'db_password', 'encryption_key'):
        assert current.get(key) == saved.get(key), 'Matching site credentials/config required'
    assert current.get('db_type', 'mariadb') == 'mariadb', 'Only MariaDB is verified'
    assert current.get('maintenance_mode'), 'Keep target site in maintenance'
    os.chdir(bench / 'sites')
    import frappe
    import frappe.database
    from frappe.database.db_manager import DbManager
    from frappe.installer import extract_files
    frappe.init(site=args.site, sites_path=str(bench / 'sites'))
    frappe.connect()
    original = frappe.database.get_command
    try:
        with tempfile.TemporaryDirectory(prefix='teletena-restore-') as tmp:
            def secure_command(*values, **kwargs):
                password = kwargs.pop('password', None)
                binary, arguments, name = original(*values, **kwargs)
                if password:
                    escaped = password.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
                    with tempfile.NamedTemporaryFile(mode='w', dir=tmp, delete=False) as stream:
                        stream.write('[client]\npassword="' + escaped + '"\n')
                        path = stream.name
                    arguments.insert(0, '--defaults-extra-file=' + path)
                assert not any(str(a).startswith('--password') for a in arguments), 'Unsafe native command'
                return binary, arguments, name
            with patch('frappe.database.get_command', secure_command):
                DbManager.restore_database(False, current['db_name'], str(backup / 'database.sql.gz'), current.get('db_user') or current['db_name'], current['db_password'])
        frappe.destroy()
        for archive in ('public-files.tar', 'private-files.tar'):
            copied = extract_files(args.site, str(backup / archive))
            Path(copied).unlink()
        print('PASS: same-site native database/public/private restore; no migration or credential change')
    finally:
        frappe.destroy()


if __name__ == '__main__':
    main()
