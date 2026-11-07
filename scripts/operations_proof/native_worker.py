"""Burst worker only for the fixed disposable clone and explicitly authorized V2."""
import os,sys,runpy,importlib
assert os.environ.get('TELE_TENA_NATIVE_V2')=='1'
import scripts.operations_proof.native_wsgi
from tele_tena.operations import providers
module=importlib.reload(providers);snapshot=module.replay_snapshot;export=module.archive_export
from scripts.operations_proof.native_v2 import send_native,export_native
providers.replay_snapshot=lambda session,chunk,events:send_native(session,chunk,events,snapshot)
providers.archive_export=lambda recording:export_native(recording,export)
providers.archive_capability=lambda:True # isolated selected-project proof gate only

def disabled(*a,**kw):raise providers.Unconfigured('native_v2_other_transport_disabled')
for name in ('archive_delete_provider','archive_provider_absent','posthog_event','bugsink_error','telegram'):setattr(providers,name,disabled)
sys.argv=['bench','frappe','worker','--queue','teletena_ops','--burst']
runpy.run_module('frappe.utils.bench_helper',run_name='__main__')
