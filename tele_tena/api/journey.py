"""Authorized, transactional milestone commands. No real funds or clinical fixtures."""
import functools
import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta, timezone

import frappe
from frappe.sessions import get_csrf_token


def fail(message, code='invalid_input'):
    frappe.local.response['tele_tena_error'] = code
    frappe.throw(message, frappe.ValidationError)


def actor(role=None):
    user = frappe.session.user
    if user == 'Guest' or not user:
        frappe.throw('Authentication required', frappe.PermissionError)
    if role and role not in frappe.get_roles(user):
        frappe.throw('Role required', frappe.PermissionError)
    return user


def rows(query, values=()):
    return frappe.db.sql(query, values, as_dict=True)


def one(query, values=()):
    found = rows(query, values)
    if not found:
        fail('Record unavailable')
    return found[0]


def profile(kind, lock=False):
    user = actor('Tele Tena ' + kind.title())
    p = one('SELECT * FROM tt_profile WHERE user=%s' + (' FOR UPDATE' if lock else ''), (user,))
    if p.kind != kind:
        frappe.throw('Profile role mismatch', frappe.PermissionError)
    return p


def approved(user, lock=False):
    app = one('SELECT status FROM tt_application WHERE user=%s' + (' FOR UPDATE' if lock else ''), (user,))
    if app.status != 'Approved':
        fail('Clinician approval required', 'approval_required')
    if 'Tele Tena Clinician' not in frappe.get_roles(user) or not frappe.db.get_value('User', user, 'enabled'):
        fail('Clinician unavailable')


def query(method='GET'):
    def decorate(fn):
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except (frappe.PermissionError, frappe.ValidationError):
                raise
            except Exception:
                if getattr(frappe.local, 'request', None):
                    frappe.local.form_dict.clear()
                    fail('Operation unavailable; retry later')
                raise
        return frappe.whitelist(methods=[method])(wrapped)
    return decorate


def command(fn):
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        actor()
        savepoint = 'tt_' + uuid.uuid4().hex
        frappe.db.savepoint(savepoint)
        try:
            return fn(*args, **kwargs)
        except frappe.QueryDeadlockError:
            frappe.db.rollback()
            fail('Concurrent update; retry with the same submission key', 'concurrent_update')
        except (frappe.PermissionError, frappe.ValidationError):
            frappe.db.rollback(save_point=savepoint)
            raise
        except Exception:
            frappe.db.rollback(save_point=savepoint)
            if getattr(frappe.local, 'request', None):
                frappe.local.form_dict.clear()
                fail('Operation failed; review inputs and retry with the same submission key')
            raise
    return frappe.whitelist(methods=['POST'])(wrapped)


def text(value, maximum, required=True):
    if not isinstance(value, str) or len(value.strip()) > maximum or (required and not value.strip()):
        fail('Invalid text')
    return value.strip()


def integer(value, minimum, maximum):
    # Reject fractional values, booleans and scientific notation; never use floats.
    if isinstance(value, bool) or not re.fullmatch(r'[0-9]+', str(value)):
        fail('Expected a whole number')
    result = int(value)
    if not minimum <= result <= maximum:
        fail('Number outside supported range')
    return result


def boolean(value):
    if value not in (True, False, 0, 1, '0', '1'):
        fail('Expected a sharing choice')
    return value in (True, 1, '1')


def instant(value):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            fail('UTC offset required')
        return result.astimezone(timezone.utc).replace(tzinfo=None)
    except (ValueError, TypeError, AttributeError):
        fail('Invalid timestamp')


def iso(value):
    return value.isoformat(timespec='seconds') + 'Z'


def choices(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            fail('Invalid sharing choices')
    if not isinstance(value, dict) or set(value) != {'name', 'history'}:
        fail('Choose name and history disclosure explicitly')
    return {key: boolean(value[key]) for key in ('name', 'history')}


def disclosure(p, request_text, selected):
    result = {'request': text(request_text, 2000)}
    if selected['name']:
        result['name'] = p.display_name
    if selected['history']:
        result['history'] = p.history
    return result


def _clinic_workspace_available(user):
    # Clinic navigation is a convenience hint only. Every clinic API still
    # checks its own membership role and verified-clinic state.
    return bool(frappe.db.sql('''
        SELECT 1 FROM `tabTele Tena Clinic Membership` m
        JOIN `tabTele Tena Clinic` c ON c.name=m.clinic
        WHERE m.member_user=%s AND m.status='Active'
          AND m.membership_role IN ('Clinic Manager','Scheduling')
          AND c.status='Verified'
        UNION ALL
        SELECT 1 FROM `tabTele Tena Clinic` c
        WHERE c.submitted_by=%s AND c.status='Verified'
        UNION ALL
        SELECT 1 FROM `tabTele Tena Clinic Membership` m
        JOIN `tabTele Tena Clinic` c ON c.name=m.clinic
        JOIN tt_contact_identity i ON i.channel='email' AND i.contact=m.invite_email
          AND i.user=%s AND i.verified_at IS NOT NULL
        WHERE m.status='Invited' AND c.status='Verified'
        LIMIT 1''', (user, user, user)))


@query()
def session():
    user = actor()
    p = rows('SELECT * FROM tt_profile WHERE user=%s', (user,))
    return {'user': user, 'roles': frappe.get_roles(user), 'profile': p[0] if p else None,
            'clinic_workspace': _clinic_workspace_available(user),
            'csrf_token': get_csrf_token(), 'simulation': simulation_enabled()}


@command
def save_profile(kind, display_name, adult, history='', share_name=None, share_history=None, languages=None):
    if kind not in ('patient', 'clinician'):
        fail('Unsupported profile type')
    user = actor('Tele Tena ' + kind.title())
    if not boolean(adult):
        fail('Adults 18+ only')
    existing = rows('SELECT kind,share_name,share_history,languages,public_id FROM tt_profile WHERE user=%s FOR UPDATE', (user,))
    if existing and existing[0].kind != kind:
        fail('Profile type cannot change')
    share_name = existing[0].share_name if share_name is None and existing else (False if share_name is None else share_name)
    share_history = existing[0].share_history if share_history is None and existing else (False if share_history is None else share_history)
    name = text(display_name, 120)
    history = text(history, 4000, False) if kind == 'patient' else ''
    if languages is None:
        language_values = json.loads(existing[0].languages or '[]') if existing else []
    else:
        if isinstance(languages, str):
            try:
                languages = json.loads(languages)
            except ValueError:
                fail('Choose the languages you can provide care in')
        supported = {'en', 'am', 'om'}
        if not isinstance(languages, list) or len(set(languages)) != len(languages) or not set(languages).issubset(supported):
            fail('Choose supported care languages')
        language_values = sorted(set(languages)) if kind == 'clinician' else []
    public_id = existing[0].public_id if existing else str(uuid.uuid4())
    frappe.db.sql('''INSERT INTO tt_profile (user,kind,display_name,history,share_name,share_history,languages,public_id)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE display_name=VALUES(display_name),
        history=VALUES(history),share_name=VALUES(share_name),share_history=VALUES(share_history),languages=VALUES(languages)''',
        (user, kind, name, history, boolean(share_name), boolean(share_history), json.dumps(language_values), public_id))
    if kind == 'patient':
        frappe.db.sql('INSERT IGNORE INTO tt_wallet (patient) VALUES (%s)', (user,))
    audit(user, 'ProfileConsent', {'adult_attested': True, 'share_name': boolean(share_name), 'share_history': boolean(share_history)})
    return {'saved': True}


@command
def apply(statement, requested_services='[]'):
    user = actor()
    p = one('SELECT * FROM tt_profile WHERE user=%s FOR UPDATE', (user,))
    if p.kind != 'clinician':
        frappe.throw('Clinician profile required', frappe.PermissionError)
    if isinstance(requested_services, str):
        try:
            requested_services = json.loads(requested_services)
        except ValueError:
            fail('Invalid requested service scopes')
    if not isinstance(requested_services, list) or len(requested_services) > 30:
        fail('Invalid requested service scopes')
    requested = sorted(set(text(service, 80) for service in requested_services))
    for service in requested:
        if not rows('SELECT name FROM `tabTele Tena Service` WHERE name=%s AND active=1', (service,)):
            fail('Choose from available services')
    statement = text(statement, 2000)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    frappe.db.sql('''INSERT INTO tt_application (user,statement,status,requested_services,submitted_at)
        VALUES (%s,%s,'Pending',%s,%s) ON DUPLICATE KEY UPDATE statement=VALUES(statement),
        status='Pending',reviewed_by=NULL,reviewed_at=NULL,requested_services=VALUES(requested_services),
        submitted_at=VALUES(submitted_at)''',
        (p.user, statement, json.dumps(requested), now))
    audit(p.user, 'Application', {'status': 'Pending', 'requested_services': requested})
    return {'status': 'Pending'}


@query()
def applications():
    user = actor()
    if 'Tele Tena Approver' in frappe.get_roles(user):
        result = rows('''SELECT a.*,p.display_name FROM tt_application a
            JOIN tt_profile p ON p.user=a.user ORDER BY a.submitted_at IS NULL,a.submitted_at,a.user''')
        for item in result:
            try:
                item.requested_services = json.loads(item.requested_services or '[]')
            except ValueError:
                item.requested_services = []
            item.requested_service_labels = []
            for service in item.requested_services:
                label = rows('SELECT service_label FROM `tabTele Tena Service` WHERE name=%s', (service,))
                item.requested_service_labels.append(label[0].service_label if label else 'Unavailable service')
            evidence = rows('SELECT content_size,revision,uploaded_at FROM tt_resume_evidence WHERE clinician=%s',
                            (item.user,))
            item.resume_uploaded = bool(evidence)
            item.resume_size = evidence[0].content_size if evidence else None
            item.resume_revision = evidence[0].revision if evidence else None
            item.submission_date_available = bool(item.submitted_at)
            item.evidence_complete = bool(item.statement.strip() and evidence)
            item.verified_contacts = rows('SELECT channel,contact,verified_at FROM tt_contact_identity WHERE user=%s',
                                          (item.user,))
        return result
    p = one('SELECT kind FROM tt_profile WHERE user=%s', (user,))
    if p.kind != 'clinician':
        frappe.throw('Clinician application unavailable', frappe.PermissionError)
    return rows('SELECT * FROM tt_application WHERE user=%s', (user,))


@command
def review(clinician, decision):
    reviewer = actor('Tele Tena Approver')
    if clinician == reviewer or decision not in ('Approved', 'Rejected'):
        fail('Invalid approval decision')
    one('SELECT user FROM tt_profile WHERE user=%s AND kind=%s FOR UPDATE', (clinician, 'clinician'))
    one('SELECT user FROM tt_application WHERE user=%s FOR UPDATE', (clinician,))
    frappe.db.sql('UPDATE tt_application SET status=%s,reviewed_by=%s,reviewed_at=UTC_TIMESTAMP(6) WHERE user=%s',
                  (decision, reviewer, clinician))
    # This one role transition is part of the approver-guarded command. Public
    # phone signup itself assigns only Patient or non-privileged Applicant.
    from tele_tena.account_context import authorized_user_change
    with authorized_user_change():
        user_doc = frappe.get_doc('User', clinician)
        if decision == 'Approved':
            user_doc.add_roles('Tele Tena Clinician')
            user_doc.remove_roles('Tele Tena Applicant')
        else:
            user_doc.remove_roles('Tele Tena Clinician')
            user_doc.add_roles('Tele Tena Applicant')
    audit(clinician, 'Review', {'status': decision})
    return {'status': decision}


@command
def save_service(service, label):
    actor('Tele Tena Approver')
    if not re.fullmatch(r'[a-z0-9-]{1,80}', service):
        fail('Invalid service identifier')
    if frappe.db.exists('Tele Tena Service', service):
        doc = frappe.get_doc('Tele Tena Service', service)
        doc.service_label = text(label, 120)
        doc.save()
    else:
        from tele_tena.review import enabled as review_enabled
        legacy_demo = review_enabled() or frappe.local.site == 'erp.localhost'
        frappe.get_doc(dict(doctype='Tele Tena Service', service_key=service,
                            service_label=text(label, 120), active=1 if legacy_demo else 0,
                            catalog_status='Legacy test' if legacy_demo else 'Draft',
                            clinical_review_status='Not reviewed', vetting_required=0 if legacy_demo else 1)).insert()
    return {'saved': True}


@command
def review_service_scope(clinician, service, decision, vetting_action=False):
    actor('Tele Tena Approver')
    if decision not in ('Approved', 'Revoked'):
        fail('Invalid service scope decision')
    service_doc = one('SELECT vetting_required FROM `tabTele Tena Service` WHERE name=%s', (service,))
    if decision == 'Approved' and service_doc.vetting_required and not vetting_action:
        fail('This service requires a completed, recorded scope vetting decision.', 'scope_vetting_required')
    if decision == 'Approved' and service_doc.vetting_required:
        approved_application = rows("""SELECT name FROM `tabTele Tena Vetting Scope Application`
            WHERE clinician=%s AND service=%s AND status='Approved' FOR UPDATE""", (clinician, service))
        if not approved_application:
            fail('Complete the human scope assessment before approval.', 'scope_vetting_required')
    from tele_tena.backoffice import scope_name
    name = scope_name(clinician, service)
    frappe.local.tele_tena_vetting_decision = bool(vetting_action)
    try:
        if frappe.db.exists('Tele Tena Service Scope', name):
            doc = frappe.get_doc('Tele Tena Service Scope', name)
            doc.status = decision
            doc.save()
        else:
            frappe.get_doc(dict(doctype='Tele Tena Service Scope', clinician=clinician,
                                service=service, status=decision)).insert()
    finally:
        frappe.local.tele_tena_vetting_decision = False
    return {'status': decision}


@query()
def service_scopes():
    actor('Tele Tena Approver')
    return frappe.get_list('Tele Tena Service Scope', fields=['clinician', 'service', 'status'])


def approved_service(clinician, service, lock=False):
    if not service_scope_is_current(clinician, service, lock=lock):
        definitions = rows('''SELECT active,catalog_status,clinical_review_status FROM `tabTele Tena Service`
            WHERE name=%s''', (service,))
        if not definitions:
            fail('This service is not currently available.', 'service_definition_unavailable')
        definition = definitions[0]
        if not definition.active or definition.catalog_status not in ('Active', 'Legacy test'):
            fail('This service is not currently available.', 'service_definition_unavailable')
        if definition.clinical_review_status != 'Approved' and definition.catalog_status == 'Active':
            fail('This service definition has not completed clinical review.', 'catalog_not_approved')
        fail('Clinician is not approved for this service', 'service_scope_required')


def service_scope_is_current(clinician, service, lock=False):
    """Fail-closed current service permission used by discovery and commands."""
    suffix = ' FOR UPDATE' if lock else ''
    definitions = rows('''SELECT active,catalog_status,vetting_required,clinical_review_status
        FROM `tabTele Tena Service` WHERE name=%s''', (service,))
    if not definitions:
        return False
    definition = definitions[0]
    if not definition or not definition.active:
        return False
    if definition.catalog_status == 'Legacy test':
        from tele_tena.review import enabled as review_enabled
        if not (review_enabled() or frappe.local.site == 'erp.localhost'):
            return False
    elif definition.catalog_status != 'Active':
        return False
    if definition.vetting_required and definition.clinical_review_status != 'Approved':
        return False
    scope = rows("SELECT name FROM `tabTele Tena Service Scope` WHERE clinician=%s AND service=%s AND status='Approved'" + suffix,
                 (clinician, service))
    if not scope:
        return False
    if not definition.vetting_required:
        return True
    current = rows('''SELECT a.name FROM `tabTele Tena Vetting Scope Application` a
        JOIN `tabTele Tena Vetting Assessment` v ON v.scope_application=a.name
        WHERE a.clinician=%s AND a.service=%s AND a.status='Approved'
          AND v.decision='Approved'
          AND (a.credential_expiry IS NULL OR a.credential_expiry >= %s)
        ORDER BY v.creation DESC LIMIT 1''', (clinician, service, frappe.utils.today()))
    return bool(current)


@query()
def services():
    actor()
    from tele_tena.review import enabled as review_enabled
    legacy_allowed = int(review_enabled() or frappe.local.site == 'erp.localhost')
    return rows('''SELECT name AS id,service_label AS label FROM `tabTele Tena Service`
        WHERE active=1 AND (catalog_status='Active' OR (catalog_status='Legacy test' AND %s=1))
        ORDER BY service_label''', (legacy_allowed,))


@command
def publish(service, price, minutes, title=None, description='', offering_id=None, retry_key=None):
    """Create an offering or edit one owned offering without widening scope.

    New clients supply a retry key for safe create retries. Legacy clients keep
    the prior upsert behavior only while exactly one matching offering exists.
    """
    p = profile('clinician', True)
    fee, duration = integer(price, 1, 100000000), integer(minutes, 5, 240)
    service_row = one('SELECT service_label FROM `tabTele Tena Service` WHERE name=%s AND active=1', (service,))
    normalized_title = (str(title).strip() if title is not None else service_row.service_label)
    normalized_description = str(description or '').strip()
    if not normalized_title or len(normalized_title) > 160 or len(normalized_description) > 1000:
        fail('Add a title up to 160 characters and a description up to 1,000 characters.', 'offering_text_invalid')
    key = str(retry_key or '').strip()
    if key and (len(key) > 100 or not re.fullmatch(r'[A-Za-z0-9._:-]{12,100}', key)):
        fail('Use a valid offering submission key.', 'offering_retry_key_invalid')
    payload = {'service': service, 'title': normalized_title, 'description': normalized_description,
               'price': fee, 'minutes': duration}
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

    # The same short-lived gate used by booking commands serializes create
    # retries so a duplicate browser submission cannot create another row.
    frappe.db.sql('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    if key:
        prior = rows('SELECT id,payload_hash FROM tt_offering WHERE clinician=%s AND retry_key=%s FOR UPDATE',
                     (p.user, key))
        if prior:
            if prior[0].payload_hash != payload_hash:
                fail('This submission key was already used for different offering details.', 'offering_retry_conflict')
            return {'saved': True, 'offering': prior[0].id, 'replayed': True}

    approved(p.user, True)
    approved_service(p.user, service, True)
    if offering_id:
        current = rows('SELECT id,service FROM tt_offering WHERE id=%s AND clinician=%s FOR UPDATE',
                       (offering_id, p.user))
        if not current:
            frappe.throw('Offering unavailable.', frappe.PermissionError)
        if current[0].service != service:
            fail('An offering cannot be changed to a different approved service. Create another offering instead.',
                 'offering_scope_immutable')
        frappe.db.sql('''UPDATE tt_offering SET title=%s,description=%s,price=%s,minutes=%s,active=1
            WHERE id=%s AND clinician=%s''',
            (normalized_title, normalized_description, fee, duration, offering_id, p.user))
        saved_id = offering_id
        action_name = 'Offering updated'
    else:
        existing = rows('SELECT id FROM tt_offering WHERE clinician=%s AND service=%s ORDER BY id FOR UPDATE',
                        (p.user, service))
        if not key and len(existing) > 1:
            fail('Choose a specific offering to edit, or submit a new offering with a retry key.',
                 'offering_selection_required')
        if not key and existing:
            saved_id = existing[0].id
            frappe.db.sql('''UPDATE tt_offering SET title=%s,description=%s,price=%s,minutes=%s,active=1
                WHERE id=%s AND clinician=%s''',
                (normalized_title, normalized_description, fee, duration, saved_id, p.user))
            action_name = 'Offering updated'
        else:
            saved_id = str(uuid.uuid4())
            frappe.db.sql('''INSERT INTO tt_offering
                (id,clinician,service,title,description,price,minutes,active,retry_key,payload_hash)
                VALUES (%s,%s,%s,%s,%s,%s,%s,1,%s,%s)''',
                (saved_id, p.user, service, normalized_title, normalized_description, fee, duration,
                 key or None, payload_hash))
            action_name = 'Offering published'
    audit(p.user, action_name, {'offering': saved_id, **payload})
    return {'saved': True, 'offering': saved_id, 'replayed': False}


@command
def add_availability(start, end):
    p = profile('clinician', True)
    approved(p.user, True)
    start, end = instant(start), instant(end)
    if start <= datetime.now(timezone.utc).replace(tzinfo=None) or end <= start or end - start > timedelta(days=1):
        fail('Choose a future window of at most one day', 'invalid_availability_window')
    if rows('SELECT id FROM tt_availability WHERE clinician=%s AND start<%s AND end>%s', (p.user, end, start)):
        fail('Availability overlaps an existing window', 'availability_overlap')
    frappe.db.sql('INSERT INTO tt_availability (id,clinician,start,end) VALUES (%s,%s,%s,%s)',
                  (str(uuid.uuid4()), p.user, start, end))
    return {'saved': True}


@query()
def discover(service=None):
    actor('Tele Tena Patient')
    from tele_tena.review import enabled as review_enabled
    legacy_allowed = int(review_enabled() or frappe.local.site == 'erp.localhost')
    results = rows('''SELECT o.id,p.public_id AS clinician_id,p.display_name,p.languages AS care_languages,o.clinician,o.service,
        COALESCE(NULLIF(o.title,''),s.service_label) AS label,s.service_label AS service_category,o.description,o.price,o.minutes,
        sc.id AS schedule_id,sc.timezone AS schedule_timezone,sc.consultation_format
        FROM tt_offering o JOIN tt_profile p ON p.user=o.clinician
        JOIN tt_application a ON a.user=o.clinician JOIN `tabTele Tena Service` s ON s.name=o.service
        LEFT JOIN tt_schedule sc ON sc.offering=o.id AND sc.status='Published'
        JOIN tabUser u ON u.name=o.clinician
        WHERE a.status='Approved' AND o.active=1 AND s.active=1 AND u.enabled=1
        AND EXISTS (SELECT 1 FROM `tabTele Tena Service Scope` sc WHERE sc.clinician=o.clinician AND sc.service=o.service AND sc.status='Approved')
        AND EXISTS (SELECT 1 FROM `tabHas Role` r WHERE r.parent=o.clinician AND r.role='Tele Tena Clinician')
        AND (s.catalog_status='Active' OR (s.catalog_status='Legacy test' AND %s=1))
        AND (%s IS NULL OR o.service=%s) ORDER BY s.service_label,p.display_name''',
        (legacy_allowed, service or None, service or None))
    visible = []
    for item in results:
        if not service_scope_is_current(item.clinician, item.service):
            continue
        try:
            languages = json.loads(item.care_languages or '[]')
        except (TypeError, ValueError):
            languages = []
        if not isinstance(languages, list):
            languages = []
        item.care_languages = sorted({value for value in languages if value in {'en', 'am', 'om'}})
        # The account key is needed only for the server-side eligibility
        # filter. Never serialize an account email to patient discovery.
        item.pop('clinician', None)
        visible.append(item)
    return visible


@query()
def previous_clinicians():
    """Return only clinicians this patient personally consulted and completed.

    The opaque public profile key is intentionally unrelated to account names or
    emails. No encounter is linked across patients, and only clinicians with a
    currently approved scope and a public active offering are included.
    """
    patient = profile('patient')
    history = rows('''SELECT p.public_id AS clinician_id,p.display_name,
        MAX(a.start) AS last_consultation,COUNT(DISTINCT a.id) AS completed_sessions,
        p.user AS clinician_account
        FROM tt_appointment a JOIN tt_profile p ON p.user=a.clinician AND p.kind='clinician'
        JOIN tt_application app ON app.user=p.user AND app.status='Approved'
        JOIN tabUser u ON u.name=p.user AND u.enabled=1
        JOIN `tabHas Role` hr ON hr.parent=p.user AND hr.role='Tele Tena Clinician'
        WHERE a.patient=%s AND a.state='Completed'
        AND EXISTS (
          SELECT 1 FROM tt_offering o
          JOIN `tabTele Tena Service` svc ON svc.name=o.service AND svc.active=1
          JOIN `tabTele Tena Service Scope` sc ON sc.clinician=o.clinician
            AND sc.service=o.service AND sc.status='Approved'
          JOIN tt_schedule sched ON sched.offering=o.id AND sched.status='Published'
          WHERE o.clinician=p.user AND o.active=1
        )
        GROUP BY p.public_id,p.display_name,p.user
        ORDER BY last_consultation DESC LIMIT 20''', (patient.user,))
    visible = []
    for item in history:
        if not service_scope_is_current_for_any_offering(item.clinician_account):
            continue
        item.pop('clinician_account', None)
        item.completed_sessions = int(item.completed_sessions)
        visible.append(item)
    return visible


def service_scope_is_current_for_any_offering(clinician):
    offerings = rows('''SELECT o.service FROM tt_offering o
        JOIN tt_schedule s ON s.offering=o.id AND s.status='Published'
        WHERE o.clinician=%s AND o.active=1''', (clinician,))
    return any(service_scope_is_current(clinician, item.service) for item in offerings)


@query()
def windows(offering):
    actor('Tele Tena Patient')
    o = one('SELECT * FROM tt_offering WHERE id=%s AND active=1', (offering,))
    approved(o.clinician)
    approved_service(o.clinician, o.service)
    available = rows('SELECT start,end FROM tt_availability WHERE clinician=%s AND end>UTC_TIMESTAMP() ORDER BY start', (o.clinician,))
    busy = rows('SELECT start,end FROM tt_appointment WHERE clinician=%s AND end>UTC_TIMESTAMP()', (o.clinician,))
    # Publish occupied times only, never identities or disclosures.
    return {'windows': [{'start': iso(w.start), 'end': iso(w.end)} for w in available],
            'busy': [{'start': iso(w.start), 'end': iso(w.end)} for w in busy]}


@query('POST')
def preview(request_text, sharing):
    p = profile('patient')
    selected = choices(sharing)
    return {'disclosure': disclosure(p, request_text, selected), 'sharing': selected}


def simulation_enabled():
    from tele_tena.review import enabled
    return enabled() or (frappe.local.site == 'erp.localhost' and bool(frappe.conf.get('tele_tena_simulation_enabled')))


@command
def simulated_deposit(amount, retry_key):
    p = profile('patient')
    if not simulation_enabled():
        frappe.throw('Development simulation disabled', frappe.PermissionError)
    amount = integer(amount, 1, 100000000)
    key = text(retry_key, 80)
    wallet = one('SELECT * FROM tt_wallet WHERE patient=%s FOR UPDATE', (p.user,))
    from tele_tena.accounting import account_id, check_wallet_projection, post
    check_wallet_projection(p.user, wallet)
    reference = 'deposit:' + hashlib.sha256((p.user + ':' + key).encode()).hexdigest()
    previous = rows('SELECT amount FROM tt_ledger WHERE reference=%s', (reference,))
    if previous:
        if previous[0].amount != amount:
            fail('Retry key payload changed', 'retry_changed')
        return {'simulated': True}
    if wallet.available + wallet.reserved + amount > 1000000000:
        fail('Demo balance limit exceeded')
    frappe.db.sql('UPDATE tt_wallet SET available=available+%s WHERE patient=%s', (amount, p.user))
    simulation_log(p.user, 'Deposit', amount, reference)
    post(reference, 'Deposit', reference, [
        (account_id('', '', 'cash_clearing'), amount, 0),
        (account_id('patient', p.user, 'available'), 0, amount)], {'simulated': True})
    return {'simulated': True}


def simulation_log(patient, kind, amount, reference):
    frappe.db.sql('INSERT INTO tt_ledger (id,patient,kind,amount,reference,created) VALUES (%s,%s,%s,%s,%s,UTC_TIMESTAMP(6))',
                  (str(uuid.uuid4()), patient, kind, amount, reference))


@command
def book(offering, start, request_text, sharing, retry_key, expected_price, expected_minutes,
         expected_disclosure, booked_timezone='UTC', custom_offer_id=None,
         booking_link_token=None):
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    p = profile('patient', True)
    selected = choices(sharing)
    if isinstance(expected_disclosure, str):
        try:
            expected_disclosure = json.loads(expected_disclosure)
        except ValueError:
            fail('Invalid disclosure preview')
    start = instant(start)
    key = text(retry_key, 80)
    payload_values = [offering, iso(start), request_text, selected, expected_price,
                      expected_minutes, expected_disclosure, booked_timezone]
    # Keep the historic direct-booking digest stable. Link-origin retries bind
    # the opaque token into their idempotency payload without storing it.
    if booking_link_token:
        payload_values.append({'booking_link_token': booking_link_token})
    if custom_offer_id:
        if getattr(frappe.local, 'tele_tena_accepting_offer', None) != custom_offer_id:
            frappe.throw('Offer acceptance must use its authorized request workflow', frappe.PermissionError)
        payload_values.append({'request_offer': custom_offer_id})
    payload = json.dumps(payload_values, sort_keys=True)
    digest = hashlib.sha256(payload.encode()).hexdigest()
    wallet = one('SELECT * FROM tt_wallet WHERE patient=%s FOR UPDATE', (p.user,))
    from tele_tena.accounting import account_id, check_wallet_projection, post
    check_wallet_projection(p.user, wallet)
    prior = rows('SELECT id,payload_hash FROM tt_appointment WHERE patient=%s AND retry_key=%s FOR UPDATE', (p.user, key))
    if prior:
        if prior[0].payload_hash != digest:
            fail('Retry key payload changed', 'retry_changed')
        return {'id': prior[0].id, 'simulated': True}
    trusted_disclosure = getattr(frappe.local, 'tele_tena_offer_disclosure', None)
    if custom_offer_id and getattr(frappe.local, 'tele_tena_accepting_offer', None) == custom_offer_id:
        shared = trusted_disclosure
        if not isinstance(shared, dict) or expected_disclosure != shared:
            fail('Review the exact request disclosure before accepting this offer.', 'request_disclosure_changed')
    else:
        shared = disclosure(p, request_text, selected)
        if expected_disclosure != shared:
            fail('Profile changed; review disclosure again', 'preview_changed')
    o = one('SELECT * FROM tt_offering WHERE id=%s AND active=1', (offering,))
    # All scheduling mutations acquire the clinician profile lock, across services.
    one('SELECT user FROM tt_profile WHERE user=%s AND kind=%s FOR UPDATE', (o.clinician, 'clinician'))
    approved(o.clinician, True)
    approved_service(o.clinician, o.service, True)
    o = one('''SELECT o.*,COALESCE(NULLIF(o.title,''),s.service_label) AS label
        FROM tt_offering o JOIN `tabTele Tena Service` s ON s.name=o.service
        WHERE o.id=%s AND o.active=1 AND s.active=1 FOR UPDATE''', (offering,))
    if booking_link_token:
        if custom_offer_id:
            fail('Choose either a clinician booking link or a private request offer.',
                 'booking_source_conflict')
        from tele_tena.api.scheduling import validate_booking_link_token
        validate_booking_link_token(booking_link_token, o.id)
        acquisition_source = 'clinician_share'
    elif custom_offer_id:
        acquisition_source = 'open_request'
    else:
        acquisition_source = 'direct_booking'
    booking_price = int(o.price)
    immediate_request = False
    if custom_offer_id:
        quoted = one("""SELECT ro.price_minor,ro.offering,ro.clinician,r.patient,r.state,r.urgency,
                r.earliest_start,r.latest_start,
                ro.state offer_state,ro.valid_until
            FROM tt_request_offer ro JOIN tt_open_request r ON r.id=ro.request_id
            WHERE ro.id=%s AND r.patient=%s AND r.state='Open' AND ro.state='Active' FOR UPDATE""",
            (custom_offer_id, p.user))
        if quoted.offering != o.id or quoted.valid_until <= datetime.now(timezone.utc).replace(tzinfo=None):
            fail('This offer is no longer available', 'request_offer_expired')
        booking_price = int(quoted.price_minor)
        immediate_request = quoted.urgency == 'immediate'
        if immediate_request:
            presence = rows('''SELECT expires_at FROM tt_clinician_request_presence
                WHERE clinician=%s AND ready=1 AND expires_at>UTC_TIMESTAMP(6) FOR UPDATE''', (o.clinician,))
            if not presence:
                fail('Clinician immediate availability has expired', 'request_presence_stale')
    if integer(expected_price, 1, 100000000) != booking_price or integer(expected_minutes, 5, 240) != o.minutes:
        fail('Offering changed; review price and duration again', 'offering_changed')
    end = start + timedelta(minutes=o.minutes)
    if start <= datetime.now(timezone.utc).replace(tzinfo=None):
        fail('Appointment must be in the future', 'future_required')
    from tele_tena.api import scheduling
    schedule = scheduling.validate_slot(o, start, p.user, lock=True,
                                        immediate_ready=immediate_request,
                                        immediate_window=(quoted.earliest_start, quoted.latest_start)
                                        if immediate_request else None)
    schedule_timezone = schedule.timezone if schedule else scheduling._zone(booked_timezone).key
    before = int(schedule.buffer_before) if schedule else 0
    after = int(schedule.buffer_after) if schedule else 0
    if rows('''SELECT id FROM tt_appointment WHERE
        ((clinician=%s AND state IN ('Booked','PendingConfirmation')
          AND (expires_at IS NULL OR expires_at>UTC_TIMESTAMP(6))
          AND DATE_SUB(start,INTERVAL buffer_before MINUTE)<%s
          AND DATE_ADD(end,INTERVAL buffer_after MINUTE)>%s)
         OR (patient=%s AND state IN ('Booked','PendingConfirmation')
          AND (expires_at IS NULL OR expires_at>UTC_TIMESTAMP(6)) AND start<%s AND end>%s))
        FOR UPDATE''', (o.clinician, end + timedelta(minutes=after),
                       start - timedelta(minutes=before), p.user, end, start)):
        fail('Appointment conflict', 'appointment_conflict')
    if wallet.available < booking_price:
        fail('Insufficient simulated funds', 'insufficient_funds')
    appointment = str(uuid.uuid4())
    # Accepting the clinician's offer is already explicit confirmation.
    mode = 'automatic' if custom_offer_id else (schedule.confirmation_mode if schedule else 'automatic')
    expires = None
    state = 'Booked'
    confirmed = datetime.now(timezone.utc).replace(tzinfo=None) if mode == 'automatic' else None
    if mode == 'manual':
        hours = int(frappe.conf.get('tele_tena_pending_expiry_hours', 24))
        hours = max(1, min(168, hours))
        expires = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=hours)
        state = 'PendingConfirmation'
    fee_bps = int(frappe.conf.get('tele_tena_demo_platform_fee_bps', 0))
    dispute_minutes = int(frappe.conf.get('tele_tena_demo_dispute_window_minutes', 60))
    if not 0 <= fee_bps <= 10000 or not 0 <= dispute_minutes <= 10080:
        fail('Demonstration earnings policy configuration is invalid', 'financial_policy_invalid')
    policy = {'version': 'demo-full-release-before-start-v1',
              'cancel_before_start': 'full_simulated_reservation_release',
              'cancellation_cutoff': iso(start),
              'financial': {'version': 'demo-earnings-v1', 'fee_bps': fee_bps,
                            'dispute_window_minutes': dispute_minutes,
                            'external_settlement': False}}
    created = datetime.now(timezone.utc).replace(tzinfo=None)
    frappe.db.sql('''INSERT INTO tt_appointment (id,patient,clinician,offering,start,end,state,price,acquisition_source,minutes,
        service_label,disclosure,choices,retry_key,payload_hash,timezone,schedule_id,confirmation_mode,
        expires_at,confirmed_at,consultation_format,buffer_before,buffer_after,policy_snapshot,created)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
        (appointment, p.user, o.clinician, offering, start, end, state, booking_price,
         acquisition_source, o.minutes, o.label,
         json.dumps(shared), json.dumps(selected), key, digest, schedule_timezone,
         schedule.id if schedule else None, mode, expires, confirmed,
         schedule.consultation_format if schedule else 'video', before, after, json.dumps(policy), created))
    frappe.db.sql('''INSERT INTO tt_appointment_event (id,appointment,event_type,actor,created)
        VALUES (%s,%s,%s,%s,%s)''', (str(uuid.uuid4()), appointment,
        'Requested' if state == 'PendingConfirmation' else 'Booked', p.user, created))
    frappe.db.sql('UPDATE tt_wallet SET available=available-%s,reserved=reserved+%s WHERE patient=%s', (booking_price, booking_price, p.user))
    simulation_log(p.user, 'Reservation', booking_price, 'booking:' + appointment)
    post('booking:' + appointment, 'Reservation', 'booking:' + appointment, [
        (account_id('patient', p.user, 'available'), booking_price, 0),
        (account_id('patient', p.user, 'reserved'), 0, booking_price)], {'appointment': appointment})
    return {'id': appointment, 'state': state, 'expires_at': iso(expires) if expires else None,
            'simulated': True}


@query()
def wallet():
    p = profile('patient')
    w = one('SELECT available,reserved FROM tt_wallet WHERE patient=%s', (p.user,))
    return {**w, 'currency': 'ETB', 'simulated': True}


@query()
def appointments():
    user = actor()
    p = one('SELECT kind FROM tt_profile WHERE user=%s', (user,))
    profile(p.kind)
    field = 'patient' if p.kind == 'patient' else 'clinician'
    # Clinician never receives patient account identity, history or mutable profile.
    result = rows(f'''SELECT a.id,a.start,a.end,a.state,a.price,a.minutes,a.service_label,a.disclosure,a.choices,
        a.timezone,a.consultation_format,a.confirmation_mode,a.expires_at,a.confirmed_at,
        a.cancelled_by,a.cancelled_at,a.cancel_reason,a.policy_snapshot,
        c.state AS call_state,c.ended AS call_ended,n.status AS documentation_state
        FROM tt_appointment a LEFT JOIN tt_consultation c ON c.appointment=a.id
        LEFT JOIN tt_consultation_note n ON n.appointment=a.id
        WHERE a.{field}=%s ORDER BY a.start''', (user,))
    for appointment in result:
        appointment.start, appointment.end = iso(appointment.start), iso(appointment.end)
        appointment.disclosure = json.loads(appointment.disclosure)
        appointment.choices = json.loads(appointment.choices)
        appointment.cancelled_at = iso(appointment.cancelled_at) if appointment.cancelled_at else None
        appointment.call_ended = iso(appointment.call_ended) if appointment.call_ended else None
        appointment.expires_at = iso(appointment.expires_at) if appointment.expires_at else None
        appointment.confirmed_at = iso(appointment.confirmed_at) if appointment.confirmed_at else None
        appointment.policy_snapshot = json.loads(appointment.policy_snapshot) if appointment.policy_snapshot else None
        if p.kind == 'patient':
            identity = rows('SELECT display_name FROM tt_profile WHERE user=%s AND kind=%s',
                            (appointment.clinician, 'clinician'))
            appointment.display_identity = identity[0].display_name if identity else 'Your clinician'
        else:
            appointment.display_identity = appointment.disclosure.get('name') or 'Private patient'
    return result


def audit(subject, action, evidence):
    frappe.db.sql('INSERT INTO tt_audit (id,actor,subject,action,evidence,created) VALUES (%s,%s,%s,%s,%s,UTC_TIMESTAMP(6))',
                  (str(uuid.uuid4()), actor(), subject, action, json.dumps(evidence)))


@query()
def practice():
    """Owner-only practice summary; no cross-clinician clinical information."""
    user = actor()
    p = one('SELECT kind FROM tt_profile WHERE user=%s', (user,))
    if p.kind != 'clinician':
        frappe.throw('Clinician profile required', frappe.PermissionError)
    applications = rows('SELECT status,statement FROM tt_application WHERE user=%s', (user,))
    offerings = rows('''SELECT o.id,o.service,COALESCE(NULLIF(o.title,''),s.service_label) label,
        o.title,o.description,o.price,o.minutes,o.active,s.service_label service_label
        FROM tt_offering o JOIN `tabTele Tena Service` s ON s.name=o.service
        WHERE o.clinician=%s''', (user,))
    available = rows('SELECT start,end FROM tt_availability WHERE clinician=%s AND end>UTC_TIMESTAMP() ORDER BY start', (user,))
    from tele_tena.api.scheduling import schedules as clinician_schedules
    schedule_rows = clinician_schedules() if 'Tele Tena Clinician' in frappe.get_roles(user) else []
    return {'application': applications[0] if applications else None, 'offerings': offerings,
            'availability': [{'start': iso(row.start), 'end': iso(row.end)} for row in available],
            'schedules': schedule_rows}
