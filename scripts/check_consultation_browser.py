"""End-to-end fake-media test against a disposable local LiveKit server."""
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time

APP = Path(__file__).resolve().parents[1]
BENCH = APP.parents[1]
SITE = BENCH / 'sites' / 'erp.localhost'
SECRET_FILE = SITE / 'private' / 'tele_tena_livekit.json'
SERVER = Path('/tmp/livekit-server')
os.chdir(BENCH / 'sites')
sys.path.insert(0, str(BENCH / 'apps/frappe'))

import frappe
from tele_tena.api import journey

spec_path = APP / 'tests/integration.py'
import importlib.util
spec = importlib.util.spec_from_file_location('consultation_fixtures', spec_path)
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


def write_private(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, 'w') as output:
        json.dump(value, output)
        output.flush()
        os.fsync(output.fileno())


def main():
    if not SERVER.is_file():
        raise RuntimeError('Temporary LiveKit server binary is unavailable')
    if SECRET_FILE.exists() or SECRET_FILE.is_symlink():
        raise RuntimeError('Local LiveKit configuration already exists; refusing to replace it')
    key, secret = 'test_' + secrets.token_urlsafe(18), secrets.token_urlsafe(36)
    fixture_file = None
    server = None
    log = None
    created_credentials = False
    fixtures_ready = False
    try:
        with tempfile.TemporaryDirectory(prefix='tele-tena-livekit-check-') as tmp:
            directory = Path(tmp)
            config = directory / 'livekit.yaml'
            config.write_text('port: 7880\nrtc:\n  tcp_port: 7881\n  port_range_start: 50000\n  port_range_end: 50100\nkeys:\n  ' + json.dumps(key) + ': ' + json.dumps(secret) + '\n')
            config.chmod(0o600)
            log_path = directory / 'livekit.log'
            log = open(log_path, 'w')
            os.chmod(log_path, 0o600)
            write_private(SECRET_FILE, {'url': 'ws://127.0.0.1:7880', 'api_key': key, 'api_secret': secret})
            created_credentials = True
            server = subprocess.Popen([str(SERVER), '--config', str(config)], stdout=log, stderr=subprocess.STDOUT)
            for _ in range(60):
                if server.poll() is not None:
                    raise RuntimeError('Temporary LiveKit server did not start')
                try:
                    with socket.create_connection(('127.0.0.1', 7880), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.5)
            else:
                raise RuntimeError('Temporary LiveKit server did not become ready')

            fixtures.Integration.setUpClass()
            fixtures_ready = True
            fixtures.login('p1')
            journey.simulated_deposit(3000, 'livekit-browser-test-fund')
            args = fixtures.booking(fixtures.Integration.offers['c1'], fixtures.at(1), 'livekit-browser-booking')
            appointment = journey.book(**args)['id']
            # Move only this disposable synthetic booking into its demo join window.
            frappe.db.sql('''UPDATE tt_appointment SET start=UTC_TIMESTAMP()-INTERVAL 1 MINUTE,
                end=UTC_TIMESTAMP()+INTERVAL 29 MINUTE WHERE id=%s''', (appointment,))
            frappe.db.commit()
            fixture_path = directory / 'browser-fixture.json'
            write_private(fixture_path, {'users': fixtures.USERS, 'password': fixtures.PASSWORD,
                                         'appointment_id': appointment, 'appointment_label': 'Synthetic test consultation'})
            fixture_file = fixture_path
            env = dict(os.environ, TELE_TENA_CALL_FIXTURE=str(fixture_path),
                       NODE_PATH='/tmp/tele-tena-browser/node_modules')
            result = subprocess.run(['node', str(APP / 'scripts/browser-consultation-media.cjs')],
                                    env=env, cwd=APP, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            if result.returncode:
                for line in result.stdout.splitlines():
                    if line.startswith('FAIL: consultation browser checkpoint '):
                        print(line)
                raise RuntimeError('Independent browser media check failed')
            print(result.stdout.strip())
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
        if log:
            log.close()
        if created_credentials and SECRET_FILE.is_file() and not SECRET_FILE.is_symlink():
            SECRET_FILE.unlink()
        if fixture_file and fixture_file.exists():
            fixture_file.unlink()
        if fixtures_ready:
            try:
                fixtures.Integration.tearDownClass()
            except Exception:
                frappe.destroy()
                raise


if __name__ == '__main__':
    main()
