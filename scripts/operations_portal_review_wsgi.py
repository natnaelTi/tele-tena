"""Fixed loopback review only; synthetic site, outbound transports disabled."""
import os
from pathlib import Path
assert os.environ.get('TELE_TENA_LOCAL_OPERATIONS_SCENARIO')=='1'
import frappe.app
from werkzeug.middleware.shared_data import SharedDataMiddleware
from tele_tena.operations import providers,capture,archive
from tele_tena import email_delivery,sms
SITE='teletena-ops-v154-release.localhost';SITES=Path('/home/frappe/teletena-compat/bench/sites');ROOT=Path(__file__).resolve().parents[1]
assert (SITES/SITE/'private/operations-portal-review.json').is_file()
frappe.app._site=SITE;frappe.app._sites_path=str(SITES)
def disabled(*a,**k):raise providers.Unconfigured('isolated_review_no_provider_transport')
for name in ('posthog_event','bugsink_error','telegram','replay_snapshot','archive_export','archive_delete_provider','archive_provider_absent'):setattr(providers,name,disabled)
email_delivery.send_notice=disabled;email_delivery.send_code=disabled;sms.send_notice=disabled;sms.send_otp=disabled
# Local generated fixture playback only. This is NOT a selected-provider proof.
providers.archive_capability=lambda:True
capture.capability=lambda:False
providers.settings=lambda:{}
base_status=archive.status
def local_status():
 value=base_status();value.update(project_proof_verified=False,available=False,playback_available=True,reason='Local generated playback fixture only; this does not establish selected-provider settled export or production retention.')
 return value
archive.status=local_status
application=SharedDataMiddleware(frappe.app.application,{'/assets/tele_tena':str(ROOT/'tele_tena/public')})
