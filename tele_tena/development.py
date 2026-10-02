"""CLI-only synthetic fixture setup, strictly isolated from production sites."""
import json
import getpass
import os
import secrets
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

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


def configure_livekit():
    """Interactive local-only secret setup; never echoes or returns secret values."""
    _configuration_site()
    if frappe.session.user != 'Administrator':
        frappe.throw('Administrator required', frappe.PermissionError)
    url = input('LiveKit public connection URL (wss://; ws://localhost for local development): ').strip()
    key = getpass.getpass('LiveKit API key: ').strip()
    secret = getpass.getpass('LiveKit API secret: ')
    confirm = getpass.getpass('Repeat LiveKit API secret: ')
    parsed = urlsplit(url)
    local = parsed.hostname in ('localhost', '127.0.0.1', '::1')
    if parsed.scheme != 'wss' and not (local and parsed.scheme == 'ws'):
        frappe.throw('Use wss, except ws is allowed for a loopback development server')
    if not parsed.netloc or parsed.username or parsed.password or not key or len(secret) < 16 or secret != confirm:
        frappe.throw('Invalid URL/key/secret or secret confirmation')
    target = Path(frappe.get_site_path('private', 'tele_tena_livekit.json'))
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(target.parent, 0o700)
    if target.is_symlink():
        frappe.throw('Refusing a symlinked LiveKit secret path')
    fd, temporary = tempfile.mkstemp(prefix='.tele-tena-livekit-', dir=target.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump({'url': url, 'api_key': key, 'api_secret': secret}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        os.chmod(target, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {'configured': True, 'path': str(target), 'mode': '0600'}

def configure_sms():
    """Prompt locally for provider credentials and account-confirmed header."""
    _configuration_site()
    if frappe.session.user != 'Administrator':
        frappe.throw('Administrator required', frappe.PermissionError)
    path = Path(frappe.get_site_path('private', 'tele_tena_sms.json'))
    if path.is_symlink():
        frappe.throw('SMS credential path may not be a symbolic link')
    key = getpass.getpass('SMS Ethiopia API key (input hidden): ').strip()
    if not key or '\n' in key or len(key) > 512:
        frappe.throw('A valid SMS API key is required')
    header = input('Account-confirmed API key header (KEY or Authorization): ').strip()
    if header not in ('KEY', 'Authorization'):
        frappe.throw('Choose the header specified by your provider account')
    scheme = 'raw'
    if header == 'Authorization':
        scheme = input('Authorization value format (raw or bearer): ').strip().lower()
        if scheme not in ('raw', 'bearer'):
            frappe.throw('Choose raw or bearer from your provider account documentation')
    config = {'api_key': key, 'auth_header': header, 'auth_scheme': scheme}
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    fd, temporary = tempfile.mkstemp(prefix='.tele-tena-sms-', dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(config, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {'configured': True, 'credentials_file': 'private/tele_tena_sms.json',
            'provider': 'SMSEthiopia', 'auth_header': header, 'live_send_performed': False}


def configure_email():
    """Local SMTP secret setup; direct TLS-only delivery, no queued plaintext codes."""
    _configuration_site()
    host = input('SMTP hostname: ').strip()
    port = input('SMTP TLS port (465 or 587): ').strip()
    sender = input('Verified sender email address: ').strip()
    username = getpass.getpass('SMTP username (hidden): ').strip()
    password = getpass.getpass('SMTP password/app password (hidden): ')
    if port not in ('465', '587') or not host or '@' not in sender or not username or not password:
        frappe.throw('Incomplete SMTP configuration')
    if any('\n' in value or '\r' in value for value in (host, sender, username)):
        frappe.throw('Invalid SMTP configuration')
    target = Path(frappe.get_site_path('private', 'tele_tena_email.json'))
    if target.is_symlink():
        frappe.throw('Refusing symlinked secret path')
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.tele-tena-email-', dir=target.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w') as output:
            json.dump(dict(host=host, port=int(port), sender=sender, username=username, password=password), output)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {'configured': True}


def _configuration_site():
    from tele_tena.review import cli
    cli(require_enabled=frappe.local.site != 'erp.localhost')
