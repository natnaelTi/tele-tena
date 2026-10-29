"""Loopback disposable-site transport. Never import in a hosted environment."""
import hashlib,json,os
from pathlib import Path
import frappe.app
from werkzeug.middleware.shared_data import SharedDataMiddleware
from tele_tena import email_delivery,sms
ROOT=Path(__file__).resolve().parents[1];BENCH=Path('/home/frappe/teletena-compat/bench');SITE='teletena-payments-v147-fresh.localhost';CAPTURE=Path('/home/frappe/teletena-offline-sprint/codes')
assert os.environ.get('TELE_TENA_TEST_SITE')==SITE and os.environ.get('TELE_TENA_LOCAL_JOB_TEST')=='1'
CAPTURE.mkdir(mode=0o700,exist_ok=True)
def code(contact,value):
    assert contact.endswith('@offline-test.invalid') or contact.startswith('+251900020')
    file=CAPTURE/hashlib.sha256(contact.encode()).hexdigest();fd=os.open(file,os.O_CREAT|os.O_TRUNC|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as out:json.dump({'code':value},out)
email_delivery.configuration=lambda:{'test_transport':True}
email_delivery.send_code=code;sms.send_otp=code;sms._config=lambda:{'test_transport':True}
email_delivery.send_notice=lambda *a,**k:None;sms.send_notice=lambda *a,**k:None
frappe.app._site=SITE;frappe.app._sites_path=str(BENCH/'sites')
application=SharedDataMiddleware(frappe.app.application,{'/assets/tele_tena':str(ROOT/'tele_tena/public')})
