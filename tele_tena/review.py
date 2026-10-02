"""Explicit, site-bound review setup. Never called by installation or HTTP."""
import json
import fcntl
import os
import secrets
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

import frappe


def enabled():
    return (frappe.conf.get('tele_tena_review_site') == frappe.local.site
            and frappe.conf.get('tele_tena_review_enabled') is True)


def cli(require_enabled=True):
    if getattr(frappe.local, 'request', None) or frappe.session.user != 'Administrator':
        frappe.throw('Local administrator command required', frappe.PermissionError)
    if require_enabled and not enabled():
        frappe.throw('This site is not explicitly configured for review', frappe.PermissionError)


def phone_enabled():
    if frappe.local.site == 'erp.localhost':
        return True
    return enabled() and frappe.conf.get('tele_tena_phone_otp_enabled') is True


def registration_enabled(kind):
    if kind not in ('patient', 'clinician'):
        return False
    if frappe.local.site == 'erp.localhost':
        return True
    return enabled() and frappe.conf.get('tele_tena_' + kind + '_registration_enabled') is True


def sms_cap():
    """A review-site cap; malformed/missing config fails closed."""
    if not enabled():
        return 100
    value = frappe.conf.get('tele_tena_sms_24h_cap', 20)
    return value if type(value) is int and 1 <= value <= 100 else 0


def guard_contact_access(channel='phone', legacy=False):
    if frappe.local.site == 'erp.localhost':
        return
    if not enabled() or legacy or (channel == 'phone' and not phone_enabled()):
        frappe.local.response['tele_tena_error'] = 'review_password_required'
        frappe.throw('Phone verification is unavailable on this site.', frappe.PermissionError)
    if channel == 'email':
        from tele_tena import email_delivery
        try:
            email_delivery.configuration()
        except email_delivery.DeliveryUnavailable:
            frappe.local.response['tele_tena_error'] = 'email_otp_unavailable'
            frappe.throw('Email code delivery is not configured; use your password.', frappe.PermissionError)


def configure_contact_access():
    """Local Administrator-only site flags; independent of review funding."""
    cli()
    if frappe.conf.get('developer_mode') or frappe.conf.get('ignore_csrf'):
        raise ValueError('Developer mode and CSRF bypass must remain disabled')
    site = frappe.local.site
    if input('Type the exact review site name to update contact access: ').strip() != site:
        raise ValueError('Site confirmation mismatch')

    def choice(label):
        answer = input(label + ' (yes/no): ').strip().lower()
        if answer not in ('yes', 'no'):
            raise ValueError('Answer yes or no')
        return answer == 'yes'

    phone = choice('Enable phone OTP sign-in')
    patient = choice('Allow new adult patient registration')
    clinician = choice('Allow new clinician applications')
    cap_text = input('Maximum site-wide SMS send attempts per rolling 24 hours (1-100): ').strip()
    if not cap_text.isascii() or not cap_text.isdecimal() or not 1 <= int(cap_text) <= 100:
        raise ValueError('SMS cap must be a whole number from 1 to 100')
    if phone:
        from tele_tena import sms
        sms._config()  # Fail before changing settings if the private key is absent.
    from frappe.installer import update_site_config
    for key, value in (
        ('tele_tena_phone_otp_enabled', phone),
        ('tele_tena_patient_registration_enabled', patient),
        ('tele_tena_clinician_registration_enabled', clinician),
        ('tele_tena_sms_24h_cap', int(cap_text)),
    ):
        update_site_config(key, value)
    frappe.clear_cache()
    return {'site': site, 'phone_otp': phone, 'patient_registration': patient,
            'clinician_registration': clinician, 'sms_24h_cap': int(cap_text)}


def write_private(path, value):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Refusing symbolic link')
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.tele-tena-', dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w') as output:
            json.dump(value, output, indent=2)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def configure():
    cli(False)
    if frappe.conf.get('developer_mode') or frappe.conf.get('ignore_csrf'):
        raise ValueError('Review requires developer mode and CSRF bypass to be disabled')
    site = frappe.local.site
    confirmation = input('Dedicated synthetic review site: type its exact site name: ').strip()
    if confirmation != site or site == 'erp.localhost':
        raise ValueError('Site confirmation mismatch or retained development site')
    origin = input('Public HTTPS origin (for example https://review.example.com): ').strip().rstrip('/')
    url = urlsplit(origin)
    if url.scheme != 'https' or not url.hostname or url.username or url.password or url.path or url.query or url.fragment:
        raise ValueError('An HTTPS origin without path or credentials is required')
    from frappe.installer import update_site_config
    update_site_config('tele_tena_review_site', site)
    update_site_config('tele_tena_review_enabled', True)
    update_site_config('host_name', origin)
    # Generic Frappe signup is separate from TeleTena contact verification.
    frappe.db.set_single_value('Website Settings', 'disable_signup', 1)
    frappe.db.commit()
    frappe.clear_cache()
    return {'review_site': site, 'application_path': '/teletena/', 'public_enrollment': False}


def seed():
    cli()
    # Serialize local invocations even across API helpers that commit internally.
    lock = Path(frappe.get_site_path('private', '.tele_tena_review_seed.lock'))
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return _seed()


def _seed():
    """Idempotent synthetic release fixtures; passwords saved only in private storage."""
    cli()
    from frappe.utils.password import update_password
    from tele_tena.api import journey as api
    from tele_tena.api import scheduling
    from datetime import datetime, timedelta, timezone
    credentials_path = Path(frappe.get_site_path('private', 'tele_tena_review_accounts.json'))
    marker = Path(frappe.get_site_path('private', 'tele_tena_review_seed.json'))
    frappe.db.sql('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    if marker.exists():
        existing = json.loads(marker.read_text())
        if all(frappe.db.exists('User', user) for user in existing['users'].values()):
            return {'seeded': False, 'already_present': True, 'credentials_file': str(credentials_path)}
        raise ValueError('Incomplete seed; restore the site and private files together')
    if credentials_path.exists():
        raise ValueError('Unfinished seed; inspect locally before retrying, credentials retained')
    tag = secrets.token_hex(6)
    users = {role: f'review-{tag}-{role}@example.invalid' for role in ('patient', 'clinician', 'reviewer')}
    passwords = {user: secrets.token_urlsafe(24) for user in users.values()}
    write_private(credentials_path, passwords)
    for role, user in users.items():
        doc = frappe.get_doc(dict(doctype='User', email=user, first_name='Review ' + role.title(),
                            send_welcome_email=0, user_type='Website User'))
        doc.insert()
        doc.add_roles('Tele Tena ' + {'patient': 'Patient', 'clinician': 'Clinician', 'reviewer': 'Approver'}[role])
        update_password(user, passwords[user])
    for kind in ('patient', 'clinician'):
        frappe.set_user(users[kind])
        api.save_profile(kind, 'Review ' + kind.title(), True, history='Synthetic review history')
    import base64
    from tele_tena.api import presentation
    presentation.upload_resume('review-resume.pdf', base64.b64encode(b'%PDF-1.4\nSynthetic review evidence only\n%%EOF').decode())
    api.apply('Synthetic demonstration credentials. Not professional verification.')
    frappe.set_user(users['reviewer'])
    service = 'review-' + tag
    api.save_service(service, 'Review conversation')
    api.review(users['clinician'], 'Approved')
    api.review_service_scope(users['clinician'], service, 'Approved')
    frappe.set_user(users['clinician'])
    api.publish(service, 60000, 30)
    offering = api.one('SELECT id FROM tt_offering WHERE clinician=%s AND service=%s', (users['clinician'], service)).id
    # Daily daytime schedule in Addis Ababa. All slots still pass normal API validation.
    schedule = dict(offering=offering, schedule_name='Review availability', timezone_name='Africa/Addis_Ababa',
        intervals=[{'weekday': day, 'start': '08:00', 'end': '20:00'} for day in range(7)],
        exceptions=[], minimum_notice_minutes=0, horizon_days=60, buffer_before=0, buffer_after=0,
        confirmation_mode='automatic', status='Published', consultation_format='video')
    scheduling.save_schedule(**schedule)
    frappe.set_user(users['patient'])
    api.simulated_deposit(500000, 'review-seed-' + tag)
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0).isoformat()
    payload = dict(offering=offering, start=start, retry_key='review-book-' + tag,
        request_text='Synthetic review consultation', sharing={'name': False, 'history': False},
        expected_price=60000, expected_minutes=30, expected_disclosure={'request': 'Synthetic review consultation'})
    appointment = api.book(**payload)
    cancelled = api.book(**{**payload, 'start': (datetime.fromisoformat(start) + timedelta(hours=1)).isoformat(), 'retry_key':'review-cancel-' + tag})
    presentation.cancel_appointment(cancelled['id'], 'Synthetic cancellation example')
    frappe.set_user(users['clinician'])
    scheduling.save_schedule(**{**schedule, 'confirmation_mode':'manual'})
    frappe.set_user(users['patient'])
    pending = api.book(**{**payload, 'start': (datetime.fromisoformat(start) + timedelta(hours=2)).isoformat(), 'retry_key':'review-pending-' + tag})
    frappe.db.commit()
    write_private(marker, {'users': users, 'offering': offering, 'appointment': appointment['id'], 'cancelled': cancelled['id'], 'pending': pending['id']})
    frappe.set_user('Administrator')
    return {'seeded': True, 'credentials_file': str(credentials_path), 'synthetic': True}
