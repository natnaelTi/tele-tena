"""Private, bounded open-request delivery and patient-only offer acceptance."""
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone

import frappe
from tele_tena.api import journey
from tele_tena.api.journey import actor, approved, approved_service, fail, integer, one, profile, query, rows, text

LANGUAGES = {'en', 'am', 'om'}
FORMATS = {'audio', 'video'}
DEFAULT_PRESENCE_SECONDS = 90
DEFAULT_REQUEST_MINUTES = 15
DEFAULT_OFFER_MINUTES = 15
MAX_RECIPIENTS = 10
MAX_OFFERS = 10


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def timestamp(value, required=True):
    if not value and not required:
        return None
    return journey.instant(value)


def metric(request_id, event, eligible_supply=None, external_event_id=None, occurred_at=None):
    frappe.db.sql('''INSERT IGNORE INTO tt_request_metric
        (id,request_id,event,occurred_at,eligible_supply,external_event_id)
        VALUES (%s,%s,%s,COALESCE(%s,UTC_TIMESTAMP(6)),%s,%s)''',
        (str(uuid.uuid4()), request_id, event, occurred_at, eligible_supply, external_event_id))


def clinician_languages(user):
    row = one('SELECT languages FROM tt_profile WHERE user=%s', (user,))
    try:
        values = json.loads(row.languages or '[]')
    except (TypeError, ValueError):
        values = []
    return set(values) if isinstance(values, list) else set()


def _eligible(request, exclude_delivered=True, limit=None):
    """Deterministic eligibility. Never returns patient identities to clinicians."""
    presence = request.urgency == 'immediate'
    candidates = rows('''SELECT DISTINCT o.clinician,o.id offering,s.id schedule,
        s.timezone,s.consultation_format,p.languages,
        COALESCE(pr.expires_at,'1970-01-01') presence_until
        FROM tt_offering o
        JOIN tt_profile p ON p.user=o.clinician AND p.kind='clinician'
        JOIN tt_application a ON a.user=o.clinician AND a.status='Approved'
        JOIN tabUser u ON u.name=o.clinician AND u.enabled=1
        JOIN `tabHas Role` hr ON hr.parent=o.clinician AND hr.role='Tele Tena Clinician'
        JOIN `tabTele Tena Service Scope` sc ON sc.clinician=o.clinician
            AND sc.service=o.service AND sc.status='Approved'
        JOIN tt_schedule s ON s.offering=o.id AND s.status='Published'
        LEFT JOIN tt_clinician_request_presence pr ON pr.clinician=o.clinician
        WHERE o.active=1 AND o.service=%s AND s.consultation_format=%s
        AND (%s=0 OR (pr.ready=1 AND pr.expires_at>UTC_TIMESTAMP(6)))
        AND (%s=0 OR NOT EXISTS (SELECT 1 FROM tt_request_recipient rr
            WHERE rr.request_id=%s AND rr.clinician=o.clinician))
        ORDER BY presence_until DESC,o.clinician,o.id''',
        (request.service, request.consultation_format, 1 if presence else 0,
         1 if exclude_delivered else 0, request.id))
    result = []
    for item in candidates:
        try:
            languages = json.loads(item.languages or '[]')
        except (TypeError, ValueError):
            languages = []
        if request.language not in languages:
            continue
        if presence:
            ready = one('SELECT expires_at FROM tt_clinician_request_presence WHERE clinician=%s AND ready=1',
                        (item.clinician,))
            if ready.expires_at <= now():
                continue
        if not _has_slot(item, request):
            continue
        result.append(item)
        if limit is not None and len(result) >= limit:
            break
    return result


def _has_slot(candidate, request):
    """Check the request range against generated or continuous immediate time."""
    from tele_tena.api import scheduling
    from zoneinfo import ZoneInfo
    schedule = scheduling._schedule_for(candidate.offering)
    if not schedule or schedule.status != 'Published':
        return False
    offer = one('SELECT * FROM tt_offering WHERE id=%s AND active=1', (candidate.offering,))
    if request.urgency == 'immediate':
        return scheduling.immediate_start(schedule, offer, candidate.clinician, request.patient,
                                          request.earliest_start, request.latest_start) is not None
    zone = ZoneInfo(schedule.timezone)
    first_day = request.earliest_start.replace(tzinfo=timezone.utc).astimezone(zone).date()
    last_day = request.latest_start.replace(tzinfo=timezone.utc).astimezone(zone).date()
    booked = rows('''SELECT start,end,buffer_before,buffer_after FROM tt_appointment
        WHERE clinician=%s AND state IN ('Booked','PendingConfirmation')
        AND (expires_at IS NULL OR expires_at>UTC_TIMESTAMP(6))
        AND start<%s AND end>%s''',
        (candidate.clinician, request.latest_start + timedelta(days=1),
         request.earliest_start - timedelta(days=1)))
    patient_booked = rows('''SELECT start,end FROM tt_appointment WHERE patient=%s
        AND state IN ('Booked','PendingConfirmation')
        AND (expires_at IS NULL OR expires_at>UTC_TIMESTAMP(6))
        AND start<%s AND end>%s''',
        (request.patient, request.latest_start + timedelta(days=1),
         request.earliest_start - timedelta(days=1)))
    day = first_day
    while day <= last_day:
        for start_at, _end_at, _local in scheduling._slots_for_day(
                schedule, offer, day, booked, patient_booked):
            if request.earliest_start <= start_at <= request.latest_start:
                return True
        day += timedelta(days=1)
    return False


def _deliver(request, candidates=None):
    delivered = int(one('SELECT COUNT(*) n FROM tt_request_recipient WHERE request_id=%s',
                        (request.id,)).n)
    remaining = MAX_RECIPIENTS - delivered
    if remaining <= 0:
        return 0, delivered
    candidates = candidates if candidates is not None else _eligible(request, limit=remaining)
    added = 0
    for item in candidates[:remaining]:
        already = rows('SELECT clinician FROM tt_request_recipient WHERE request_id=%s AND clinician=%s',
                       (request.id, item.clinician))
        if already:
            continue
        frappe.db.sql('''INSERT IGNORE INTO tt_request_recipient
            (request_id,clinician,notified_at,delivered_round) VALUES (%s,%s,UTC_TIMESTAMP(6),1)''',
            (request.id, item.clinician))
        added += 1
    if added:
        metric(request.id, 'FirstEligibleNotified' if not delivered else 'EligibleNotified', delivered + added)
        frappe.db.sql('''UPDATE tt_open_request SET first_notice_at=COALESCE(first_notice_at,UTC_TIMESTAMP(6))
            WHERE id=%s''', (request.id,))
    return added, delivered + added


@journey.command
def set_request_presence(ready):
    clinician = actor('Tele Tena Clinician')
    if not journey.boolean(ready):
        ready = False
    else:
        ready = True
    approved(clinician, lock=True)
    p = profile('clinician', lock=True)
    if ready:
        languages = clinician_languages(clinician)
        if not languages.intersection(LANGUAGES):
            fail('Choose at least one language you can provide care in before becoming available for requests',
                 'request_languages_required')
        active = rows('''SELECT o.id FROM tt_offering o JOIN `tabTele Tena Service Scope` sc
            ON sc.clinician=o.clinician AND sc.service=o.service AND sc.status='Approved'
            JOIN tt_schedule s ON s.offering=o.id AND s.status='Published'
            WHERE o.clinician=%s AND o.active=1 LIMIT 1''', (clinician,))
        if not active:
            fail('Publish an approved service schedule before becoming available for requests',
                 'request_schedule_required')
    ttl = int(frappe.conf.get('tele_tena_request_presence_ttl_seconds', DEFAULT_PRESENCE_SECONDS))
    ttl = max(30, min(300, ttl))
    expires = now() + timedelta(seconds=ttl)
    frappe.db.sql('''INSERT INTO tt_clinician_request_presence (clinician,ready,heartbeat_at,expires_at)
        VALUES (%s,%s,UTC_TIMESTAMP(6),%s) ON DUPLICATE KEY UPDATE ready=VALUES(ready),
        heartbeat_at=VALUES(heartbeat_at),expires_at=VALUES(expires_at)''',
        (clinician, 1 if ready else 0, expires))
    if ready:
        dispatch_open_requests()
    return {'ready': ready, 'expires_at': expires.isoformat() + 'Z', 'ttl_seconds': ttl}


@journey.command
def publish_request(service, request_text, urgency, language, consultation_format,
                    sharing, retry_key, timezone_name='Africa/Addis_Ababa',
                    earliest_start=None, latest_start=None, max_price_minor=None):
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    patient = profile('patient', lock=True)
    if urgency not in ('immediate', 'scheduled') or language not in LANGUAGES or consultation_format not in FORMATS:
        fail('Choose when you need care, a language and a session format')
    service_row = one('SELECT name FROM `tabTele Tena Service` WHERE name=%s AND active=1', (service,))
    del service_row
    content = text(request_text, 2000)
    selected = journey.choices(sharing)
    key = text(retry_key, 80)
    try:
        from zoneinfo import ZoneInfo
        zone = ZoneInfo(timezone_name)
    except Exception:
        fail('Choose a valid timezone', 'request_timezone_invalid')
    current = now()
    if urgency == 'immediate':
        earliest = current
        immediate_minutes = int(frappe.conf.get('tele_tena_immediate_window_minutes', 30))
        latest = current + timedelta(minutes=max(5, min(60, immediate_minutes)))
    else:
        earliest = timestamp(earliest_start)
        latest = timestamp(latest_start)
        if earliest < current or latest < earliest or latest - earliest > timedelta(days=90):
            fail('Choose a future range of up to 90 days', 'request_time_range_invalid')
    maximum = None if max_price_minor in (None, '') else integer(max_price_minor, 1, 100000000)
    # Immediate time bounds are generated server-side. Excluding those moving
    # values keeps a retry after a lost response idempotent for the same user
    # payload. The persisted request still keeps its original exact bounds.
    payload = {'service': service, 'text': content, 'urgency': urgency, 'language': language,
               'format': consultation_format, 'sharing': selected, 'timezone': zone.key,
               'earliest': earliest.isoformat() if urgency == 'scheduled' else 'immediate',
               'latest': latest.isoformat() if urgency == 'scheduled' else 'immediate',
               'maximum': maximum}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    prior = rows('SELECT id,payload_hash,state FROM tt_open_request WHERE patient=%s AND retry_key=%s FOR UPDATE',
                 (patient.user, key))
    if prior:
        if prior[0].payload_hash != digest:
            fail('Request retry details changed', 'request_retry_changed')
        return {'id': prior[0].id, 'state': prior[0].state, 'idempotent': True}
    disclosed = journey.disclosure(patient, content, selected)
    active = int(one("SELECT COUNT(*) n FROM tt_open_request WHERE patient=%s AND state='Open' AND expires_at>UTC_TIMESTAMP(6)",
                      (patient.user,)).n)
    if active >= int(frappe.conf.get('tele_tena_max_active_requests', 3)):
        fail('You already have several open requests. Close one before starting another.', 'request_active_limit')
    sent = int(one('''SELECT COUNT(*) n FROM tt_open_request WHERE patient=%s
        AND published_at>UTC_TIMESTAMP(6)-INTERVAL 1 HOUR''', (patient.user,)).n)
    if sent >= int(frappe.conf.get('tele_tena_request_hourly_limit', 5)):
        fail('Please wait before publishing another request.', 'request_rate_limit')
    req_id = str(uuid.uuid4())
    expiry_minutes = int(frappe.conf.get('tele_tena_request_expiry_minutes', DEFAULT_REQUEST_MINUTES))
    expiry_minutes = max(5, min(60, expiry_minutes))
    expiry = current + timedelta(minutes=expiry_minutes)
    frappe.db.sql('''INSERT INTO tt_open_request
        (id,patient,state,urgency,service,language,consultation_format,request_text,
         disclosure_snapshot,max_price_minor,earliest_start,latest_start,timezone,retry_key,
         payload_hash,sharing_choices,published_at,expires_at)
        VALUES (%s,%s,'Open',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
        (req_id, patient.user, urgency, service, language, consultation_format, content,
         json.dumps(disclosed, separators=(',', ':'), sort_keys=True), maximum, earliest, latest,
         zone.key, key, digest, json.dumps(selected, separators=(',', ':'), sort_keys=True), current, expiry))
    req = one('SELECT * FROM tt_open_request WHERE id=%s', (req_id,))
    # Count the full eligible supply at publication; _deliver still sends to
    # only the bounded first wave and expands later through the scheduler.
    candidates = _eligible(req)
    metric(req_id, 'Published', len(candidates))
    _deliver(req, candidates)
    return {'id': req_id, 'state': 'Open', 'expires_at': expiry.isoformat() + 'Z',
            'eligible_supply': len(candidates), 'notified': min(len(candidates), MAX_RECIPIENTS)}


@query()
def my_requests():
    patient = profile('patient')
    requests = rows('''SELECT r.id,r.state,r.urgency,r.service,s.service_label AS category,
        r.language,r.consultation_format,r.request_text,r.disclosure_snapshot,r.max_price_minor,
        r.earliest_start,r.latest_start,r.timezone,r.published_at,r.expires_at,r.appointment,
        r.first_notice_at,r.first_offer_at,r.matched_at
        FROM tt_open_request r JOIN `tabTele Tena Service` s ON s.name=r.service
        WHERE r.patient=%s ORDER BY r.published_at DESC LIMIT 30''', (patient.user,))
    for req in requests:
        offers = rows('''SELECT o.id,o.start,o.duration_minutes,o.consultation_format,o.price_minor,o.timezone,
            o.price_source,o.state,o.valid_until,p.display_name clinician_name,p.public_id clinician_id,
            s.service_label specialty
            FROM tt_request_offer o JOIN tt_profile p ON p.user=o.clinician
            JOIN tt_offering off ON off.id=o.offering
            JOIN `tabTele Tena Service` s ON s.name=off.service WHERE o.request_id=%s
            ORDER BY o.created_at DESC''', (req.id,))
        for offer in offers:
            offer.start = offer.start.isoformat() + 'Z'
            offer.valid_until = offer.valid_until.isoformat() + 'Z'
        req.offers = offers
        req.published_at = req.published_at.isoformat() + 'Z'
        req.expires_at = req.expires_at.isoformat() + 'Z'
        for field in ('earliest_start','latest_start','first_notice_at','first_offer_at','matched_at'):
            if req.get(field):
                req[field] = req[field].isoformat() + 'Z'
        req.disclosure_snapshot = json.loads(req.disclosure_snapshot)
    return requests


@query()
def clinician_profile(clinician_id):
    """Patient-facing approved clinician profile addressed only by opaque ID."""
    actor('Tele Tena Patient')
    if not isinstance(clinician_id, str) or len(clinician_id) != 36:
        fail('Clinician profile unavailable', 'clinician_profile_unavailable')
    clinician = rows('''SELECT p.user,p.display_name FROM tt_profile p
        JOIN tt_application a ON a.user=p.user AND a.status='Approved'
        JOIN `tabHas Role` r ON r.parent=p.user AND r.role='Tele Tena Clinician'
        JOIN tabUser u ON u.name=p.user AND u.enabled=1
        WHERE p.public_id=%s AND p.kind='clinician' LIMIT 1''', (clinician_id,))
    if not clinician:
        fail('Clinician profile unavailable', 'clinician_profile_unavailable')
    clinician = clinician[0]
    services = rows('''SELECT o.id offering,s.service_label label,o.price,o.minutes,schedule.consultation_format,
        schedule.timezone FROM tt_offering o
        JOIN `tabTele Tena Service Scope` scope ON scope.clinician=o.clinician
            AND scope.service=o.service AND scope.status='Approved'
        JOIN `tabTele Tena Service` s ON s.name=o.service AND s.active=1
        JOIN tt_schedule schedule ON schedule.offering=o.id AND schedule.status='Published'
        WHERE o.clinician=%s AND o.active=1 ORDER BY s.service_label''', (clinician.user,))
    return {'display_name': clinician.display_name, 'services': services,
            'approval_meaning': 'Application and listed service scopes are manually approved.'}


@query()
def clinician_requests():
    clinician = actor('Tele Tena Clinician')
    profile('clinician')
    result = rows('''SELECT r.id,r.urgency,r.language,r.consultation_format,r.request_text,
        r.disclosure_snapshot,r.max_price_minor,r.earliest_start,r.latest_start,r.timezone,
        r.expires_at,s.service_label category,rr.notified_at,own.id own_offer_id,
        own.start own_offer_start,own.price_minor own_offer_price,own.valid_until own_offer_until
        FROM tt_request_recipient rr JOIN tt_open_request r ON r.id=rr.request_id
        JOIN `tabTele Tena Service` s ON s.name=r.service
        LEFT JOIN tt_request_offer own ON own.request_id=r.id AND own.clinician=rr.clinician AND own.state='Active'
        WHERE rr.clinician=%s AND r.state='Open' AND r.expires_at>UTC_TIMESTAMP(6)
        ORDER BY r.urgency='immediate' DESC,rr.notified_at LIMIT 30''', (clinician,))
    for req in result:
        req.disclosure_snapshot = json.loads(req.disclosure_snapshot)
        req.suggested_start = None
        if req.urgency == 'immediate':
            offerings = rows('''SELECT o.id FROM tt_offering o
                JOIN `tabTele Tena Service Scope` sc ON sc.clinician=o.clinician
                    AND sc.service=o.service AND sc.status='Approved'
                JOIN tt_schedule s ON s.offering=o.id AND s.status='Published'
                WHERE o.clinician=%s AND o.service=%s AND o.active=1
                    AND s.consultation_format=%s ORDER BY o.id''',
                (clinician, req.service, req.consultation_format))
            from tele_tena.api import scheduling
            for offering_row in offerings:
                schedule = scheduling._schedule_for(offering_row.id)
                offer = one('SELECT * FROM tt_offering WHERE id=%s AND active=1', (offering_row.id,))
                feasible = scheduling.immediate_start(schedule, offer, clinician, req.patient,
                    req.earliest_start, req.latest_start)
                if feasible:
                    req.suggested_start = feasible.isoformat(timespec='seconds') + 'Z'
                    req.suggested_timezone = schedule.timezone
                    break
        for field in ('earliest_start','latest_start','expires_at','notified_at','own_offer_start','own_offer_until'):
            if req.get(field):
                req[field] = req[field].isoformat() + 'Z'
    return result


@query()
def request_presence():
    clinician = actor('Tele Tena Clinician')
    profile('clinician')
    row = rows('SELECT ready,expires_at FROM tt_clinician_request_presence WHERE clinician=%s', (clinician,))
    return {'ready': bool(row and row[0].ready and row[0].expires_at > now()),
            'expires_at': row[0].expires_at.isoformat() + 'Z' if row else None}


@journey.command
def submit_offer(request_id, offering, start, price_minor=None):
    clinician = actor('Tele Tena Clinician')
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    approved(clinician, lock=True)
    profile('clinician', lock=True)
    req = one("SELECT * FROM tt_open_request WHERE id=%s AND state='Open' AND expires_at>UTC_TIMESTAMP(6) FOR UPDATE",
              (request_id,))
    recipient = rows('SELECT clinician FROM tt_request_recipient WHERE request_id=%s AND clinician=%s FOR UPDATE',
                     (request_id, clinician))
    if not recipient:
        frappe.throw('Request unavailable', frappe.PermissionError)
    start_at = timestamp(start)
    requested_price = None if price_minor in (None, '') else integer(price_minor, 1, 100000000)
    existing = rows("""SELECT * FROM tt_request_offer WHERE request_id=%s AND clinician=%s
        AND state='Active' AND valid_until>UTC_TIMESTAMP(6) FOR UPDATE""", (request_id, clinician))
    if existing and existing[0].offering == offering and existing[0].start == start_at \
            and ((requested_price is None and existing[0].price_source == 'published')
                 or int(existing[0].price_minor) == requested_price):
        return {'id': existing[0].id, 'state': 'Active', 'idempotent': True,
                'valid_until': existing[0].valid_until.isoformat() + 'Z'}
    if existing:
        fail('Withdraw your current offer before sending another.', 'request_offer_exists')
    approved(clinician, lock=True)
    profile('clinician', lock=True)
    if req.urgency == 'immediate':
        present = one('SELECT expires_at FROM tt_clinician_request_presence WHERE clinician=%s AND ready=1 FOR UPDATE',
                      (clinician,))
        if present.expires_at <= now():
            fail('Your available-now status has expired. Turn it on again before offering.', 'request_presence_stale')
    offer = one('''SELECT o.*,s.consultation_format,s.timezone,s.status FROM tt_offering o
        JOIN tt_schedule s ON s.offering=o.id WHERE o.id=%s AND o.clinician=%s AND o.active=1 FOR UPDATE''',
        (offering, clinician))
    approved_service(clinician, offer.service, True)
    if offer.service != req.service or offer.consultation_format != req.consultation_format or req.language not in clinician_languages(clinician):
        fail('This request no longer matches your approved service, language or format.', 'request_eligibility_changed')
    if start_at < req.earliest_start or start_at > req.latest_start:
        fail('Choose a start time within the patient’s requested range.', 'request_time_invalid')
    price = int(offer.price) if requested_price is None else requested_price
    if req.max_price_minor is not None and price > int(req.max_price_minor):
        fail('Your quote exceeds the patient’s stated price limit.', 'request_price_limit')
    total = int(one("SELECT COUNT(*) n FROM tt_request_offer WHERE request_id=%s", (request_id,)).n)
    if total >= MAX_OFFERS:
        fail('This request has reached its response limit.', 'request_offer_limit')
    from tele_tena.api import scheduling
    scheduling.validate_slot(offer, start_at, req.patient, lock=True,
                             immediate_ready=req.urgency == 'immediate',
                             immediate_window=(req.earliest_start, req.latest_start)
                             if req.urgency == 'immediate' else None)
    offer_id = str(uuid.uuid4())
    valid_minutes = int(frappe.conf.get('tele_tena_offer_expiry_minutes', DEFAULT_OFFER_MINUTES))
    valid_until = min(req.expires_at, now() + timedelta(minutes=max(2, min(60, valid_minutes))))
    source = 'published' if price == int(offer.price) else 'custom'
    frappe.db.sql('''INSERT INTO tt_request_offer
        (id,request_id,clinician,offering,start,duration_minutes,consultation_format,
         price_minor,price_source,state,valid_until,created_at,timezone)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'Active',%s,UTC_TIMESTAMP(6),%s)''',
        (offer_id, request_id, clinician, offering, start_at, offer.minutes, offer.consultation_format,
         price, source, valid_until, offer.timezone))
    # submit_offer holds the request row lock, so only the first accepted
    # offer submission records this milestone even under concurrent offers.
    if not req.first_offer_at:
        frappe.db.sql('''UPDATE tt_open_request SET first_offer_at=UTC_TIMESTAMP(6)
            WHERE id=%s AND first_offer_at IS NULL''', (request_id,))
        metric(request_id, 'FirstOffer')
    return {'id': offer_id, 'state': 'Active', 'valid_until': valid_until.isoformat() + 'Z'}


@journey.command
def respond_offer(request_id, offer_id, decision, sharing=None, expected_disclosure=None):
    patient = actor('Tele Tena Patient')
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    req = one('SELECT * FROM tt_open_request WHERE id=%s AND patient=%s FOR UPDATE', (request_id, patient))
    item = one('SELECT * FROM tt_request_offer WHERE id=%s AND request_id=%s FOR UPDATE', (offer_id, request_id))
    if item.state != 'Active':
        result = {'state': item.state, 'idempotent': True}
        if item.appointment:
            result['appointment'] = item.appointment
        return result
    if decision == 'decline':
        frappe.db.sql("UPDATE tt_request_offer SET state='Declined' WHERE id=%s", (offer_id,))
        return {'state': 'Declined'}
    if decision != 'accept' or req.state != 'Open' or req.expires_at <= now() or item.valid_until <= now():
        fail('This offer is no longer available. Choose another or browse clinicians.', 'request_offer_expired')
    # Eligibility is rechecked at acceptance, after acquiring the global booking
    # lock shared with direct bookings and all other offer acceptances.
    approved(item.clinician, lock=True)
    approved_service(item.clinician, req.service, True)
    recipient = rows('SELECT 1 FROM tt_request_recipient WHERE request_id=%s AND clinician=%s',
                     (request_id, item.clinician))
    if not recipient or req.language not in clinician_languages(item.clinician):
        fail('This clinician is no longer eligible for the request.', 'request_eligibility_changed')
    if req.urgency == 'immediate':
        present = rows('SELECT expires_at FROM tt_clinician_request_presence WHERE clinician=%s AND ready=1 FOR UPDATE',
                       (item.clinician,))
        if not present or present[0].expires_at <= now():
            fail('This clinician is no longer available for an immediate request.', 'request_presence_stale')
    from tele_tena.api import scheduling
    off = one('SELECT * FROM tt_offering WHERE id=%s AND clinician=%s AND active=1 FOR UPDATE',
              (item.offering, item.clinician))
    schedule = scheduling.validate_slot(off, item.start, patient, lock=True,
                                        immediate_ready=req.urgency == 'immediate',
                                        immediate_window=(req.earliest_start, req.latest_start)
                                        if req.urgency == 'immediate' else None)
    if not schedule:
        fail('That time is no longer available. Choose another offer.', 'appointment_conflict')
    if int(off.minutes) != int(item.duration_minutes) or schedule.consultation_format != item.consultation_format:
        fail('The offered service changed. Ask for another offer.', 'request_offer_changed')
    if item.price_source == 'published' and int(off.price) != int(item.price_minor):
        fail('The published price changed. Ask for a new offer.', 'request_offer_changed')
    if req.max_price_minor is not None and int(item.price_minor) > int(req.max_price_minor):
        fail('The offer price is no longer valid.', 'request_offer_changed')
    selected = json.loads(req.sharing_choices)
    expected = json.loads(req.disclosure_snapshot)
    if isinstance(expected_disclosure, str):
        expected_disclosure = json.loads(expected_disclosure)
    if expected_disclosure != expected:
        fail('Your disclosure changed. Review what will be shared before accepting.', 'request_disclosure_changed')
    key = 'open-request:' + req.id
    frappe.local.tele_tena_accepting_offer = item.id
    frappe.local.tele_tena_offer_disclosure = expected
    try:
        booking = journey.book(item.offering, item.start.isoformat(timespec='seconds') + 'Z', req.request_text,
                               json.dumps(selected), key, int(item.price_minor),
                               int(item.duration_minutes), json.dumps(expected), req.timezone,
                               custom_offer_id=item.id)
    finally:
        frappe.local.tele_tena_accepting_offer = None
        frappe.local.tele_tena_offer_disclosure = None
    appt = booking['id']
    frappe.db.sql("UPDATE tt_request_offer SET state='Accepted',appointment=%s WHERE id=%s", (appt, offer_id))
    frappe.db.sql("UPDATE tt_request_offer SET state='Superseded' WHERE request_id=%s AND id<>%s AND state='Active'",
                  (request_id, offer_id))
    frappe.db.sql("UPDATE tt_open_request SET state='Matched',appointment=%s,matched_at=UTC_TIMESTAMP(6) WHERE id=%s",
                  (appt, request_id))
    metric(request_id, 'AppointmentCreated')
    return {'state': 'Matched', 'appointment': appt, 'simulated': True}


@journey.command
def close_request(request_id, reason='cancelled'):
    patient = actor('Tele Tena Patient')
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    req = one('SELECT * FROM tt_open_request WHERE id=%s AND patient=%s FOR UPDATE', (request_id, patient))
    if req.state in ('Cancelled', 'Expired'):
        return {'state': req.state, 'idempotent': True}
    if req.state != 'Open':
        fail('A matched request cannot be cancelled here.', 'request_already_matched')
    frappe.db.sql("UPDATE tt_open_request SET state='Cancelled' WHERE id=%s", (request_id,))
    frappe.db.sql("UPDATE tt_request_offer SET state='Superseded' WHERE request_id=%s AND state='Active'", (request_id,))
    metric(request_id, 'Cancelled')
    return {'state': 'Cancelled'}


@journey.command
def withdraw_offer(offer_id):
    clinician = actor('Tele Tena Clinician')
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    item = rows('SELECT * FROM tt_request_offer WHERE id=%s AND clinician=%s FOR UPDATE',
                (offer_id, clinician))
    if not item:
        frappe.throw('Offer unavailable', frappe.PermissionError)
    offer = item[0]
    if offer.state == 'Withdrawn':
        return {'state': 'Withdrawn', 'idempotent': True}
    if offer.state != 'Active':
        fail('This offer can no longer be withdrawn.', 'request_offer_closed')
    frappe.db.sql("UPDATE tt_request_offer SET state='Withdrawn' WHERE id=%s", (offer_id,))
    return {'state': 'Withdrawn'}


def dispatch_open_requests():
    """Bounded minute-level delivery. No request body enters a notification."""
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    candidates = rows("SELECT id FROM tt_open_request WHERE state='Open' AND expires_at>UTC_TIMESTAMP(6) ORDER BY published_at LIMIT 100")
    for candidate in candidates:
        req = rows('SELECT * FROM tt_open_request WHERE id=%s', (candidate.id,))
        if req:
            try:
                _deliver(req[0])
            except Exception:
                frappe.log_error(message='A private request inbox delivery attempt could not be completed.',
                                 title='TeleTena request delivery failed')


def expire_requests():
    """Close stale requests/offers and deliver bounded inbox notifications."""
    dispatch_open_requests()
    frappe.db.sql("UPDATE tt_request_offer SET state='Expired' WHERE state='Active' AND valid_until<=UTC_TIMESTAMP(6)")
    expired = rows("SELECT id FROM tt_open_request WHERE state='Open' AND expires_at<=UTC_TIMESTAMP(6) ORDER BY expires_at LIMIT 100")
    for req in expired:
        frappe.db.sql("UPDATE tt_open_request SET state='Expired' WHERE id=%s AND state='Open'", (req.id,))
        frappe.db.sql("UPDATE tt_request_offer SET state='Expired' WHERE request_id=%s AND state='Active'", (req.id,))
        metric(req.id, 'Expired')
    frappe.db.sql("UPDATE tt_clinician_request_presence SET ready=0 WHERE ready=1 AND expires_at<=UTC_TIMESTAMP(6)")


@query()
def request_metrics():
    actor('Tele Tena Approver')
    from statistics import median
    requests = rows('''SELECT id,state,urgency,published_at,matched_at FROM tt_open_request
        WHERE published_at>=UTC_TIMESTAMP(6)-INTERVAL 90 DAY ORDER BY published_at''')
    def percentile(values, p):
        if not values:
            return None
        values = sorted(values)
        return values[min(len(values)-1, max(0, int((len(values)-1)*p + 0.999999)))]
    immediate = [req for req in requests if req.urgency == 'immediate']
    first_offer, confirmed, both_joined = [], [], []
    counts = {'matched': 0, 'unmatched': 0, 'expired': 0, 'cancelled': 0, 'open': 0,
              'failed_acceptance': 0, 'matched_under_3_minutes': 0, 'eligible_supply_total': 0}
    for req in immediate:
        supply = rows("SELECT eligible_supply FROM tt_request_metric WHERE request_id=%s AND event='Published' LIMIT 1", (req.id,))
        counts['eligible_supply_total'] += int(supply[0].eligible_supply or 0) if supply else 0
        metrics = rows('SELECT event,occurred_at FROM tt_request_metric WHERE request_id=%s', (req.id,))
        events = {item.event: item.occurred_at for item in metrics}
        if 'FirstOffer' in events:
            first_offer.append(int((events['FirstOffer'] - req.published_at).total_seconds()))
        if req.state == 'Matched' and req.matched_at:
            counts['matched'] += 1
            delay = int((req.matched_at - req.published_at).total_seconds())
            confirmed.append(delay)
            if delay <= 180:
                counts['matched_under_3_minutes'] += 1
        elif req.state == 'Expired':
            counts['expired'] += 1
        elif req.state == 'Cancelled':
            counts['cancelled'] += 1
        elif req.state == 'Open':
            counts['open'] += 1
        if any(item.event == 'AcceptFailed' for item in metrics):
            counts['failed_acceptance'] += 1
        if 'ParticipantJoinedPatient' in events and 'ParticipantJoinedClinician' in events:
            both_joined.append(int((max(events['ParticipantJoinedPatient'], events['ParticipantJoinedClinician']) - req.published_at).total_seconds()))
    denominator = len(immediate)
    counts['unmatched'] = counts['expired'] + counts['cancelled'] + counts['open']
    counts['immediate_total'] = denominator
    counts['average_eligible_supply'] = counts['eligible_supply_total'] / denominator if denominator else None
    counts['matched_within_3_minutes_percent'] = round(counts['matched_under_3_minutes'] * 100 / denominator, 2) if denominator else None
    return {'synthetic_demo_only': True, 'period_days': 90,
            'immediate_outcomes': counts,
            'seconds_to_first_offer': {'median': median(first_offer) if first_offer else None, 'p90': percentile(first_offer,.9)},
            'seconds_to_confirmed_match': {'median': median(confirmed) if confirmed else None, 'p90': percentile(confirmed,.9)},
            'seconds_until_both_participants_join': {'median': median(both_joined) if both_joined else None, 'p90': percentile(both_joined,.9)},
            'scheduled_requests': len([req for req in requests if req.urgency == 'scheduled'])}


@journey.command
def record_accept_failure(request_id, offer_id, attempt_key, reason):
    patient = profile('patient')
    key = text(attempt_key, 80)
    allowed = {'insufficient_funds', 'appointment_conflict', 'request_offer_expired',
               'request_eligibility_changed', 'request_presence_stale', 'request_offer_changed'}
    if reason not in allowed:
        reason = 'other_supported_failure'
    req = rows("SELECT id FROM tt_open_request WHERE id=%s AND patient=%s AND state='Open'",
               (request_id, patient.user))
    offer = rows("SELECT id FROM tt_request_offer WHERE id=%s AND request_id=%s", (offer_id, request_id))
    if not req or not offer:
        frappe.throw('Request unavailable', frappe.PermissionError)
    metric(request_id, 'AcceptFailed',
           external_event_id='accept-failure:' + request_id + ':' + key)
    return {'recorded': True}


@frappe.whitelist(allow_guest=True, methods=['POST'])
def livekit_webhook():
    """Accept signed LiveKit participant events; never log raw payloads or identities."""
    try:
        body = frappe.request.get_data(as_text=True)
        auth = frappe.request.headers.get('Authorization', '')
        _url, key, secret = __import__('tele_tena.livekit', fromlist=['_credentials'])._credentials()
        from livekit import api
        receiver = api.WebhookReceiver(api.TokenVerifier(key, secret))
        event = receiver.receive(body, auth)
        if event.event not in ('participant_joined', 'participant_left'):
            return {'received': True}
        room_name = event.room.name if event.HasField('room') else ''
        identity = event.participant.identity if event.HasField('participant') else ''
        if not room_name or not identity:
            return {'received': True}
        sessions = rows('''SELECT c.appointment,c.patient_identity,c.clinician_identity,r.id request_id
            FROM tt_consultation c JOIN tt_open_request r ON r.appointment=c.appointment
            WHERE c.room_name=%s LIMIT 1''', (room_name,))
        if not sessions:
            return {'received': True}
        session = sessions[0]
        role = 'Patient' if identity == session.patient_identity else ('Clinician' if identity == session.clinician_identity else None)
        if not role:
            return {'received': True}
        event_name = 'ParticipantJoined' + role if event.event == 'participant_joined' else 'ParticipantLeft' + role
        occurred = datetime.fromtimestamp(event.created_at, timezone.utc).replace(tzinfo=None)
        metric(session.request_id, event_name, external_event_id=(event.id or None), occurred_at=occurred)
        return {'received': True}
    except Exception:
        # Provider retries on non-success; return a generic response and never
        # record the untrusted body, signature, aliases or exception text.
        frappe.local.response['http_status_code'] = 401
        return {'received': False}
