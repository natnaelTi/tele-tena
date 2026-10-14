"""Account browser acceptance using owned accounts, never retained review edits.
Run with the bench Python and TELE_TENA_TEST_SITE=tele-tena-pr12-fresh.localhost.
Does not migrate, seed presentation records, or send notifications.
"""
import importlib.util
import json
import os
import subprocess
import tempfile
from pathlib import Path

app = Path(__file__).resolve().parents[1]
assert os.environ.get('TELE_TENA_TEST_SITE') == 'tele-tena-pr12-fresh.localhost'
spec = importlib.util.spec_from_file_location('account_browser_fixtures', app / 'tests/presentation.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
cls = module.Presentation
cls.setUpClass()
credential_file = None
try:
    fd, filename = tempfile.mkstemp(prefix='tt-owned-account-', suffix='.json')
    credential_file = Path(filename)
    with os.fdopen(fd, 'w') as stream:
        json.dump({'site': module.fixtures.SITE, 'users': module.fixtures.USERS,
                   'password': module.fixtures.PASSWORD}, stream)
    result = subprocess.run(['node', str(app / 'scripts/browser-mvp-account.cjs')],
        env={**os.environ, 'NODE_PATH': '/tmp/tele-tena-browser/node_modules',
             'TELE_TENA_ACCOUNT_FIXTURE': str(credential_file)}, timeout=180)
    if result.returncode:
        raise RuntimeError('Account browser acceptance failed; private details withheld')
    module.frappe.db.rollback()
    profile = module.frappe.db.sql('SELECT display_name,share_name,share_history FROM tt_profile WHERE user=%s',
                                   (module.fixtures.USERS['p1'],), as_dict=True)[0]
    assert profile.display_name == 'Meriem' and profile.share_name == 0 and profile.share_history == 1
    preference = module.frappe.db.sql('SELECT locale,timezone FROM tt_preferences WHERE user=%s',
                                      (module.fixtures.USERS['p1'],), as_dict=True)[0]
    assert preference.locale == 'en' and preference.timezone == 'UTC'
    print('PASS: owned profile, defaults and timezone persisted in MariaDB; fixtures cleaned up.')
finally:
    if credential_file:
        credential_file.unlink(missing_ok=True)
    cls.tearDownClass()
