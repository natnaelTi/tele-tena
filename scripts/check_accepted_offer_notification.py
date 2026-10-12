"""Isolated persisted offer fixture; no presentation-site record changes or provider sends."""
import importlib.util,json,os,secrets,subprocess,tempfile,time,urllib.request
from pathlib import Path
APP=Path(__file__).resolve().parents[1];BENCH=APP.parents[1]
assert os.environ.get('TELE_TENA_TEST_SITE')=='tele-tena-pr12-fresh.localhost'
spec=importlib.util.spec_from_file_location('notification_test',APP/'tests/presentation.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
fixtures=module.fixtures;journey=module.journey;requests=module.open_requests
server=None;ready=False
try:
 module.Presentation.setUpClass();ready=True
 day=module.day_offset(21);offering=fixtures.Integration.offers['c1'];fixtures.login('c1');journey.save_profile('clinician','Fictional notification clinician',True,languages=['en']);module.scheduling.save_schedule(**module.schedule_payload(offering,day,mode='automatic'))
 fixtures.login('p1');journey.simulated_deposit(100000,secrets.token_hex(12));test=module.Presentation();slot=test.slots(offering,day)[0]
 req=requests.publish_request(service=fixtures.PREFIX,request_text='Fictional request for a notification journey.',urgency='scheduled',language='en',consultation_format='video',sharing={'name':False,'history':False},retry_key=secrets.token_hex(12),timezone_name='Africa/Addis_Ababa',earliest_start=slot['start'],latest_start=slot['start'])
 detail=requests.my_request_detail(req['id']);fixtures.login('c1');offer=requests.submit_offer(req['id'],offering,slot['start']);module.frappe.db.commit()
 with tempfile.TemporaryDirectory(prefix='tt-notification-') as temp:
  path=Path(temp)/'fixture.json';fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'w') as f:json.dump({'patient':fixtures.USERS['p1'],'clinician':fixtures.USERS['c1'],'password':fixtures.PASSWORD,'request':req['id'],'offer':offer['id'],'disclosure':detail['disclosure_snapshot']},f)
  env=dict(os.environ,NODE_PATH='/tmp/tele-tena-browser/node_modules',TELE_TENA_NOTIFICATION_FIXTURE=str(path))
  server=subprocess.Popen([str(BENCH/'env/bin/gunicorn'),'--bind','127.0.0.1:8028','--workers','1','--pythonpath',str(APP),'--chdir',str(BENCH/'sites'),'scripts.review_test_wsgi:application'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  for _ in range(40):
   assert server.poll() is None
   try:urllib.request.urlopen('http://127.0.0.1:8028/teletena/',timeout=1).close();break
   except Exception:time.sleep(.25)
  else:raise RuntimeError('Isolated browser server not ready')
  subprocess.run(['node',str(APP/'scripts/browser-accepted-offer-notification.cjs')],env=env,cwd=APP,check=True,timeout=100)
finally:
 if server:server.terminate();server.wait(timeout=10)
 if ready:module.Presentation.tearDownClass()
 print('Isolated fixture and owned server cleanup complete; presentation records untouched.')
