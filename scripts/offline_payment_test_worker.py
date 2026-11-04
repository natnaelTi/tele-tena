"""Owned one-site RQ test transport, never a hosted worker entrypoint."""
assert __name__=='__main__', 'This fixture may run only as an explicit local CLI, never by import'

import json,os,runpy,sys
from pathlib import Path
ROOT=Path('/home/frappe/teletena-offline-sprint');SITE='teletena-payments-v147-fresh.localhost'
assert os.environ.get('TELE_TENA_LOCAL_JOB_TEST')=='1' and Path.cwd()==ROOT/'jobs/sites'
assert [p.name for p in Path.cwd().iterdir() if p.is_dir() and p.name.endswith('.localhost')]==[SITE]
from tele_tena import email_delivery,sms
import frappe

def capture(destination,message):
    assert frappe.local.site==SITE and destination.endswith('@offline-test.invalid')
    assert '/teletena/' in message
    fd=os.open(ROOT/'worker-transport.jsonl',os.O_APPEND|os.O_CREAT|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as out:out.write(json.dumps({'site':SITE,'transport':'private-test','provider_accepted':True,'delivered':False})+'\n')
email_delivery.send_notice=capture;sms.send_notice=capture
sys.argv=['bench','frappe','worker','--queue','default,short,long']
runpy.run_module('frappe.utils.bench_helper',run_name='__main__')
