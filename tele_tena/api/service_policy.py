"""Human-reviewed, audited controls for immediate request eligibility."""
import hashlib
import json
import uuid

import frappe

from tele_tena.api import journey


@journey.query()
def immediate_services():
    journey.actor('Tele Tena Approver')
    from tele_tena.review import enabled as review_enabled

    rows = frappe.db.sql('''SELECT name AS id,service_label AS label,catalog_status,
            clinical_review_status,immediate_care_enabled,definition_version
        FROM `tabTele Tena Service`
        WHERE active=1 AND (catalog_status='Active' OR
            (catalog_status='Legacy test' AND %s=1))
        ORDER BY service_label,name''', (int(review_enabled()),), as_dict=True)
    return rows


@journey.command
def set_immediate_policy(service, enabled, reason, idempotency_key):
    reviewer = journey.actor('Tele Tena Approver')
    service = journey.text(service, 80)
    reason = journey.text(reason, 1000)
    if len(reason) < 20:
        journey.fail('Record a review reason of at least 20 characters', 'review_reason_required')
    key = journey.text(idempotency_key, 100)
    if not all(ch.isalnum() or ch in '-_' for ch in key) or len(key) < 16:
        journey.fail('Invalid submission key')
    enabled = journey.boolean(enabled)

    # Serialize reviewer actions and protect idempotency across concurrent tabs.
    journey.one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    journey.one('SELECT name FROM `tabTele Tena Service` WHERE name=%s FOR UPDATE', (service,))
    existing = journey.rows('''SELECT * FROM tt_immediate_service_policy_event
        WHERE service=%s AND idempotency_key=%s FOR UPDATE''', (service, key))
    payload = {'service': service, 'enabled': enabled, 'reason': reason}
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if existing:
        if existing[0].payload_hash != payload_hash:
            journey.fail('This submission key was already used for different policy details', 'idempotency_conflict')
        return {'event': existing[0].id, 'enabled': bool(existing[0].enabled),
                'changed': bool(existing[0].previous_enabled != existing[0].enabled), 'replayed': True}

    doc = frappe.get_doc('Tele Tena Service', service)
    if not doc.active or doc.catalog_status not in ('Active', 'Legacy test'):
        journey.fail('Only active, reviewed services can use immediate requests', 'service_unavailable')
    if enabled:
        if doc.catalog_status == 'Active' and doc.clinical_review_status != 'Approved':
            journey.fail('Clinical terminology review must be approved first', 'clinical_review_required')
        if doc.catalog_status == 'Legacy test':
            from tele_tena.review import enabled as review_enabled
            if not review_enabled():
                journey.fail('Legacy test services are limited to the bound review site', 'review_site_required')
    before = bool(doc.immediate_care_enabled)
    if before and not enabled:
        active = int(journey.one('''SELECT COUNT(*) AS n FROM tt_open_request
            WHERE service=%s AND urgency='immediate' AND state='Open'
              AND expires_at>UTC_TIMESTAMP(6)''', (service,)).n)
        if active:
            journey.fail('Wait for active immediate requests to close before pausing this service',
                         'active_immediate_requests')

    event_id = str(uuid.uuid4())
    changed = before != enabled
    if changed:
        frappe.local.tele_tena_service_policy_action = True
        try:
            doc.immediate_care_enabled = int(enabled)
            doc.save()
        finally:
            frappe.local.tele_tena_service_policy_action = False
    frappe.db.sql('''INSERT INTO tt_immediate_service_policy_event
        (id,service,previous_enabled,enabled,reviewer,reason,definition_version,
         idempotency_key,payload_hash,created)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,UTC_TIMESTAMP(6))''',
        (event_id, service, int(before), int(enabled), reviewer,
         reason, doc.definition_version or 'unknown', key, payload_hash))
    return {'event': event_id, 'enabled': enabled, 'changed': changed, 'replayed': False}


@journey.query()
def immediate_policy_history(service):
    journey.actor('Tele Tena Approver')
    service = journey.text(service, 80)
    if not frappe.db.exists('Tele Tena Service', service):
        journey.fail('Service unavailable')
    return journey.rows('''SELECT id,previous_enabled,enabled,reviewer,reason,
            definition_version,created FROM tt_immediate_service_policy_event
        WHERE service=%s ORDER BY created DESC LIMIT 50''', (service,))
