"""Local disposable-site verification only. Not a remote server entrypoint."""
import os
from pathlib import Path
import frappe.app
from werkzeug.middleware.shared_data import SharedDataMiddleware

BENCH = Path(__file__).resolve().parents[3]
frappe.app._site = os.environ.get('TELE_TENA_TEST_SITE')
assert frappe.app._site and frappe.app._site.startswith(('tele-tena-', 'teletena-')) and frappe.app._site.endswith('.localhost')
frappe.app._sites_path = str(BENCH / 'sites')
application = SharedDataMiddleware(frappe.app.application, {
    '/assets/tele_tena': str(BENCH / 'apps/tele_tena/tele_tena/public'),
})
