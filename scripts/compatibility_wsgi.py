"""Loopback compatibility-test entrypoint; never a production server configuration."""
import os
from pathlib import Path
import frappe.app
from werkzeug.middleware.shared_data import SharedDataMiddleware

BENCH = Path(__file__).resolve().parents[3]
assert BENCH.parent.name == 'teletena-compat', 'Separate compatibility bench required'
site = os.environ.get('TELE_TENA_TEST_SITE')
assert site and site.startswith(('tele-tena-', 'teletena-')) and site.endswith('.localhost')
frappe.app._site = site
frappe.app._sites_path = str(BENCH / 'sites')
application = SharedDataMiddleware(frappe.app.application, {'/assets': str(BENCH / 'sites/assets')})
