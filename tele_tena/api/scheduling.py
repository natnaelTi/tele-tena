"""Timezone-aware recurring clinician schedules and server-generated slots."""
import json
import hashlib
import hmac
import uuid
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import frappe

from tele_tena.api.journey import actor, approved, approved_service, fail, integer, one, profile, query, rows, text

SLOT_STEP_MINUTES = 15


def _booking_link_token(offering, initialize_key=False):
    key = frappe.conf.get('encryption_key')
    if not key and initialize_key:
        # Only the authorized clinician link-creation command may initialize
        # Frappe's site key. Resolving guessed tokens remains read-only.
        from frappe.utils.password import get_encryption_key
        key = get_encryption_key()
    if not isinstance(key, str) or not key:
        fail('Booking links are unavailable on this site', 'booking_link_unavailable')
    message = ('tele-tena:published-booking:v1:' + offering).encode()
    return hmac.new(key.encode(), message, hashlib.sha256).hexdigest()


def validate_booking_link_token(token, offering):
    """Validate that this patient's booking originated from this offering link."""
    if not isinstance(token, str) or len(token) != 64:
        fail('This booking link is unavailable', 'booking_link_unavailable')
    if not hmac.compare_digest(_booking_link_token(offering), token):
        fail('This booking link is unavailable', 'booking_link_unavailable')
    return True


@frappe.whitelist(methods=['POST'])
def booking_link(offering):
    clinician = actor('Tele Tena Clinician')
    offer = one('''SELECT o.id,o.service FROM tt_offering o
        JOIN tt_schedule s ON s.offering=o.id AND s.status='Published'
        WHERE o.id=%s AND o.clinician=%s AND o.active=1''', (offering, clinician))
    approved(clinician)
    approved_service(clinician, offer.service)
    return {'token': _booking_link_token(offer.id, initialize_key=True)}


@query()
def resolve_booking_link(token):
    actor('Tele Tena Patient')
    if not isinstance(token, str) or len(token) != 64:
        fail('This booking link is unavailable', 'booking_link_unavailable')
    candidates = rows('''SELECT o.id,o.clinician,o.service,o.price,o.minutes,
        COALESCE(NULLIF(o.title,''),sc.service_label) AS service_label,
        p.display_name,s.consultation_format,s.timezone FROM tt_offering o
        JOIN tt_schedule s ON s.offering=o.id AND s.status='Published'
        JOIN `tabTele Tena Service` sc ON sc.name=o.service
        JOIN tt_profile p ON p.user=o.clinician
        WHERE o.active=1 AND sc.active=1 ORDER BY o.id''')
    offer = next((item for item in candidates
                  if hmac.compare_digest(_booking_link_token(item.id), token)), None)
    if not offer:
        fail('This booking link is unavailable', 'booking_link_unavailable')
    approved(offer.clinician)
    approved_service(offer.clinician, offer.service)
    return {'offering': offer.id, 'service': offer.service_label,
            'clinician': offer.display_name, 'price': offer.price,
            'minutes': offer.minutes, 'format': offer.consultation_format,
            'timezone': offer.timezone}


def _zone(name):
    if not isinstance(name, str) or len(name) > 80:
        fail('Choose a valid timezone', 'schedule_timezone_invalid')
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        fail('Choose a valid timezone', 'schedule_timezone_invalid')


def _json(value, label):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            fail('Review the ' + label + ' fields', 'schedule_data_invalid')
    if not isinstance(value, list):
        fail('Review the ' + label + ' fields', 'schedule_data_invalid')
    return value


def _local_time(value, field='time'):
    try:
        parsed = time.fromisoformat(value)
        if parsed.tzinfo or parsed.second or parsed.microsecond:
            fail('Enter a time in whole minutes', 'schedule_' + field + '_invalid')
        return parsed
    except (TypeError, ValueError):
        fail('Enter a valid ' + field.replace('_', ' ') + ' (HH:MM)', 'schedule_' + field + '_invalid')


def _interval_time(item, field):
    """Accept legacy start/end and the documented start_local/end_local API shape."""
    local = field + '_local'
    if field in item and local in item and item[field] != item[local]:
        fail('Conflicting interval times', 'schedule_interval_invalid')
    return item.get(local, item.get(field))


def _db_time(value):
    if isinstance(value, timedelta):
        return (datetime.min + value).time()
    return value


def _validate_intervals(intervals, allow_weekday=True):
    if len(intervals) > 160:
        fail('Remove some intervals; the limit is 160', 'schedule_intervals_limit')
    result = []
    for item in intervals:
        if not isinstance(item, dict):
            fail('Review the interval fields', 'schedule_interval_invalid')
        weekday = integer(item.get('weekday'), 0, 6) if allow_weekday else None
        start = _local_time(_interval_time(item, 'start'), 'start')
        end = _local_time(_interval_time(item, 'end'), 'end')
        if end <= start:
            fail('End time must be after start time', 'schedule_interval_order')
        result.append({'weekday': weekday, 'start': start, 'end': end})
    ordered = sorted(result, key=lambda i: (i['weekday'] if allow_weekday else 0, i['start']))
    for left, right in zip(ordered, ordered[1:]):
        if (not allow_weekday or left['weekday'] == right['weekday']) and right['start'] < left['end']:
            fail('Times on the same day cannot overlap', 'schedule_interval_overlap')
    return result


def _validate_exceptions(value):
    items = _json(value, 'date exceptions')
    if len(items) > 366:
        fail('Too many date exceptions')
    result = []
    for item in items:
        if not isinstance(item, dict) or item.get('kind') not in ('unavailable', 'replace', 'break'):
            fail('Invalid date exception')
        try:
            local_date = date.fromisoformat(item.get('date', ''))
        except (TypeError, ValueError):
            fail('Invalid exception date')
        kind = item['kind']
        if kind == 'unavailable':
            result.append({'date': local_date, 'kind': kind, 'start': None, 'end': None})
        else:
            start = _local_time(_interval_time(item, 'start'), 'exception_start')
            end = _local_time(_interval_time(item, 'end'), 'exception_end')
            if end <= start:
                fail('Exception end time must be after its start', 'schedule_exception_order')
            result.append({'date': local_date, 'kind': kind, 'start': start, 'end': end})
    for day in {x['date'] for x in result}:
        daily = [x for x in result if x['date'] == day]
        if any(x['kind'] == 'unavailable' for x in daily) and len(daily) != 1:
            fail('Unavailable dates cannot also have intervals')
        for kind in ('replace', 'break'):
            _validate_intervals([{'start': x['start'].isoformat(), 'end': x['end'].isoformat()}
                                 for x in daily if x['kind'] == kind], allow_weekday=False)
        if any(x['kind'] == 'replace' for x in daily) and any(x['kind'] == 'break' for x in daily):
            pass  # Breaks intentionally subtract time from replacement intervals.
    return result


@frappe.whitelist(methods=['POST'])
def save_schedule(offering, schedule_name, timezone_name, consultation_format,
                  confirmation_mode, minimum_notice_minutes, horizon_days,
                  buffer_before, buffer_after, intervals, exceptions, status='Draft'):
    clinician = actor('Tele Tena Clinician')
    savepoint = 'tt_schedule_' + uuid.uuid4().hex
    frappe.db.savepoint(savepoint)
    try:
        profile('clinician', True)
        approved(clinician, True)
        offer = one('SELECT * FROM tt_offering WHERE id=%s AND clinician=%s AND active=1 FOR UPDATE',
                    (offering, clinician))
        approved_service(clinician, offer.service, True)
        zone = _zone(timezone_name)
        name = text(schedule_name, 120)
        if consultation_format not in ('video', 'audio') or confirmation_mode not in ('automatic', 'manual'):
            fail('Choose a supported consultation format and confirmation preference')
        if status not in ('Draft', 'Published', 'Paused'):
            fail('Invalid schedule status')
        notice = integer(minimum_notice_minutes, 0, 60 * 24 * 30)
        horizon = integer(horizon_days, 1, 365)
        before = integer(buffer_before, 0, 240)
        after = integer(buffer_after, 0, 240)
        weekly = _validate_intervals(_json(intervals, 'weekly availability'))
        dates = _validate_exceptions(exceptions)
        if status == 'Published' and not weekly and not any(item['kind'] == 'replace' for item in dates):
            fail('Add at least one available time before publishing', 'schedule_times_required')
        schedule = rows('SELECT id FROM tt_schedule WHERE offering=%s FOR UPDATE', (offering,))
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        schedule_id = schedule[0].id if schedule else str(uuid.uuid4())
        if schedule:
            frappe.db.sql('''UPDATE tt_schedule SET schedule_name=%s,timezone=%s,consultation_format=%s,
                confirmation_mode=%s,minimum_notice_minutes=%s,horizon_days=%s,buffer_before=%s,
                buffer_after=%s,status=%s,modified=%s WHERE id=%s''',
                (name, zone.key, consultation_format, confirmation_mode, notice, horizon, before, after,
                 status, now, schedule_id))
            frappe.db.sql('DELETE FROM tt_schedule_rule WHERE schedule_id=%s', (schedule_id,))
            frappe.db.sql('DELETE FROM tt_schedule_exception WHERE schedule_id=%s', (schedule_id,))
        else:
            frappe.db.sql('''INSERT INTO tt_schedule
                (id,clinician,offering,schedule_name,timezone,consultation_format,confirmation_mode,
                 minimum_notice_minutes,horizon_days,buffer_before,buffer_after,status,created,modified)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                (schedule_id, clinician, offering, name, zone.key, consultation_format, confirmation_mode,
                 notice, horizon, before, after, status, now, now))
        for interval in weekly:
            frappe.db.sql('''INSERT INTO tt_schedule_rule (id,schedule_id,weekday,start_local,end_local)
                VALUES (%s,%s,%s,%s,%s)''',
                (str(uuid.uuid4()), schedule_id, interval['weekday'], interval['start'], interval['end']))
        for exception in dates:
            frappe.db.sql('''INSERT INTO tt_schedule_exception
                (id,schedule_id,local_date,kind,start_local,end_local) VALUES (%s,%s,%s,%s,%s,%s)''',
                (str(uuid.uuid4()), schedule_id, exception['date'], exception['kind'],
                 exception['start'], exception['end']))
        return {'id': schedule_id, 'status': status, 'saved': True}
    except (frappe.PermissionError, frappe.ValidationError):
        frappe.db.rollback(save_point=savepoint)
        raise
    except Exception:
        frappe.db.rollback(save_point=savepoint)
        raise


@query()
def schedules():
    clinician = actor('Tele Tena Clinician')
    profile('clinician')
    result = rows('''SELECT sc.*,o.service,o.price,o.minutes,
        COALESCE(NULLIF(o.title,''),s.service_label) AS service_label
        FROM tt_schedule sc JOIN tt_offering o ON o.id=sc.offering
        JOIN `tabTele Tena Service` s ON s.name=o.service
        WHERE sc.clinician=%s ORDER BY sc.modified DESC''', (clinician,))
    for schedule in result:
        schedule.intervals = rows('''SELECT weekday,start_local,end_local FROM tt_schedule_rule
            WHERE schedule_id=%s ORDER BY weekday,start_local''', (schedule.id,))
        schedule.exceptions = rows('''SELECT local_date `date`,kind,start_local,end_local
            FROM tt_schedule_exception WHERE schedule_id=%s ORDER BY local_date,start_local''', (schedule.id,))
        for interval in schedule.intervals:
            interval.start_local = _db_time(interval.start_local).strftime('%H:%M')
            interval.end_local = _db_time(interval.end_local).strftime('%H:%M')
        for exception in schedule.exceptions:
            if exception.start_local is not None:
                exception.start_local = _db_time(exception.start_local).strftime('%H:%M')
            if exception.end_local is not None:
                exception.end_local = _db_time(exception.end_local).strftime('%H:%M')
    return result


def _valid_local(local, zone):
    first = local.replace(tzinfo=zone, fold=0)
    round_trip = first.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)
    if round_trip != local:
        return None  # DST gap.
    second = local.replace(tzinfo=zone, fold=1)
    if first.utcoffset() != second.utcoffset():
        return None  # Ambiguous wall time; never guess a fold.
    return first.astimezone(timezone.utc).replace(tzinfo=None)


def _ranges_for_day(schedule, day):
    exceptions = rows('''SELECT kind,start_local,end_local FROM tt_schedule_exception
        WHERE schedule_id=%s AND local_date=%s ORDER BY start_local''', (schedule.id, day))
    if any(e.kind == 'unavailable' for e in exceptions):
        return [], []
    replacement = [(_db_time(e.start_local), _db_time(e.end_local)) for e in exceptions if e.kind == 'replace']
    breaks = [(_db_time(e.start_local), _db_time(e.end_local)) for e in exceptions if e.kind == 'break']
    if replacement:
        return replacement, breaks
    weekly = rows('''SELECT start_local,end_local FROM tt_schedule_rule
        WHERE schedule_id=%s AND weekday=%s ORDER BY start_local''', (schedule.id, day.weekday()))
    return [(_db_time(w.start_local), _db_time(w.end_local)) for w in weekly], breaks


def _blocked(row, start, end, before, after):
    start -= timedelta(minutes=before)
    end += timedelta(minutes=after)
    existing_start = row.start - timedelta(minutes=int(row.buffer_before or 0))
    existing_end = row.end + timedelta(minutes=int(row.buffer_after or 0))
    return start < existing_end and existing_start < end


def _slots_for_day(schedule, offer, day, booked, patient_booked=(), minimum_notice_override=None):
    zone = ZoneInfo(schedule.timezone)
    intervals, breaks = _ranges_for_day(schedule, day)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    horizon_end = now + timedelta(days=int(schedule.horizon_days))
    notice = schedule.minimum_notice_minutes if minimum_notice_override is None else minimum_notice_override
    minimum = now + timedelta(minutes=int(notice))
    result = []
    duration = int(offer.minutes)
    for local_start, local_end in intervals:
        cursor = datetime.combine(day, local_start)
        final = datetime.combine(day, local_end)
        while cursor + timedelta(minutes=duration) <= final:
            start = _valid_local(cursor, zone)
            if start:
                end = start + timedelta(minutes=duration)
                if start >= minimum and start <= horizon_end:
                    local_finish = (end.replace(tzinfo=timezone.utc).astimezone(zone)
                                    .replace(tzinfo=None))
                    if local_finish <= final:
                        break_hit = any(cursor < datetime.combine(day, b) + (datetime.combine(day, e)-datetime.combine(day, b))
                                        and datetime.combine(day, b) < local_finish for b, e in breaks)
                        if not break_hit and not any(_blocked(row, start, end, schedule.buffer_before,
                                                              schedule.buffer_after) for row in booked) \
                                and not any(row.start < end and row.end > start for row in patient_booked):
                            result.append((start, end, cursor))
            cursor += timedelta(minutes=SLOT_STEP_MINUTES)
    return result


def _schedule_for(offering, lock=False):
    return one('SELECT * FROM tt_schedule WHERE offering=%s' + (' FOR UPDATE' if lock else ''),
               (offering,)) if rows('SELECT id FROM tt_schedule WHERE offering=%s', (offering,)) else None


def _minute_ceiling(value):
    if value.second or value.microsecond:
        return value.replace(second=0, microsecond=0) + timedelta(minutes=1)
    return value


def immediate_start(schedule, offer, clinician, patient, earliest_start, latest_start,
                    booked=None, patient_booked=None, preferred_start=None):
    """Find a feasible continuous start for a fresh immediate request.

    Immediate requests are not constrained to the pre-generated 15-minute
    direct-booking grid. Their allowed window is supplied by the request; the
    clinician's explicit fresh presence authorizes bypassing scheduled notice.
    The entire session and both sides' buffers must fit before a start is returned.
    """
    if not schedule or schedule.status != 'Published' or not offer:
        return None
    earliest_start = earliest_start.replace(tzinfo=None)
    latest_start = latest_start.replace(tzinfo=None)
    if preferred_start is not None:
        starts = (preferred_start.replace(tzinfo=None),)
    else:
        cursor = _minute_ceiling(earliest_start)
        # The service policy bounds request windows to at most 60 minutes.
        values = []
        while cursor <= latest_start:
            values.append(cursor)
            cursor += timedelta(minutes=1)
        starts = values
    try:
        zone = ZoneInfo(schedule.timezone)
    except (ZoneInfoNotFoundError, ValueError):
        return None
    if booked is None:
        booked = rows('''SELECT id,start,end,buffer_before,buffer_after FROM tt_appointment
            WHERE clinician=%s AND state IN ('Booked','PendingConfirmation')
            AND (expires_at IS NULL OR expires_at>UTC_TIMESTAMP(6))
            AND start<%s AND end>%s''',
            (clinician, latest_start + timedelta(days=1), earliest_start - timedelta(days=1)))
    if patient_booked is None:
        patient_booked = rows('''SELECT id,start,end FROM tt_appointment WHERE patient=%s
            AND state IN ('Booked','PendingConfirmation')
            AND (expires_at IS NULL OR expires_at>UTC_TIMESTAMP(6))
            AND start<%s AND end>%s''',
            (patient, latest_start + timedelta(days=1), earliest_start - timedelta(days=1)))
    duration = timedelta(minutes=int(offer.minutes))
    horizon_end = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=int(schedule.horizon_days))
    day_ranges = {}
    for candidate in starts:
        if candidate < earliest_start or candidate > latest_start or candidate <= datetime.now(timezone.utc).replace(tzinfo=None):
            continue
        end = candidate + duration
        if candidate > horizon_end:
            continue
        local_start = candidate.replace(tzinfo=timezone.utc).astimezone(zone)
        local_end = end.replace(tzinfo=timezone.utc).astimezone(zone)
        day = local_start.date()
        if local_end.date() != day or local_start.utcoffset() != local_end.utcoffset():
            continue
        if day not in day_ranges:
            day_ranges[day] = _ranges_for_day(schedule, day)
        intervals, breaks = day_ranges[day]
        start_wall = local_start.replace(tzinfo=None).time()
        end_wall = local_end.replace(tzinfo=None).time()
        if _valid_local(local_start.replace(tzinfo=None), zone) is None:
            continue
        if not any(start_wall >= interval_start and end_wall <= interval_end
                   for interval_start, interval_end in intervals):
            continue
        if any(start_wall < break_end and break_start < end_wall for break_start, break_end in breaks):
            continue
        if any(_blocked(row, candidate, end, int(schedule.buffer_before), int(schedule.buffer_after))
               for row in booked):
            continue
        if any(row.start < end and row.end > candidate for row in patient_booked):
            continue
        return candidate
    return None


def validate_slot(offer, start, patient, lock=True, immediate_ready=False, immediate_window=None,
                  exclude_appointment=None):
    """Recompute an exact offered slot while the booking gate/clinician are locked."""
    schedule = _schedule_for(offer.id, lock)
    if schedule:
        if schedule.status != 'Published':
            fail('This schedule is not currently published', 'schedule_unavailable')
        if int(schedule.minimum_notice_minutes) < 0 or int(schedule.horizon_days) < 1:
            fail('Schedule is unavailable')
        zone = ZoneInfo(schedule.timezone)
        day = start.replace(tzinfo=timezone.utc).astimezone(zone).date()
        booked = rows('''SELECT id,start,end,buffer_before,buffer_after FROM tt_appointment
            WHERE clinician=%s AND state IN ('Booked','PendingConfirmation')
            AND (expires_at IS NULL OR expires_at>UTC_TIMESTAMP(6))
            AND start<%s AND end>%s''',
            (offer.clinician, start + timedelta(days=1), start - timedelta(days=1)))
        # Mutual rescheduling retains the existing booking until consent. Its own
        # occupied interval must not conflict with its proposed replacement.
        if exclude_appointment:
            booked = [item for item in booked if item.id != exclude_appointment]
        patient_booked = rows('''SELECT id,start,end FROM tt_appointment WHERE patient=%s
            AND state IN ('Booked','PendingConfirmation')
            AND (expires_at IS NULL OR expires_at>UTC_TIMESTAMP(6))
            AND start<%s AND end>%s''',
            (patient, start + timedelta(days=1), start - timedelta(days=1)))
        if exclude_appointment:
            patient_booked = [item for item in patient_booked if item.id != exclude_appointment]
        if immediate_ready:
            earliest, latest = immediate_window or (start, start)
            match = immediate_start(schedule, offer, offer.clinician, patient, earliest, latest,
                                    booked, patient_booked, preferred_start=start)
        else:
            valid = _slots_for_day(schedule, offer, day, booked, patient_booked)
            match = next((slot[0] for slot in valid if slot[0] == start), None)
        if not match:
            fail('That time is no longer available. Choose another slot.', 'slot_unavailable')
        return schedule
    # Legacy one-off windows remain supported; arbitrary instants are still rejected.
    end = start + timedelta(minutes=int(offer.minutes))
    available = rows('SELECT start,end FROM tt_availability WHERE clinician=%s AND start<=%s AND end>=%s',
                     (offer.clinician, start, end))
    if not available:
        fail('Outside availability', 'outside_availability')
    return None


@query()
def calendar(offering, from_date=None, days=35, display_timezone=None):
    user = actor()
    offer = one('SELECT * FROM tt_offering WHERE id=%s AND active=1', (offering,))
    roles = set(frappe.get_roles(user))
    if 'Tele Tena Patient' not in roles and not ('Tele Tena Clinician' in roles and offer.clinician == user):
        frappe.throw('Schedule unavailable', frappe.PermissionError)
    approved(offer.clinician)
    approved_service(offer.clinician, offer.service)
    display_zone = _zone(display_timezone) if display_timezone else None
    schedule = _schedule_for(offering)
    day_count = integer(days, 1, 62)
    if schedule:
        clinic_zone = ZoneInfo(schedule.timezone)
        if display_zone and from_date:
            display_from = date.fromisoformat(from_date)
            from_local = datetime.combine(display_from, time.min).replace(tzinfo=display_zone)
            start_day = (from_local.astimezone(clinic_zone).date() - timedelta(days=1))
            end_day = start_day + timedelta(days=day_count + 3)
        else:
            start_day = date.fromisoformat(from_date) if from_date else datetime.now(clinic_zone).date()
            end_day = start_day + timedelta(days=day_count)
        start_utc = datetime.combine(start_day, time.min).replace(tzinfo=clinic_zone).astimezone(timezone.utc).replace(tzinfo=None)
        end_utc = datetime.combine(end_day, time.max).replace(tzinfo=clinic_zone).astimezone(timezone.utc).replace(tzinfo=None)
    else:
        start_day = date.fromisoformat(from_date) if from_date else datetime.now(timezone.utc).date()
        start_utc = datetime.combine(start_day, time.min)
        end_utc = start_utc + timedelta(days=day_count + 1)
        end_day = start_day + timedelta(days=day_count + 1)
        clinic_zone = display_zone or timezone.utc
    booked = rows('''SELECT start,end,buffer_before,buffer_after FROM tt_appointment
        WHERE clinician=%s AND state IN ('Booked','PendingConfirmation')
        AND (expires_at IS NULL OR expires_at>UTC_TIMESTAMP(6)) AND start<%s AND end>%s''',
        (offer.clinician, end_utc + timedelta(days=1), start_utc - timedelta(days=1)))
    patient_booked = rows('''SELECT start,end FROM tt_appointment WHERE patient=%s
        AND state IN ('Booked','PendingConfirmation') AND (expires_at IS NULL OR expires_at>UTC_TIMESTAMP(6))
        AND start<%s AND end>%s''',
        (user, end_utc, start_utc)) if 'Tele Tena Patient' in roles else []
    grouped = {}
    if schedule and schedule.status == 'Published':
        day = start_day
        iterations = (end_day - start_day).days
        for _ in range(iterations):
            for start, end, local_start in _slots_for_day(schedule, offer, day, booked, patient_booked):
                display_start = start.replace(tzinfo=timezone.utc).astimezone(display_zone or clinic_zone)
                display_day = display_start.date().isoformat()
                if from_date and not (date.fromisoformat(from_date) <= display_start.date() < date.fromisoformat(from_date) + timedelta(days=day_count)):
                    continue
                grouped.setdefault(display_day, []).append({
                    'start': start.isoformat(timespec='seconds') + 'Z',
                    'end': end.isoformat(timespec='seconds') + 'Z',
                    'local_time': display_start.strftime('%H:%M'),
                    'timezone': (display_zone or clinic_zone).key,
                    'schedule_timezone': schedule.timezone,
                })
            day += timedelta(days=1)
    elif not schedule:
        legacy = rows('''SELECT start,end FROM tt_availability WHERE clinician=%s
            AND end>%s AND start<%s ORDER BY start''', (offer.clinician, start_utc, end_utc))
        for window in legacy:
            cursor = window.start
            while cursor + timedelta(minutes=offer.minutes) <= window.end:
                end = cursor + timedelta(minutes=offer.minutes)
                if not any(_blocked(row, cursor, end, 0, 0) for row in booked) and not any(
                        row.start < end and row.end > cursor for row in patient_booked):
                    display_start = cursor.replace(tzinfo=timezone.utc).astimezone(display_zone or timezone.utc)
                    grouped.setdefault(display_start.date().isoformat(), []).append({
                        'start': cursor.isoformat(timespec='seconds') + 'Z',
                        'end': end.isoformat(timespec='seconds') + 'Z',
                        'local_time': display_start.strftime('%H:%M'),
                        'timezone': (display_zone or timezone.utc).key,
                        'schedule_timezone': None,
                    })
                cursor += timedelta(minutes=SLOT_STEP_MINUTES)
    return {'days': [{'date': key, 'slots': grouped[key]} for key in sorted(grouped)],
            'timezone': (display_zone or clinic_zone).key,
            'schedule_timezone': schedule.timezone if schedule else None,
            'duration': offer.minutes,
            'format': schedule.consultation_format if schedule else 'video',
            'price': offer.price}
