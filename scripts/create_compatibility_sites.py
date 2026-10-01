"""Fresh sites only in the separate, disposable target-stack bench.

No framework files are patched. The bootstrap client receives passwords via a
mode-600 option file rather than command arguments. Never use on a shared bench.
"""
import contextlib
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
from unittest.mock import patch

BENCH = Path(__file__).resolve().parents[3]
RUNTIME = BENCH.parent / 'runtime'
assert BENCH.parent.name == 'teletena-compat' and os.geteuid() != 0
assert str(BENCH) != '/home/frappe/frappe/frappe-bench'
os.chdir(BENCH / 'sites')
import frappe
import frappe.database
from frappe.commands.site import new_site

credential_file = RUNTIME / 'database-admin.json'
assert credential_file.is_file() and (credential_file.stat().st_mode & 0o777) == 0o600
credentials = json.loads(credential_file.read_text())
original = frappe.database.get_command
sites = [('erp.localhost', 'tt16dev'), ('tele-tena-pr2-test.localhost', 'tt16review')]
if len(sys.argv) == 2:
    sites = [item for item in sites if item[0] == sys.argv[1]]
    assert sites, 'Unsupported disposable site'
for site, database in sites:
    assert not (BENCH / 'sites' / site).exists(), 'Refusing to replace an existing site'
    log = RUNTIME / (site + '-install.log')
    fd = os.open(log, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with tempfile.TemporaryDirectory(prefix='tt16-client-', dir=RUNTIME) as directory:
        def secure_command(*args, **kwargs):
            password = kwargs.pop('password', None)
            binary, arguments, name = original(*args, **kwargs)
            if password:
                assert all(c in '0123456789abcdef' for c in password)
                target = Path(directory) / (secrets.token_hex(12) + '.cnf')
                out = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                with os.fdopen(out, 'w') as stream:
                    stream.write('[client]\npassword=' + password + '\n')
                arguments.insert(0, '--defaults-extra-file=' + str(target))
            assert not any(str(arg).startswith('--password') for arg in arguments)
            return binary, arguments, name
        try:
            with os.fdopen(fd, 'w') as output, contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                with patch('frappe.database.get_command', secure_command):
                    new_site.callback(site=site, db_name=database, db_type='mariadb',
                        db_socket=str(RUNTIME / 'mariadb-target.sock'),
                        db_root_username=credentials['username'], db_root_password=credentials['password'],
                        admin_password=secrets.token_hex(32), db_password=secrets.token_hex(32),
                        mariadb_user_host_login_scope='localhost', install_app=['erpnext', 'tele_tena'])
        except Exception as error:
            import traceback
            for frame in traceback.extract_tb(error.__traceback__):
                print('Install failure location:', Path(frame.filename).name, frame.lineno, frame.name)
            raise SystemExit('Fresh site failed: ' + type(error).__name__ + '; private log retained')
    os.chmod(BENCH / 'sites' / site / 'site_config.json', 0o600)
    frappe.destroy()
    frappe.init(site=site, sites_path=str(BENCH / 'sites'))
    frappe.connect()
    assert {'frappe', 'erpnext', 'tele_tena'} <= set(frappe.get_installed_apps())
    from tele_tena.api.journey import simulation_enabled
    assert not simulation_enabled()
    if site == 'erp.localhost':
        from frappe.installer import update_site_config
        update_site_config('tele_tena_simulation_enabled', True)
    frappe.destroy()
    print('PASS: fresh target-stack installation, simulation initially disabled:', site, flush=True)
