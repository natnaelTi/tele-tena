"""Disposable local Frappe16 browser harness. Never a production entrypoint."""
import json,os
from pathlib import Path
from werkzeug.middleware.shared_data import SharedDataMiddleware
import frappe.app
from tele_tena import email_delivery,sms
assert os.environ.get('TELE_TENA_TEST_SITE')=='teletena-guest-first-test.localhost'
BENCH=Path('/home/frappe/teletena-compat/bench');ROOT=Path(__file__).resolve().parents[1]
CAPTURE=Path('/home/frappe/teletena-onboarding-sprint/codes');CAPTURE.mkdir(mode=0o700,exist_ok=True)

def capture(contact,code):
    assert contact.endswith('@onboarding.invalid') or contact.startswith('+251900010')
    import hashlib
    p=CAPTURE/hashlib.sha256(contact.encode()).hexdigest()
    fd=os.open(p,os.O_CREAT|os.O_TRUNC|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as f:json.dump({'code':code},f)
email_delivery.configuration=lambda:{'test_transport':True}
email_delivery.send_code=capture
sms.send_otp=capture
sms._config=lambda:{'test_transport':True}
# No outbound provider route exists in this disposable process.
email_delivery.send_notice=lambda *a,**k:(_ for _ in ()).throw(email_delivery.DeliveryUnavailable())
sms.send_notice=lambda *a,**k:(_ for _ in ()).throw(sms.SMSRejected())
frappe.app._site=os.environ['TELE_TENA_TEST_SITE'];frappe.app._sites_path=str(BENCH/'sites')
application=SharedDataMiddleware(frappe.app.application,{'/assets/tele_tena':str(ROOT/'tele_tena/public')})
