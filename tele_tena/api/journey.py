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


@query()
def session():
    user = actor()
    p = rows('SELECT * FROM tt_profile WHERE user=%s', (user,))
    return {'user': user, 'roles': frappe.get_roles(user), 'profile': p[0] if p else None,
            'csrf_token': get_csrf_token(), 'simulation': simulation_enabled()}


@command
def save_profile(kind, display_name, adult, history='', share_name=None, share_history=None):
    if kind not in ('patient', 'clinician'):
        fail('Unsupported profile type')
    user = actor('Tele Tena ' + kind.title())
    if not boolean(adult):
        fail('Adults 18+ only')
    existing = rows('SELECT kind,share_name,share_history FROM tt_profile WHERE user=%s FOR UPDATE', (user,))
    if existing and existing[0].kind != kind:
        fail('Profile type cannot change')
    share_name = existing[0].share_name if share_name is None and existing else (False if share_name is None else share_name)
    share_history = existing[0].share_history if share_history is None and existing else (False if share_history is None else share_history)
    name = text(display_name, 120)
    history = text(history, 4000, False) if kind == 'patient' else ''
    frappe.db.sql('''INSERT INTO tt_profile (user,kind,display_name,history,share_name,share_history)
        VALUES (%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE display_name=VALUES(display_name),
        history=VALUES(history),share_name=VALUES(share_name),share_history=VALUES(share_history)''',
        (user, kind, name, history, boolean(share_name), boolean(share_history)))
    if kind == 'patient':
        frappe.db.sql('INSERT IGNORE INTO tt_wallet (patient) VALUES (%s)', (user,))
    audit(user, 'ProfileConsent', {'adult_attested': True, 'share_name': boolean(share_name), 'share_history': boolean(share_history)})
    return {'saved': True}


@command
def apply(statement):
    p = profile('clinician', True)
    frappe.db.sql('''INSERT INTO tt_application (user,statement,status) VALUES (%s,%s,'Pending')
        ON DUPLICATE KEY UPDATE statement=VALUES(statement),status='Pending',reviewed_by=NULL,reviewed_at=NULL''',
        (p.user, text(statement, 2000)))
    audit(p.user, 'Application', {'statement': text(statement, 2000), 'status': 'Pending'})
    return {'status': 'Pending'}


@query()
def applications():
    user = actor()
    if 'Tele Tena Approver' in frappe.get_roles(user):
        return rows('SELECT a.*,p.display_name FROM tt_application a JOIN tt_profile p ON p.user=a.user')
    profile('clinician')
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
    audit(clinician, 'Review', {'status': decision})
    return {'status': decision}


@command
def save_service(service, label):
    actor('Tele Tena Approver')
    if not re.fullmatch(r'[a-z0-9-]{1,80}', service):
        fail('Invalid service identifier')
    if frappe.db.exists('Tele Tena Service', service):
        doc = frappe.get_doc('Tele Tena Service', service)
        doc.service_label, doc.active = text(label, 120), 1
        doc.save()
    else:
        frappe.get_doc(dict(doctype='Tele Tena Service', service_key=service,
                            service_label=text(label, 120), active=1)).insert()
    return {'saved': True}


@command
def review_service_scope(clinician, service, decision):
    actor('Tele Tena Approver')
    if decision not in ('Approved', 'Revoked'):
        fail('Invalid service scope decision')
    from tele_tena.backoffice import scope_name
    name = scope_name(clinician, service)
    if frappe.db.exists('Tele Tena Service Scope', name):
        doc = frappe.get_doc('Tele Tena Service Scope', name)
        doc.status = decision
        doc.save()
    else:
        frappe.get_doc(dict(doctype='Tele Tena Service Scope', clinician=clinician,
                            service=service, status=decision)).insert()
    return {'status': decision}


@query()
def service_scopes():
    actor('Tele Tena Approver')
    return frappe.get_list('Tele Tena Service Scope', fields=['clinician', 'service', 'status'])


def approved_service(clinician, service, lock=False):
    scopes = rows("SELECT name FROM `tabTele Tena Service Scope` WHERE clinician=%s AND service=%s AND status='Approved'" + (' FOR UPDATE' if lock else ''), (clinician, service))
    if not scopes:
        fail('Clinician is not approved for this service', 'service_scope_required')


@query()
def services():
    actor()
    return rows('SELECT name AS id,service_label AS label FROM `tabTele Tena Service` WHERE active=1 ORDER BY service_label')


@command
def publish(service, price, minutes):
    p = profile('clinician', True)
    approved(p.user, True)
    approved_service(p.user, service, True)
    one('SELECT name FROM `tabTele Tena Service` WHERE name=%s AND active=1', (service,))
    fee, duration = integer(price, 1, 100000000), integer(minutes, 5, 240)
    frappe.db.sql('''INSERT INTO tt_offering (id,clinician,service,price,minutes,active) VALUES (%s,%s,%s,%s,%s,1)
        ON DUPLICATE KEY UPDATE price=VALUES(price),minutes=VALUES(minutes),active=1''',
        (str(uuid.uuid4()), p.user, service, fee, duration))
    audit(p.user, 'Offering', {'service': service, 'price': fee, 'minutes': duration})
    return {'saved': True}


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
    return rows('''SELECT o.id,o.clinician,p.display_name,o.service,s.service_label AS label,o.price,o.minutes
        FROM tt_offering o JOIN tt_profile p ON p.user=o.clinician
        JOIN tt_application a ON a.user=o.clinician JOIN `tabTele Tena Service` s ON s.name=o.service
        JOIN tabUser u ON u.name=o.clinician
        WHERE a.status='Approved' AND o.active=1 AND s.active=1 AND u.enabled=1
        AND EXISTS (SELECT 1 FROM `tabTele Tena Service Scope` sc WHERE sc.clinician=o.clinician AND sc.service=o.service AND sc.status='Approved')
        AND EXISTS (SELECT 1 FROM `tabHas Role` r WHERE r.parent=o.clinician AND r.role='Tele Tena Clinician')
        AND (%s IS NULL OR o.service=%s) ORDER BY s.service_label,p.display_name''', (service or None, service or None))


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
    return frappe.local.site == 'erp.localhost' and bool(frappe.conf.get('tele_tena_simulation_enabled'))


@command
def simulated_deposit(amount, retry_key):
    p = profile('patient')
    if not simulation_enabled():
        frappe.throw('Development simulation disabled', frappe.PermissionError)
    amount = integer(amount, 1, 100000000)
    key = text(retry_key, 80)
    wallet = one('SELECT * FROM tt_wallet WHERE patient=%s FOR UPDATE', (p.user,))
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
    return {'simulated': True}


def simulation_log(patient, kind, amount, reference):
    frappe.db.sql('INSERT INTO tt_ledger (id,patient,kind,amount,reference,created) VALUES (%s,%s,%s,%s,%s,UTC_TIMESTAMP(6))',
                  (str(uuid.uuid4()), patient, kind, amount, reference))


@command
def book(offering, start, request_text, sharing, retry_key, expected_price, expected_minutes, expected_disclosure):
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
    payload = json.dumps([offering, iso(start), request_text, selected, expected_price, expected_minutes, expected_disclosure], sort_keys=True)
    digest = hashlib.sha256(payload.encode()).hexdigest()
    wallet = one('SELECT * FROM tt_wallet WHERE patient=%s FOR UPDATE', (p.user,))
    prior = rows('SELECT id,payload_hash FROM tt_appointment WHERE patient=%s AND retry_key=%s FOR UPDATE', (p.user, key))
    if prior:
        if prior[0].payload_hash != digest:
            fail('Retry key payload changed', 'retry_changed')
        return {'id': prior[0].id, 'simulated': True}
    shared = disclosure(p, request_text, selected)
    if expected_disclosure != shared:
        fail('Profile changed; review disclosure again', 'preview_changed')
    o = one('SELECT * FROM tt_offering WHERE id=%s AND active=1', (offering,))
    # All scheduling mutations acquire the clinician profile lock, across services.
    one('SELECT user FROM tt_profile WHERE user=%s AND kind=%s FOR UPDATE', (o.clinician, 'clinician'))
    approved(o.clinician, True)
    approved_service(o.clinician, o.service, True)
    o = one('SELECT o.*,s.service_label AS label FROM tt_offering o JOIN `tabTele Tena Service` s ON s.name=o.service WHERE o.id=%s AND o.active=1 AND s.active=1 FOR UPDATE', (offering,))
    if integer(expected_price, 1, 100000000) != o.price or integer(expected_minutes, 5, 240) != o.minutes:
        fail('Offering changed; review price and duration again', 'offering_changed')
    end = start + timedelta(minutes=o.minutes)
    if start <= datetime.now(timezone.utc).replace(tzinfo=None):
        fail('Appointment must be in the future', 'future_required')
    if not rows('SELECT id FROM tt_availability WHERE clinician=%s AND start<=%s AND end>=%s FOR UPDATE', (o.clinician, start, end)):
        fail('Outside availability', 'outside_availability')
    if rows('SELECT id FROM tt_appointment WHERE (clinician=%s OR patient=%s) AND start<%s AND end>%s FOR UPDATE', (o.clinician, p.user, end, start)):
        fail('Appointment conflict', 'appointment_conflict')
    if wallet.available < o.price:
        fail('Insufficient simulated funds', 'insufficient_funds')
    appointment = str(uuid.uuid4())
    frappe.db.sql('''INSERT INTO tt_appointment (id,patient,clinician,offering,start,end,state,price,minutes,
        service_label,disclosure,choices,retry_key,payload_hash) VALUES (%s,%s,%s,%s,%s,%s,'Booked',%s,%s,%s,%s,%s,%s,%s)''',
        (appointment, p.user, o.clinician, offering, start, end, o.price, o.minutes, o.label,
         json.dumps(shared), json.dumps(selected), key, digest))
    frappe.db.sql('UPDATE tt_wallet SET available=available-%s,reserved=reserved+%s WHERE patient=%s', (o.price, o.price, p.user))
    simulation_log(p.user, 'Reservation', o.price, 'booking:' + appointment)
    return {'id': appointment, 'simulated': True}


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
    result = rows(f'''SELECT id,start,end,state,price,minutes,service_label,disclosure,choices
        FROM tt_appointment WHERE {field}=%s ORDER BY start''', (user,))
    for appointment in result:
        appointment.start, appointment.end = iso(appointment.start), iso(appointment.end)
        appointment.disclosure = json.loads(appointment.disclosure)
        appointment.choices = json.loads(appointment.choices)
    return result


def audit(subject, action, evidence):
    frappe.db.sql('INSERT INTO tt_audit (id,actor,subject,action,evidence,created) VALUES (%s,%s,%s,%s,%s,UTC_TIMESTAMP(6))',
                  (str(uuid.uuid4()), actor(), subject, action, json.dumps(evidence)))
