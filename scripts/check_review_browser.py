"""Temporary synthetic browser fixtures, cleaned without altering retained demo data."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile

APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('review_fixtures', APP / 'tests/integration.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
fixtures.Integration.setUpClass()
try:
    for kind, name in (('c1', 'Synthetic Clinician A'), ('c2', 'Synthetic Clinician B')):
        fixtures.login(kind)
        fixtures.api.save_profile('clinician', name, True)
    fixtures.frappe.db.commit()
    with tempfile.TemporaryDirectory(prefix='tt-pr2-browser-') as directory:
        path = Path(directory) / 'fixtures.json'
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(dict(users=fixtures.USERS, password=fixtures.PASSWORD, service=fixtures.PREFIX,
                           start=fixtures.at(2)[:16]), stream)
        env = dict(os.environ, TELE_TENA_BROWSER_FIXTURES=str(path))
        result = subprocess.run(['node', str(APP / 'scripts/browser-pr2-review.cjs')], env=env)
        assert result.returncode == 0, 'Synthetic browser regression failed'
finally:
    fixtures.Integration.tearDownClass()
    print('Temporary synthetic browser fixtures cleaned up')
