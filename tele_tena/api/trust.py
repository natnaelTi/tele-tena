"""Encounter-authorized, structured patient session-experience feedback."""
import uuid

import frappe

from tele_tena.api.journey import actor, command, fail, integer, one, profile, rows
from tele_tena.trust_metrics import SESSION_EXPERIENCE_VERSION


@command
def submit_session_feedback(appointment, rating):
    """Save one non-clinical experience rating for a finalized encounter."""
    patient = actor('Tele Tena Patient')
    value = integer(rating, 1, 5)
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    profile('patient', lock=True)
    item = rows('''SELECT id,state,patient,clinician FROM tt_appointment
        WHERE id=%s AND patient=%s FOR UPDATE''', (appointment, patient))
    if not item:
        frappe.throw('Feedback unavailable for this consultation', frappe.PermissionError)
    item = item[0]

    previous = rows('''SELECT rating,created_at FROM tt_session_feedback
        WHERE appointment=%s AND patient=%s''', (item.id, patient))
    if previous:
        if int(previous[0].rating) == value:
            return {'submitted': True, 'idempotent': True}
        fail('Feedback for this consultation has already been submitted', 'feedback_already_submitted')

    if item.state != 'Completed':
        fail('Feedback is available after the clinician completes the consultation', 'feedback_not_ready')
    call = rows("SELECT state FROM tt_consultation WHERE appointment=%s", (item.id,))
    note = rows("SELECT status FROM tt_consultation_note WHERE appointment=%s", (item.id,))
    if not call or call[0].state != 'Ended' or not note or note[0].status != 'Finalized':
        fail('Feedback is available after the consultation is finalized', 'feedback_not_ready')

    frappe.db.sql('''INSERT INTO tt_session_feedback
        (id,appointment,patient,clinician,rating,metric_version,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,UTC_TIMESTAMP(6))''',
        (str(uuid.uuid4()), item.id, patient, item.clinician, value, SESSION_EXPERIENCE_VERSION))
    from tele_tena.api.presentation import _event
    _event(item.id, 'PatientSessionExperienceSubmitted', patient)
    return {'submitted': True, 'idempotent': False}
