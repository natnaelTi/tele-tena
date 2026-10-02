"""Phone OTP request, verification and narrowly scoped signup endpoints."""
import hashlib
import hmac
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import frappe
from frappe.sessions import get_csrf_token

from tele_tena import sms
from tele_tena.api.journey import fail, text, boolean


OTP_TTL_SECONDS = 300
MAX_ATTEMPTS = 5
RESEND_COOLDOWN_SECONDS = 60
PHONE_WINDOW_LIMIT = 3
IP_WINDOW_LIMIT = 10
PHONE_DAILY_LIMIT = 5
VERIFY_PHONE_WINDOW_LIMIT = 10
VERIFY_IP_WINDOW_LIMIT = 20


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_phone(value):
    """Normalize supported Ethiopian mobile input to canonical +251 E.164."""
    if not isinstance(value, str) or len(value) > 40:
        fail('Invalid mobile number', 'invalid_phone')
    compact = re.sub(r'[\s().-]', '', value)
    if compact.startswith('00'):
        compact = '+' + compact[2:]
    if compact.startswith('0'):
        compact = '+251' + compact[1:]
    elif compact.startswith('251'):
        compact = '+' + compact
    if not re.fullmatch(r'\+251[79][0-9]{8}', compact):
        fail('Enter a supported Ethiopian mobile number', 'invalid_phone')
    return compact


def _keyed(label, value):
    key = sms.otp_hmac_key().encode()
    return hmac.new(key, (label + '\0' + value).encode(), hashlib.sha256).hexdigest()


def _otp_digest(challenge, phone_digest, purpose, code):
    key = sms.otp_hmac_key().encode()
    message = '\0'.join((challenge, phone_digest, purpose, code)).encode()
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def _json_error(message, code):
    frappe.local.response['tele_tena_error'] = code
    frappe.throw(message, frappe.ValidationError)


def _generic_result(challenge_id=''):
    return {'requested': True, 'challenge_id': challenge_id}


def _increment_limit(kind, subject, now, seconds, limit):
    bucket_key = _keyed('limit:' + kind, subject)
    frappe.db.sql('''INSERT IGNORE INTO tt_otp_rate_limit (bucket_key,window_start,attempts)
        VALUES (%s,%s,0)''', (bucket_key, now))
    row = frappe.db.sql('SELECT window_start,attempts FROM tt_otp_rate_limit WHERE bucket_key=%s FOR UPDATE',
                        (bucket_key,), as_dict=True)[0]
    if row.window_start <= now - timedelta(seconds=seconds):
        frappe.db.sql('UPDATE tt_otp_rate_limit SET window_start=%s,attempts=0 WHERE bucket_key=%s',
                      (now, bucket_key))
        count = 0
    else:
        count = row.attempts
    if count >= limit:
        return False
    frappe.db.sql('UPDATE tt_otp_rate_limit SET attempts=attempts+1 WHERE bucket_key=%s', (bucket_key,))
    return True


def _peer_ip():
    # WSGI peer only. Frappe request_ip can use an arbitrary X-Forwarded-For header.
    # If this is a proxy address, the limit is conservatively shared by its users.
    request = getattr(frappe.local, 'request', None)
    return getattr(request, 'remote_addr', None) or 'unknown-peer'


def _eligible(phone, purpose):
    existing = frappe.db.sql('SELECT user FROM tt_phone_identity WHERE phone=%s', (phone,))
    return bool(existing) if purpose == 'login' else not bool(existing)


def reserve_sms_budget(now):
    """Called under tt_otp_gate before a provider attempt, including uncertain sends."""
    from tele_tena.review import sms_cap
    cap = sms_cap()
    if cap <= 0:
        return False
    used = frappe.db.sql('''SELECT COUNT(*) FROM tt_otp_challenge
        WHERE purpose IN ('contact_phone','patient_signup','clinician_application','login')
        AND dispatch_state IN ('Sending','Accepted','Rejected','Uncertain')
        AND created>%s''', (now - timedelta(hours=24),))[0][0]
    # The caller inserts and commits Sending while still holding tt_otp_gate.
    return used < cap


@frappe.whitelist(allow_guest=True)
def csrf_token():
    """Issue the current session CSRF value needed by public POST commands."""
    return {'csrf_token': get_csrf_token()}


@frappe.whitelist(allow_guest=True, methods=['POST'])
def request_code(phone, purpose, request_id):
    from tele_tena.review import guard_contact_access
    guard_contact_access(legacy=True)
    """Create one challenge and make at most one bounded provider request."""
    if purpose not in ('patient_signup', 'clinician_application', 'login'):
        _json_error('Unsupported verification purpose', 'invalid_request')
    phone = normalize_phone(phone)
    if not isinstance(request_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{20,100}', request_id):
        _json_error('Invalid request identifier', 'invalid_request')
    phone_digest = _keyed('phone', phone)
    request_digest = hashlib.sha256(request_id.encode()).hexdigest()
    now = _now()
    # Serialize idempotency, cooldown and rate counter creation. SMS volume is low;
    # this narrow gate avoids duplicate first-insert races across worker processes.
    frappe.db.sql('SELECT id FROM tt_otp_gate WHERE id=1 FOR UPDATE')
    prior = frappe.db.sql('''SELECT id FROM tt_otp_challenge WHERE phone_digest=%s
        AND purpose=%s AND request_digest=%s''', (phone_digest, purpose, request_digest))
    if prior:
        frappe.db.commit()
        return _generic_result(prior[0][0])

    peer = _peer_ip()
    allowed = (_increment_limit('phone-window', phone_digest, now, 900, PHONE_WINDOW_LIMIT)
               and _increment_limit('phone-day', phone_digest, now, 86400, PHONE_DAILY_LIMIT)
               and _increment_limit('ip-window', peer, now, 900, IP_WINDOW_LIMIT))
    recent = frappe.db.sql('''SELECT id FROM tt_otp_challenge WHERE phone_digest=%s
        AND created>%s ORDER BY created DESC LIMIT 1''',
        (phone_digest, now - timedelta(seconds=RESEND_COOLDOWN_SECONDS),), as_dict=True)
    if not allowed or recent:
        frappe.db.commit()
        return _generic_result(recent[0].id if recent else '')

    challenge_id = str(uuid.uuid4())
    code = f'{secrets.randbelow(1_000_000):06d}'
    eligible = _eligible(phone, purpose)
    dispatch_state = 'Sending' if eligible and reserve_sms_budget(now) else 'Suppressed'
    frappe.db.sql('''INSERT INTO tt_otp_challenge
        (id,phone_digest,purpose,otp_digest,request_digest,created,expires,attempts,dispatch_state)
        VALUES (%s,%s,%s,%s,%s,%s,%s,0,%s)''',
        (challenge_id, phone_digest, purpose, _otp_digest(challenge_id, phone_digest, purpose, code),
         request_digest, now, now + timedelta(seconds=OTP_TTL_SECONDS), dispatch_state))
    # Commit a send-once state before the external call. A crash or timeout is
    # never recovered by another provider send for this idempotency key.
    frappe.db.commit()
    if dispatch_state == 'Sending':
        try:
            sms.send_otp(phone, code)
            state, reason = 'Accepted', None
        except sms.SMSRejected as error:
            state, reason = 'Rejected', str(error)[:40]
        except sms.SMSUncertain as error:
            state, reason = 'Uncertain', str(error)[:40]
        except Exception:
            # The provider may have received the request; do not retry.
            state, reason = 'Uncertain', 'provider_outcome_unknown'
        frappe.db.sql('UPDATE tt_otp_challenge SET dispatch_state=%s,dispatch_code=%s WHERE id=%s AND dispatch_state=%s',
                      (state, reason, challenge_id, 'Sending'))
        frappe.db.commit()
    return _generic_result(challenge_id)


def _establish_login(user):
    manager = getattr(frappe.local, 'login_manager', None)
    if manager is None:
        from frappe.auth import LoginManager
        manager = LoginManager()
    manager.login_as(user)


@frappe.whitelist(allow_guest=True, methods=['POST'])
def verify_code(phone, challenge_id, code, purpose, display_name='', adult=0, statement=''):
    from tele_tena.review import guard_contact_access
    guard_contact_access(legacy=True)
    """Verify a phone, then continue only into an owner-only onboarding draft."""
    if purpose not in ('patient_signup', 'clinician_application', 'login'):
        _json_error('Invalid verification', 'otp_invalid')
    phone = normalize_phone(phone)
    if not isinstance(challenge_id, str) or not re.fullmatch(r'[0-9a-f-]{36}', challenge_id):
        _json_error('Invalid verification', 'otp_invalid')
    if not isinstance(code, str) or not re.fullmatch(r'[0-9]{6}', code):
        code = ''
    phone_digest = _keyed('phone', phone)
    frappe.db.sql('SELECT id FROM tt_otp_gate WHERE id=1 FOR UPDATE')
    row = frappe.db.sql('SELECT * FROM tt_otp_challenge WHERE id=%s FOR UPDATE', (challenge_id,), as_dict=True)
    if not row:
        _json_error('Verification code is invalid or expired', 'otp_invalid')
    challenge = row[0]
    if (challenge.phone_digest != phone_digest or challenge.purpose != purpose
            or challenge.dispatch_state not in ('Accepted', 'Uncertain')
            or challenge.consumed or challenge.expires <= _now()
            or challenge.attempts >= MAX_ATTEMPTS):
        _json_error('Verification code is invalid or expired', 'otp_invalid')
    peer = _peer_ip()
    verify_allowed = (_increment_limit('verify-phone', phone_digest, _now(), 900, VERIFY_PHONE_WINDOW_LIMIT)
                      and _increment_limit('verify-ip', peer, _now(), 900, VERIFY_IP_WINDOW_LIMIT))
    expected = _otp_digest(challenge.id, phone_digest, purpose, code)
    if not verify_allowed or not hmac.compare_digest(challenge.otp_digest, expected):
        frappe.db.sql('UPDATE tt_otp_challenge SET attempts=attempts+1 WHERE id=%s', (challenge.id,))
        frappe.db.commit()
        _json_error('Verification code is invalid or expired', 'otp_invalid')

    if purpose == 'login':
        found = frappe.db.sql('SELECT user FROM tt_phone_identity WHERE phone=%s FOR UPDATE', (phone,))
        if not found:
            _json_error('Verification code is invalid or expired', 'otp_invalid')
        user = found[0][0]
    else:
        # Signup is contact proof only. Caller-supplied name, role, statement and
        # adult flag cannot complete onboarding or create any profile/role.
        from tele_tena.api import contact_auth
        user = contact_auth._identity('phone', phone)
        frappe.db.sql('''INSERT IGNORE INTO tt_phone_identity (user,phone,verified_at,created)
            VALUES (%s,%s,UTC_TIMESTAMP(6),UTC_TIMESTAMP(6))''', (user, phone))
    frappe.db.sql('UPDATE tt_otp_challenge SET consumed=UTC_TIMESTAMP(6),attempts=attempts+1 WHERE id=%s',
                  (challenge.id,))
    frappe.db.commit()
    _establish_login(user)
    return {'authenticated': True, 'onboarding_required': purpose != 'login'}
