"""CLI-only synthetic fixture setup, strictly isolated from production sites."""
import json
import os
import secrets
from pathlib import Path

import frappe
from frappe.utils.password import update_password


def setup():
    if frappe.local.site != 'erp.localhost':
        frappe.throw('Synthetic setup is restricted to erp.localhost')
    if frappe.session.user != 'Administrator':
        frappe.throw('Administrator required', frappe.PermissionError)
    from tele_tena.schema import install
    install()
    credentials = {}
    for email, name, role in (
        ('patient-demo@example.invalid', 'Synthetic Patient', 'Tele Tena Patient'),
        ('clinician-demo@example.invalid', 'Synthetic Clinician', 'Tele Tena Clinician'),
        ('approver-demo@example.invalid', 'Synthetic Approver', 'Tele Tena Approver'),
    ):
        if not frappe.db.exists('User', email):
            frappe.get_doc(dict(doctype='User', email=email, first_name=name,
                                user_type='Website User', send_welcome_email=0)).insert()
        user = frappe.get_doc('User', email)
        user.add_roles(role)
        password = secrets.token_urlsafe(24)
        update_password(email, password)
        credentials[email] = password
    path = Path('/tmp/tele-tena-demo-credentials.json')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(credentials, stream)
    # Local flag only. No credential or config is committed.
    from frappe.installer import update_site_config
    update_site_config('tele_tena_simulation_enabled', True)
    frappe.db.commit()
    return {'credentials_file': str(path), 'synthetic': True}
