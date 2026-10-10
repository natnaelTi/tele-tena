"""Patient-controlled, encounter-specific clinic scheduling disclosure."""
import json
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import frappe
from frappe.utils import now_datetime

from tele_tena.api.journey import actor, command, fail, one, query, rows


def _patient():
    user = actor('Tele Tena Patient')
    if not frappe.db.get_value('User', user, 'enabled'):
        frappe.throw('Account unavailable.', frappe.PermissionError)
    return user


def _appointment_for_patient(appointment, patient, lock=False):
    found = rows('''SELECT * FROM tt_appointment WHERE id=%s AND patient=%s''' +
                 (' FOR UPDATE' if lock else ''), (appointment, patient))
    if not found:
        frappe.throw('Appointment unavailable.', frappe.PermissionError)
    from tele_tena.api.couples import plan_for
    if plan_for(appointment):
        frappe.throw('Shared sessions require each recipient’s permission; clinic sharing is unavailable.', frappe.PermissionError)
    return found[0]


def _staff_clinic_ids(user):
    roles = rows('''SELECT DISTINCT clinic FROM `tabTele Tena Clinic Membership`
        WHERE member_user=%s AND status='Active'
          AND membership_role IN ('Clinic Manager','Scheduling')''', (user,))
    owned = rows('''SELECT name AS clinic FROM `tabTele Tena Clinic`
        WHERE submitted_by=%s AND status='Verified' ''', (user,))
    return {r.clinic for r in (*roles, *owned)}


def _care_clinic_ids(user):
    return {r.clinic for r in rows('''SELECT DISTINCT clinic
        FROM `tabTele Tena Clinic Membership`
        WHERE member_user=%s AND status='Active' AND membership_role='Care Coordination' ''', (user,))}


def _calendar_week_utc_bounds(start_day, zone):
    end_day = start_day + timedelta(days=7)
    start_utc = datetime.combine(start_day, time.min, zone).astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = datetime.combine(end_day, time.min, zone).astimezone(timezone.utc).replace(tzinfo=None)
    return start_utc, end_utc


@query()
def eligible_clinics_for_appointment(appointment):
    patient = _patient()
    item = _appointment_for_patient(appointment, patient)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if item.state != 'Booked' or item.start <= now:
        return []
    affiliations = rows('''SELECT c.name,c.clinic_name,c.jurisdiction
        FROM `tabTele Tena Clinic Affiliation` a
        JOIN `tabTele Tena Clinic` c ON c.name=a.clinic
        WHERE a.clinician=%s AND a.status='Verified' AND c.status='Verified'
        ORDER BY c.clinic_name LIMIT 100''', (item.clinician,))
    active = {r.clinic for r in rows('''SELECT clinic FROM `tabTele Tena Clinic Encounter Access`
        WHERE appointment=%s AND patient=%s AND purpose='Scheduling coordination'
          AND status='Active' AND expires_at>UTC_TIMESTAMP(6)''',
        (item.id, patient))}
    return [{'clinic': c.name, 'clinic_name': c.clinic_name,
             'jurisdiction': c.jurisdiction, 'already_shared': c.name in active}
            for c in affiliations]


@command
def grant_schedule_access(appointment, clinic):
    patient = _patient()
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    item = _appointment_for_patient(appointment, patient, lock=True)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if item.state != 'Booked' or item.start <= now:
        fail('Only a future confirmed appointment can be shared.', 'appointment_not_shareable')
    valid = rows('''SELECT c.name FROM `tabTele Tena Clinic` c
        JOIN `tabTele Tena Clinic Affiliation` a ON a.clinic=c.name
        WHERE c.name=%s AND c.status='Verified' AND a.clinician=%s AND a.status='Verified' ''',
        (clinic, item.clinician))
    if not valid:
        fail('Choose a verified clinic linked to your treating clinician.', 'clinic_not_eligible')
    existing = rows('''SELECT name FROM `tabTele Tena Clinic Encounter Access`
        WHERE appointment=%s AND clinic=%s AND patient=%s AND purpose='Scheduling coordination' AND status='Active'
          AND expires_at>UTC_TIMESTAMP(6) FOR UPDATE''', (item.id, clinic, patient))
    if existing:
        return {'grant': existing[0].name, 'status': 'Active', 'idempotent': True}
    doc = frappe.new_doc('Tele Tena Clinic Encounter Access')
    doc.update({
        'clinic': clinic,
        'appointment': item.id,
        'patient': patient,
        'clinician': item.clinician,
        'purpose': 'Scheduling coordination',
        'status': 'Active',
        'granted_by': patient,
        'granted_at': now_datetime(),
        'expires_at': item.end + timedelta(days=7),
    })
    frappe.local.tele_tena_clinic_access_action = 'grant'
    try:
        doc.insert()
    finally:
        frappe.local.tele_tena_clinic_access_action = None
    from tele_tena.api.presentation import _event
    _event(item.id, 'ClinicScheduleAccessGranted', patient)
    return {'grant': doc.name, 'status': 'Active', 'idempotent': False}


@query()
def eligible_clinics_for_summary(appointment):
    patient = _patient()
    item = _appointment_for_patient(appointment, patient)
    if item.state != 'Completed' or not rows('''SELECT revision FROM tt_note_revision
        WHERE appointment=%s AND summary_published=1 LIMIT 1''', (item.id,)):
        return []
    affiliations = rows('''SELECT c.name,c.clinic_name,c.jurisdiction
        FROM `tabTele Tena Clinic Affiliation` a
        JOIN `tabTele Tena Clinic` c ON c.name=a.clinic
        WHERE a.clinician=%s AND a.status='Verified' AND c.status='Verified'
        ORDER BY c.clinic_name LIMIT 100''', (item.clinician,))
    active = {r.clinic for r in rows('''SELECT clinic FROM `tabTele Tena Clinic Encounter Access`
        WHERE appointment=%s AND patient=%s AND purpose='Patient-shared summary'
          AND status='Active' ''', (item.id, patient))}
    return [{'clinic': c.name, 'clinic_name': c.clinic_name,
             'jurisdiction': c.jurisdiction, 'already_shared': c.name in active}
            for c in affiliations]


@command
def grant_published_summary_access(appointment, clinic):
    patient = _patient()
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    item = _appointment_for_patient(appointment, patient, lock=True)
    if item.state != 'Completed' or not rows('''SELECT revision FROM tt_note_revision
        WHERE appointment=%s AND summary_published=1 LIMIT 1''', (item.id,)):
        fail('A published summary is required before sharing this encounter.', 'summary_not_shareable')
    valid = rows('''SELECT c.name FROM `tabTele Tena Clinic` c
        JOIN `tabTele Tena Clinic Affiliation` a ON a.clinic=c.name
        WHERE c.name=%s AND c.status='Verified' AND a.clinician=%s AND a.status='Verified' ''',
        (clinic, item.clinician))
    if not valid:
        fail('Choose a verified clinic linked to your treating clinician.', 'clinic_not_eligible')
    existing = rows('''SELECT name FROM `tabTele Tena Clinic Encounter Access`
        WHERE appointment=%s AND clinic=%s AND patient=%s
          AND purpose='Patient-shared summary' AND status='Active' FOR UPDATE''',
        (item.id, clinic, patient))
    if existing:
        return {'grant': existing[0].name, 'status': 'Active', 'idempotent': True}
    doc = frappe.new_doc('Tele Tena Clinic Encounter Access')
    doc.update({'clinic': clinic, 'appointment': item.id, 'patient': patient,
        'clinician': item.clinician, 'purpose': 'Patient-shared summary',
        'status': 'Active', 'granted_by': patient, 'granted_at': now_datetime(),
        'expires_at': None})
    frappe.local.tele_tena_clinic_access_action = 'grant'
    try:
        doc.insert()
    finally:
        frappe.local.tele_tena_clinic_access_action = None
    from tele_tena.api.presentation import _event
    _event(item.id, 'ClinicSummaryAccessGranted', patient)
    return {'grant': doc.name, 'status': 'Active', 'idempotent': False}


@command
def revoke_schedule_access(grant, reason=''):
    patient = _patient()
    reason = (reason or '').strip()
    if len(reason) > 300:
        fail('Keep the reason under 300 characters.')
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    found = rows('''SELECT name FROM `tabTele Tena Clinic Encounter Access`
        WHERE name=%s AND patient=%s FOR UPDATE''', (grant, patient))
    if not found:
        frappe.throw('Clinic access unavailable.', frappe.PermissionError)
    doc = frappe.get_doc('Tele Tena Clinic Encounter Access', found[0].name)
    if doc.status == 'Revoked':
        return {'status': 'Revoked', 'idempotent': True}
    doc.status = 'Revoked'
    doc.revoked_by = patient
    doc.revoked_at = now_datetime()
    doc.revocation_reason = reason
    frappe.local.tele_tena_clinic_access_action = 'revoke'
    try:
        doc.save()
    finally:
        frappe.local.tele_tena_clinic_access_action = None
    from tele_tena.api.presentation import _event
    _event(doc.appointment, 'ClinicScheduleAccessRevoked', patient)
    return {'status': 'Revoked', 'idempotent': False}


@query()
def my_schedule_access(appointment=None):
    patient = _patient()
    extra = ' AND g.appointment=%s' if appointment else ''
    params = (patient, appointment) if appointment else (patient,)
    grants = rows('''SELECT g.name,g.status,g.purpose,g.granted_at,g.expires_at,g.revoked_at,
        g.appointment,c.clinic_name,a.state,a.start,a.timezone,a.service_label
        FROM `tabTele Tena Clinic Encounter Access` g
        JOIN `tabTele Tena Clinic` c ON c.name=g.clinic
        JOIN tt_appointment a ON a.id=g.appointment
        WHERE g.patient=%s''' + extra + ' ORDER BY g.granted_at DESC LIMIT 100', params)
    return [{'grant': r.name, 'appointment': r.appointment,
             'purpose': r.purpose,
             'status': ('Expired' if r.status == 'Active'
                        and r.purpose == 'Scheduling coordination'
                        and r.expires_at and r.expires_at <= now_datetime() else r.status),
             'granted_at': r.granted_at,
             'expires_at': r.expires_at, 'revoked_at': r.revoked_at,
             'clinic_name': r.clinic_name, 'appointment_status': r.state,
             'start': r.start, 'timezone': r.timezone, 'service': r.service_label}
            for r in grants]


@query()
def clinic_schedule_access():
    user = actor()
    allowed_clinics = _staff_clinic_ids(user)
    if not allowed_clinics:
        return []
    grants = rows('''SELECT g.name,g.clinic,g.appointment,g.expires_at,c.clinic_name,
        a.state,a.start,a.end,a.timezone,a.service_label,a.consultation_format,a.minutes,
        a.disclosure,a.clinician
        FROM `tabTele Tena Clinic Encounter Access` g
        JOIN `tabTele Tena Clinic` c ON c.name=g.clinic
        JOIN tt_appointment a ON a.id=g.appointment
        WHERE g.purpose='Scheduling coordination' AND g.status='Active'
          AND g.expires_at>UTC_TIMESTAMP(6) AND c.status='Verified'
          AND a.state='Booked' AND a.start>UTC_TIMESTAMP(6)
          AND g.clinic IN ({})
        ORDER BY a.start LIMIT 200'''.format(','.join(['%s'] * len(allowed_clinics))),
        tuple(sorted(allowed_clinics)))
    output=[]
    for item in grants:
        disclosure=json.loads(item.disclosure or '{}')
        output.append({
            'access': item.name,
            'clinic': item.clinic_name,
            'patient_label': disclosure.get('name') or 'Private patient',
            'service': item.service_label,
            'start': item.start,
            'end': item.end,
            'timezone': item.timezone,
            'format': item.consultation_format,
            'minutes': int(item.minutes),
            'status': item.state,
        })
    return output


@query()
def clinic_schedule_week(week_start=None, display_timezone='Africa/Addis_Ababa'):
    """Return only patient-shared upcoming appointments for one local week."""
    user = actor()
    allowed_clinics = _staff_clinic_ids(user)
    if not allowed_clinics:
        frappe.throw('Clinic calendar access required.', frappe.PermissionError)
    if not isinstance(display_timezone, str) or len(display_timezone) > 80:
        fail('Choose a valid calendar timezone.', 'invalid_timezone')
    try:
        zone = ZoneInfo(display_timezone)
    except (ZoneInfoNotFoundError, ValueError):
        fail('Choose a valid calendar timezone.', 'invalid_timezone')
    try:
        if week_start:
            if not isinstance(week_start, str):
                fail('Choose a valid week start date.', 'invalid_week')
            start_day = date.fromisoformat(week_start)
            if start_day.isoformat() != week_start:
                fail('Choose a valid week start date.', 'invalid_week')
        else:
            today = datetime.now(zone).date()
            start_day = today - timedelta(days=today.weekday())
    except (TypeError, ValueError):
        fail('Choose a valid week start date.', 'invalid_week')
    if start_day.weekday() != 0:
        fail('A calendar week must start on Monday.', 'invalid_week')
    start_utc, end_utc = _calendar_week_utc_bounds(start_day, zone)
    grants = rows('''SELECT c.clinic_name,a.start,a.end,a.timezone,a.service_label,
            a.consultation_format,a.minutes,a.disclosure,a.state
        FROM `tabTele Tena Clinic Encounter Access` g
        JOIN `tabTele Tena Clinic` c ON c.name=g.clinic AND c.status='Verified'
        JOIN `tabTele Tena Clinic Affiliation` af ON af.clinic=g.clinic
          AND af.clinician=g.clinician AND af.status='Verified'
        JOIN tt_appointment a ON a.id=g.appointment AND a.patient=g.patient
          AND a.state='Booked' AND a.start>UTC_TIMESTAMP(6)
          AND a.start >= %s AND a.start < %s
        WHERE g.purpose='Scheduling coordination' AND g.status='Active'
          AND g.expires_at>UTC_TIMESTAMP(6) AND g.clinic IN ({})
        ORDER BY a.start LIMIT 200'''.format(','.join(['%s'] * len(allowed_clinics))),
        (start_utc, end_utc, *sorted(allowed_clinics)))
    output = []
    for item in grants:
        disclosure = json.loads(item.disclosure or '{}')
        start = item.start.replace(tzinfo=timezone.utc) if item.start.tzinfo is None else item.start.astimezone(timezone.utc)
        end = item.end.replace(tzinfo=timezone.utc) if item.end.tzinfo is None else item.end.astimezone(timezone.utc)
        output.append({
            'clinic_name': item.clinic_name,
            'patient_label': disclosure.get('name') or 'Private patient',
            'service': item.service_label,
            'start': start.isoformat(),
            'end': end.isoformat(),
            'appointment_timezone': item.timezone,
            'format': item.consultation_format,
            'minutes': int(item.minutes),
            'status': item.state,
        })
    return {'week_start': start_day.isoformat(), 'display_timezone': display_timezone,
            'appointments': output}


@query()
def clinic_shared_summaries():
    user = actor()
    allowed_clinics = _care_clinic_ids(user)
    if not allowed_clinics:
        return []
    grants = rows('''SELECT g.name access,g.clinic,g.appointment,g.granted_at,c.clinic_name,
        a.start,a.timezone,a.service_label,a.disclosure,n.revision,n.patient_summary,n.created published_at
        FROM `tabTele Tena Clinic Encounter Access` g
        JOIN `tabTele Tena Clinic Membership` m ON m.clinic=g.clinic AND m.member_user=%s
          AND m.status='Active' AND m.membership_role='Care Coordination'
        JOIN `tabTele Tena Clinic` c ON c.name=g.clinic AND c.status='Verified'
        JOIN `tabTele Tena Clinic Affiliation` af ON af.clinic=g.clinic
          AND af.clinician=g.clinician AND af.status='Verified'
        JOIN tt_appointment a ON a.id=g.appointment AND a.patient=g.patient AND a.state='Completed'
        JOIN tt_note_revision n ON n.appointment=a.id AND n.summary_published=1
        WHERE g.status='Active' AND g.purpose='Patient-shared summary'
          AND g.clinic IN ({})
        ORDER BY n.created DESC LIMIT 200'''.format(','.join(['%s'] * len(allowed_clinics))),
        (user, *sorted(allowed_clinics)))
    output=[]
    for item in grants:
        disclosure=json.loads(item.disclosure or '{}')
        output.append({'access': item.access, 'clinic': item.clinic_name,
            'patient_label': disclosure.get('name') or 'Private patient',
            'service': item.service_label, 'start': item.start.isoformat() + 'Z', 'timezone': item.timezone,
            'summary': item.patient_summary, 'revision': int(item.revision),
            'published_at': item.published_at.isoformat() + 'Z',
            'shared_at': item.granted_at.isoformat() + 'Z'})
    return output
