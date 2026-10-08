"""Run the built-app clinic calendar journey with private synthetic accounts."""
import os
from pathlib import Path
import subprocess
import sys

APP = Path(__file__).resolve().parents[1]
BENCH = APP.parents[1]
SITE = os.environ.get('TELE_TENA_TEST_SITE', '')
if not SITE.startswith('tele-tena-') or not SITE.endswith('.localhost'):
    raise SystemExit('Set TELE_TENA_TEST_SITE to an isolated synthetic site.')
SITE_PATH = BENCH / 'sites' / SITE
env = dict(os.environ)
env.update({
    'TELE_TENA_REVIEW_SITE_PATH': str(SITE_PATH),
    'TELE_TENA_BROWSER_ORIGIN': env.get('TELE_TENA_BROWSER_ORIGIN', 'http://127.0.0.1:8017'),
    'NODE_PATH': '/tmp/tele-tena-browser/node_modules',
})
result = subprocess.run(
    ['node', str(APP / 'scripts' / 'browser-clinic-calendar.cjs')],
    cwd=APP, env=env, check=False,
)
raise SystemExit(result.returncode)
