"""Owner-only neutral notification inbox. No health text or arbitrary destinations."""
import uuid
from datetime import datetime,timezone
import frappe
from tele_tena.api.journey import actor,rows,query,command

KINDS={
 'PaymentReminder':('Direct Payment Reminder','reminders'),
 'PaymentVerificationReminder':('Payment Verification Reminder','reminders'),
 'PaymentSubmitted':('Payment Submitted for Verification','appointments'),
 'PaymentVerified':('Payment Receipt Verified','appointments'),
 'PaymentCorrection':('Payment Correction Requested','appointments'),
 'PaymentReconciliation':('Payment Reconciliation Update','appointments'),
 'Confirmed':('Appointment Confirmed','appointments'),
 'Pending':('Awaiting Clinician Confirmation','appointments'),
 'ConfirmationReminder':('Booking Confirmation Reminder','appointments'),
 'AppointmentReminder':('Upcoming Appointment Reminder','reminders'),
 'Cancelled':('Appointment Cancelled','appointments'),
 'Declined':('Booking Request Declined','appointments'),
 'Expired':('Booking Request Expired','appointments'),
 'CallEnded':('Consultation Ended','consultations'),
 'Completed':('Consultation Completed','consultations'),
 'SummaryReady':('Shared Consultation Update Available','consultations'),
 'FollowUpReady':('Follow-Up Instructions Available','followups'),
 'TimeChanged':('Appointment Time Updated','appointments'),
 'TimeChangeRequested':('Appointment Time Change Requested','appointments'),
 'TimeChangeDeclined':('Appointment Time Change Declined','appointments'),
 'TimeChangeExpired':('Appointment Time Change Request Expired','appointments'),
 'TimeChangeWithdrawn':('Appointment Time Change Withdrawn','appointments'),
 'TimeChangeUnavailable':('Proposed Appointment Time Unavailable','appointments'),
 'AccountUpdated':('Account Settings Updated','account'),
 'SystemUpdate':('TeleTena System Update','system'),
}

def emit(user,event_key,kind,appointment=None):
    """Internal only. Caller supplies a stable durable event key, never clinical text."""
    if kind not in KINDS or not isinstance(event_key,str) or not 0<len(event_key)<=180:
        raise ValueError('Unsupported notification event')
    frappe.db.sql('''INSERT IGNORE INTO tt_user_notification
      (id,user,event_key,kind,appointment,created) VALUES (%s,%s,%s,%s,%s,UTC_TIMESTAMP(6))''',
      (str(uuid.uuid4()),user,event_key,kind,appointment))


def participants(appointment):
    found=rows('SELECT patient,clinician FROM tt_appointment WHERE id=%s',(appointment,))
    if not found:return set()
    app=found[0]
    people={app.patient,app.clinician}
    couple=rows('SELECT id FROM tt_couple_plan WHERE appointment=%s',(appointment,))
    if couple:
        people={app.clinician}
        people.update(p.user for p in rows("SELECT user FROM tt_couple_participant WHERE plan=%s AND state='Consented'",(couple[0].id,)))
    return people


def lifecycle(appointment,event,event_key=None):
    kind={'Cancelled':'Cancelled','Declined':'Declined','Expired':'Expired','CallEnded':'CallEnded',
          'Completed':'Completed','RescheduleAccepted':'TimeChanged',
          'RescheduleProposed':'TimeChangeRequested','RescheduleDeclined':'TimeChangeDeclined',
          'RescheduleExpired':'TimeChangeExpired','RescheduleWithdrawn':'TimeChangeWithdrawn',
          'RescheduleUnavailable':'TimeChangeUnavailable','RescheduleSlotUnavailable':'TimeChangeUnavailable'}.get(event)
    if event in ('Cancelled','Declined','Expired'):
        from tele_tena.booking_notifications import queue_external
        queue_external(appointment,event,participants(appointment))
    if kind:
        for user in participants(appointment):emit(user,kind+':'+(event_key or appointment),kind,appointment)
    if event in ('Confirmed','Declined','Expired'):
        frappe.db.sql('''UPDATE tt_confirmation_observation SET response=%s,
          first_presented_at=IF(%s='Expired',first_presented_at,COALESCE(first_presented_at,UTC_TIMESTAMP(6))),
          responded_at=IF(%s='Expired',responded_at,UTC_TIMESTAMP(6)),
          expired_at=IF(%s='Expired',UTC_TIMESTAMP(6),expired_at)
          WHERE appointment=%s AND response IS NULL''',(event,event,event,event,appointment))


@command
def confirmation_presented(appointment):
    from tele_tena.api.presentation import _authorized
    app,user,role=_authorized(appointment)
    if role!='clinician':frappe.throw('Confirmation prompt unavailable',frappe.PermissionError)
    if app.state=='PendingConfirmation':
        frappe.db.sql('UPDATE tt_confirmation_observation SET first_presented_at=COALESCE(first_presented_at,UTC_TIMESTAMP(6)) WHERE appointment=%s AND clinician=%s AND response IS NULL',(appointment,user))
    return {'recorded':True}


@query()
def feed():
    user=actor();result=[]
    # No body, notes, identities, phone numbers or emails in inbox projections.
    notices=rows('''SELECT id,kind,appointment,event_key,created,read_at FROM tt_user_notification
        WHERE user=%s ORDER BY created DESC LIMIT 100''',(user,))
    bookings=rows("""SELECT id,event kind,appointment,context_key,created,read_at FROM tt_booking_notice
        WHERE user=%s AND channel='in_app' AND state='Available' ORDER BY created DESC LIMIT 100""",(user,))
    payment_events=set()
    for source,items in (('user',notices),('booking',bookings)):
        for item in items:
            if item.kind not in KINDS:continue
            if item.appointment and user not in participants(item.appointment):continue
            href=None
            if item.kind.startswith('Payment'):
                from tele_tena.api.direct_payments import notice_path
                event_id=item.event_key[7:] if source=='user' and item.event_key.startswith('direct:') else item.get('context_key') or None
                href=notice_path(item.appointment,user,event_id)
                if not href:continue
                identity=(event_id,item.kind,href)
                if identity in payment_events:continue
                payment_events.add(identity)
            result.append({'id':item.id,'source':source,'kind':item.kind,'title':KINDS[item.kind][0],'href':href,
                           'category':KINDS[item.kind][1],'appointment':item.appointment,
                           'created':item.created.isoformat()+'Z','read':bool(item.read_at)})
    return sorted(result,key=lambda item:item['created'],reverse=True)[:100]


@command
def mark_read(id,source):
    user=actor()
    if source not in ('user','booking'):frappe.throw('Notification unavailable',frappe.PermissionError)
    table='tt_user_notification' if source=='user' else 'tt_booking_notice'
    found=rows(f"SELECT appointment,{'kind' if source=='user' else 'event'} notice_kind FROM {table} WHERE id=%s AND user=%s",(id,user))
    if not found or (found[0].appointment and user not in participants(found[0].appointment)):
        frappe.throw('Notification unavailable',frappe.PermissionError)
    frappe.db.sql(f'UPDATE {table} SET read_at=COALESCE(read_at,UTC_TIMESTAMP(6)) WHERE id=%s AND user=%s',(id,user))
    if found[0].notice_kind in ('Pending','ConfirmationReminder') and found[0].appointment and user==rows('SELECT clinician FROM tt_appointment WHERE id=%s',(found[0].appointment,))[0].clinician:
        confirmation_presented(found[0].appointment)
    return {'read':True}


def confirmation_metric(clinician):
    """90-day operational response among resolved, actually presented prompts only."""
    sample=rows('''SELECT response,first_presented_at,responded_at FROM tt_confirmation_observation
      WHERE clinician=%s AND requested_at>=UTC_TIMESTAMP(6)-INTERVAL 90 DAY
      AND first_presented_at IS NOT NULL AND response IS NOT NULL''',(clinician,))
    responded=[r for r in sample if r.responded_at and r.response in ('Confirmed','Declined')]
    timely=sum(0<=(r.responded_at-r.first_presented_at).total_seconds()<=180 for r in responded)
    count=len(sample)
    return {'metric_version':'booking-confirmation-response-v1','observation_window_days':90,
            'minimum_sample':5,'sample_count':count,'response_count':len(responded),'timely_count':timely,
            'expired_count':sum(r.response=='Expired' for r in sample),
            'rate_percent':int(timely*10000//count)/100 if count>=5 else None,
            'status':'available' if count>=5 else 'more_data_needed' if count else 'new'}


def published_content(appointment,revision,recipient_ids,shared,followups):
    """Participant row IDs are not account IDs. Resolve only this consented encounter."""
    app=rows('SELECT patient FROM tt_appointment WHERE id=%s',(appointment,))[0]
    couple=rows('SELECT id FROM tt_couple_plan WHERE appointment=%s',(appointment,))
    recipients=[]
    if shared:
        if not couple:recipients=[app.patient]
        elif recipient_ids:
            recipients=[p.user for p in rows("SELECT user FROM tt_couple_participant WHERE plan=%s AND state='Consented' AND id IN %s",(couple[0].id,tuple(recipient_ids)))]
    for user in recipients:emit(user,f'summary:{appointment}:{revision}','SummaryReady',appointment)
    for followup in followups:
        if not couple:continue
        targets=rows("SELECT user FROM tt_couple_participant WHERE plan=%s AND id=%s AND state='Consented'",(couple[0].id,followup.recipient))
        for target in targets:emit(target.user,f'followup:{appointment}:{revision}:{followup.recipient}','FollowUpReady',appointment)
