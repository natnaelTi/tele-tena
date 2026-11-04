"""Neutral transactional communication, sharing the appointment delivery outbox."""
import uuid
from datetime import datetime,timezone,timedelta
import frappe
from tele_tena.api.journey import rows,query

EVENTS = {
    'ApplicationSubmitted': ('Application Received — Under Review', 'account'),
    'ApplicationReviewUpdate': ('Application Review Update', 'account'),
    'ApplicationApproved': ('Professional Application Approved', 'account'),
    'ApplicationRejected': ('Professional Application Not Approved', 'account'),
    'ScopeResubmitted': ('Additional Information Received — In Review', 'account'),
    'ScopeApproved': ('Service Scope Approved', 'account'),
    'ScopeRejected': ('Service Scope Not Approved', 'account'),
    'ScopeClarification': ('More Information Requested', 'account'),
    'ScopeSuspended': ('Service Scope Suspended', 'account'),
    'ScopeExpired': ('Service Scope Approval Expired', 'account'),
    'ScopeAppealDecision': ('Reconsideration Decision Available', 'account'),
    'LanguageReviewUpdated': ('Care-Language Review Updated', 'account'),
    'NewRequest': ('New Consultation Request', 'requests'),
    'OfferReceived': ('New Offer for Your Request', 'offers'),
    'OfferAccepted': ('Your Offer Was Selected', 'offers'),
    'OfferDeclined': ('Your Offer Was Not Selected', 'offers'),
}


def external_state(user, channel):
    if getattr(frappe.flags, 'tele_tena_fixture_notifications', False):
        return 'Suppressed'
    pref = rows('SELECT email_enabled,sms_enabled FROM tt_notice_preference WHERE user=%s', (user,))
    return 'Suppressed' if pref and not pref[0][channel+'_enabled'] else 'Pending'


def wake_dispatch():
    """Durable rows survive queue outages. Minute scheduler remains the fallback."""
    if not getattr(frappe.flags, 'tele_tena_fixture_notifications', False):
        frappe.db.after_commit.add(_enqueue)


def _enqueue():
    try:
        frappe.enqueue('tele_tena.booking_notifications.dispatch', queue='short',
                       job_id='teletena-notice-dispatch:'+frappe.local.site, deduplicate=True)
    except Exception:
        # Never undo a durable workflow or expose contact/provider data in logs.
        # Pending status stays observable and the scheduled job retries enqueueing.
        pass


def queue(user, event, context_kind, context_ref, event_key, in_app=True):
    """Internal call only, from an already-authorized durable transition."""
    if event not in EVENTS or context_kind not in ('application','scope','language','request','offer'):
        raise ValueError('Unsupported communication context')
    if not isinstance(event_key,str) or not 0<len(event_key)<=180:
        raise ValueError('Invalid durable communication key')
    for channel in (('in_app','email','sms') if in_app else ('email','sms')):
        frappe.db.sql('''INSERT IGNORE INTO tt_booking_notice
            (id,appointment,user,event,channel,state,event_key,context_kind,context_ref,created,modified)
            VALUES (%s,NULL,%s,%s,%s,%s,%s,%s,%s,UTC_TIMESTAMP(6),UTC_TIMESTAMP(6))''',
            (str(uuid.uuid4()),user,event,channel,'Available' if channel=='in_app' else external_state(user,channel),
             event_key,context_kind,context_ref))
    wake_dispatch()


def application_submitted(user):
    app=rows('SELECT submitted_at FROM tt_application WHERE user=%s',(user,))
    profile=rows('SELECT public_id FROM tt_profile WHERE user=%s AND kind=\'clinician\'',(user,))
    if app and profile:
        queue(user,'ApplicationSubmitted','application',profile[0].public_id,
              'application-submitted:'+profile[0].public_id+':'+str(app[0].submitted_at))


def describe(notice, dispatch=False):
    """Revalidate the owner/recipient and return allowlisted neutral copy/routes.

    Never loads request text, evidence, findings, contact information or identity
    disclosures into a notification payload.
    """
    event,user,ref=notice.event,notice.user,notice.context_ref
    if event not in EVENTS or not frappe.db.get_value('User',user,'enabled'):
        return None
    title=EVENTS[event][0]
    if notice.context_kind=='application':
        app=rows('''SELECT a.status,a.submitted_at FROM tt_application a JOIN tt_profile p ON p.user=a.user
            WHERE a.user=%s AND p.public_id=%s AND p.kind='clinician' ''',(user,ref))
        if not app:return None
        href='/clinician/account'
        if event=='ApplicationSubmitted':
            body='We have received your application. It is under review, and you will receive an update within the next 24 hours.'
            if app[0].status!='Pending':body='We have received your application. A review update is available in your account.'
            elif app[0].submitted_at and app[0].submitted_at<=datetime.now(timezone.utc).replace(tzinfo=None)-timedelta(hours=24):
                body='Your application is still under review. Open your account for the current status.'
        elif event=='ApplicationReviewUpdate':
            if dispatch and app[0].status!='Pending':return None
            body='Your application is still under review. We will notify you when a reviewer records a decision.'
        elif event=='ApplicationApproved':body='Your professional application has been approved. Service scopes and care languages require their own decisions. Open your account for your next steps.'
        elif event.startswith('Scope'):body='A reviewer has updated a service authorization. Open your service applications for the current status.'
        else:body='A reviewer has recorded an update to your professional application. Sign in to read the decision and next steps.'
    elif notice.context_kind=='scope':
        if not rows('SELECT name FROM `tabTele Tena Vetting Scope Application` WHERE name=%s AND clinician=%s',(ref,user)):return None
        href='/clinician/vetting/'+ref;body='A reviewer has recorded a decision on a service application. Sign in to read the outcome, feedback and next steps.'
        if event=='ScopeResubmitted':body='Your additional information has been received. This service application is back in review. We will notify you when a reviewer records an update.'
    elif notice.context_kind=='language':
        if not rows('SELECT language FROM tt_care_language_claim WHERE clinician=%s AND language=%s',(user,ref)):return None
        href='/clinician/account';body='A reviewer has updated a care-language application. Sign in to read the decision and feedback.'
    elif notice.context_kind=='request':
        request=rows('SELECT patient,state,expires_at,service FROM tt_open_request WHERE id=%s',(ref,))
        if not request:return None
        request=request[0]
        if event=='NewRequest':
            if not rows('SELECT clinician FROM tt_request_recipient WHERE request_id=%s AND clinician=%s',(ref,user)):return None
            from tele_tena.api.journey import service_scope_is_current
            if not service_scope_is_current(user,request.service):return None
            if dispatch and (request.state!='Open' or request.expires_at<=datetime.now(timezone.utc).replace(tzinfo=None)):return None
            href='/clinician/requests';body='A new consultation request is available. Sign in to review your eligible request inbox.'
        else:
            if request.patient!=user:return None
            href='/patient/requests/'+ref;body='A clinician has sent an offer for your request. Sign in to review the offer and your next steps.'
    elif notice.context_kind=='offer':
        offer=rows('SELECT clinician,appointment,state FROM tt_request_offer WHERE id=%s',(ref,))
        if not offer or offer[0].clinician!=user:return None
        offer=offer[0]
        href='/clinician/offers/'+ref
        body='Your offer was selected. Open the appointment for its current payment, confirmation and consultation steps.' if event=='OfferAccepted' else 'Your offer was not selected. Open your offer history for its status.'
    else:return None
    return {'title':title,'body':body,'href':href}


def application_updates():
    """An honest status update at 24 hours; no promise of an approval deadline."""
    for app in rows('''SELECT a.user,a.submitted_at,p.public_id FROM tt_application a JOIN tt_profile p ON p.user=a.user
        WHERE a.status='Pending' AND a.submitted_at<=UTC_TIMESTAMP(6)-INTERVAL 24 HOUR
        AND EXISTS (SELECT 1 FROM tt_booking_notice n WHERE n.user=a.user AND n.event='ApplicationSubmitted'
            AND n.created>=a.submitted_at)
        AND NOT EXISTS (SELECT 1 FROM tt_booking_notice n WHERE n.user=a.user AND n.event='ApplicationReviewUpdate'
            AND n.created>=a.submitted_at) LIMIT 100'''):
        queue(app.user,'ApplicationReviewUpdate','application',app.public_id,
              'application-24h:'+app.public_id+':'+str(app.submitted_at))


@query()
def delivery_status():
    """Owner-only diagnostics; no destinations, provider secrets or health text."""
    from tele_tena.api.journey import actor
    from tele_tena.notifications import participants,KINDS
    import re
    user=actor();items=[]
    for row in rows('''SELECT id,user,event,appointment,context_kind,context_ref,channel,state,attempts,created,modified
        FROM tt_booking_notice WHERE user=%s AND channel IN ('email','sms') ORDER BY created DESC,id DESC LIMIT 50''',(user,)):
        if row.appointment:
            if user not in participants(row.appointment):continue
        elif not describe(row):continue
        items.append({k:row[k] for k in ('id','event','channel','state','attempts','created','modified')})
        items[-1]['title']=KINDS.get(row.event,('TeleTena Update',))[0]
    identities=rows('SELECT channel,contact FROM tt_contact_identity WHERE user=%s AND verified_at IS NOT NULL',(user,))
    return {'items':items,'verified_email':any(c.channel=='email' for c in identities),
            'verified_sms':any(c.channel=='phone' and re.fullmatch(r'\+251[79][0-9]{8}',c.contact) for c in identities)}
