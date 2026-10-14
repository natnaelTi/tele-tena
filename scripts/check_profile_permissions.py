"""Focused profile and retry regressions with matching DB and HTTP fixture site."""
import os, subprocess, time, urllib.request
from pathlib import Path
APP=Path(__file__).resolve().parents[1]
BENCH=APP.parents[1]
SITE='tele-tena-pr12-fresh.localhost'
assert os.environ.get('TELE_TENA_TEST_SITE')==SITE
server=None
try:
    env=dict(os.environ,TELE_TENA_TEST_BASE='http://127.0.0.1:8028')
    server=subprocess.Popen([str(BENCH/'env/bin/gunicorn'),'--bind','127.0.0.1:8028','--workers','1','--pythonpath',str(APP),'--chdir',str(BENCH/'sites'),'scripts.review_test_wsgi:application'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(40):
        if server.poll() is not None:raise RuntimeError('Owned isolated server exited')
        try:
            with urllib.request.urlopen('http://127.0.0.1:8028/teletena/sign-in',timeout=1) as response:
                if response.status==200:break
        except Exception:time.sleep(.25)
    else:raise RuntimeError('Owned isolated server not ready')
    subprocess.run([str(BENCH/'env/bin/python'),str(APP/'tests/integration.py'),'Integration.test_public_introduction_is_explicit_owner_content','Integration.test_pending_applicant_can_edit_only_existing_own_profile','Integration.test_12_successful_retry_precedes_mutable_profile_validation','Integration.test_13_request_overrides_never_change_profile_defaults'],env=env,cwd=APP,timeout=150,check=True)
finally:
    if server:
        server.terminate()
        try:server.wait(timeout=10)
        except subprocess.TimeoutExpired:server.kill();server.wait()
    print('Owned matching-site regression server stopped; site settings and OTP limits unchanged.')
