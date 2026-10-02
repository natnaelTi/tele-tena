"""Local disposable-site verification only. Not a remote server entrypoint."""
from pathlib import Path
import frappe.app
from werkzeug.middleware.shared_data import SharedDataMiddleware

BENCH = Path(__file__).resolve().parents[3]
frappe.app._site = 'tele-tena-pr2-test.localhost'
frappe.app._sites_path = str(BENCH / 'sites')
application = SharedDataMiddleware(frappe.app.application, {
    '/assets/tele_tena': str(BENCH / 'apps/tele_tena/tele_tena/public'),
})
