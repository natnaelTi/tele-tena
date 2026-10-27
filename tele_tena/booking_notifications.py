"""Transactional notice outbox;neutral content,explicit delivery opt-in,one send claim."""
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import uuid
import frappe
from tele_tena.api.journey import actor,rows,query,command


def create(appointment,state,plan_id=None):
    if state not in ('Booked','PendingConfirmation'):return
    event='Confirmed' if state=='Booked' else 'Pending'
    if event=='Confirmed':
        frappe.db.sql("UPDATE tt_booking_notice SET state='Superseded',modified=UTC_TIMESTAMP(6) WHERE appointment=%s AND event='Pending' AND state IN ('Available','Pending','Unavailable','Rejected')",(appointment,))
    found=rows('SELECT patient,clinician,offering FROM tt_appointment WHERE id=%s',(appointment,))
    if not found:return
    app=found[0];recipients={app.patient,app.clinician}
    # Both separately consented adults receive neutral booking logistics,never
    # one another's intake,identity or clinical summary. The booking command
    # supplies the validated plan before its appointment link is committed.
    people=rows("""SELECT p.user FROM tt_couple_participant p JOIN tt_couple_plan cp ON cp.id=p.plan
      WHERE (cp.appointment=%s OR cp.id=%s) AND cp.payer=%s AND cp.offering=%s
      AND p.state='Consented'""",(appointment,plan_id,app.patient,app.offering))
    recipients.update(p.user for p in people)
    if event=='Pending':
        policy=rows('SELECT policy_snapshot,created,payment_mode FROM tt_appointment WHERE id=%s',(appointment,))[0]
        if policy.payment_mode=='Offline':
            payment=rows("SELECT verified_at FROM tt_direct_payment WHERE appointment=%s AND reference_type='Appointment'",(appointment,))
            if not payment or not payment[0].verified_at:return
            policy.created=payment[0].verified_at
        import json
        if json.loads(policy.policy_snapshot or '{}').get('notifications',{}).get('version')=='booking-notices-v2':
            frappe.db.sql('INSERT IGNORE INTO tt_confirmation_observation (appointment,clinician,requested_at) VALUES (%s,%s,%s)',(appointment,app.clinician,policy.created))
    for user in sorted(recipients):
        prefs=rows('SELECT * FROM tt_notice_preference WHERE user=%s',(user,))
        channels=['in_app']+[channel for channel in ('email','sms') if not prefs or prefs[0][channel+'_enabled']]
        for channel in channels:
            frappe.db.sql('''INSERT IGNORE INTO tt_booking_notice
              (id,appointment,user,event,channel,state,created,modified)
              VALUES (%s,%s,%s,%s,%s,%s,UTC_TIMESTAMP(6),UTC_TIMESTAMP(6))''',
              (str(uuid.uuid4()),appointment,user,event,channel,'Available' if channel=='in_app' else 'Pending'))


@query()
def notices():
    user=actor()
    return rows('''SELECT n.id,n.appointment,n.event,n.channel,n.state,n.created,n.read_at,a.state appointment_state
      FROM tt_booking_notice n JOIN tt_appointment a ON a.id=n.appointment WHERE n.user=%s ORDER BY n.created DESC LIMIT 50''',(user,))


@command
def mark_read(id):
    user=actor();frappe.db.sql('UPDATE tt_booking_notice SET read_at=COALESCE(read_at,UTC_TIMESTAMP(6)) WHERE id=%s AND user=%s',(id,user));return {'read':True}


@query()
def preferences():
    user=actor();found=rows('SELECT email_enabled,sms_enabled FROM tt_notice_preference WHERE user=%s',(user,))
    return dict(found[0]) if found else {'email_enabled':True,'sms_enabled':True}


@command
def save_preferences(email_enabled=False,sms_enabled=False):
    from tele_tena.api.journey import boolean
    user=actor();email=boolean(email_enabled);sms=boolean(sms_enabled)
    frappe.db.sql('SELECT name FROM tabUser WHERE name=%s FOR UPDATE',(user,))
    before=preferences()
    frappe.db.sql('''INSERT INTO tt_notice_preference VALUES (%s,%s,%s)
      ON DUPLICATE KEY UPDATE email_enabled=VALUES(email_enabled),sms_enabled=VALUES(sms_enabled)''',(user,email,sms))
    if before!={'email_enabled':email,'sms_enabled':sms}:
        from tele_tena.notifications import emit
        emit(user,'notice-preferences:'+str(uuid.uuid4()),'AccountUpdated')
    return preferences()


@command
def retry(id):
    user=actor()
    # Uncertain/Sending/provider-accepted requests may already have been delivered.
    # They can never be retried without a provider-supported reconciliation result.
    found=rows("SELECT state,attempts FROM tt_booking_notice WHERE id=%s AND user=%s FOR UPDATE",(id,user))
    if not found or found[0].state not in ('Unavailable','Rejected') or found[0].attempts>=3:
        frappe.throw('This delivery cannot safely be retried.',frappe.PermissionError)
    frappe.db.sql("UPDATE tt_booking_notice SET state='Pending',modified=UTC_TIMESTAMP(6) WHERE id=%s",(id,))
    return {'state':'Pending'}


EVENT_STATES={**{k:('PendingConfirmation','Booked','Expired','Cancelled','Completed') for k in ('PaymentSubmitted','PaymentVerified','PaymentCorrection','PaymentReconciliation','PaymentReminder','PaymentVerificationReminder')},'Confirmed':('Booked',),'Pending':('PendingConfirmation',),'ConfirmationReminder':('PendingConfirmation',),
              'AppointmentReminder':('Booked',),'Cancelled':('Cancelled',),'Declined':('Cancelled',),'Expired':('Expired',)}

def dispatch():
    # A crashed/uncertain send is not retried automatically:SMTP/SMS lack a verified
    # provider idempotency key. Pending rows are claimed durably before external I/O.
    frappe.db.sql("UPDATE tt_booking_notice SET state='Unknown',modified=UTC_TIMESTAMP(6) WHERE state='Sending' AND modified<UTC_TIMESTAMP(6)-INTERVAL 15 MINUTE")
    frappe.db.commit()
    items=rows("SELECT id FROM tt_booking_notice WHERE state='Pending' AND channel IN ('email','sms') ORDER BY created LIMIT 20")
    for item in items:
        frappe.db.sql("SELECT id FROM tt_booking_notice WHERE id=%s FOR UPDATE",(item.id,))
        notice=rows("SELECT * FROM tt_booking_notice WHERE id=%s AND state='Pending'",(item.id,))
        if not notice:frappe.db.commit();continue
        notice=notice[0]
        app=rows('SELECT * FROM tt_appointment WHERE id=%s',(notice.appointment,))
        if not app or app[0].state not in EVENT_STATES.get(notice.event,()):
            frappe.db.sql("UPDATE tt_booking_notice SET state='Superseded',modified=UTC_TIMESTAMP(6) WHERE id=%s",(item.id,));frappe.db.commit();continue
        if notice.event.startswith('Payment'):
            payments=rows('SELECT p.state FROM tt_direct_payment p JOIN tt_direct_payment_event e ON e.payment=p.id WHERE e.id=%s',(notice.context_key,))
            valid={'PaymentReminder':('AwaitingPayment','CorrectionRequired'),'PaymentVerificationReminder':('Submitted',),'PaymentSubmitted':('Submitted','ReconciliationRequired'),'PaymentVerified':('Verified',),'PaymentCorrection':('CorrectionRequired','Rejected'),'PaymentReconciliation':('ReconciliationRequired','RefundRequired','RefundReported','RefundConfirmed')}
            if not payments or payments[0].state not in valid.get(notice.event,()):
                frappe.db.sql("UPDATE tt_booking_notice SET state='Superseded' WHERE id=%s",(item.id,));frappe.db.commit();continue
        if not frappe.db.get_value('User',notice.user,'enabled'):
            frappe.db.sql("UPDATE tt_booking_notice SET state='Superseded',modified=UTC_TIMESTAMP(6) WHERE id=%s",(item.id,));frappe.db.commit();continue
        if notice.user not in (app[0].patient,app[0].clinician):
            consent=rows("""SELECT 1 FROM tt_couple_participant p JOIN tt_couple_plan cp ON cp.id=p.plan
              WHERE cp.appointment=%s AND p.user=%s AND p.state='Consented'""",(notice.appointment,notice.user))
            if not consent:
                frappe.db.sql("UPDATE tt_booking_notice SET state='Superseded',modified=UTC_TIMESTAMP(6) WHERE id=%s",(item.id,));frappe.db.commit();continue
        prefs=rows('SELECT * FROM tt_notice_preference WHERE user=%s',(notice.user,))
        identities=rows('SELECT contact FROM tt_contact_identity WHERE user=%s AND channel=%s AND verified_at IS NOT NULL LIMIT 1',(notice.user,'phone' if notice.channel=='sms' else 'email'))
        if (prefs and not prefs[0][notice.channel+'_enabled']) or not identities:
            frappe.db.sql("UPDATE tt_booking_notice SET state='Unavailable',modified=UTC_TIMESTAMP(6) WHERE id=%s",(item.id,));frappe.db.commit();continue
        if notice.channel=='sms':
            from tele_tena.review import phone_enabled
            from tele_tena.api.phone_auth import reserve_sms_budget,_now
            frappe.db.sql('SELECT id FROM tt_otp_gate WHERE id=1 FOR UPDATE')
            if not phone_enabled() or not reserve_sms_budget(_now()):
                frappe.db.sql("UPDATE tt_booking_notice SET state='Unavailable',modified=UTC_TIMESTAMP(6) WHERE id=%s",(item.id,));frappe.db.commit();continue
        frappe.db.sql("UPDATE tt_booking_notice SET state='Sending',attempts=attempts+1,modified=UTC_TIMESTAMP(6) WHERE id=%s",(item.id,));frappe.db.commit()
        app=app[0];state='Unknown'
        label={'PaymentReminder':'direct payment awaiting submission','PaymentVerificationReminder':'payment receipt awaiting your verification','PaymentSubmitted':'payment submitted for verification','PaymentVerified':'payment receipt verified','PaymentCorrection':'payment correction requested','PaymentReconciliation':'payment reconciliation updated','Confirmed':'confirmed','Pending':'awaiting your confirmation' if notice.user==app.clinician else 'awaiting clinician confirmation',
               'ConfirmationReminder':'still awaiting your confirmation; please confirm or decline before the deadline',
               'AppointmentReminder':'coming up soon','Cancelled':'cancelled','Declined':'declined','Expired':'expired without confirmation'}.get(notice.event,'updated')
        when=app.start.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(app.timezone or 'Africa/Addis_Ababa')).strftime('%d %b %Y %H:%M')
        # Site-bound relative authenticated link;no permanent token or health text.
        link=frappe.utils.get_url('/teletena/'+('clinician' if notice.user==app.clinician else 'patient')+'/consultations/'+app.id)
        from urllib.parse import urlsplit,urlunsplit
        parsed=urlsplit(link)
        if parsed.hostname and not parsed.hostname.endswith('.localhost') and parsed.hostname not in ('localhost','127.0.0.1'):
            link=urlunsplit(('https',parsed.netloc,parsed.path,'',''))
        message=f'TeleTena appointment {label}. {when} ({app.timezone}). Reference {app.id[:8]}. Sign in: {link}'
        if notice.user==app.patient and notice.event in ('Confirmed','Pending') and rows('SELECT id FROM tt_journal WHERE event_ref=%s',('booking:'+app.id,)):
            minor=int(app.price);message+=f' Demonstration balance: ETB {minor//100}.{minor%100:02d} reserved. No external payment collected.'
        if notice.user==app.patient and notice.event in ('Cancelled','Declined','Expired') and rows('SELECT id FROM tt_journal WHERE event_ref=%s',('release:'+app.id,)):
            message+=' Demonstration balance reservation released. No external refund was processed.'
        if notice.event in ('Pending','ConfirmationReminder') and app.expires_at:
            deadline=app.expires_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(app.timezone or 'Africa/Addis_Ababa')).strftime('%d %b %Y %H:%M')
            message+=f' Response deadline: {deadline} ({app.timezone}).'
        try:
            if notice.channel=='email':
                from tele_tena.email_delivery import send_notice
                send_notice(identities[0].contact,message)
            else:
                from tele_tena.sms import send_notice
                send_notice(identities[0].contact,message)
            state='ProviderAccepted'
        except Exception as error:
            # Never log address,message,provider body or credentials. Unknown send
            # outcomes remain terminal and visible;never claim delivery.
            from tele_tena.sms import SMSRejected
            from tele_tena.email_delivery import DeliveryUnavailable
            state='Rejected' if isinstance(error,SMSRejected) and error.args==('provider_rejected',) else 'Unavailable' if (isinstance(error,SMSRejected) and error.args==('not_configured',)) or (isinstance(error,DeliveryUnavailable) and error.args==('email_not_configured',)) else 'Unknown'
        frappe.db.sql('UPDATE tt_booking_notice SET state=%s,modified=UTC_TIMESTAMP(6) WHERE id=%s',(state,item.id));frappe.db.commit()


def queue_external(appointment,event,recipients,channels=('email','sms'),context_key=''):
    if event not in EVENT_STATES:raise ValueError('Unsupported delivery event')
    for user in recipients:
        prefs=rows('SELECT * FROM tt_notice_preference WHERE user=%s',(user,))
        for channel in channels:
            state='Suppressed' if prefs and not prefs[0][channel+'_enabled'] else 'Pending'
            frappe.db.sql("""INSERT IGNORE INTO tt_booking_notice
              (id,appointment,user,event,channel,state,context_key,created,modified)
              VALUES (%s,%s,%s,%s,%s,%s,%s,UTC_TIMESTAMP(6),UTC_TIMESTAMP(6))""",
              (str(uuid.uuid4()),appointment,user,event,channel,state,context_key))


def process_reminders():
    """Minute scheduler job. Durable keys and gate serialize with clinician response."""
    from tele_tena.api.direct_payments import process_reminders as payment_reminders
    payment_reminders()
    from tele_tena.notifications import emit,participants
    from tele_tena.api.journey import one
    candidates=rows("""SELECT a.id FROM tt_appointment a JOIN tt_confirmation_observation o ON o.appointment=a.id
        WHERE a.state='PendingConfirmation' AND a.expires_at>UTC_TIMESTAMP(6)
        AND o.reminded_at IS NULL AND o.requested_at<=UTC_TIMESTAMP(6)-INTERVAL 3 MINUTE ORDER BY o.requested_at,a.id LIMIT 100""")
    for candidate in candidates:
        one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
        app=rows("SELECT * FROM tt_appointment WHERE id=%s AND state='PendingConfirmation' AND expires_at>UTC_TIMESTAMP(6) FOR UPDATE",(candidate.id,))
        observation=rows('SELECT * FROM tt_confirmation_observation WHERE appointment=%s AND reminded_at IS NULL FOR UPDATE',(candidate.id,))
        if not app or not observation:continue
        queue_external(candidate.id,'ConfirmationReminder',[app[0].clinician],('email',))
        emit(app[0].clinician,'confirmation-reminder:'+candidate.id,'ConfirmationReminder',candidate.id)
        frappe.db.sql('UPDATE tt_confirmation_observation SET reminded_at=UTC_TIMESTAMP(6) WHERE appointment=%s',(candidate.id,))
    # Only bookings explicitly accepting the new policy get automatic reminders.
    upcoming=rows("SELECT a.* FROM tt_appointment a WHERE a.state='Booked' AND a.start>UTC_TIMESTAMP(6) AND a.start<=UTC_TIMESTAMP(6)+INTERVAL 1 HOUR AND JSON_UNQUOTE(JSON_EXTRACT(IF(JSON_VALID(a.policy_snapshot),a.policy_snapshot,'{}'),'$.notifications.version'))='booking-notices-v2' AND NOT EXISTS (SELECT 1 FROM tt_user_notification n WHERE n.appointment=a.id AND n.kind='AppointmentReminder') ORDER BY a.start,a.id LIMIT 100")
    import json
    for app in upcoming:
        one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
        current=rows("SELECT * FROM tt_appointment WHERE id=%s AND state='Booked' AND start>UTC_TIMESTAMP(6) FOR UPDATE",(app.id,))
        if not current:continue
        app=current[0]
        if json.loads(app.policy_snapshot or '{}').get('notifications',{}).get('version')!='booking-notices-v2':continue
        for user in participants(app.id):emit(user,'appointment-reminder:'+app.id,'AppointmentReminder',app.id)
        queue_external(app.id,'AppointmentReminder',participants(app.id))

    # Reconcile neutral ended-call inbox events independently of the token/room
    # closure transaction; notification storage can never undo authoritative End.
    ended=rows("""SELECT a.* FROM tt_appointment a JOIN tt_consultation c ON c.appointment=a.id
        WHERE c.state='Ended' AND c.ended>=UTC_TIMESTAMP(6)-INTERVAL 7 DAY
        AND JSON_UNQUOTE(JSON_EXTRACT(IF(JSON_VALID(a.policy_snapshot),a.policy_snapshot,'{}'),'$.notifications.version'))='booking-notices-v2'
        AND NOT EXISTS (SELECT 1 FROM tt_user_notification n WHERE n.appointment=a.id AND n.kind='CallEnded')
        ORDER BY c.ended,a.id LIMIT 100""")
    for app in ended:
        if json.loads(app.policy_snapshot or '{}').get('notifications',{}).get('version')!='booking-notices-v2':continue
        for user in participants(app.id):emit(user,'CallEnded:'+app.id,'CallEnded',app.id)
