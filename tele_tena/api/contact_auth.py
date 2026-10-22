"""Contact possession, then owner-only resumable onboarding. No public role input."""
import hashlib
import hmac
import json
import re
import secrets
import uuid
from datetime import timedelta

import frappe
from tele_tena import email_delivery, sms
from tele_tena.api import phone_auth as otp
from tele_tena.api.journey import actor, boolean, command, fail, query, text


def normalize(channel, contact):
    if channel == 'phone':
        return otp.normalize_phone(contact)
    if channel != 'email' or not isinstance(contact, str):
        fail('Enter a valid contact', 'invalid_contact')
    contact = contact.strip().lower()
    if len(contact) > 140 or not re.fullmatch(r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+", contact):
        fail('Enter a valid email address', 'invalid_contact')
    return contact


def _result(challenge_id):
    return {'challenge_id': challenge_id, 'resend_after': 60, 'expires_after': 300,
            'message': 'If delivery is available, a code will arrive shortly.'}


@frappe.whitelist(allow_guest=True, methods=['POST'])
def request_code(channel, contact, request_id):
    from tele_tena.review import guard_contact_access
    guard_contact_access(channel)
    contact = normalize(channel, contact)
    if not isinstance(request_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{20,100}', request_id):
        fail('Invalid request', 'invalid_request')
    digest = otp._keyed('contact:' + channel, contact)
    purpose = 'contact_' + channel
    request_digest = hashlib.sha256(request_id.encode()).hexdigest()
    now = otp._now()
    frappe.db.sql('SELECT id FROM tt_otp_gate WHERE id=1 FOR UPDATE')
    prior = frappe.db.sql('''SELECT id FROM tt_otp_challenge WHERE phone_digest=%s
        AND purpose=%s AND request_digest=%s''', (digest, purpose, request_digest))
    if prior:
        frappe.db.commit()
        return _result(prior[0][0])
    allowed = (otp._increment_limit('contact-window', digest, now, 900, 3)
               and otp._increment_limit('contact-day', digest, now, 86400, 5)
               and otp._increment_limit('contact-ip', otp._peer_ip(), now, 900, 10))
    recent = frappe.db.sql('''SELECT id FROM tt_otp_challenge WHERE phone_digest=%s
        AND created>%s ORDER BY created DESC LIMIT 1''', (digest, now - timedelta(seconds=60)))
    if not allowed or recent:
        frappe.db.commit()
        # Rate outcomes are independent of account existence.
        fail('Please wait before requesting another code', 'resend_cooldown')
    if channel == 'phone' and not otp.reserve_sms_budget(now):
        frappe.db.commit()
        fail('Code sending is temporarily unavailable. Please try again later.', 'sms_budget_exhausted')
    challenge = str(uuid.uuid4())
    code = f'{secrets.randbelow(1000000):06d}'
    frappe.db.sql('''INSERT INTO tt_otp_challenge
        (id,phone_digest,purpose,otp_digest,request_digest,created,expires,attempts,dispatch_state)
        VALUES (%s,%s,%s,%s,%s,%s,%s,0,'Sending')''',
        (challenge, digest, purpose, otp._otp_digest(challenge, digest, purpose, code),
         request_digest, now, now + timedelta(seconds=300)))
    frappe.db.commit()  # Durable send-once claim before provider interaction.
    try:
        (sms.send_otp if channel == 'phone' else email_delivery.send_code)(contact, code)
        state = 'Accepted'
    except sms.SMSRejected:
        state = 'Rejected'
    except Exception:
        state = 'Uncertain'
    frappe.db.sql('UPDATE tt_otp_challenge SET dispatch_state=%s WHERE id=%s', (state, challenge))
    frappe.db.commit()
    # Outcome never depends on whether an account exists. Accepted is not delivered.
    delivery = 'SMS' if channel == 'phone' else 'email'
    messages = {
        'Accepted': f'The {delivery} provider accepted the request. Delivery is not guaranteed.',
        'Rejected': f'The {delivery} provider rejected the request. Check the contact and try again after the cooldown.',
        'Uncertain': 'We could not confirm provider acceptance. If the code arrives, use it here; wait before requesting another.',
    }
    return {**_result(challenge), 'delivery_state': state.lower(), 'message': messages[state]}


def _identity(channel, contact):
    existing = frappe.db.sql('SELECT user FROM tt_contact_identity WHERE channel=%s AND contact=%s FOR UPDATE', (channel, contact))
    if channel == 'phone':
        legacy = frappe.db.sql('SELECT user FROM tt_phone_identity WHERE phone=%s FOR UPDATE', (contact,))
        if existing and legacy and existing[0][0] != legacy[0][0]:
            fail('Contact identity needs administrator review', 'account_unavailable')
        existing = existing or legacy
    if not existing and channel == 'email':
        # Only reached AFTER contact proof. Never accept a claimed account/user ID.
        name = frappe.db.get_value('User', {'email': contact}, 'name')
        existing = [(name,)] if name else []
    if existing:
        user = existing[0][0]
        if not frappe.db.get_value('User', user, 'enabled'):
            fail('This account is unavailable', 'account_unavailable')
    else:
        from tele_tena.review import registration_enabled
        if not any(registration_enabled(kind) for kind in ('patient', 'clinician')):
            fail('New registration is unavailable on this site', 'registration_unavailable')
        user = contact if channel == 'email' else 'contact-' + secrets.token_hex(20) + '@accounts.tele-tena.invalid'
        from tele_tena.account_context import authorized_user_change
        with authorized_user_change():
            doc = frappe.get_doc(dict(doctype='User', email=user, first_name='TeleTena member',
                                     user_type='Website User', enabled=1, send_welcome_email=0, roles=[]))
            doc.insert()
        user = doc.name
    frappe.db.sql('''INSERT IGNORE INTO tt_contact_identity (channel,contact,user,verified_at)
        VALUES (%s,%s,%s,UTC_TIMESTAMP(6))''', (channel, contact, user))
    if not frappe.db.sql('SELECT user FROM tt_profile WHERE user=%s', (user,)):
        frappe.db.sql('''INSERT IGNORE INTO tt_onboarding (user,answers,modified)
            VALUES (%s,'{}',UTC_TIMESTAMP(6))''', (user,))
    return user


@frappe.whitelist(allow_guest=True, methods=['POST'])
def verify_code(channel, contact, challenge_id, code):
    from tele_tena.review import guard_contact_access
    guard_contact_access(channel)
    contact = normalize(channel, contact)
    digest = otp._keyed('contact:' + channel, contact)
    purpose = 'contact_' + channel
    if not isinstance(challenge_id, str) or not re.fullmatch(r'[0-9a-f-]{36}', challenge_id):
        fail('Code invalid or expired', 'otp_invalid')
    # Same lock order for request and verification, including first identity creation.
    frappe.db.sql('SELECT id FROM tt_otp_gate WHERE id=1 FOR UPDATE')
    now = otp._now()
    allowed = (otp._increment_limit('contact-verify', digest, now, 900, 10)
               and otp._increment_limit('contact-verify-ip', otp._peer_ip(), now, 900, 20))
    rows = frappe.db.sql('SELECT * FROM tt_otp_challenge WHERE id=%s FOR UPDATE', (challenge_id,), as_dict=True)
    valid = bool(rows and allowed)
    row = rows[0] if rows else None
    valid = valid and row.phone_digest == digest and row.purpose == purpose and not row.consumed and row.expires > now and row.attempts < 5 and row.dispatch_state in ('Accepted', 'Uncertain')
    valid = valid and isinstance(code, str) and bool(re.fullmatch(r'[0-9]{6}', code)) and hmac.compare_digest(row.otp_digest, otp._otp_digest(challenge_id, digest, purpose, code))
    if not valid:
        if row and row.phone_digest == digest and row.purpose == purpose:
            frappe.db.sql('UPDATE tt_otp_challenge SET attempts=attempts+1 WHERE id=%s', (challenge_id,))
        frappe.db.commit()
        fail('Code invalid or expired', 'otp_invalid')
    user = _identity(channel, contact)
    frappe.db.sql('UPDATE tt_otp_challenge SET consumed=UTC_TIMESTAMP(6),attempts=attempts+1 WHERE id=%s', (challenge_id,))
    frappe.db.commit()
    otp._establish_login(user)
    return {'authenticated': True}


@frappe.whitelist(allow_guest=True)
def sign_in_options():
    """Site capabilities only; never reveal contact/account existence."""
    from tele_tena.review import enabled, phone_enabled, registration_enabled
    available_email = False
    if enabled() or frappe.local.site == 'erp.localhost':
        try:
            email_delivery.configuration()
            available_email = True
        except email_delivery.DeliveryUnavailable:
            pass
    available_phone = phone_enabled()
    if enabled():
        try:
            sms._config()
        except sms.SMSRejected:
            available_phone = False
    return {'phone_otp': available_phone, 'email_otp': available_email,
            'patient_registration': registration_enabled('patient'),
            'clinician_registration': registration_enabled('clinician')}


@frappe.whitelist(allow_guest=True)
def session():
    if frappe.session.user == 'Guest':
        return {'authenticated': False}
    from tele_tena.api.journey import session as current
    return {'authenticated': True, **current()}


@query()
def onboarding():
    user = actor()
    rows = frappe.db.sql('SELECT kind,step,answers,completed FROM tt_onboarding WHERE user=%s', (user,), as_dict=True)
    if not rows:
        return {'kind': 'patient', 'step': 0, 'answers': {}, 'completed': False}
    return {**rows[0], 'answers': json.loads(rows[0].answers), 'completed': bool(rows[0].completed)}


@query()
def application_services():
    """Contact-verified/onboarding accounts can choose non-bookable draft scopes."""
    actor()
    return frappe.db.sql("""SELECT name AS id,service_label AS label,clinical_review_status
        FROM `tabTele Tena Service` WHERE vetting_required=1
        AND catalog_status IN ('Draft','Active') ORDER BY service_label,name""", as_dict=True)


@command
def save_onboarding(kind, step, answers, complete=0):
    user = actor()
    if kind not in ('patient', 'clinician') or str(step) not in ('0', '1', '2', '3', '4', '5', '6', '7') or (str(step) == '4' and kind != 'patient') or (str(step) == '5' and kind != 'clinician'):
        fail('Invalid onboarding step')
    from tele_tena.review import registration_enabled
    if not registration_enabled(kind):
        fail('This registration path is unavailable', 'registration_unavailable')
    if not frappe.db.sql('SELECT user FROM tt_contact_identity WHERE user=%s', (user,)):
        fail('Verify a contact before onboarding', 'contact_required')
    rows = frappe.db.sql('SELECT completed FROM tt_onboarding WHERE user=%s FOR UPDATE', (user,))
    if not rows or rows[0][0]:
        fail('Onboarding already complete')
    if not isinstance(answers, dict) or set(answers) - {'name', 'adult', 'consent', 'language', 'share_name', 'share_history', 'statement', 'affiliations', 'requested_services', 'history', 'professional', 'care_languages', 'introduction','care_alias','terms_accepted','privacy_acknowledged','terms_version','privacy_version','marketing'}:
        fail('Invalid onboarding answers')
    clean = {k: text(v, 4000 if k == 'history' else 2000 if k == 'statement' else 120, False) for k, v in answers.items() if k in ('name', 'language', 'statement', 'affiliations', 'history','care_alias','terms_version','privacy_version')}
    for key in ('adult', 'consent', 'share_name', 'share_history','terms_accepted','privacy_acknowledged','marketing'):
        clean[key] = boolean(answers.get(key, kind == 'patient' and key in ('share_name', 'share_history')))
    requested_services = answers.get('requested_services', [])
    if not isinstance(requested_services, list) or len(requested_services) > 30:
        fail('Invalid requested service scopes')
    requested_services = sorted(set(text(item, 80) for item in requested_services))
    for service in requested_services:
        if not frappe.db.sql("SELECT name FROM `tabTele Tena Service` WHERE name=%s AND (active=1 OR (vetting_required=1 AND catalog_status='Draft'))", (service,)):
            fail('Choose from available services')
    clean['requested_services'] = requested_services
    if clean.get('language', 'en') not in ('en', 'am', 'om'):
        fail('Unsupported language')
    if kind == 'clinician' and clean.get('history'):
        fail('Care background is for patient registration')
    professional_keys = {'professional_category', 'qualification', 'issuing_institution',
                         'registration_number', 'issuing_authority', 'jurisdiction',
                         'credential_expiry', 'experience_years', 'competencies', 'certifications', 'credential_valid_from'}
    if kind != 'clinician' and any(key in answers for key in ('professional', 'care_languages', 'introduction')):
        fail('Professional application fields are for clinician registration')
    if 'professional' in answers:
        values = answers['professional']
        if not isinstance(values, dict) or set(values) - professional_keys:
            fail('Application contains unsupported fields.')
        from tele_tena.api.vetting import _validated_form
        clean['professional'] = _validated_form(values)
    if 'care_languages' in answers:
        languages = answers['care_languages']
        if not isinstance(languages, list) or any(not isinstance(value, str) for value in languages) or len(languages) != len(set(languages)) or not set(languages).issubset({'en', 'am', 'om'}):
            fail('Choose supported care languages')
        clean['care_languages'] = sorted(languages)
    if 'introduction' in answers:
        clean['introduction'] = text(answers['introduction'], 2000, False)
    finish = boolean(complete)
    if finish and kind == 'clinician':
        from tele_tena.api.professional import validate, persist, validate_bio
        draft = frappe.db.sql('SELECT payload FROM tt_professional_draft WHERE user=%s', (user,))
        if draft:
            structured = validate(json.loads(draft[0][0]), user, True)
            def label(key,other):
                id=structured.get(key,'')
                if id=='Other':return structured.get(other,'')
                found=frappe.db.sql('SELECT label FROM tt_reference WHERE id=%s',(id,))
                return found[0][0] if found else ''
            clean['name']=' '.join(filter(None,[structured.get('prefix_other') if structured.get('prefix')=='Other' else structured.get('prefix'),structured['first_name'],structured['last_name']]))
            clean['adult']=structured['adult'];clean['introduction']=structured.get('bio','')
            clean['professional']={'professional_category':label('profession','profession_other'),'qualification':structured['qualification_title'],'issuing_institution':label('issuer','issuer_other'),'registration_number':structured.get('license_number',''),'issuing_authority':label('authority','authority_other'),'jurisdiction':structured.get('jurisdiction',''),'credential_valid_from':structured.get('valid_from',''),'credential_expiry':structured.get('valid_until',''),'experience_years':structured.get('experience_years') or '0'}
    if finish:
        from tele_tena.api.policies import record
        record(user,clean)
        name = text(clean.get('name', ''), 120)
        if not clean['adult'] or not clean['consent']:
            fail('Adult eligibility and consent are required', 'adult_required')
        if kind == 'clinician':
            if not clean.get('professional'):
                text(clean.get('statement', ''), 2000)
            if not requested_services:
                fail('Choose at least one service for review')
            if not frappe.db.sql('SELECT clinician FROM tt_resume_evidence WHERE clinician=%s', (user,)) and not (draft and structured.get('cv_files')):
                fail('Upload a PDF resume before submitting your application', 'resume_required')
        if kind == 'clinician' and clean.get('professional'):
            if any(not clean['professional'].get(key) for key in ('professional_category', 'qualification', 'issuing_institution')) or not clean.get('care_languages'):
                fail('Complete your profession, qualification, institution and care languages before submission', 'professional_required')
        role = 'Tele Tena Patient' if kind == 'patient' else 'Tele Tena Applicant'
        from tele_tena.account_context import authorized_user_change
        with authorized_user_change():
            frappe.get_doc('User', user).add_roles(role)
        frappe.db.sql('''INSERT INTO tt_profile (user,kind,display_name,history,share_name,share_history,public_id,languages,introduction)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
            (user, kind, name, clean.get('history', '') if kind == 'patient' else '', clean['share_name'], clean['share_history'], str(uuid.uuid4()),
             json.dumps(clean.get('care_languages', []) if kind == 'clinician' else []),
             clean.get('introduction', '') if kind == 'clinician' else ''))
        if kind == 'patient':
            frappe.db.sql('INSERT IGNORE INTO tt_preferences (user,locale,modified) VALUES (%s,%s,UTC_TIMESTAMP(6))',(user,clean.get('language','en')))
            frappe.db.sql('UPDATE tt_profile SET care_alias=%s WHERE user=%s',(clean.get('care_alias') or 'Care guest',user))
            frappe.db.sql('INSERT INTO tt_wallet (patient) VALUES (%s)', (user,))
        else:
            frappe.db.sql("INSERT INTO tt_application (user,statement,status,requested_services,submitted_at) VALUES (%s,%s,'Pending',%s,UTC_TIMESTAMP(6))",
                          (user, clean.get('statement', ''), json.dumps(requested_services)))
    frappe.db.sql('''UPDATE tt_onboarding SET kind=%s,step=%s,answers=%s,
        completed=IF(%s,UTC_TIMESTAMP(6),NULL),modified=UTC_TIMESTAMP(6) WHERE user=%s''',
        (kind, int(step), json.dumps(clean), finish, user))
    if finish and kind=='clinician' and draft:
        persist(user,structured,submit=True)
    return {'saved': True, 'completed': finish}
