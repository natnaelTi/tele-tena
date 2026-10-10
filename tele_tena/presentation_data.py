"""Explicit local presentation accounts, separate from automated review fixtures.

No installation hook, HTTP endpoint, credential verification or clinical approval.
Only the named disposable presentation site may run this command.
"""
import base64
import fcntl
import json
import os
import secrets
from pathlib import Path

import frappe

from tele_tena.review import cli, write_private

SITE = 'teletena-mvp-presentation.localhost'
VERSION = 'presentation-v1'
# Illustrative demonstration values; not Ethiopian market-rate claims.
PRICES = {'individual-counseling': 30000, 'stress-support': 40000, 'couples-counseling': 120000}


def setup():
    cli()
    if frappe.local.site != SITE:
        raise ValueError('Presentation setup is restricted to its dedicated local site')
    private = Path(frappe.get_site_path('private'))
    fd = os.open(private / '.tele_tena_presentation.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return _setup(private)


def _setup(private):
    from frappe.utils.password import update_password
    from tele_tena.api import journey, presentation

    marker = private / 'tele_tena_presentation_seed.json'
    credentials = private / 'tele_tena_presentation_accounts.json'
    if marker.exists():
        state = json.loads(marker.read_text())
        if not credentials.is_file() or not all(frappe.db.exists('User', u) for u in state['users'].values()):
            raise ValueError('Incomplete presentation setup; inspect records without resetting them')
        return {'already_present': True, 'credentials_file': str(credentials)}
    if credentials.exists():
        raise ValueError('Unfinished setup; private credentials retained for diagnosis')
    users = {key: f'{key}.presentation@example.invalid' for key in ('patient', 'clinician', 'second_clinician', 'reviewer')}
    if any(frappe.db.exists('User', u) for u in users.values()):
        raise ValueError('Presentation account conflict; existing accounts will not be changed')
    names = {'patient': 'Selam Bekele', 'clinician': 'Hana Tesfaye', 'second_clinician': 'Dawit Alemu', 'reviewer': 'Mekdes Abebe'}
    passwords = {u: secrets.token_urlsafe(24) for u in users.values()}
    write_private(credentials, passwords)
    for key, user in users.items():
        doc = frappe.get_doc({'doctype': 'User', 'email': user, 'first_name': names[key],
                             'send_welcome_email': 0, 'user_type': 'Website User'})
        doc.insert()
        doc.add_roles('Tele Tena ' + ('Approver' if key == 'reviewer' else 'Patient' if key == 'patient' else 'Clinician'))
        update_password(user, passwords[user])
    frappe.set_user(users['reviewer'])
    for code, label in [('individual-counseling', 'Individual counseling'), ('stress-support', 'Stress and anxiety support')]:
        journey.save_service('presentation-' + code, label)
    for key in ('patient', 'clinician', 'second_clinician'):
        frappe.set_user(users[key])
        journey.save_profile('patient' if key == 'patient' else 'clinician', names[key], True,
                             languages=None if key == 'patient' else ['en', 'am'])
        if key != 'patient':
            presentation.upload_resume('professional-profile.pdf', base64.b64encode(
                b'%PDF-1.4\nFictional presentation applicant. No real qualifications or license verified.\n%%EOF').decode())
            journey.apply('Fictional presentation application. Evidence and service eligibility require a human review; no actual professional credentials are claimed.',
                          ['presentation-individual-counseling', 'presentation-stress-support'])
            # Profile creation uses the legacy owner command; the completed seed
            # leaves applicants unprivileged until the human review transition.
            frappe.set_user('Administrator')
            doc = frappe.get_doc('User', users[key])
            doc.remove_roles('Tele Tena Clinician')
            doc.add_roles('Tele Tena Applicant')
    frappe.set_user(users['patient'])
    journey.simulated_deposit(100000, VERSION + ':opening-funds')
    frappe.db.commit()
    write_private(marker, {'version': VERSION, 'users': users, 'prices_minor': PRICES,
                           'approval': 'Pending human demonstration review', 'fictional': True})
    frappe.set_user('Administrator')
    return {'created': True, 'credentials_file': str(credentials), 'applications_pending': 2}
