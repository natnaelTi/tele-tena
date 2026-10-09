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
ROUTING_WAVES = ((0, 3), (30, 3), (75, 4))


def immediate_window_minutes():
    """One bounded policy window for readiness and immediate request matching."""
    try:
        configured = int(frappe.conf.get('tele_tena_immediate_window_minutes', 30))
    except (TypeError, ValueError):
        configured = 30
    return max(5, min(60, configured))


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


def route_event(request_id, clinician, wave, event, reason_code=None):
    frappe.db.sql('''INSERT INTO tt_request_route_log
        (id,request_id,clinician,wave,event,reason_code,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,UTC_TIMESTAMP(6))''',
        (str(uuid.uuid4()), request_id, clinician, wave, event, reason_code))


def wave_policy():
    """Bound per-site demo tuning; no request can exceed the hard total cap."""
    delays = (0, int(frappe.conf.get('tele_tena_request_wave_2_seconds', 30)),
              int(frappe.conf.get('tele_tena_request_wave_3_seconds', 75)))
    sizes = (int(frappe.conf.get('tele_tena_request_wave_1_size', 3)),
             int(frappe.conf.get('tele_tena_request_wave_2_size', 3)),
             int(frappe.conf.get('tele_tena_request_wave_3_size', 4)))
    delays = (0, max(10, min(180, delays[1])), max(delays[1] + 10, min(240, delays[2])))
    sizes = tuple(max(1, min(MAX_RECIPIENTS, size)) for size in sizes)
    return tuple(zip(delays, sizes))


def clinician_languages(user):
    row = one('SELECT languages FROM tt_profile WHERE user=%s', (user,))
    try:
        values = json.loads(row.languages or '[]')
    except (TypeError, ValueError):
        values = []
    return set(values) if isinstance(values, list) else set()


def immediate_service_enabled(service):
    if service.immediate_care_enabled:
        return True
    from tele_tena.review import enabled as review_enabled
    return bool(service.catalog_status == 'Legacy test' and
                (review_enabled() or frappe.local.site == 'erp.localhost') and
                frappe.conf.get('tele_tena_demo_immediate_care_enabled') is True)


def _has_immediate_capacity(clinician, offerings):
    """Require a complete, conflict-free session in the current request window."""
    from tele_tena.api import scheduling
    earliest = now()
    latest = earliest + timedelta(minutes=immediate_window_minutes())
    for item in offerings:
        if not item.get('schedule_id') or not immediate_service_enabled(item):
            continue
        schedule = scheduling._schedule_for(item.id)
        offer = one('SELECT * FROM tt_offering WHERE id=%s AND active=1', (item.id,))
        if scheduling.immediate_start(schedule, offer, clinician, None, earliest, latest):
            return True
    return False


def _eligible(request, exclude_delivered=True, limit=None):
    """Deterministic eligibility. Never returns patient identities to clinicians."""
    presence = request.urgency == 'immediate'
    service = one('''SELECT immediate_care_enabled,catalog_status FROM `tabTele Tena Service`
        WHERE name=%s AND active=1''', (request.service,))
    if presence and not immediate_service_enabled(service):
        return []
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
        ORDER BY o.clinician,o.id''',
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
        if not journey.service_scope_is_current(item.clinician, request.service):
            continue
        if presence:
            ready = one('SELECT expires_at FROM tt_clinician_request_presence WHERE clinician=%s AND ready=1',
                        (item.clinician,))
            if ready.expires_at <= now():
                continue
        feasible = _feasible_start(item, request)
        if not feasible:
            continue
        item.feasible_start = feasible
        item.exposure_count = int(one('''SELECT COUNT(*) n FROM tt_request_recipient rr
            JOIN tt_open_request prior ON prior.id=rr.request_id
            WHERE rr.clinician=%s AND rr.enqueued_at>=UTC_TIMESTAMP(6)-INTERVAL 30 DAY''',
            (item.clinician,)).n)
        result.append(item)
    result.sort(key=lambda item: (item.feasible_start, item.exposure_count, item.clinician, item.offering))
    if limit is not None:
        result = result[:limit]
    return result


def _feasible_start(candidate, request):
    """Check the request range against generated or continuous immediate time."""
    from tele_tena.api import scheduling
    from zoneinfo import ZoneInfo
    schedule = scheduling._schedule_for(candidate.offering)
    if not schedule or schedule.status != 'Published':
        return None
    offer = one('SELECT * FROM tt_offering WHERE id=%s AND active=1', (candidate.offering,))
    if request.urgency == 'immediate':
        return scheduling.immediate_start(schedule, offer, candidate.clinician, request.patient,
                                          request.earliest_start, request.latest_start)
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
                return start_at
        day += timedelta(days=1)
    return None


def _has_slot(candidate, request):
    return _feasible_start(candidate, request) is not None


def _deliver(request, candidates=None, wave=None):
    delivered = int(one('SELECT COUNT(*) n FROM tt_request_recipient WHERE request_id=%s',
                        (request.id,)).n)
    remaining = MAX_RECIPIENTS - delivered
    if remaining <= 0:
        return 0, delivered
    wave = int(wave or request.current_wave or 1)
    if wave not in (1, 2, 3):
        return 0, delivered
    wave_size = wave_policy()[wave - 1][1]
    wave_already = int(one('SELECT COUNT(*) n FROM tt_request_recipient WHERE request_id=%s AND wave=%s',
                           (request.id, wave)).n)
    wave_remaining = max(0, wave_size - wave_already)
    if wave_remaining <= 0:
        return 0, delivered
    candidates = candidates if candidates is not None else _eligible(request)
    frappe.db.sql('''UPDATE tt_open_request SET
        last_routed_at=IF(last_routed_at IS NULL OR current_wave<>%s,UTC_TIMESTAMP(6),last_routed_at),
        current_wave=%s WHERE id=%s''', (wave, wave, request.id))
    added = 0
    for item in candidates[:min(remaining, wave_remaining)]:
        already = rows('SELECT clinician FROM tt_request_recipient WHERE request_id=%s AND clinician=%s',
                       (request.id, item.clinician))
        if already:
            continue
        frappe.db.sql('''INSERT IGNORE INTO tt_request_recipient
            (request_id,clinician,notified_at,delivered_round,wave,enqueued_at)
            VALUES (%s,%s,UTC_TIMESTAMP(6),%s,%s,UTC_TIMESTAMP(6))''',
            (request.id, item.clinician, wave, wave))
        added += 1
        route_event(request.id, item.clinician, wave, 'NotificationEnqueued')
    if added:
        metric(request.id, 'NoticesEnqueued', delivered + added)
        if not request.first_notice_at:
            metric(request.id, 'FirstNoticeEnqueued', delivered + added)
        frappe.db.sql('''UPDATE tt_open_request SET first_notice_at=COALESCE(first_notice_at,UTC_TIMESTAMP(6))
            WHERE id=%s''', (request.id,))
    elif not delivered:
        route_event(request.id, None, wave, 'EligibilityEvaluated', 'no_feasible_supply')
    metric(request.id, 'RoutingWave', len(candidates))
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
        offerings = rows('''SELECT o.id,o.service,s.id schedule_id,svc.immediate_care_enabled,svc.catalog_status
            FROM tt_offering o JOIN `tabTele Tena Service` svc ON svc.name=o.service AND svc.active=1
            LEFT JOIN tt_schedule s ON s.offering=o.id AND s.status='Published'
            WHERE o.clinician=%s AND o.active=1''', (clinician,))
        if not offerings:
            fail('Publish a service offering before becoming available for requests.',
                 'offering_required')
        scoped = [item for item in offerings if journey.service_scope_is_current(clinician, item.service, lock=True)]
        if not scoped:
            fail('An active service scope must be approved before you can receive requests.',
                 'scope_approval_required')
        scheduled = [item for item in scoped if item.schedule_id]
        if not scheduled:
            fail('Publish recurring availability for an approved service before receiving requests.',
                 'request_schedule_required')
        immediate = [item for item in scheduled if immediate_service_enabled(item)]
        if not immediate:
            fail('No published service is enabled for immediate requests. Choose scheduled care or ask an administrator to enable the service policy.',
                 'immediate_policy_required')
        if not _has_immediate_capacity(clinician, immediate):
            fail('There is no conflict-free time for a full session in the next 30 minutes. Update availability or pause request presence.',
                 'no_immediate_capacity')
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
    service_row = one('SELECT name,catalog_status FROM `tabTele Tena Service` WHERE name=%s AND active=1', (service,))
    from tele_tena.review import enabled as review_enabled
    if service_row.catalog_status != 'Active' and not (
            service_row.catalog_status == 'Legacy test' and
            (review_enabled() or frappe.local.site == 'erp.localhost')):
        fail('This service is not currently available for matching.', 'service_definition_unavailable')
    if urgency == 'immediate':
        policy = one('SELECT immediate_care_enabled,catalog_status FROM `tabTele Tena Service` WHERE name=%s', (service,))
        if not immediate_service_enabled(policy):
            fail('This service is not configured for immediate requests. Choose scheduled care instead.',
                 'immediate_care_unavailable')
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
        latest = current + timedelta(minutes=immediate_window_minutes())
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
    notified, _total = _deliver(req, candidates, wave=1)
    return {'id': req_id, 'state': 'Open', 'expires_at': expiry.isoformat() + 'Z',
            'eligible_supply': len(candidates), 'notified': notified, 'wave': 1,
            'start_window_minutes': immediate_window_minutes() if urgency == 'immediate' else None}


@journey.command
def find_more_options(request_id):
    """Patient explicitly expands to the next bounded, unchanged eligibility wave."""
    patient = profile('patient', lock=True)
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    req = one("SELECT * FROM tt_open_request WHERE id=%s AND patient=%s AND state='Open' FOR UPDATE",
              (request_id, patient.user))
    if req.expires_at <= now():
        fail('This request has expired. Start another request or browse clinicians.', 'request_expired')
    if int(req.current_wave or 1) >= 3:
        return {'state': 'Open', 'wave': int(req.current_wave or 1), 'more_available': False, 'notified': 0}
    wave = int(req.current_wave or 1) + 1
    candidates = _eligible(req)
    added, delivered = _deliver(req, candidates, wave=wave)
    route_event(req.id, None, wave, 'PatientExpandedWave', 'patient_requested_more_options')
    return {'state': 'Open', 'wave': wave, 'eligible_supply': len(candidates),
            'notified': added, 'delivered_total': delivered, 'more_available': wave < 3}


@query()
def my_requests():
    patient = profile('patient')
    requests = rows('''SELECT r.id,r.state,r.urgency,r.service,s.service_label AS category,
        r.language,r.consultation_format,r.request_text,r.disclosure_snapshot,r.max_price_minor,r.current_wave,
        r.earliest_start,r.latest_start,r.timezone,r.published_at,r.expires_at,r.appointment,
        r.first_notice_at,r.first_offer_at,r.matched_at
        FROM tt_open_request r JOIN `tabTele Tena Service` s ON s.name=r.service
        WHERE r.patient=%s ORDER BY r.published_at DESC LIMIT 30''', (patient.user,))
    return [_serialize_patient_request(req) for req in requests]


def _serialize_patient_request(req):
    supply = rows('''SELECT eligible_supply FROM tt_request_metric
        WHERE request_id=%s AND event='Published' ORDER BY occurred_at LIMIT 1''', (req.id,))
    req.eligible_supply = int(supply[0].eligible_supply or 0) if supply else None
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
    return req


@query()
def my_request_detail(request_id):
    """Return one request only to its patient; unknown and foreign IDs are identical."""
    patient = profile('patient')
    if not isinstance(request_id, str) or len(request_id) > 64:
        fail('Request unavailable.', 'request_unavailable')
    request = rows('''SELECT r.id,r.state,r.urgency,r.service,s.service_label AS category,
        r.language,r.consultation_format,r.request_text,r.disclosure_snapshot,r.max_price_minor,r.current_wave,
        r.earliest_start,r.latest_start,r.timezone,r.published_at,r.expires_at,r.appointment,
        r.first_notice_at,r.first_offer_at,r.matched_at
        FROM tt_open_request r JOIN `tabTele Tena Service` s ON s.name=r.service
        WHERE r.id=%s AND r.patient=%s LIMIT 1''', (request_id, patient.user))
    if not request:
        fail('Request unavailable.', 'request_unavailable')
    return _serialize_patient_request(request[0])


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
    services = rows('''SELECT o.id offering,o.service,COALESCE(NULLIF(o.title,''),s.service_label) label,
        o.description,s.service_label service_category,o.price,o.minutes,schedule.consultation_format,
        schedule.timezone FROM tt_offering o
        JOIN `tabTele Tena Service Scope` scope ON scope.clinician=o.clinician
            AND scope.service=o.service AND scope.status='Approved'
        JOIN `tabTele Tena Service` s ON s.name=o.service AND s.active=1
        JOIN tt_schedule schedule ON schedule.offering=o.id AND schedule.status='Published'
        WHERE o.clinician=%s AND o.active=1 ORDER BY s.service_label''', (clinician.user,))
    services = [item for item in services if journey.service_scope_is_current(clinician.user, item.service)]
    for item in services:
        item.pop('service', None)
    from tele_tena.trust_metrics import (
        summarize_clinician_cancellations,
        summarize_response_behavior,
        summarize_session_experience,
    )
    experience = one('''SELECT COUNT(*) sample_count,AVG(rating) mean_rating
        FROM tt_session_feedback WHERE clinician=%s
        AND created_at>=UTC_TIMESTAMP(6)-INTERVAL 365 DAY''', (clinician.user,))
    response = one('''SELECT COUNT(DISTINCT rr.request_id) presented_count,
        COUNT(DISTINCT CASE WHEN offer.request_id IS NOT NULL THEN rr.request_id END) offered_count
        FROM tt_request_recipient rr
        JOIN tt_open_request r ON r.id=rr.request_id AND r.urgency='immediate'
        LEFT JOIN tt_request_offer offer ON offer.request_id=rr.request_id
            AND offer.clinician=rr.clinician AND offer.created_at>=rr.inbox_fetched_at
        WHERE rr.clinician=%s AND rr.inbox_fetched_at IS NOT NULL
          AND rr.inbox_fetched_at>=UTC_TIMESTAMP(6)-INTERVAL 90 DAY''', (clinician.user,))
    reliability = one('''SELECT
        SUM(CASE WHEN a.state='Completed' THEN 1 ELSE 0 END) completed_count,
        SUM(CASE WHEN a.state='Cancelled' AND a.cancelled_by=%s THEN 1 ELSE 0 END) clinician_cancelled_count
        FROM tt_appointment a
        WHERE a.clinician=%s AND a.confirmed_at IS NOT NULL
          AND ((a.state='Completed' AND EXISTS (
                  SELECT 1 FROM tt_appointment_event e WHERE e.appointment=a.id
                  AND e.event_type='Completed' AND e.created>=UTC_TIMESTAMP(6)-INTERVAL 365 DAY))
            OR (a.state='Cancelled' AND a.cancelled_by=%s
                AND a.cancelled_at>=UTC_TIMESTAMP(6)-INTERVAL 365 DAY))''',
        (clinician.user, clinician.user, clinician.user))
    return {'display_name': clinician.display_name, 'services': services,
            'approval_meaning': 'Application and listed service scopes are manually approved.',
            'trust_indicators': {
                'credential_status': 'Manually reviewed application and listed scopes',
                'relevant_expertise': 'See the approved service scopes above',
                'responsiveness': summarize_response_behavior(
                    response.presented_count, response.offered_count),
                'reliability': summarize_clinician_cancellations(
                    reliability.completed_count, reliability.clinician_cancelled_count),
                'session_experience': summarize_session_experience(
                    experience.sample_count, experience.mean_rating),
            }}


@query()
def clinician_requests():
    clinician = actor('Tele Tena Clinician')
    profile('clinician')
    application = one('SELECT status FROM tt_application WHERE user=%s', (clinician,))
    if not application or application.status != 'Approved':
        return []
    result = rows('''SELECT r.id,r.service _routing_service,r.urgency,r.language,r.consultation_format,r.request_text,
        r.disclosure_snapshot,r.max_price_minor,r.earliest_start,r.latest_start,r.timezone,
        r.expires_at,r.patient _routing_patient,s.service_label category,rr.notified_at,rr.wave,own.id own_offer_id,
        own.start own_offer_start,own.price_minor own_offer_price,own.valid_until own_offer_until
        FROM tt_request_recipient rr JOIN tt_open_request r ON r.id=rr.request_id
        JOIN `tabTele Tena Service` s ON s.name=r.service
        LEFT JOIN tt_request_offer own ON own.request_id=r.id AND own.clinician=rr.clinician AND own.state='Active'
        WHERE rr.clinician=%s AND r.state='Open' AND r.expires_at>UTC_TIMESTAMP(6)
        ORDER BY r.urgency='immediate' DESC,rr.notified_at LIMIT 30''', (clinician,))
    visible = []
    for req in result:
        if not journey.service_scope_is_current(clinician, req._routing_service):
            continue
        if req.urgency == 'immediate':
            # A recipient row records that a bounded notification was enqueued;
            # it is not a permanent grant to view the patient's disclosure.
            # Revalidate the live gates whenever the inbox is fetched.
            if req.language not in clinician_languages(clinician):
                continue
            present = rows('''SELECT clinician FROM tt_clinician_request_presence
                WHERE clinician=%s AND ready=1 AND expires_at>UTC_TIMESTAMP(6)''', (clinician,))
            if not present:
                continue
            service = one('''SELECT immediate_care_enabled,catalog_status FROM `tabTele Tena Service`
                WHERE name=%s AND active=1''', (req._routing_service,))
            if not immediate_service_enabled(service):
                continue
        req.disclosure_snapshot = json.loads(req.disclosure_snapshot)
        # Offering titles are clinician-owned copy, not authorization keys.
        # Return only this clinician's currently published offerings within
        # the exact request scope/format; submission still revalidates the slot.
        req.eligible_offering_ids = [item.id for item in rows('''
            SELECT o.id FROM tt_offering o JOIN tt_schedule schedule ON schedule.offering=o.id
            WHERE o.clinician=%s AND o.service=%s AND o.active=1
                AND schedule.status='Published' AND schedule.consultation_format=%s
            ORDER BY o.id''', (clinician, req._routing_service, req.consultation_format))]
        req.suggested_start = None
        if req.urgency == 'immediate':
            offerings = rows('''SELECT o.id FROM tt_offering o
                JOIN `tabTele Tena Service Scope` sc ON sc.clinician=o.clinician
                    AND sc.service=o.service AND sc.status='Approved'
                JOIN tt_schedule s ON s.offering=o.id AND s.status='Published'
                WHERE o.clinician=%s AND o.service=%s AND o.active=1
                    AND s.consultation_format=%s ORDER BY o.id''',
                (clinician, req._routing_service, req.consultation_format))
            from tele_tena.api import scheduling
            for offering_row in offerings:
                schedule = scheduling._schedule_for(offering_row.id)
                offer = one('SELECT * FROM tt_offering WHERE id=%s AND active=1', (offering_row.id,))
                feasible = scheduling.immediate_start(schedule, offer, clinician, req._routing_patient,
                    req.earliest_start, req.latest_start)
                if feasible:
                    req.suggested_start = feasible.isoformat(timespec='seconds') + 'Z'
                    req.suggested_timezone = schedule.timezone
                    break
            if not req.suggested_start:
                continue
        for field in ('earliest_start','latest_start','expires_at','notified_at','own_offer_start','own_offer_until'):
            if req.get(field):
                req[field] = req[field].isoformat() + 'Z'
        # The patient id is required only to evaluate schedule conflicts. Never
        # serialize it to the clinician inbox API.
        del req['_routing_patient']
        del req['_routing_service']
        visible.append(req)
    return visible


@query()
def clinician_offers(page=0, view=None):
    """Own quotes and outcomes, including closed requests, with bounded paging.

    No request narrative, patient account identity, competitor quote, or new
    profile disclosure is returned. A matched appointment belongs to this actor.
    Read-time expiry keeps the view correct even while the scheduler is delayed.
    """
    from tele_tena.offer_status import effective_offer_state, offer_patient_label
    clinician = actor('Tele Tena Clinician')
    profile('clinician')
    page_number = integer(page, 0, 10000)
    if view not in (None, 'Active', 'History'):
        fail('Choose an offer view.', 'request_offer_view_invalid')
    active_condition = "(o.state='Active' AND r.state='Open' AND o.valid_until>UTC_TIMESTAMP(6) AND r.expires_at>UTC_TIMESTAMP(6))"
    view_filter = '' if view is None else ' AND ' + (active_condition if view == 'Active' else 'NOT ' + active_condition)
    offers = rows('''SELECT o.id,o.start,o.duration_minutes,o.consultation_format,
        o.price_minor,o.price_source,o.state,o.valid_until,o.created_at,o.timezone,
        r.state AS request_state,r.expires_at AS request_expires_at,r.disclosure_snapshot,s.service_label AS category,
        a.id AS appointment
        FROM tt_request_offer o JOIN tt_open_request r ON r.id=o.request_id
        JOIN tt_offering off ON off.id=o.offering
        JOIN `tabTele Tena Service` s ON s.name=off.service
        LEFT JOIN tt_appointment a ON a.id=o.appointment AND a.clinician=%s
        WHERE o.clinician=%s''' + view_filter + ''' ORDER BY o.created_at DESC,o.id DESC
        LIMIT 51 OFFSET %s''', (clinician, clinician, page_number * 50))
    has_more = len(offers) > 50
    result = []
    current_time = now()
    for offer in offers[:50]:
        if offer.request_state == "Open" and offer.request_expires_at <= current_time:
            offer.request_state = "Expired"
        del offer["request_expires_at"]
        offer.state = effective_offer_state(offer.state, offer.request_state,
                                             offer.valid_until, current_time)
        offer.patient_label = offer_patient_label(json.loads(offer.disclosure_snapshot))
        del offer['disclosure_snapshot']
        for field in ('start', 'valid_until', 'created_at'):
            offer[field] = offer[field].isoformat() + 'Z'
        result.append(offer)
    return {'items': result, 'page': page_number, 'has_more': has_more}


@journey.command
def acknowledge_inbox_fetch(request_ids):
    """Record that request cards were returned to this authenticated inbox client."""
    clinician = actor('Tele Tena Clinician')
    if isinstance(request_ids, str):
        try:
            request_ids = json.loads(request_ids)
        except ValueError:
            fail('Inbox update could not be recorded.')
    if not isinstance(request_ids, list) or len(request_ids) > 30:
        fail('Inbox update could not be recorded.')
    for request_id in set(request_ids):
        if not isinstance(request_id, str) or len(request_id) != 36:
            continue
        recipient = rows('''SELECT rr.wave,rr.inbox_fetched_at FROM tt_request_recipient rr
            JOIN tt_open_request r ON r.id=rr.request_id
            WHERE rr.request_id=%s AND rr.clinician=%s AND r.state='Open' AND r.expires_at>UTC_TIMESTAMP(6)
              AND (r.urgency<>'immediate' OR EXISTS (
                  SELECT 1 FROM tt_clinician_request_presence pr WHERE pr.clinician=%s
                  AND pr.ready=1 AND pr.expires_at>UTC_TIMESTAMP(6)))
            FOR UPDATE''', (request_id, clinician, clinician))
        if recipient and not recipient[0].inbox_fetched_at:
            frappe.db.sql('''UPDATE tt_request_recipient SET inbox_fetched_at=UTC_TIMESTAMP(6)
                WHERE request_id=%s AND clinician=%s AND inbox_fetched_at IS NULL''', (request_id, clinician))
            route_event(request_id, clinician, int(recipient[0].wave or 1), 'InboxFetched')
    return {'recorded': True}


@query()
def request_presence():
    clinician = actor('Tele Tena Clinician')
    profile('clinician')
    row = rows('SELECT ready,expires_at FROM tt_clinician_request_presence WHERE clinician=%s', (clinician,))
    reasons = []
    app = rows("SELECT status FROM tt_application WHERE user=%s", (clinician,))
    if not app or app[0].status != 'Approved':
        reasons.append('approval_required')
    language_set = clinician_languages(clinician)
    if not language_set.intersection(LANGUAGES):
        reasons.append('language_required')
    all_offerings = rows('''SELECT o.id,o.service,s.id schedule_id,svc.immediate_care_enabled,svc.catalog_status
        FROM tt_offering o JOIN `tabTele Tena Service` svc ON svc.name=o.service AND svc.active=1
        LEFT JOIN tt_schedule s ON s.offering=o.id AND s.status='Published'
        WHERE o.clinician=%s AND o.active=1''', (clinician,))
    if not all_offerings:
        reasons.append('offering_required')
    scoped = [item for item in all_offerings if journey.service_scope_is_current(clinician, item.service)]
    if all_offerings and not scoped:
        reasons.append('scope_approval_required')
    scheduled = [item for item in scoped if item.schedule_id]
    if scoped and not scheduled:
        reasons.append('published_schedule_required')
    immediate_services = [item for item in scheduled if immediate_service_enabled(item)]
    if not immediate_services:
        reasons.append('immediate_policy_required')
    elif not _has_immediate_capacity(clinician, immediate_services):
        reasons.append('no_immediate_capacity')
    live = bool(row and row[0].ready and row[0].expires_at > now())
    # A previously valid lease is not enough after schedule, scope, or policy
    # changes. Do not display Available while current hard eligibility fails.
    effective_ready = live and not reasons
    return {'ready': effective_ready, 'configured': not reasons, 'reasons': reasons,
            'immediate_window_minutes': immediate_window_minutes(),
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
    offer = one('''SELECT o.*,s.consultation_format,s.timezone,s.status,svc.immediate_care_enabled,
        svc.catalog_status FROM tt_offering o
        JOIN `tabTele Tena Service` svc ON svc.name=o.service AND svc.active=1
        JOIN tt_schedule s ON s.offering=o.id WHERE o.id=%s AND o.clinician=%s AND o.active=1 FOR UPDATE''',
        (offering, clinician))
    if not offer:
        fail('This offering or schedule is no longer available.', 'offering_unavailable')
    if req.urgency == 'immediate' and not immediate_service_enabled(offer):
        fail('This service is no longer configured for immediate requests. Choose scheduled care instead.',
             'immediate_care_unavailable')
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
    route_event(request_id, clinician, int(req.current_wave or 1), 'OfferSubmitted')
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
    service_policy = one('''SELECT immediate_care_enabled,catalog_status FROM `tabTele Tena Service`
        WHERE name=%s AND active=1 FOR UPDATE''', (req.service,))
    if req.urgency == 'immediate' and not immediate_service_enabled(service_policy):
        fail('This service is no longer configured for immediate requests.', 'immediate_care_unavailable')
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
    route_event(request_id, item.clinician, int(req.current_wave or 1), 'OfferAccepted')
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
    """Reconcile due routing waves; a minute scheduler is the retry fallback."""
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    candidates = rows("SELECT id FROM tt_open_request WHERE state='Open' AND expires_at>UTC_TIMESTAMP(6) ORDER BY published_at LIMIT 100")
    policy = wave_policy()
    for candidate in candidates:
        req = rows("SELECT * FROM tt_open_request WHERE id=%s AND state='Open' AND expires_at>UTC_TIMESTAMP(6) FOR UPDATE",
                   (candidate.id,))
        if req:
            current_wave = max(1, int(req[0].current_wave or 1))
            if current_wave >= 3:
                continue
            active_offer = one("SELECT COUNT(*) n FROM tt_request_offer WHERE request_id=%s AND state='Active' AND valid_until>UTC_TIMESTAMP(6)",
                               (candidate.id,)).n
            if active_offer:
                continue
            wave_elapsed = (now() - (req[0].last_routed_at or req[0].published_at)).total_seconds()
            current_size = policy[current_wave - 1][1]
            current_count = int(one('SELECT COUNT(*) n FROM tt_request_recipient WHERE request_id=%s AND wave=%s',
                                    (candidate.id, current_wave)).n)
            next_wave = current_wave
            next_delay = policy[current_wave][0]
            if wave_elapsed < next_delay:
                # Re-check a partially filled wave when a clinician becomes
                # newly eligible (for example, they just enabled presence).
                # _deliver is recipient-deduplicated and leaves its clock intact
                # when no new recipient is found.
                if current_count >= current_size:
                    continue
            else:
                next_wave = current_wave + 1
            try:
                _deliver(req[0], wave=next_wave)
            except Exception:
                frappe.log_error(message='A private request inbox delivery attempt could not be completed.',
                                 title='TeleTena request delivery failed')


def expire_requests():
    """Close stale requests/offers and reconcile progressive delivery waves."""
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
