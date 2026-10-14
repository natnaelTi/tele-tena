"""Explicit review-only, additive, versioned fictional demonstration dataset.

No HTTP endpoint, installation hook or external delivery. Account/record ownership
is persisted in a mode600 checkpoint before each idempotent application operation.
"""
import base64
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import fcntl
import json
import os
from pathlib import Path
import secrets

import frappe
from tele_tena.review import cli, write_private

DATASET = 'tt-demo-mvp-v2'
CONTENT_REVISION = 2
NAMES = {'patient':'Mahi Kebede', 'private_patient':'Aster Yilma', 'oromo_patient':'Bontu Gemechu',
         'couple_payer':'Liya Tadesse', 'couple_partner':'Yonatan Girma',
         'counselor':'Sara Getachew', 'therapist':'Michael Assefa', 'psychiatrist':'Ruth Belay',
         'applicant':'Netsanet Fikru', 'reviewer':'Meron Abate'}
SERVICES = [('counseling','Individual counseling','counseling',30000,30),
            ('stress','Stress and anxiety support','counseling',40000,30),
            ('grief','Grief and loss counseling','counseling',35000,45),
            ('psychotherapy','Individual psychotherapy','psychotherapy',60000,45),
            ('couples','Couples counseling','relationship-care',90000,60),
            ('premarital','Premarital counseling','relationship-care',80000,60),
            ('psychiatry','Psychiatric consultation','psychiatry',70000,45)]
QUALIFICATIONS = {'professional_category':'Mental health professional (fictional)',
    'qualification':'Fictional mental-health qualification — demonstration only',
    'issuing_institution':'Fictional Addis Learning Institute', 'registration_number':'FICTIONAL-NOT-A-LICENSE',
    'issuing_authority':'Fictional training registry, no external verification',
    'jurisdiction':'Development demonstration only', 'experience_years':5,
    'population_adults':1,'independent_practice':1,'relevant_training':'Fictional adult-care training exercise.',
    'competencies':'Fictional counseling, consent and privacy training.',
    'certifications':'Fictional demonstration certificate; not a real credential.',
    'applicant_statement':'Fictional application created for an operator-authorized demonstration.'}


def _flag(value):
    return value not in (None, False, 0, '', '0', 'false', 'False')


def _guard():
    cli()
    from tele_tena.api.journey import simulation_enabled
    if not simulation_enabled() or any(_flag(frappe.conf.get(key)) for key in (
            'tele_tena_real_money_enabled','tele_tena_real_payments_enabled',
            'tele_tena_payments_enabled','tele_tena_real_payouts_enabled')):
        raise ValueError('Refusing financial demo seeding on a real-money or non-review site')
    if frappe.conf.get('developer_mode') or frappe.conf.get('ignore_csrf'):
        raise ValueError('Developer mode/CSRF bypass are not permitted for review')
    if not frappe.db.sql("SHOW TABLES LIKE 'tt_profile_photo'"):
        raise ValueError('Migrate this target site before seeding')


def paths():
    private = Path(frappe.get_site_path('private')).resolve()
    return private / (DATASET+'-records.json'), private / (DATASET+'-accounts.json')


def setup(dry_run=True):
    """bench --site SITE execute tele_tena.demo_dataset.setup --kwargs '{"dry_run":False}'"""
    _guard()
    if type(dry_run) is not bool:
        raise ValueError('dry_run must be a JSON boolean')
    marker, credentials = paths()
    users = {key:DATASET+'-'+key+'@example.invalid' for key in NAMES}
    conflicts = [key for key,user in users.items() if frappe.db.exists('User',user)]
    if not marker.exists() and (credentials.exists() or conflicts or any(
            frappe.db.exists('Tele Tena Service',DATASET+'-'+row[0]) for row in SERVICES)):
        raise ValueError('Dataset identifier conflict: existing records will not be adopted or overwritten')
    if dry_run:
        return {'dry_run':True,'dataset':DATASET,'existing_dataset':marker.exists(),
                'accounts':len(users),'services':len(SERVICES),'site':frappe.local.site,
                'external_delivery':False,'changes':False}
    lock=Path(frappe.get_site_path('private',DATASET+'.lock'))
    fd=os.open(lock,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        original=frappe.session.user
        try:
            if marker.exists():
                state=json.loads(marker.read_text())
                if state.get('dataset')!=DATASET or state.get('site')!=frappe.local.site or state.get('users')!=users or not credentials.is_file():
                    raise ValueError('Dataset checkpoint mismatch; restore private files with the database')
            else:
                state={'dataset':DATASET,'site':frappe.local.site,'fictional':True,
                       'created_at':datetime.now(timezone.utc).isoformat(),'users':users,'steps':{},
                       'historical_window_minutes':int(frappe.conf.get('tele_tena_demo_dispute_window_minutes',60)),
                       'illustrative_prices_minor':{row[0]:row[3] for row in SERVICES}}
                write_private(credentials,{user:secrets.token_urlsafe(28) for user in users.values()})
                write_private(marker,state)
            if state.get('complete') and state.get('content_revision')==CONTENT_REVISION:
                return {'already_present':True,'dataset':DATASET,'credentials_file':str(credentials),
                        'reconciliation':reconcile(state),'refreshed':False}
            passwords=json.loads(credentials.read_text())
            seed=Builder(state,marker,passwords)
            seed.run()
            state['reconciliation']=reconcile(state)
            state['complete']=True
            state['content_revision']=CONTENT_REVISION
            write_private(marker,state)
            return {'created':True,'dataset':DATASET,'credentials_file':str(credentials),
                    'records_file':str(marker),'accounts':len(users),'reconciliation':state['reconciliation'],
                    'outbound_delivery':False}
        finally:
            frappe.set_user(original)


class Builder:
    def __init__(self,state,marker,passwords):
        self.state,self.marker,self.passwords=state,marker,passwords
        self.users=state['users']
        self.anchor=datetime.fromisoformat(state['created_at'])

    def step(self,key,role,fn):
        completed=self.state['steps'].get(key)
        if completed and completed.get('done'):
            return completed['result']
        self.state['steps'][key]={'started':True}
        write_private(self.marker,self.state)
        frappe.set_user(self.users.get(role,role))
        try:
            result=fn()
            frappe.db.commit()
            self.state['steps'][key]={'done':True,'result':result}
            write_private(self.marker,self.state)
            return result
        except Exception:
            frappe.db.rollback()
            raise

    def result(self,key):
        return self.state['steps'][key]['result']

    def account(self,key):
        from frappe.utils.password import update_password
        user=self.users[key]
        if frappe.db.exists('User',user):
            # A retry may follow a committed step whose private checkpoint write
            # was interrupted. Never change that account/password/profile.
            return {'user':user}
        doc=frappe.get_doc({'doctype':'User','email':user,'first_name':NAMES[key],
            'send_welcome_email':0,'user_type':'Website User'})
        doc.insert()
        if key=='reviewer':doc.add_roles('Tele Tena Approver','Tele Tena Medical Lead')
        elif key in ('counselor','therapist','psychiatrist','applicant'):doc.add_roles('Tele Tena Clinician')
        else:doc.add_roles('Tele Tena Patient')
        update_password(user,self.passwords[user])
        return {'user':user}

    def profile(self,key):
        from tele_tena.api import journey as j, presentation as p
        clinician=key in ('counselor','therapist','psychiatrist','applicant')
        if not j.rows('SELECT user FROM tt_profile WHERE user=%s',(self.users[key],)):
            j.save_profile('clinician' if clinician else 'patient',NAMES[key],True,
                history='' if clinician else 'Fictional care background for privacy demonstration.',
                share_name=key!='private_patient',share_history=False,
                languages=['en','am'] if key=='counselor' else ['en','om'] if key=='therapist' else ['en'],
                **({'introduction':'Fictional professional profile for demonstrating adult mental-health care. No real credentials or care are represented.'} if clinician else {}))
        if clinician:
            frappe.db.sql('''INSERT IGNORE INTO tt_onboarding (user,kind,step,answers,modified) VALUES (%s,'clinician',0,%s,UTC_TIMESTAMP(6))''', (self.users[key],json.dumps({'professional':QUALIFICATIONS,'care_languages':['en'],'name':NAMES[key]})))
        if not clinician:p.save_preferences('om' if key=='oromo_patient' else 'am' if key=='private_patient' else 'en','Africa/Addis_Ababa')
        return {'created':True}

    def service(self,row):
        from tele_tena.api import service_catalog as c
        key,label,category,price,minutes=row
        service=DATASET+'-'+key
        if frappe.db.exists('Tele Tena Service',service):return {'id':service}
        c.save_draft_definition({'service_key':service,'service_label':label,'category':category,
            'description':'Adult '+label.lower()+'. Fictional demonstration definition, not a clinically approved production service.',
            'professional_categories':QUALIFICATIONS['professional_category'],
            'credential_requirements':'Fictional qualification and license documents are assessed in this training exercise only.',
            'participant_structure':'couple' if key in ('couples','premarital') else 'individual',
            'population_restriction':'Adults only','supported_formats':'audio\nvideo',
            'booking_rules':'direct-booking\nscheduled\nimmediate-request',
            'required_workflows':'individual-consultation\nprivate-notes\npatient-summary'+ ('\ncouples-consent' if key in ('couples','premarital') else ''),
            'required_consent_schema':'fictional-adult-demo-v2','location_jurisdiction_policy':'fictional-review-only',
            'definition_version':'demo-mvp-v2','min_duration_minutes':15,'max_duration_minutes':90,
            'catalog_source':'Fictional demonstration derivative of the adult mental-health catalog. Not medical-lead approval for real clinical use.'})
        c.submit_for_clinical_review(service)
        c.review_definition(service,'Approved','Operator-authorized fictional dataset review exercise; no real clinical authorization or external credential verification.')
        from tele_tena.api.service_policy import set_immediate_policy
        if key not in ('couples','premarital'):
            set_immediate_policy(service,True,'Fictional adult immediate-care exercise; not an emergency response.',DATASET+'-immediate-'+key)
        return {'id':service}

    def application(self,key,services):
        from tele_tena.api import journey as j,presentation as p
        if not j.rows('SELECT user FROM tt_application WHERE user=%s',(self.users[key],)):
            p.upload_resume('fictional-resume.pdf',document('Fictional resume: '+NAMES[key]))
            j.apply('Fictional professional application — no real license, qualification or external verification is represented.',services)
        return {'submitted':True}

    def scope(self,key,service,decision):
        from tele_tena.api import vetting as v
        values={**QUALIFICATIONS,'credential_valid_from':(self.anchor.date()-timedelta(days=365)).isoformat(),
                'credential_expiry':(self.anchor.date()+timedelta(days=365)).isoformat()}
        existing=frappe.db.sql('SELECT name,status FROM `tabTele Tena Vetting Scope Application` WHERE clinician=%s AND service=%s',(self.users[key],service),as_dict=True)
        if existing and existing[0].status in ('Approved','Rejected','Clarification','Submitted'):
            return {'name':existing[0].name}
        result=v.save_scope_application(service,values,submit=False)
        evidence=v.upload_scope_evidence(result['name'],'License or registration','fictional-license.pdf',document('Fictional license training document. NOT VALID: '+NAMES[key]))
        v.save_scope_application(service,values,submit=True)
        return {'name':result['name'],'evidence':evidence['id']}

    def decide(self,key,scope,decision):
        from tele_tena.api import vetting as v
        name=scope['name'];status=frappe.db.get_value('Tele Tena Vetting Scope Application',name,'status')
        if status not in ('Submitted','Resubmitted'):return {'status':status}
        evidence=scope.get('evidence') or frappe.db.get_value('Tele Tena Scope Evidence',{'scope_application':name,'evidence_type':'License or registration'},'name')
        scores={dimension:{'score':2,'rationale':'Fictional evidence assessment exercise. Not an actual competence claim.','evidence':[evidence]} for dimension in ('scope_education','supervised_experience','approach_training','adult_population','ethics_safeguarding','assessment_interview')}
        kwargs={'findings':('Fictional exercise: '+decision+'. No external credential source checked.'),'restrictions':'Development demonstration only. No real clinical practice.'}
        if decision=='Approved':kwargs.update(identity_reviewed=True,credential_verified=True,qualification_relevant=True,experience_adequate=True,adult_scope_appropriate=True,interview_completed=True,scored_criteria=scores,credential_source='Fictional training register; not an external authority',credential_checked_on=frappe.utils.today(),credential_evidence=evidence,credential_source_reference=DATASET+'-fictional-source')
        return v.review_scope_application(name,decision,**kwargs)

    def offering(self,key,service):
        from tele_tena.api import journey as j,scheduling as s
        row=next(r for r in SERVICES if DATASET+'-'+r[0]==service)
        result=j.publish(service,row[3],row[4],title=row[1],description='Fictional review session with clear consent and privacy choices.',retry_key=DATASET+'-'+key+'-'+row[0])
        offering=result['offering']
        s.save_schedule(offering=offering,schedule_name=row[1]+' availability',timezone_name='Africa/Addis_Ababa',
            intervals=[{'weekday':day,'start_local':'00:00','end_local':'23:59'} for day in range(7)],
            exceptions=[{'date':(self.anchor.date()+timedelta(days=10)).isoformat(),'kind':'unavailable'}],
            minimum_notice_minutes=0,horizon_days=60,buffer_before=0,buffer_after=0,
            confirmation_mode='automatic',status='Published',consultation_format='audio' if key=='psychiatrist' else 'video')
        return {'id':offering}

    def book(self,key,offering,day_offset,hour,retry):
        from tele_tena.api import journey as j
        start=(self.anchor+timedelta(days=day_offset)).replace(hour=hour,minute=0,second=0,microsecond=0)
        offer=j.one('SELECT price,minutes FROM tt_offering WHERE id=%s',(offering,))
        request='I would like a supportive conversation about everyday stress. Fictional demonstration.'
        sharing={'name':key!='private_patient','history':False}
        disclosure=j.disclosure(j.profile('patient'),request,sharing)
        return j.book(offering,j.iso(start.replace(tzinfo=None)),request,sharing,DATASET+'-'+retry,offer.price,offer.minutes,disclosure,'Africa/Addis_Ababa')

    def run(self):
        from tele_tena.api import journey as j, presentation as p, clinics, couples, open_requests as requests, trust
        from tele_tena import accounting
        for key in NAMES:self.step('account-'+key,'Administrator',lambda key=key:self.account(key))
        for key in NAMES:
            if key!='reviewer':self.step('profile-'+key,key,lambda key=key:self.profile(key))
        for row in SERVICES:self.step('service-'+row[0],'reviewer',lambda row=row:self.service(row))
        scopes={'counselor':['counseling','stress','grief'],'therapist':['psychotherapy','couples','premarital','counseling'],'psychiatrist':['psychiatry'],'applicant':['counseling','stress','grief']}
        for key,scope_keys in scopes.items():
            services=[DATASET+'-'+x for x in scope_keys]
            self.step('application-'+key,key,lambda key=key,services=services:self.application(key,services))
            if key!='applicant':self.step('general-review-'+key,'reviewer',lambda key=key:j.review(self.users[key],'Approved'))
            else:
                def pending_roles(key=key):
                    doc=frappe.get_doc('User',self.users[key]);doc.remove_roles('Tele Tena Clinician');doc.add_roles('Tele Tena Applicant');return {'pending':True}
                self.step('pending-role-'+key,'Administrator',pending_roles)
            for scope in scope_keys:
                service=DATASET+'-'+scope
                application=self.step('scope-'+key+'-'+scope,key,lambda key=key,service=service:self.scope(key,service,'Submitted'))
                if key!='applicant':
                    self.step('scope-decision-'+key+'-'+scope,'reviewer',lambda key=key,application=application:self.decide(key,application,'Approved'))
                    self.step('offering-'+key+'-'+scope,key,lambda key=key,service=service:self.offering(key,service))
                elif scope!='counseling':
                    self.step('scope-decision-'+key+'-'+scope,'reviewer',lambda key=key,application=application,scope=scope:self.decide(key,application,'Clarification' if scope=='stress' else 'Rejected'))
        for key in ('patient','private_patient','oromo_patient','couple_payer','couple_partner'):
            self.step('fund-'+key,key,lambda key=key:j.simulated_deposit(200000,DATASET+'-opening-'+key))
        clinic=self.step('clinic-application','therapist',lambda:clinics.submit_clinic_application('Abay Care Studio (fictional)','Abay Care Studio (fictional)',DATASET+'-clinic','Development demonstration only','Fictional practice for affiliation review. Not a real clinic.'))
        self.step('clinic-review','reviewer',lambda:clinics.review_clinic(clinic['application'],'Verified','Fictional registration review exercise, no real authority checked.'))
        affiliation=self.step('affiliation-application','therapist',lambda:clinics.submit_affiliation(clinic['application'],'Counselor (fictional)','Fictional clinic affiliation exercise.'))
        self.step('affiliation-review','reviewer',lambda:clinics.review_affiliation(affiliation['application'],'Verified','Fictional affiliation review, not evidence of professional competence.'))
        offering=self.result('offering-counselor-counseling')['id']
        self.step('upcoming','patient',lambda:self.book('patient',offering,2,8,'upcoming'))
        cancelled=self.step('cancellation-booking','private_patient',lambda:self.book('private_patient',offering,3,9,'cancelled'))
        self.step('cancel','private_patient',lambda:p.cancel_appointment(cancelled['id'],'Plans changed — fictional demonstration.'))
        couple_offer=self.result('offering-therapist-couples')['id']
        def invite():
            request='We would like support with communication. Fictional demonstration.'
            sharing={'name':True,'history':False}
            return couples.invite(couple_offer,j.iso((self.anchor+timedelta(days=2)).replace(hour=12,minute=0,second=0,microsecond=0,tzinfo=None)),request,sharing,j.disclosure(j.profile('patient'),request,sharing),True,DATASET+'-couples','Africa/Addis_Ababa')
        invitation=self.step('couple-invitation','couple_payer',invite)
        def consent():
            content='I choose to join this shared conversation. Fictional demonstration.'
            sharing={'name':False,'history':False}
            return couples.consent(invitation['token'],content,sharing,j.disclosure(j.profile('patient'),content,sharing),True)
        self.step('couple-consent','couple_partner',consent)
        self.step('couple-booking','couple_payer',lambda:couples.confirm(invitation['id']))
        # Historical synthetic scenarios use private process-local domain timing
        # and an offline room adapter; no server clock/configuration is changed.
        for scenario,days in [('released',-2),('pending',0),('held',0)]:
            shifted=(self.anchor-timedelta(minutes=int(self.state.get('historical_window_minutes',frappe.conf.get('tele_tena_demo_dispute_window_minutes',60)))+120)) if scenario=='released' else self.anchor+timedelta(hours=1 if scenario=='held' else 0)
            with simulation_context(shifted):
                hour=(shifted+timedelta(minutes=5)).hour
                start=(shifted+timedelta(minutes=5)).replace(second=0,microsecond=0)
                known=self.state['steps'].get('booking-'+scenario)
                if known and known.get('done'):
                    existing=j.one('SELECT start FROM tt_appointment WHERE id=%s',(known['result']['id'],))
                    selected=existing.start.replace(tzinfo=timezone.utc)
                else:
                    from tele_tena.api import scheduling
                    day=start.astimezone(timezone.utc).date().isoformat()
                    frappe.set_user(self.users['private_patient'])
                    calendar=scheduling.calendar(offering,day,2,'UTC')
                    starts=[datetime.fromisoformat(slot['start'].replace('Z','+00:00')) for day_row in calendar['days'] for slot in day_row['slots']]
                    starts=[value for value in starts if value>=shifted and value<=shifted+timedelta(minutes=15)]
                    if not starts:raise ValueError('No generated slot for synthetic completion; inspect retained records')
                    selected=starts[0]
                def actual_booking(selected=selected,scenario=scenario):
                    info=j.one('SELECT price,minutes FROM tt_offering WHERE id=%s',(offering,))
                    body='Fictional consultation for documentation and earnings review.'
                    sharing={'name':False,'history':False}
                    return j.book(offering,j.iso(selected.replace(tzinfo=None)),body,sharing,DATASET+'-'+scenario,info.price,info.minutes,j.disclosure(j.profile('patient'),body,sharing),'Africa/Addis_Ababa')
                booked=self.step('booking-'+scenario,'private_patient',actual_booking)
                # Held scenario uses a distinct time; join at that time in this
                # controlled fictional clock rather than changing any booking.
                with simulation_context(selected):
                    from tele_tena.api import consultations
                    self.step('session-'+scenario,'counselor',lambda:offline_session(booked['id']))
                    self.step('notes-'+scenario,'counselor',lambda:p.save_note_draft(booked['id'],'Fictional private working note, visible only to the treating clinician.','Fictional next steps: consider a regular rest routine and book a follow-up if helpful.'))
                    self.step('finalize-'+scenario,'counselor',lambda:p.finalize_consultation(booked['id'],publish_summary=1))
            if scenario=='held':self.step('dispute','private_patient',lambda:accounting.open_earning_dispute(booked['id'],'Fictional demonstration hold pending reviewer resolution.'))
            if scenario=='released':
                self.step('feedback','private_patient',lambda:trust.submit_session_feedback(booked['id'],4))
        self.step('release','Administrator',lambda:(accounting.release_eligible_earnings([self.result('booking-released')['id']]) or {'processed':True}))
        self.step('payout','counselor',lambda:accounting.request_payout(10000,DATASET+'-payout'))
        cancelled_payout=self.step('cancelled-payout','counselor',lambda:accounting.request_payout(5000,DATASET+'-cancelled-payout'))
        self.step('cancel-payout','counselor',lambda:accounting.cancel_payout(cancelled_payout['id'],'Fictional cancelled payout request.'))
        # Scheduled request distribution works without requiring fresh presence.
        day=(self.anchor+timedelta(days=4)).replace(hour=9,minute=0,second=0,microsecond=0)
        def request():return requests.publish_request(DATASET+'-counseling','I would like to talk about managing everyday stress. Fictional request.','scheduled','en','video',{'name':False,'history':False},DATASET+'-request',earliest_start=j.iso(day.replace(tzinfo=None)),latest_start=j.iso((day+timedelta(hours=3)).replace(tzinfo=None)))
        req=self.step('request','patient',request)
        for key in ('counselor','therapist'):
            self.step('offer-'+key,key,lambda key=key:requests.submit_offer(req['id'],self.result('offering-'+key+'-counseling')['id'],j.iso(day.replace(tzinfo=None))))
        # Separate requests retain diverse genuine supported transitions.
        for scenario,patient_key in [('matched','oromo_patient'),('cancelled','private_patient'),('withdrawn','couple_partner')]:
            start=day+timedelta(days=1,hours=3 if scenario=='withdrawn' else 2)
            def publish(scenario=scenario,start=start):
                return requests.publish_request(DATASET+'-counseling','I would like a supportive conversation. Fictional private request.','scheduled','en','video',{'name':False,'history':False},DATASET+'-request-'+scenario,earliest_start=j.iso(start.replace(tzinfo=None)),latest_start=j.iso((start+timedelta(hours=2)).replace(tzinfo=None)))
            request=self.step('request-'+scenario,patient_key,publish)
            if scenario=='cancelled':
                self.step('close-request-'+scenario,patient_key,lambda request=request:requests.close_request(request['id']))
            else:
                offer=self.step('scenario-offer-'+scenario,'counselor',lambda request=request,start=start:requests.submit_offer(request['id'],offering,j.iso(start.replace(tzinfo=None))))
                if scenario=='withdrawn':self.step('withdraw-offer','counselor',lambda offer=offer:requests.withdraw_offer(offer['id']))
                else:self.step('accept-offer',patient_key,lambda request=request,offer=offer:requests.respond_offer(request['id'],offer['id'],'accept',sharing={'name':False,'history':False},expected_disclosure={'request':'I would like a supportive conversation. Fictional private request.'}))
        self.step('ready-counselor','counselor',lambda:requests.set_request_presence(False))


def document(label):
    """Small valid PDF with visible fictional watermark; never executable content."""
    text=('FICTIONAL DEMONSTRATION ONLY - '+label).replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
    stream=f'BT /F1 12 Tf 40 750 Td ({text}) Tj ET'.encode('ascii',errors='replace')
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream']
    data=b'%PDF-1.4\n';offsets=[0]
    for index,obj in enumerate(objects,1):offsets.append(len(data));data+=str(index).encode()+b' 0 obj\n'+obj+b'\nendobj\n'
    start=len(data);data+=b'xref\n0 6\n0000000000 65535 f \n'+b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets[1:]);data+=f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{start}\n%%EOF'.encode()
    return base64.b64encode(data).decode()


@contextmanager
def simulation_context(at):
    """Private CLI process only: historical demo timing, never a public bypass.

    No database balances/states are patched; ordinary application commands run.
    Media is an offline adapter, not evidence of hosted/physical-device calls.
    """
    from tele_tena.review import enabled
    if getattr(frappe.local,'request',None) or not enabled():
        raise RuntimeError('Offline simulation is restricted to the local review seed process')
    state=json.loads(paths()[0].read_text())
    if frappe.session.user not in ('Administrator',*state['users'].values()):
        raise RuntimeError('Only dataset actors may run this simulation')
    from tele_tena.api import journey,scheduling,presentation,consultations,couples
    from tele_tena import accounting,livekit
    modules=(journey,scheduling,presentation,consultations,couples,accounting)
    class Clock(datetime):
        @classmethod
        def now(cls,tz=None):return at.astimezone(tz) if tz else at.replace(tzinfo=None)
    originals=[(module,module.datetime) for module in modules]
    credentials,close=livekit._credentials,livekit.close_room
    try:
        for module,_ in originals:module.datetime=Clock
        livekit._credentials=lambda:('wss://fictional-demo.invalid','fictional-demo-key',secrets.token_urlsafe(32))
        livekit.close_room=lambda *args,**kwargs:None
        yield
    finally:
        for module,original in originals:module.datetime=original
        livekit._credentials,livekit.close_room=credentials,close


def offline_session(appointment):
    from tele_tena.api import consultations,journey
    # This function can only be reached in the non-HTTP review seed command.
    if getattr(frappe.local,'request',None):raise RuntimeError('CLI only')
    consultations.join(appointment)  # Scoped ephemeral token is discarded, never logged.
    consultations.end(appointment)
    journey.audit(appointment,'FictionalSession',{'dataset':DATASET,'actual_media':False,'clock':'process-local synthetic scenario'})
    return {'state':'Ended','actual_media':False}


def reconcile(state=None):
    from tele_tena import accounting
    state=state or json.loads(paths()[0].read_text())
    users=state['users']
    result={'patient_owners':0,'clinician_owners':0,'balanced':True}
    for key,user in users.items():
        wallet=frappe.db.sql('SELECT available,reserved FROM tt_wallet WHERE patient=%s',(user,),as_dict=True)
        if wallet:
            accounting.check_wallet_projection(user,wallet[0]);result['patient_owners']+=1
        if key in ('counselor','therapist','psychiatrist','applicant'):
            pending=int(frappe.db.sql("SELECT COALESCE(SUM(net_minor),0) FROM tt_earning WHERE clinician=%s AND state IN ('Pending','Disputed')",(user,))[0][0])
            released=int(frappe.db.sql("SELECT COALESCE(SUM(net_minor),0) FROM tt_earning WHERE clinician=%s AND state='Released'",(user,))[0][0])
            reserved=int(frappe.db.sql("SELECT COALESCE(SUM(amount_minor),0) FROM tt_payout WHERE clinician=%s AND state IN ('Requested','Processing')",(user,))[0][0])
            for bucket,expected in [('pending',pending),('earnings_available',released-reserved),('payout_reserved',reserved)]:
                if expected<0 or accounting.balance('clinician',user,bucket)!=expected:
                    raise ValueError('Clinician obligation/subledger mismatch; records preserved')
            result['clinician_owners']+=1
    unbalanced=frappe.db.sql('SELECT j.id FROM tt_journal j JOIN tt_journal_line l ON l.journal_id=j.id GROUP BY j.id HAVING SUM(l.debit_minor)<>SUM(l.credit_minor) LIMIT 1')
    if unbalanced:raise ValueError('Unbalanced journal; preserved for investigation')
    return result
