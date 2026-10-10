"""Real browser OTP recovery on the retained disposable fixture site only.
No SMS is sent. Site configuration restored and captured random codes removed.
"""
import json, os, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
BENCH=Path(__file__).resolve().parents[3]
APP=Path(__file__).resolve().parents[1]
SITE='tele-tena-pr12-fresh.localhost'
assert os.environ.get('TELE_TENA_TEST_SITE')==SITE
root=BENCH/'sites'/SITE
assert root.is_dir()
if len(sys.argv)>1:
    # Controlled expiry of only the challenge captured by this test's transport.
    assert sys.argv[1]=='expire'
    os.chdir(BENCH/'sites');sys.path.insert(0,str(BENCH/'apps/frappe'))
    import frappe
    from tele_tena.api import phone_auth
    capture=json.loads((root/'private/tele_tena_test_delivery.json').read_text())
    control=json.loads((root/'private/tele_tena_registration_control.json').read_text())
    frappe.init(site=SITE,sites_path=str(BENCH/'sites'));frappe.connect()
    digest=phone_auth._keyed('contact:phone',capture['contact'])
    row=frappe.db.sql("SELECT phone_digest,purpose,consumed FROM tt_otp_challenge WHERE id=%s",(control['challenge'],),as_dict=True)
    assert row and row[0].phone_digest==digest and row[0].purpose=='contact_phone' and not row[0].consumed
    frappe.db.sql('UPDATE tt_otp_challenge SET expires=UTC_TIMESTAMP(6)-INTERVAL 1 SECOND WHERE id=%s',(control['challenge'],))
    frappe.db.commit();frappe.destroy();sys.exit(0)
config=root/'site_config.json';before=config.read_bytes()
server=None
try:
    values=json.loads(before)
    values.update(tele_tena_phone_otp_enabled=True,tele_tena_patient_registration_enabled=True,tele_tena_clinician_registration_enabled=True)
    config.write_text(json.dumps(values));os.chmod(config,0o600)
    env=dict(os.environ,TELE_TENA_LOCAL_OTP_TEST='1',TELE_TENA_TEST_SITE=SITE,NODE_PATH='/tmp/tele-tena-browser/node_modules',TELE_TENA_REGISTRATION_ROOT=str(root))
    server=subprocess.Popen([str(BENCH/'env/bin/gunicorn'),'--bind','127.0.0.1:8028','--workers','1','--pythonpath',str(APP),'--chdir',str(BENCH/'sites'),'scripts.presentation_otp_test_wsgi:application'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(40):
        if server.poll() is not None:raise RuntimeError('Isolated test server exited')
        try:
            with urllib.request.urlopen('http://127.0.0.1:8028/teletena/sign-in',timeout=1) as response:
                if response.status==200:break
        except Exception:time.sleep(.25)
    else:raise RuntimeError('Isolated test server not ready')
    result=subprocess.run(['node',str(APP/'scripts/browser-registration-recovery.cjs')],env=env,cwd=APP,timeout=300)
    if result.returncode:raise RuntimeError('Registration recovery browser failed; diagnostic stage shown without secrets')
finally:
    if server:
        server.terminate()
        try:server.wait(timeout=10)
        except subprocess.TimeoutExpired:server.kill();server.wait()
    config.write_bytes(before);os.chmod(config,0o600)
    for file in ('tele_tena_test_delivery.json','tele_tena_registration_control.json'):
        (root/'private'/file).unlink(missing_ok=True)
    print('Disposable registration settings restored; loopback server stopped and captured codes removed.')
