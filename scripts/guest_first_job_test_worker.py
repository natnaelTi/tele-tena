"""Loopback disposable-site notice transport for a real isolated RQ worker.
Never import this as an HTTP/production entrypoint. No actual delivery occurs.
"""
import os,runpy,sys
from pathlib import Path
assert os.environ.get('TELE_TENA_LOCAL_JOB_TEST')=='1'
assert Path.cwd()==Path('/home/frappe/teletena-guest-first/jobs/sites')
assert (Path.cwd()/'teletena-guest-first-test.localhost').is_dir()
assert len([p for p in Path.cwd().iterdir() if p.is_dir() and p.name.endswith('.localhost')])==1
from tele_tena import email_delivery,sms
from tele_tena.review import write_private
import frappe

def capture(destination,message):
    assert frappe.local.site=='teletena-guest-first-test.localhost'
    assert 'appointment' in message and '/teletena/' in message
    write_private(Path(frappe.get_site_path('private','tele_tena_test_booking_delivery.json')),
                  {'transport':'local-test','provider_accepted':True,'delivered':False})
email_delivery.send_notice=capture
sms.send_notice=capture
sys.argv=['bench','frappe','worker','--queue','default,short,long']
runpy.run_module('frappe.utils.bench_helper',run_name='__main__')
