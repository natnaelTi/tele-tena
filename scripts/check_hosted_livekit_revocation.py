"""Verify cached participant tokens against the configured LiveKit Cloud project."""
import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

APP = Path(__file__).resolve().parents[1]
BENCH = APP.parents[1]
os.chdir(BENCH / 'sites')
sys.path.insert(0, str(BENCH / 'apps/frappe'))

import frappe
from tele_tena.api import journey
from tele_tena import livekit


def write_private(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream)
        stream.flush()
        os.fsync(stream.fileno())


def main():
    frappe.init(site='erp.localhost', sites_path=str(BENCH / 'sites'))
    url, _, _ = livekit._credentials()
    host = (urlsplit(url).hostname or '').lower()
    if not (host.endswith('.livekit.cloud') or host == 'livekit.cloud'):
        raise RuntimeError('Configured endpoint is not LiveKit Cloud; hosted revocation was not tested')
    spec = importlib.util.spec_from_file_location('consultation_fixtures', APP / 'tests/integration.py')
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    temporary = tempfile.TemporaryDirectory(prefix='tele-tena-cloud-revoke-')
    media_fixture_file = Path(temporary.name) / 'browser-media-fixture.json'
    revoke_fixture_file = Path(temporary.name) / 'browser-revocation-fixture.json'
    ready = False
    try:
        fixtures.Integration.setUpClass()
        ready = True
        fixtures.login('p1')
        journey.simulated_deposit(10000, secrets.token_hex(20))
        appointments = []
        for kind, hour in (('c1', 1), ('c2', 2)):
            args = fixtures.booking(fixtures.Integration.offers[kind], fixtures.at(hour), 'cloud-revoke-' + secrets.token_hex(8))
            appointment = journey.book(**args)['id']
            frappe.db.sql('''UPDATE tt_appointment SET start=UTC_TIMESTAMP()-INTERVAL 1 MINUTE,
                end=UTC_TIMESTAMP()+INTERVAL 29 MINUTE WHERE id=%s''', (appointment,))
            appointments.append((kind, appointment))
        frappe.db.commit()
        for filename, (kind, appointment) in zip((media_fixture_file, revoke_fixture_file), appointments):
            write_private(filename, {'users': fixtures.USERS, 'password': fixtures.PASSWORD,
                                     'appointment_id': appointment, 'appointment_label': 'Synthetic test consultation',
                                     'clinician_kind': kind})
        failures = []
        phase = os.environ.get('TELE_TENA_MEDIA_PHASE')
        checks = ([('browser-consultation-media.cjs', media_fixture_file)] if phase == 'end'
                  else [('browser-livekit-cloud-revocation.cjs', revoke_fixture_file)] if phase == 'revocation'
                  else [('browser-livekit-cloud-revocation.cjs', revoke_fixture_file),
                        ('browser-consultation-media.cjs', media_fixture_file)])
        for browser_check, fixture_file in checks:
            env = dict(os.environ, TELE_TENA_CALL_FIXTURE=str(fixture_file),
                       NODE_PATH='/tmp/tele-tena-browser/node_modules')
            result = subprocess.run(['node', str(APP / 'scripts' / browser_check)],
                                    env=env, cwd=APP, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, timeout=240)
            # The JS harness emits only safe checkpoints/results and never prints tokens.
            print(result.stdout.strip())
            if result.returncode:
                failures.append(browser_check)
        if failures:
            raise RuntimeError('Hosted browser checks failed: ' + ', '.join(failures))
    finally:
        if ready:
            try:
                fixtures.Integration.tearDownClass()
            except Exception:
                frappe.destroy()
                raise
        temporary.cleanup()


if __name__ == '__main__':
    main()
