"""Transactional notice outbox;neutral content,explicit delivery opt-in,one send claim."""
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import uuid
import frappe
from tele_tena.api.journey import actor,rows,query,command


def create(appointment,state):
    if state not in ('Booked','PendingConfirmation'):return
    event='Confirmed' if state=='Booked' else 'Pending'
    found=rows('SELECT patient,clinician FROM tt_appointment WHERE id=%s',(appointment,))
    if not found:return
    for user in (found[0].patient,found[0].clinician):
        prefs=rows('SELECT * FROM tt_notice_preference WHERE user=%s',(user,))
        channels=['in_app']+[channel for channel in ('email','sms') if prefs and prefs[0][channel+'_enabled']]
        for channel in channels:
            frappe.db.sql('''INSERT IGNORE INTO tt_booking_notice
              (id,appointment,user,event,channel,state,created,modified)
              VALUES (%s,%s,%s,%s,%s,%s,UTC_TIMESTAMP(6),UTC_TIMESTAMP(6))''',
              (str(uuid.uuid4()),appointment,user,event,channel,'Available' if channel=='in_app' else 'Pending'))


@query()
def notices():
    user=actor()
    return rows('SELECT id,appointment,event,channel,state,created,read_at FROM tt_booking_notice WHERE user=%s ORDER BY created DESC LIMIT 50',(user,))


@command
def mark_read(id):
    user=actor();frappe.db.sql('UPDATE tt_booking_notice SET read_at=COALESCE(read_at,UTC_TIMESTAMP(6)) WHERE id=%s AND user=%s',(id,user));return {'read':True}


@query()
def preferences():
    user=actor();found=rows('SELECT email_enabled,sms_enabled FROM tt_notice_preference WHERE user=%s',(user,))
    return dict(found[0]) if found else {'email_enabled':False,'sms_enabled':False}


@command
def save_preferences(email_enabled=False,sms_enabled=False):
    from tele_tena.api.journey import boolean
    user=actor();email=boolean(email_enabled);sms=boolean(sms_enabled)
    frappe.db.sql('''INSERT INTO tt_notice_preference VALUES (%s,%s,%s)
      ON DUPLICATE KEY UPDATE email_enabled=VALUES(email_enabled),sms_enabled=VALUES(sms_enabled)''',(user,email,sms))
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
        if not app or (notice.event=='Confirmed' and app[0].state!='Booked') or (notice.event=='Pending' and app[0].state!='PendingConfirmation'):
            frappe.db.sql("UPDATE tt_booking_notice SET state='Superseded',modified=UTC_TIMESTAMP(6) WHERE id=%s",(item.id,));frappe.db.commit();continue
        prefs=rows('SELECT * FROM tt_notice_preference WHERE user=%s',(notice.user,))
        identities=rows('SELECT contact FROM tt_contact_identity WHERE user=%s AND channel=%s AND verified_at IS NOT NULL LIMIT 1',(notice.user,'phone' if notice.channel=='sms' else 'email'))
        if not prefs or not prefs[0][notice.channel+'_enabled'] or not identities:
            frappe.db.sql("UPDATE tt_booking_notice SET state='Unavailable',modified=UTC_TIMESTAMP(6) WHERE id=%s",(item.id,));frappe.db.commit();continue
        if notice.channel=='sms':
            from tele_tena.review import phone_enabled
            from tele_tena.api.phone_auth import reserve_sms_budget,_now
            frappe.db.sql('SELECT id FROM tt_otp_gate WHERE id=1 FOR UPDATE')
            if not phone_enabled() or not reserve_sms_budget(_now()):
                frappe.db.sql("UPDATE tt_booking_notice SET state='Unavailable',modified=UTC_TIMESTAMP(6) WHERE id=%s",(item.id,));frappe.db.commit();continue
        frappe.db.sql("UPDATE tt_booking_notice SET state='Sending',attempts=attempts+1,modified=UTC_TIMESTAMP(6) WHERE id=%s",(item.id,));frappe.db.commit()
        app=app[0];state='Unknown'
        label='confirmed' if notice.event=='Confirmed' else 'awaiting clinician approval'
        when=app.start.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(app.timezone or 'Africa/Addis_Ababa')).strftime('%d %b %Y %H:%M')
        # Site-bound relative authenticated link;no permanent token or health text.
        link=frappe.utils.get_url('/teletena/'+('patient' if notice.user==app.patient else 'clinician')+'/consultations/'+app.id)
        from urllib.parse import urlsplit,urlunsplit
        parsed=urlsplit(link)
        if parsed.hostname and not parsed.hostname.endswith('.localhost') and parsed.hostname not in ('localhost','127.0.0.1'):
            link=urlunsplit(('https',parsed.netloc,parsed.path,'',''))
        message=f'TeleTena appointment {label}. {when} ({app.timezone}). Reference {app.id[:8]}. Sign in: {link}'
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
