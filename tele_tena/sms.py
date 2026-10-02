"""Backend-only SMS Ethiopia adapter. Never log provider request/response data."""
import json
import re
import stat
from pathlib import Path

import frappe
import requests

SEND_URL = 'https://smsethiopia.com/api/sms/send'


class SMSRejected(Exception):
    """Provider returned an explicit client-side rejection."""


class SMSUncertain(Exception):
    """The request may have been accepted; it must not be retried automatically."""


def _config():
    path = Path(frappe.get_site_path('private', 'tele_tena_sms.json'))
    if path.is_symlink() or not path.is_file() or stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise SMSRejected('not_configured')
    try:
        config = json.loads(path.read_text())
        api_key = config['api_key']
    except (OSError, ValueError, KeyError, TypeError):
        raise SMSRejected('not_configured') from None
    if not isinstance(api_key, str) or not api_key.strip():
        raise SMSRejected('not_configured')
    header = config.get('auth_header', 'KEY')  # Existing private files used KEY.
    scheme = config.get('auth_scheme', 'raw')
    if header not in ('KEY', 'Authorization') or scheme not in ('raw', 'bearer'):
        raise SMSRejected('not_configured')
    if header == 'KEY' and scheme != 'raw':
        raise SMSRejected('not_configured')
    return {'api_key': api_key, 'auth_header': header, 'auth_scheme': scheme}


def otp_hmac_key():
    path = Path(frappe.get_site_path('private', 'tele_tena_otp.key'))
    if path.is_symlink() or not path.is_file() or stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise SMSRejected('otp_key_unavailable')
    try:
        key = path.read_text().strip()
    except OSError:
        raise SMSRejected('otp_key_unavailable') from None
    if len(key) < 64:
        raise SMSRejected('otp_key_unavailable')
    return key


def send_otp(phone, code):
    """Send once; 2xx acceptance is not delivery and unknown outcomes are terminal."""
    config = _config()
    # Retain the original mock contract for pre-existing development regressions.
    if isinstance(config, str):
        config = {'api_key': config, 'auth_header': 'KEY', 'auth_scheme': 'raw'}
    credential = ('Bearer ' if config['auth_scheme'] == 'bearer' else '') + config['api_key']
    if not re.fullmatch(r'\+251[79][0-9]{8}', phone) or not re.fullmatch(r'[0-9]{6}', code):
        raise SMSRejected('invalid_request')
    try:
        response = requests.post(
            SEND_URL,
            headers={config['auth_header']: credential, 'Content-Type': 'application/json', 'Accept': 'application/json'},
            json={'msisdn': phone[1:],
                  'text': f'Tele-tena verification code: {code}. Expires in 5 minutes. Do not share this code.'},
            timeout=(3, 8),
        )
    except requests.RequestException:
        # A timeout/connection break may happen after the provider enqueued SMS.
        raise SMSUncertain('provider_outcome_unknown') from None
    if response.status_code >= 500:
        raise SMSUncertain('provider_outcome_unknown')
    if not 200 <= response.status_code < 300:
        raise SMSRejected('provider_rejected')
    try:
        result = response.json()
    except ValueError:
        raise SMSUncertain('provider_response_unknown') from None
    accepted = result.get('status') == 'success' or (
        result.get('sent') is True and result.get('description') == 'Accepted for delivery'
    ) if isinstance(result, dict) else False
    if not accepted:
        # A success-looking but undocumented body is not enough to claim acceptance.
        raise SMSUncertain('provider_response_unknown')
    return 'accepted'
