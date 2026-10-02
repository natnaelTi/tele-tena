"""Frappe production SPA renderer. Own only the explicitly enabled namespace."""
from pathlib import Path
import frappe
from werkzeug.wrappers import Response
from frappe.website.page_renderers.base_renderer import BaseRenderer
from tele_tena.review import enabled


class ReviewPage(BaseRenderer):
    def can_render(self):
        return enabled() and (self.path == 'teletena' or self.path.startswith('teletena/'))

    def render(self):
        root = Path(frappe.get_app_path('tele_tena', 'public', 'review'))
        worker = self.path == 'teletena/sw.js'
        path = root / ('sw.js' if worker else 'index.html')
        if not path.is_file():
            return Response('TeleTena assets are not installed. Contact the review administrator.', status=503,
                            headers={'Cache-Control': 'no-store'})
        return Response(path.read_text(), mimetype='application/javascript' if worker else 'text/html',
                        headers={'Cache-Control': 'no-store, private', 'X-Content-Type-Options': 'nosniff',
                                 **({'Service-Worker-Allowed': '/teletena/'} if worker else {})})
