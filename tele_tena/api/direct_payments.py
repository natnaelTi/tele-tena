"""Direct patient-to-clinician transfer claims. No custody, provider verification or wallet posting."""
import base64,hashlib,json,re,uuid
from datetime import datetime,timedelta,timezone
from urllib.parse import quote
import frappe
from tele_tena.api.journey import actor,profile,rows,one,query,command,fail,text,integer,audit

def now():return datetime.now(timezone.utc).replace(tzinfo=None)
def config(lock=False):return one('SELECT * FROM tt_payment_config WHERE id=1'+(' FOR UPDATE' if lock else ''))
def administrator():
    user=actor()
    if user!='Administrator' and 'Tele Tena Financial Configuration' not in frappe.get_roles(user):frappe.throw('Financial configuration permission required',frappe.PermissionError)
    return user
@query()
def capabilities():
    c=config();user=actor();return {'mode':c.mode,'revision':c.revision,'hold_minutes':c.hold_minutes,'verification_hours':c.verification_hours,'can_configure':user=='Administrator' or 'Tele Tena Financial Configuration' in frappe.get_roles(user),'wallet_funding':c.mode=='Wallet','platform_payouts':c.mode=='Wallet'}
@command
def configure(mode,revision,reason,hold_minutes=30,verification_hours=24):
    user=administrator();one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE');c=config(True)
    if mode not in ('Wallet','Offline'):fail('Choose a supported payment mode.')
    if int(revision)!=c.revision:fail('Payment configuration changed. Reload before saving.','payment_mode_changed')
    reason=text(reason,1000);hold_minutes=integer(hold_minutes,5,120);verification_hours=integer(verification_hours,1,72)
    if rows("SELECT id FROM tt_direct_payment WHERE state IN ('AwaitingPayment','Submitted','CorrectionRequired') LIMIT 1"):
        fail('Resolve active direct-payment holds before changing payment configuration.','payment_transition_blocked')
    frappe.db.sql('UPDATE tt_payment_config SET mode=%s,revision=revision+1,hold_minutes=%s,verification_hours=%s,modified=UTC_TIMESTAMP(6) WHERE id=1',(mode,hold_minutes,verification_hours))
    audit(user,'PaymentModeChanged',{'before':c.mode,'after':mode,'prior_revision':c.revision,'reason':reason,'hold_minutes':hold_minutes,'verification_hours':verification_hours})
    return capabilities()
@query()
def payee():
    p=profile('clinician');found=rows('SELECT phone,revision FROM tt_telebirr_payee WHERE clinician=%s',(p.user,));return {'ready':bool(found),'phone':found[0].phone if found else '', 'revision':found[0].revision if found else 0}
@command
def save_payee(phone,revision,reason):
    p=profile('clinician');from tele_tena.api.phone_auth import normalize_phone
    phone=normalize_phone(phone);reason=text(reason,500)
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE');found=rows('SELECT revision FROM tt_telebirr_payee WHERE clinician=%s FOR UPDATE',(p.user,))
    if int(revision)!=(found[0].revision if found else 0):fail('Receiving number changed. Reload before saving.','payee_changed')
    frappe.db.sql('INSERT INTO tt_telebirr_payee VALUES (%s,%s,1,UTC_TIMESTAMP(6)) ON DUPLICATE KEY UPDATE phone=VALUES(phone),revision=revision+1,modified=UTC_TIMESTAMP(6)',(p.user,phone))
    audit(p.user,'TelebirrPayeeChanged',{'revision':int(revision)+1,'reason':reason}) # Never copy phone into audit/logs.
    return payee()
def require_payee(clinician):
    found=rows('SELECT phone,revision FROM tt_telebirr_payee WHERE clinician=%s',(clinician,))
    if not found:fail('This clinician must configure a Telebirr receiving number before accepting direct payments.','payee_required')
    return found[0]
def authorize(id,lock=False):
    user=actor();p=one('SELECT * FROM tt_direct_payment WHERE id=%s'+(' FOR UPDATE' if lock else ''),(id,))
    if user not in (p.patient,p.clinician):frappe.throw('Payment unavailable',frappe.PermissionError)
    return p,user

def event(p,user,kind,key,values,evidence=None,reason=''):
    key=text(key,100);digest=hashlib.sha256(json.dumps([kind,values],sort_keys=True).encode()).hexdigest()
    old=rows('SELECT id,payload_hash FROM tt_direct_payment_event WHERE payment=%s AND actor=%s AND retry_key=%s',(p.id,user,key))
    if old:
        if old[0].payload_hash!=digest:fail('This retry contains different payment details.','retry_changed')
        return False
    id=str(uuid.uuid4());frappe.db.sql('INSERT INTO tt_direct_payment_event (id,payment,actor,event,retry_key,payload_hash,evidence,reason,details,created) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,UTC_TIMESTAMP(6))',(id,p.id,user,kind,key,digest,evidence,reason,json.dumps(values)))
    return id

def notify(p,kind,event_id):
    from tele_tena.notifications import emit
    from tele_tena.booking_notifications import queue_external
    recipients={p.clinician} if kind in ('PaymentSubmitted','PaymentVerificationReminder') else {p.patient}
    for user in recipients:emit(user,'direct:'+str(event_id),kind,p.appointment)
    queue_external(p.appointment,kind,recipients,context_key=str(event_id))

def begin(appointment,payee,c):
    a=one('SELECT * FROM tt_appointment WHERE id=%s',(appointment,));id=str(uuid.uuid4())
    hold=min(a.start,now()+timedelta(minutes=int(c.hold_minutes)));verify=min(a.start,now()+timedelta(hours=int(c.verification_hours)))
    frappe.db.sql("INSERT INTO tt_direct_payment (id,appointment,patient,clinician,amount,payee,payee_revision,mode_revision,reference_id,state,hold_until,verify_until,created) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'AwaitingPayment',%s,%s,UTC_TIMESTAMP(6))",(id,a.id,a.patient,a.clinician,a.price,payee.phone,payee.revision,c.revision,a.id,hold,verify))
    frappe.db.sql("UPDATE tt_appointment SET payment_mode='Offline',state='PendingConfirmation',confirmed_at=NULL,expires_at=%s WHERE id=%s",(hold,a.id))
    event(one('SELECT * FROM tt_direct_payment WHERE id=%s',(id,)),a.patient,'IntentCreated','intent',{'appointment':a.id,'amount':int(a.price),'mode_revision':c.revision})
    return id
@query()
def detail(id):
    p,user=authorize(id);out={k:p[k] for k in ('id','appointment','amount','currency','payee','state','hold_until','verify_until','transaction_ref','verified_at','created','reference_type','reference_id')}
    out['history']=rows('SELECT id,event,evidence,reason,details,created FROM tt_direct_payment_event WHERE payment=%s ORDER BY created,id',(id,))
    from tele_tena.api.journey import iso
    for field in ('hold_until','verify_until','verified_at','created'):out[field]=iso(out[field]) if out[field] else None
    for h in out['history']:
        h.created=iso(h.created);h.details=json.loads(h.details or '{}')
    out['can_verify']=user==p.clinician;out['payer']=user==p.patient;out['external_verification']=False
    return out
@query()
def for_appointment(appointment):
    found=rows("SELECT id FROM tt_direct_payment WHERE appointment=%s AND reference_type='Appointment'",(appointment,))
    return detail(found[0].id) if found else None
@command
def submit(id,transaction_ref,amount,filename,content_base64,retry_key):
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE');p,user=authorize(id,True)
    if user!=p.patient:frappe.throw('Only the authorized payer may submit payment proof',frappe.PermissionError)
    ref=text(transaction_ref,100).upper().replace(' ','')
    if not re.fullmatch('[A-Z0-9-]{6,100}',ref):fail('Enter the Telebirr transaction reference.','transaction_reference_invalid')
    amount=integer(amount,1,100000000)
    from tele_tena.api.history_documents import validated
    filename,mime,content=validated(filename,content_base64)
    if mime not in ('image/jpeg','image/png'):fail('Upload a JPEG or PNG receipt screenshot up to 5 MB.','receipt_invalid')
    digest=hashlib.sha256(content).hexdigest();values={'ref':ref,'amount':amount,'receipt_hash':digest}
    eid=event(p,user,'PaymentSubmitted',retry_key,values)
    if not eid:return detail(id)
    if p.state in ('Verified','RefundRequired','RefundReported','RefundConfirmed'):fail('This payment already has a recorded verification or refund.','payment_resolved')
    prior=rows('SELECT payment FROM tt_direct_transaction_ref WHERE payee=%s AND transaction_ref=%s FOR UPDATE',(p.payee,ref))
    if prior and prior[0].payment!=id:fail('This transaction reference is already assigned to another payment.','transaction_reference_reused')
    frappe.db.sql('INSERT IGNORE INTO tt_direct_transaction_ref VALUES (%s,%s,%s)',(p.payee,ref,id))
    if one('SELECT COUNT(*) AS n FROM tt_direct_receipt WHERE payment=%s',(id,)).n>=30:fail('Receipt revision limit reached. Contact support.','receipt_limit')
    evidence=str(uuid.uuid4());frappe.db.sql('INSERT INTO tt_direct_receipt VALUES (%s,%s,%s,%s,%s,FROM_BASE64(%s),%s,UTC_TIMESTAMP(6))',(evidence,id,user,filename,mime,base64.b64encode(content).decode(),digest))
    frappe.db.sql('UPDATE tt_direct_payment_event SET evidence=%s WHERE id=%s',(evidence,eid))
    late=(p.verify_until if p.transaction_ref else p.hold_until)<=now() or amount!=p.amount or one('SELECT state FROM tt_appointment WHERE id=%s',(p.appointment,)).state not in ('PendingConfirmation','Booked')
    state='ReconciliationRequired' if late else 'Submitted'
    frappe.db.sql('UPDATE tt_direct_payment SET state=%s,transaction_ref=%s WHERE id=%s',(state,ref,id))
    if not late and p.reference_type=='Appointment':frappe.db.sql('UPDATE tt_appointment SET expires_at=%s WHERE id=%s',(p.verify_until,p.appointment))
    notify(p,'PaymentSubmitted',eid);return detail(id)
@command
def review(id,decision,retry_key,reason=''):
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE');p,user=authorize(id,True)
    if user!=p.clinician:frappe.throw('Only the receiving clinician may verify receipt',frappe.PermissionError)
    if decision not in ('confirm','correct','reject','dispute'):fail('Choose a payment decision.')
    reason=text(reason,1000,decision!='confirm');eid=event(p,user,{'confirm':'ReceiptVerified','correct':'CorrectionRequested','reject':'ReceiptRejected','dispute':'PaymentDisputed'}[decision],retry_key,{'decision':decision,'reason':reason},reason=reason)
    if not eid:return detail(id)
    if decision=='dispute':
        state='ReconciliationRequired'
    elif decision in ('correct','reject'):
        if p.verified_at:fail('Use payment reconciliation for an already verified receipt.','payment_resolved')
        state='CorrectionRequired' if decision=='correct' else 'Rejected'
    else:
        if p.verified_at:return detail(id)
        if p.state not in ('Submitted','ReconciliationRequired'):fail('Review submitted payment evidence first.','receipt_required')
        app=one('SELECT * FROM tt_appointment WHERE id=%s FOR UPDATE',(p.appointment,))
        latest=rows("SELECT details FROM tt_direct_payment_event WHERE payment=%s AND event='PaymentSubmitted' ORDER BY created DESC,id DESC LIMIT 1",(id,))
        amount_matches=bool(latest and json.loads(latest[0].details).get('amount')==p.amount)
        safe=amount_matches and app.state=='PendingConfirmation' and app.expires_at and app.expires_at>now() and app.start>now()
        conflicts=rows("SELECT id FROM tt_appointment WHERE id<>%s AND clinician=%s AND state IN ('Booked','PendingConfirmation') AND (expires_at IS NULL OR expires_at>UTC_TIMESTAMP(6)) AND DATE_SUB(start,INTERVAL buffer_before MINUTE)<%s AND DATE_ADD(end,INTERVAL buffer_after MINUTE)>%s FOR UPDATE",(app.id,app.clinician,app.end+timedelta(minutes=app.buffer_after),app.start-timedelta(minutes=app.buffer_before)))
        from tele_tena.api.couples import ready
        safe=safe and not conflicts and ready(app.id)
        from tele_tena.api.journey import approved,approved_service
        if p.reference_type=='Extension':
            extension=one('SELECT * FROM tt_consultation_extension WHERE id=%s FOR UPDATE',(p.reference_id,))
            call=rows("SELECT state FROM tt_consultation WHERE appointment=%s",(app.id,))
            safe=amount_matches and app.state=='Booked' and extension.state=='PaymentPending' and p.hold_until>now() and not conflicts and ready(app.id) and bool(call and call[0].state=='Open')
        if safe:
            try:approved(p.clinician,True);approved_service(p.clinician,one('SELECT service FROM tt_offering WHERE id=%s',(app.offering,)).service,True)
            except (frappe.PermissionError,frappe.ValidationError):safe=False
            from tele_tena.api.care_languages import offering_languages
            if json.loads(app.policy_snapshot or '{}').get('care_language') not in offering_languages(app.offering):safe=False
        if safe and p.reference_type=='Extension':frappe.db.sql("UPDATE tt_consultation_extension SET state='Accepted',accepted_at=UTC_TIMESTAMP(6) WHERE id=%s",(p.reference_id,))
        state='Verified' if safe else 'RefundRequired'
        frappe.db.sql('UPDATE tt_direct_payment SET verified_at=UTC_TIMESTAMP(6),verified_by=%s WHERE id=%s',(user,id))
        if safe and p.reference_type=='Appointment':
            automatic=app.confirmation_mode=='automatic';expiry=None if automatic else min(app.start,now()+timedelta(hours=max(1,min(168,int(frappe.conf.get('tele_tena_pending_expiry_hours',24))))))
            frappe.db.sql('UPDATE tt_appointment SET state=%s,confirmed_at=%s,expires_at=%s WHERE id=%s',('Booked' if automatic else 'PendingConfirmation',now() if automatic else None,expiry,app.id))
    frappe.db.sql('UPDATE tt_direct_payment SET state=%s WHERE id=%s',(state,id))
    notify(p,'PaymentVerified' if state=='Verified' else 'PaymentCorrection' if state in ('CorrectionRequired','Rejected') else 'PaymentReconciliation',eid)
    if state=='Verified' and p.reference_type=='Appointment':
        from tele_tena.booking_notifications import create
        create(p.appointment,'Booked' if automatic else 'PendingConfirmation')
    return detail(id)
def cancel(appointment,reason):
    for p in rows('SELECT * FROM tt_direct_payment WHERE appointment=%s FOR UPDATE',(appointment,)):
        if p.state=='RefundConfirmed':continue
        state='RefundRequired' if p.verified_at else 'ReconciliationRequired' if p.transaction_ref else 'Expired'
        eid=event(p,frappe.session.user or 'System','BookingClosed','close:'+reason,{'reason':reason},reason=reason)
        frappe.db.sql('UPDATE tt_direct_payment SET state=%s WHERE id=%s',(state,p.id))
        if eid:notify(p,'PaymentReconciliation',eid)
    return False

@command
def refund(id,decision,retry_key,reason):
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE');p,user=authorize(id,True);reason=text(reason,1000)
    required=(user==p.clinician and decision=='reported' and p.state in ('RefundRequired','ReconciliationRequired')) or (user==p.patient and decision=='received' and p.state=='RefundReported')
    target='RefundReported' if decision=='reported' else 'RefundConfirmed'
    old=rows('SELECT id FROM tt_direct_payment_event WHERE payment=%s AND actor=%s AND retry_key=%s',(id,user,retry_key))
    if not required and not old:fail('This refund action is unavailable.','refund_state_invalid')
    eid=event(p,user,target,retry_key,{'decision':decision,'reason':reason},reason=reason)
    if eid:
        frappe.db.sql('UPDATE tt_direct_payment SET state=%s WHERE id=%s',(target,id));notify(p,'PaymentReconciliation',eid)
    return detail(id)
@query()
def receipt(id):
    actor()
    r=one('SELECT * FROM tt_direct_receipt WHERE id=%s',(id,));authorize(r.payment)
    from werkzeug.wrappers import Response
    return Response(bytes(r.content),mimetype=r.mime,headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff','Content-Disposition':"attachment; filename*=UTF-8''"+quote(r.filename,safe=''),'Content-Security-Policy':"sandbox; default-src 'none'"})
@query()
def ledger(page=0):
    user=actor();page=integer(page,0,100000);data=rows('SELECT p.id,p.appointment,p.amount,p.currency,p.state,p.transaction_ref,p.verified_at,p.created,p.reference_type,a.disclosure,IF(p.patient=%s,provider.display_name,NULL) clinician_name FROM tt_direct_payment p JOIN tt_appointment a ON a.id=p.appointment LEFT JOIN tt_profile provider ON provider.user=p.clinician WHERE p.patient=%s OR p.clinician=%s ORDER BY p.created DESC,p.id LIMIT 101 OFFSET %s',(user,user,user,page*100))
    from tele_tena.api.journey import iso
    has_more=len(data)>100;data=data[:100]
    for row in data:
        row.counterparty=row.pop('clinician_name') or json.loads(row.pop('disclosure') or '{}').get('name') or 'Private Patient'
        row.pop('disclosure',None)
        row.created=iso(row.created);row.verified_at=iso(row.verified_at) if row.verified_at else None
    totals={}
    for p in rows('SELECT state,SUM(amount) AS total FROM tt_direct_payment WHERE patient=%s OR clinician=%s GROUP BY state',(user,user)):totals[p.state]=int(p.total)
    return {'items':data,'totals_minor':totals,'currency':'ETB','custody':False,'page':page,'has_more':has_more}

@command
def raise_issue(id,reason,retry_key):
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE');p,user=authorize(id,True);reason=text(reason,1000)
    eid=event(p,user,'PaymentIssueReported',retry_key,{'reason':reason},reason=reason)
    if eid:
        frappe.db.sql("UPDATE tt_direct_payment SET state='ReconciliationRequired' WHERE id=%s",(id,));notify(p,'PaymentReconciliation',eid)
    return detail(id)

def begin_extension(app,extension):
    existing=rows("SELECT id FROM tt_direct_payment WHERE reference_type='Extension' AND reference_id=%s",(extension.id,))
    if existing:return existing[0].id
    receiver=require_payee(app.clinician);c=config();id=str(uuid.uuid4());expiry=min(extension.expires_at,now()+timedelta(minutes=c.hold_minutes))
    frappe.db.sql("""INSERT INTO tt_direct_payment (id,appointment,patient,clinician,amount,payee,payee_revision,mode_revision,reference_type,reference_id,state,hold_until,verify_until,created)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'Extension',%s,'AwaitingPayment',%s,%s,UTC_TIMESTAMP(6))""",(id,app.id,app.patient,app.clinician,extension.amount_minor,receiver.phone,receiver.revision,c.revision,extension.id,expiry,expiry))
    event(one('SELECT * FROM tt_direct_payment WHERE id=%s',(id,)),app.patient,'ExtensionIntentCreated','intent',{'extension':extension.id,'amount':int(extension.amount_minor)})
    return id

def close_extension(extension,reason):
    p=rows("SELECT * FROM tt_direct_payment WHERE reference_type='Extension' AND reference_id=%s FOR UPDATE",(extension.id,))
    if p:
        p=p[0];state='RefundRequired' if p.verified_at else 'ReconciliationRequired' if p.transaction_ref else 'Expired'
        eid=event(p,frappe.session.user or 'System','ExtensionClosed','extension-close',{'reason':reason},reason=reason)
        frappe.db.sql('UPDATE tt_direct_payment SET state=%s WHERE id=%s',(state,p.id))
        if eid:notify(p,'PaymentReconciliation',eid)


def process_reminders():
    """One midpoint reminder per intent/phase, via existing minute job/outbox.

    Timing derives from the snapshotted hold/verification deadline, never from
    the separate three-minute appointment-confirmation policy. No provider I/O.
    """
    for candidate in rows("""SELECT id FROM tt_direct_payment WHERE
        (state IN ('AwaitingPayment','CorrectionRequired') AND hold_until>UTC_TIMESTAMP(6)
          AND UTC_TIMESTAMP(6)>=TIMESTAMPADD(SECOND,TIMESTAMPDIFF(SECOND,created,hold_until) DIV 2,created))
        OR (state='Submitted' AND verify_until>UTC_TIMESTAMP(6)
          AND UTC_TIMESTAMP(6)>=TIMESTAMPADD(SECOND,TIMESTAMPDIFF(SECOND,created,verify_until) DIV 2,created))
        ORDER BY created,id LIMIT 100"""):
        one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
        p=one('SELECT * FROM tt_direct_payment WHERE id=%s FOR UPDATE',(candidate.id,))
        if p.state not in ('AwaitingPayment','CorrectionRequired','Submitted'):continue
        deadline=p.verify_until if p.state=='Submitted' else p.hold_until
        if deadline<=now():continue
        kind='PaymentVerificationReminder' if p.state=='Submitted' else 'PaymentReminder'
        eid=event(p,'System',kind,'reminder:'+kind,{'deadline':deadline.isoformat()})
        if eid:notify(p,kind,eid)
