"""Explicit loopback-only OTP transport for browser acceptance, never production.

Real OTP generation, HMAC storage, expiry, throttles, verification and onboarding
remain untouched. The consenting test runner consumes a mode-600 capture and
removes it; no SMS/email is sent. Do not use this entrypoint for the review server.
"""
import ipaddress
import os
from pathlib import Path

assert os.environ.get('TELE_TENA_LOCAL_OTP_TEST') == '1'
SITE=os.environ.get('TELE_TENA_TEST_SITE')
assert SITE in ('teletena-mvp-presentation.localhost','tele-tena-pr12-fresh.localhost')
from scripts.review_test_wsgi import application as frappe_application
from tele_tena import sms
from tele_tena.review import write_private
import frappe


def capture(phone, code):
    assert frappe.local.site == SITE
    write_private(Path(frappe.get_site_path('private', 'tele_tena_test_delivery.json')),
                  {'contact': phone, 'code': code})
    return 'accepted'


sms._config = lambda: {'api_key': 'local-test-no-provider', 'auth_header': 'KEY', 'auth_scheme': 'raw'}
sms.send_otp = capture


def application(environ, start_response):
    if not ipaddress.ip_address(environ.get('REMOTE_ADDR', '0.0.0.0')).is_loopback:
        start_response('403 Forbidden', [('Content-Type', 'text/plain')])
        return [b'Local test only']
    return frappe_application(environ, start_response)
