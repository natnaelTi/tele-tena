"""Explicit local presentation-only fictional portraits; never runs in migration."""
import base64
import json
from pathlib import Path
import frappe
from tele_tena.api import profile_photos


def install():
    if frappe.local.site != 'teletena-mvp-presentation.localhost':
        raise RuntimeError('This command is only for the designated local presentation site')
    metadata = Path(frappe.get_site_path('private', 'tele_tena_presentation_seed.json'))
    seed = json.loads(metadata.read_text())
    if seed.get('fictional') is not True:
        raise RuntimeError('Fictional presentation metadata required')
    assets = Path(__file__).resolve().parents[1] / 'assets/demo-portraits'
    previous_user = frappe.session.user
    result = {'added': 0, 'preserved': 0}
    try:
        for role in ('patient', 'clinician', 'second_clinician', 'reviewer'):
            user = seed['users'][role]
            if not frappe.db.exists('User', user):
                raise RuntimeError('Presentation account missing')
            frappe.set_user(user)
            if profile_photos.owner_photo(user)['url']:
                result['preserved'] += 1
                continue
            image = (assets / (role + '.png')).read_bytes()
            profile_photos.upload(role + '.png', base64.b64encode(image).decode(),
                                  published=int(role in ('clinician', 'second_clinician')))
            result['added'] += 1
        frappe.db.commit()
        return result
    except Exception:
        frappe.db.rollback()
        raise
    finally:
        frappe.set_user(previous_user)
