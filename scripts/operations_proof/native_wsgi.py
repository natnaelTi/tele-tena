"""Loopback-only disposable-clone V2 capture, no external transport in web process."""
import os,json
from pathlib import Path
assert os.environ.get('TELE_TENA_NATIVE_V2')=='1'
from scripts.operations_capture_test_wsgi import application,capture
file=Path(os.environ['TELE_TENA_NATIVE_PROOF_ROOT'])/'native-v2-account.json'
account=json.loads(file.read_text());original=capture.eligible
import frappe
capture.eligible=lambda:frappe.session.user==account['user'] and original()
from scripts.operations_proof.native_v2 import NativeRun
from tele_tena.operations import runtime as rt
from datetime import datetime,timezone
_original_admit=capture.admit

def admitted(provider_id,window_id):
 run=NativeRun(os.environ['TELE_TENA_NATIVE_PROOF_ROOT']);m,c=run.checked()
 if frappe.session.user!=account['user']:return {'state':'Disabled'}
 identifier=rt.pseudonym('replay:'+provider_id)
 if not m['recordings']:run.reserve('native-recording-'+identifier,{'replays':1})
 elif m['recordings'][0].get('native_id')!=identifier:raise frappe.PermissionError('Synthetic recording budget exhausted')
 result=_original_admit(provider_id,window_id)
 if result.get('state')=='Active' and not m['recordings']:
  row=frappe.db.sql('SELECT * FROM tt_ops_capture WHERE id=%s',(identifier,),as_dict=True)[0]
  with run.locked():
   m,c=run.checked();m['recordings'].append({'id':row.provider_id,'native_id':identifier,'registered_at':datetime.now(timezone.utc).isoformat(),'state':'Capturing','source':'new synthetic native application gateway','wire_accepted':0});run._write(run.manifest,m)
 return result
capture.admit=admitted
