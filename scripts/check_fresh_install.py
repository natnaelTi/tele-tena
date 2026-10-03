"""Disposable fresh install via the installed Bench/Frappe installer, normal user.

DB admin credential file is generated locally, never printed or passed in argv.
Only the new tele-tena-pr12-fresh.localhost / teletenapr12fresh may be created or removed.
"""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.request
from unittest.mock import patch

import frappe
import pymysql

BENCH = Path(__file__).resolve().parents[3]
SITE = 'tele-tena-pr12-fresh.localhost'
DB = 'teletenapr12fresh'
RETAINED_SITE = 'tele-tena-pr2-test.localhost'
ADMIN = 'tt_pr12_site_admin'
CREDENTIALS = Path('/tmp/tele-tena-pr12-db-admin.json')
LOG = Path('/tmp/tele-tena-pr12-fresh-install.log')
SITE_PATH = BENCH / 'sites' / SITE
assert os.geteuid() != 0, 'Run as the normal Linux user, never root'
assert not SITE_PATH.exists(), 'Disposable site already exists; refusing to overwrite it'
assert CREDENTIALS.is_file() and not CREDENTIALS.is_symlink()
assert stat.S_IMODE(CREDENTIALS.stat().st_mode) == 0o600
assert CREDENTIALS.stat().st_uid == os.getuid()
assert not LOG.exists() and not LOG.is_symlink(), 'Fresh-install log already exists; refusing to overwrite it'
credentials = json.loads(CREDENTIALS.read_text())
assert credentials['db_root_username'] == ADMIN and credentials['db_name'] == DB
socket = next(path for path in ('/run/mysqld/mysqld.sock', '/var/run/mysqld/mysqld.sock') if Path(path).exists())

def administration():
    return pymysql.connect(unix_socket=socket, user=ADMIN, password=credentials['db_root_password'], autocommit=True)


def retained_fingerprint():
    from tele_tena.schema import TABLES
    from tele_tena.patches.v1_6_presentation_release import TABLES as PRESENTATION_TABLES
    from tele_tena.patches.v1_7_demo_subledger import TABLES as SUBLEDGER_TABLES
    frappe.init(site=RETAINED_SITE, sites_path=str(BENCH / 'sites'))
    frappe.connect()
    content = {}
    for table in (*TABLES, *PRESENTATION_TABLES, *SUBLEDGER_TABLES, 'phone_identity','otp_challenge','otp_rate_limit','otp_gate','consultation','contact_identity','onboarding'):
        records = frappe.db.sql(f'SELECT * FROM tt_{table}', as_dict=True)
        content[table] = sorted(json.dumps(dict(row), sort_keys=True, default=str) for row in records)
    for table in ('tabTele Tena Service', 'tabTele Tena Service Scope'):
        content[table] = sorted(json.dumps(dict(row), sort_keys=True, default=str) for row in frappe.db.sql(f'SELECT * FROM `{table}`', as_dict=True))
    for name in ('site_config.json', 'private/tele_tena_livekit.json', 'private/tele_tena_sms.json', 'private/tele_tena_email.json'):
        path = BENCH / 'sites' / RETAINED_SITE / name
        if path.is_file():
            content[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    digest = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).digest()
    frappe.destroy()
    return digest


def enabled_registration_browser_check():
    """Exercise signup/onboarding only on this explicitly disposable fresh site."""
    from frappe.installer import update_site_config
    for key, value in (
        ('tele_tena_review_site', SITE),
        ('tele_tena_review_enabled', True),
        ('tele_tena_phone_otp_enabled', True),
        ('tele_tena_patient_registration_enabled', True),
        ('tele_tena_clinician_registration_enabled', True),
    ):
        update_site_config(key, value)
    frappe.clear_cache()
    frappe.destroy()

    port = '8021'
    app_env = dict(os.environ, TELE_TENA_TEST_SITE=SITE, PYTHONUNBUFFERED='1')
    command = [str(BENCH / 'env/bin/gunicorn'), '--bind', '127.0.0.1:' + port,
               '--workers', '2', '--pythonpath', './apps/tele_tena', '--chdir', './sites',
               'scripts.review_test_wsgi:application']
    server = subprocess.Popen(command, cwd=BENCH, env=app_env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        url = 'http://127.0.0.1:' + port + '/teletena/sign-in'
        for _ in range(80):
            if server.poll() is not None:
                raise RuntimeError('Disposable-site browser server exited before readiness')
            try:
                with urllib.request.urlopen(url, timeout=1) as response:
                    if response.status == 200:
                        break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError('Disposable-site browser server did not become ready')

        env = dict(os.environ,
                   TELE_TENA_TEST_SITE=SITE,
                   TELE_TENA_TEST_API_ORIGIN='http://127.0.0.1:' + port,
                   TELE_TENA_TEST_BASE='http://127.0.0.1:' + port + '/teletena',
                   TELE_TENA_REDIRECTED_BROWSER='1')
        result = subprocess.run([str(BENCH / 'env/bin/python'),
                                 str(APP / 'scripts/check_redesign_browser.py')],
                                cwd=BENCH, env=env, timeout=360,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        print(result.stdout.strip())
        if result.returncode:
            raise RuntimeError('Enabled-registration fresh-site browser journey failed')

        invited_env = dict(os.environ, NODE_PATH='/tmp/tele-tena-browser/node_modules',
                           TELE_TENA_TEST_BASE='http://127.0.0.1:8017/teletena')
        invited = subprocess.run(['node', str(APP / 'scripts/browser-invited-review.cjs')],
                                 cwd=APP, env=invited_env, timeout=90,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        print(invited.stdout.strip())
        if invited.returncode:
            raise RuntimeError('Invited-review browser policy check failed')
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)


os.chdir(BENCH / 'sites')
admin = administration()
with admin.cursor() as cursor:
    cursor.execute('SHOW DATABASES LIKE %s', (DB,))
    assert cursor.fetchone() is None, 'Disposable database already exists'
admin.close()
retained_before = retained_fingerprint()
attempted = False
passed = False
try:
    # Frappe 15's SQL bootstrap CLI normally places its site DB password in argv.
    # Test-only command builder adaptation uses a mode-600 client option file.
    # No framework files are edited; all real installer/model hooks still run.
    import frappe.database
    original = frappe.database.get_command
    with tempfile.TemporaryDirectory(prefix='tt-pr2-db-client-') as directory:
        def secure_command(*args, **kwargs):
            password = kwargs.pop('password', None)
            binary, arguments, name = original(*args, **kwargs)
            if password:
                assert all(char in '0123456789abcdef' for char in password)
                path = Path(directory) / ('client-' + secrets.token_hex(8) + '.cnf')
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, 'w') as stream:
                    stream.write('[client]\npassword=' + password + '\n')
                arguments.insert(0, '--defaults-extra-file=' + str(path))
            assert not any(argument.startswith('--password') for argument in arguments)
            return binary, arguments, name
        log_fd = os.open(LOG, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(log_fd, 'w') as output:
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                from frappe.commands.site import new_site
                attempted = True
                with patch('frappe.database.get_command', secure_command):
                    new_site.callback(db_name=DB, site=SITE, db_root_username=ADMIN,
                              db_root_password=credentials['db_root_password'],
                              admin_password=secrets.token_hex(32), db_password=secrets.token_hex(32),
                              db_type='mariadb', db_socket=socket,
                              mariadb_user_host_login_scope='localhost',
                              install_app=['erpnext', 'tele_tena'])
        os.chmod(SITE_PATH / 'site_config.json', 0o600)
    frappe.destroy()
    frappe.init(site=SITE, sites_path=str(BENCH / 'sites'))
    frappe.connect()
    assert {'frappe', 'erpnext', 'tele_tena'} <= set(frappe.get_installed_apps())
    from tele_tena.schema import TABLES
    from tele_tena.patches.v1_6_presentation_release import TABLES as PRESENTATION_TABLES
    from tele_tena.patches.v1_7_demo_subledger import TABLES as SUBLEDGER_TABLES
    assert all('tt_' + table in frappe.db.get_tables(cached=False) for table in (*TABLES,*PRESENTATION_TABLES,*SUBLEDGER_TABLES))
    assert 'tt_consultation' in frappe.db.get_tables(cached=False)
    assert frappe.db.exists('DocType', 'Tele Tena Service')
    assert frappe.db.exists('DocType', 'Tele Tena Service Scope')
    assert frappe.db.sql("SHOW COLUMNS FROM tt_appointment LIKE 'policy_snapshot'")
    assert frappe.db.sql("SHOW COLUMNS FROM tt_application LIKE 'requested_services'")
    assert frappe.db.count('Tele Tena Service Scope') == 0
    assert frappe.db.sql('SELECT COUNT(*) FROM tt_wallet')[0][0] == 0
    for role in ('Tele Tena Patient', 'Tele Tena Clinician', 'Tele Tena Approver'):
        assert frappe.db.exists('Role', role)
    for version in ('v1_0_command_storage', 'v1_1_native_catalog', 'v1_2_catalog_adoption_check', 'v1_3_phone_auth', 'v1_3_consultations', 'v1_4_consultation_close_state', 'v1_5_contact_onboarding', 'v1_6_presentation_release', 'v1_7_demo_subledger', 'v1_8_legacy_event_reconciliation'):
        assert frappe.db.exists('Patch Log', {'patch': 'tele_tena.patches.' + version})
    from tele_tena.api import journey
    assert not journey.simulation_enabled(), 'Simulation unexpectedly enabled on disposable site'
    frappe.set_user('Guest')
    try:
        journey.services()
        raise AssertionError('Guest app access was allowed')
    except frappe.PermissionError:
        pass
    if os.environ.get('TELE_TENA_REVIEW_CHECK') == '1':
        from check_review_site import verify
        verify()
    if os.environ.get('TELE_TENA_REVIEW_CHECK') == 'full':
        enabled_registration_browser_check()
    frappe.destroy()
    assert retained_fingerprint() == retained_before, 'Retained development records changed'
    passed = True
    print('PASS: fresh Frappe + ERPNext + tele_tena install, native models, roles, presentation and subledger schemas, ten migrations, guest denial and simulation disabled before explicit review setup; retained development records unchanged')
except Exception as error:
    import traceback
    for frame in traceback.extract_tb(error.__traceback__):
        print('Failure location:', Path(frame.filename).name, frame.lineno, frame.name)
    print('Fresh installation failed (' + type(error).__name__ + '); credential contents withheld')
    raise SystemExit(1)
finally:
    with contextlib.suppress(Exception):
        frappe.destroy()
    admin = administration()
    with admin.cursor() as cursor:
        if attempted:
            cursor.execute(f'DROP DATABASE IF EXISTS `{DB}`')
            cursor.execute(f"DROP USER IF EXISTS '{DB}'@'localhost'")
        cursor.execute(f"DROP USER '{ADMIN}'@'localhost'")
    admin.close()
    if attempted and SITE_PATH.exists():
        assert SITE_PATH.resolve() == (BENCH / 'sites' / SITE).resolve()
        shutil.rmtree(SITE_PATH)
    CREDENTIALS.unlink()
    with contextlib.suppress(FileNotFoundError):
        LOG.unlink()
    denied = False
    try:
        unexpected = administration()
        unexpected.close()
    except pymysql.err.OperationalError as error:
        denied = error.args[0] in (1045, 1698)
    assert denied and not CREDENTIALS.exists() and not SITE_PATH.exists(), 'Cleanup verification failed'
    print('CLEANUP PASS: disposable site/database/site user and temporary localhost administrator removed; credential file removed; administrator re-authentication denied')
