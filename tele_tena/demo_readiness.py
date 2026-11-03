"""Explicit owner-authorized fictional catalog readiness; never an install hook."""
import json
import hashlib
from datetime import datetime,timezone
from pathlib import Path
import frappe
from tele_tena import demo_dataset as dataset
from tele_tena.review import write_private

VERSION='demo-ready-v1'
# Existing shipped adult MVP definitions only. No future modules or inferred
# profession-to-regulator mappings. Prices are illustrative ETB minor units.
SERVICES=(
 ('initial-psychotherapy','therapist',60000,45),
 ('ongoing-psychotherapy','therapist',60000,45),
 ('individual-counselling','counselor',30000,30),
 ('stress-adjustment-support','counselor',40000,30),
 ('grief-support','counselor',35000,45),
 ('relationship-counselling','therapist',60000,45),
 ('premarital-counselling','therapist',60000,45),
 ('separation-support','therapist',60000,45),
 ('psychiatric-assessment','psychiatrist',70000,45),
 ('psychiatric-follow-up','psychiatrist',50000,30),
)
REASON='Owner-authorized fictional demonstration exercise only. No real clinical authorization, external credential check or actual licensing verification is represented.'


def setup(dry_run=True):
    """bench --site SITE execute tele_tena.demo_readiness.setup --kwargs '{"dry_run":false}'

    Adds readiness to the existing portable dataset. Never runs its full seed,
    refreshes appointments, resets passwords or changes existing financial data.
    """
    dataset._guard()
    if type(dry_run) is not bool:raise ValueError('dry_run must be a JSON boolean')
    marker,accounts=dataset.paths()
    if not marker.is_file() or not accounts.is_file():
        raise ValueError('The existing fictional dataset and private account manifest are required. No automatic reseed.')
    state=json.loads(marker.read_text())
    if state.get('dataset')!=dataset.DATASET or state.get('site')!=frappe.local.site or not state.get('fictional'):
        raise ValueError('Fictional dataset ownership does not match this site')
    users=state['users']
    for key in ('counselor','therapist','psychiatrist'):
        if users.get(key)!=dataset.DATASET+'-'+key+'@example.invalid':
            raise ValueError('Refusing to adopt or approve unrelated clinicians')
        found=frappe.db.sql('SELECT status FROM tt_application WHERE user=%s',(users[key],));status=found[0][0] if found else None
        if status!='Approved':raise ValueError('The existing operational fictional clinician must already have general approval; existing decisions were preserved')
    before=frappe.db.sql('''SELECT name,catalog_status,clinical_review_status,active
        FROM `tabTele Tena Service` WHERE name IN %s ORDER BY name''',(tuple(r[0] for r in SERVICES),),as_dict=True)
    if len(before)!=len(SERVICES):raise ValueError('Expected the shipped ten adult MVP definitions')
    if dry_run:return {'dry_run':True,'version':VERSION,'services':before,'fictional_clinicians':3,
                       'changes':False,'external_delivery':False,'credentials_unchanged':True}
    protected=_protected()
    original=frappe.session.user;flag=getattr(frappe.flags,'tele_tena_fixture_notifications',False)
    frappe.flags.tele_tena_fixture_notifications=True
    from tele_tena.api import service_catalog as catalog,vetting,care_languages,journey,scheduling,direct_payments
    from tele_tena.api.service_policy import set_immediate_policy
    builder=dataset.Builder(state,marker,{})  # No password access or account creation.
    try:
        frappe.db.savepoint('tt_demo_readiness')
        journey.one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
        if not journey.rows("SELECT version FROM tt_vetting_rubric_version WHERE status='Approved'"):
            definition=vetting.rubric_definition()
            value={k:definition[k] for k in ('title','approval_note','decision_rule','score_min','score_max','scored_criteria')}
            value.update(title='Fictional Demonstration Scope Assessment',approval_note=REASON)
            if not journey.rows('SELECT version FROM tt_vetting_rubric_version WHERE version=%s',('proposed-99.1',)):
                vetting.propose_rubric_version('proposed-99.1',value)
            vetting.approve_rubric_version('proposed-99.1',REASON)
        for index,(key,role,price,minutes) in enumerate(SERVICES):
            frappe.set_user('Administrator')
            doc=frappe.get_doc('Tele Tena Service',key)
            if doc.catalog_status=='Draft':
                if doc.clinical_review_status!='Not reviewed':
                    raise ValueError('A draft has an in-progress human review; finish or explicitly return it to draft. No review decision was overwritten.')
                payload={k:doc.get(k) for k in catalog.SERVICE_FIELDS if k not in ('catalog_status','clinical_review_status','active','vetting_required','immediate_care_enabled') and doc.get(k) is not None}
                payload.update(booking_rules=doc.booking_rules or 'direct-booking\nscheduled\nimmediate-request',
                    professional_categories=doc.professional_categories or ('Psychiatrist (fictional)' if role=='psychiatrist' else dataset.QUALIFICATIONS['professional_category']),
                    credential_requirements=doc.credential_requirements or 'Fictional qualification, license and scope evidence assessed for this demonstration only.',
                    required_consent_schema=doc.required_consent_schema or 'fictional-adult-demo-ready-v1',
                    location_jurisdiction_policy=doc.location_jurisdiction_policy or 'fictional-review-only',
                    catalog_source=(doc.catalog_source or '')+'\n'+REASON,definition_version=VERSION)
                catalog.save_draft_definition(payload)
                catalog.submit_for_clinical_review(key);catalog.review_definition(key,'Approved',REASON)
                journey.audit(key,'FictionalDemoCatalogReady',{'version':VERSION,'reason':REASON})
            elif doc.catalog_status!='Active' or not doc.active or doc.clinical_review_status!='Approved':
                raise ValueError('An existing definition is retired/disabled. Its decision was preserved.')
            if doc.participant_structure=='individual' and not doc.immediate_care_enabled:
                set_immediate_policy(key,True,REASON,VERSION+'-immediate-'+key)
            clinician=users[role]
            frappe.set_user(clinician)
            languages=care_languages.claims()
            declared=json.loads(journey.one('SELECT languages FROM tt_profile WHERE user=%s',(clinician,)).languages or '["en"]')
            if not declared:declared=['en']
            for claim in languages:
                if claim['state']=='Declined':raise ValueError('Existing language decline retained; explicit owner correction is required')
            selected={r['language']:r for r in languages if r['active']}
            # Self-assess only existing fictional profiles; never infer competence
            # for a real applicant or from nationality/interface language.
            values=[{'code':code,'proficiency':selected.get(code,{}).get('proficiency') or 3,
                     'explanation':selected.get(code,{}).get('explanation') or 'Fictional demonstration self-assessment only.'}
                    for code in sorted(set(declared)|set(selected))]
            care_languages.save_claims(values)
            frappe.set_user('Administrator')
            for item in values:
                claim=journey.one('SELECT state FROM tt_care_language_claim WHERE clinician=%s AND language=%s',(clinician,item['code']))
                if claim.state!='Approved':care_languages.decide(clinician,item['code'],'Approved',REASON)
            frappe.set_user(clinician)
            scope=builder.scope(role,key,'Submitted')
            frappe.set_user('Administrator')
            status=frappe.db.get_value('Tele Tena Vetting Scope Application',scope['name'],'status')
            if status!='Approved':
                if status not in ('Submitted','Resubmitted'):raise ValueError('Existing individual scope decision was preserved')
                builder.decide(role,scope,'Approved')
            frappe.set_user(clinician)
            payee=direct_payments.payee()
            if not payee.get('phone'):
                direct_payments.save_payee('+25190000000'+str(('counselor','therapist','psychiatrist').index(role)+1),payee['revision'],REASON)
            existing=journey.rows('SELECT id FROM tt_offering WHERE clinician=%s AND service=%s',(clinician,key))
            if not existing:
                result=journey.publish(key,price,minutes,title=doc.service_label,
                    description='Adult consultation for this fictional demonstration. No real clinical care.',
                    retry_key=VERSION+':'+role+':'+key,care_languages=[v['code'] for v in values])
                scheduling.save_schedule(result['offering'],doc.service_label+' availability','Africa/Addis_Ababa',
                    'video','automatic',0,60,0,0,[{'weekday':d,'start_local':'08:00','end_local':'20:00'} for d in range(7)],[],
                    'Published',auto_requests=True)
        frappe.set_user('Administrator')
        result={'version':VERSION,'ready_service_count':len(SERVICES),'fictional':True,
                'external_verification':False,'credentials_unchanged':True,'real_money':False}
        if protected!=_protected():raise ValueError('Readiness changed protected identity, configuration or financial state; transaction rolled back')
        frappe.db.commit()
        write_private(Path(frappe.get_site_path('private',VERSION+'.json')),result)
        return result
    except Exception:
        frappe.db.rollback(save_point='tt_demo_readiness');raise
    finally:
        frappe.flags.tele_tena_fixture_notifications=flag;frappe.set_user(original)


def _protected():
    # Catalog setup must not depend on repairing unrelated historical holds.
    # Compare exact originals instead; every original financial/auth value stays.
    tables=('tt_wallet','tt_financial_account','tt_journal','tt_journal_line','tt_ledger','tt_earning','tt_dispute','tt_payout','__Auth','tabUser','tabHas Role','tt_notice_preference')
    def value(item):return bytes(item).hex() if isinstance(item,(bytes,bytearray,memoryview)) else str(item)
    state={}
    for table in tables:
        encoded=sorted(json.dumps(row,default=value,ensure_ascii=False) for row in frappe.db.sql('SELECT * FROM `'+table+'`'))
        state[table]=hashlib.sha256(json.dumps(encoded).encode()).hexdigest()
    for name in ('site_config.json','private/tele_tena_email.json','private/tele_tena_sms.json','private/tele_tena_livekit.json','private/tele_tena_otp.key','private/'+dataset.DATASET+'-accounts.json'):
        path=Path(frappe.get_site_path(name))
        if path.is_file():state[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    return state
