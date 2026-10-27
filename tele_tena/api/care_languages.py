"""Care-language claims and human decisions confer no service/clinical permission."""
import json,uuid
import frappe
from tele_tena.api.journey import actor,profile,rows,one,query,command,integer,text,fail,audit

def valid(code):return bool(rows('SELECT code FROM tt_care_language WHERE code=%s AND active=1',(code,)))
def approved_for(clinician):return [r.language for r in rows("SELECT language FROM tt_care_language_claim WHERE clinician=%s AND active=1 AND state='Approved' ORDER BY language",(clinician,))]
def offering_languages(offering):
    r=one('SELECT o.clinician,o.care_languages,p.languages FROM tt_offering o JOIN tt_profile p ON p.user=o.clinician WHERE o.id=%s',(offering,))
    try:values=json.loads(r.care_languages if r.care_languages is not None else r.languages or '[]')
    except (ValueError,TypeError):return []
    allowed=set(approved_for(r.clinician));return list(dict.fromkeys(c for c in values if c in allowed and valid(c)))
@frappe.whitelist(allow_guest=True,methods=['GET'])
def catalog(search='',offset=0):
    search=text(search,100,False);offset=integer(offset,0,10000);term='%'+search.replace('!','!!').replace('%','!%').replace('_','!_')+'%'
    found=rows("SELECT code,english,amharic,afaan_oromo FROM tt_care_language WHERE active=1 AND (english LIKE %s ESCAPE '!' OR aliases LIKE %s ESCAPE '!' OR code=%s) ORDER BY english,code LIMIT 21 OFFSET %s",(term,term,search,offset))
    return {'items':found[:20],'has_more':len(found)>20}
@query()
def claims(clinician=None):
    user=actor();clinician=clinician or user
    if user!=clinician and 'Tele Tena Approver' not in frappe.get_roles(user):frappe.throw('Language application unavailable',frappe.PermissionError)
    return rows('SELECT c.*,l.english FROM tt_care_language_claim c JOIN tt_care_language l ON l.code=c.language WHERE clinician=%s ORDER BY l.english',(clinician,))
@command
def save_claims(values,draft=False):
    from tele_tena.api.professional import owner
    user=owner()
    if isinstance(values,str):values=json.loads(values)
    if not isinstance(values,list) or len(values)>80:fail('Choose up to 80 care languages.')
    one('SELECT name FROM tabUser WHERE name=%s FOR UPDATE',(user,));seen=set()
    for item in values:
        if not isinstance(item,dict) or set(item)-{'code','proficiency','explanation'} or not valid(item.get('code')) or item['code'] in seen:fail('Choose distinct catalog languages.')
        code=item['code'];seen.add(code);rating=integer(item.get('proficiency'),0 if draft in (True,1,'1') else 1,5) or None;explanation=text(item.get('explanation',''),1000,False)
        old=rows('SELECT * FROM tt_care_language_claim WHERE clinician=%s AND language=%s FOR UPDATE',(user,code))
        if old and old[0].proficiency==rating and (old[0].explanation or '')==explanation and old[0].active:continue
        frappe.db.sql("INSERT INTO tt_care_language_claim (clinician,language,proficiency,explanation,state,modified) VALUES (%s,%s,%s,%s,'Pending',UTC_TIMESTAMP(6)) ON DUPLICATE KEY UPDATE proficiency=VALUES(proficiency),explanation=VALUES(explanation),active=1,state='Pending',modified=UTC_TIMESTAMP(6)",(user,code,rating,explanation))
        if old and old[0].state=='Approved':flag_existing(user,code)
        record(user,code,user,'ClaimSubmitted',{'proficiency':rating,'explanation':explanation})
    removed=rows('SELECT language FROM tt_care_language_claim WHERE clinician=%s AND active=1',(user,))
    for r in removed:
        if r.language not in seen:
            frappe.db.sql('UPDATE tt_care_language_claim SET active=0,modified=UTC_TIMESTAMP(6) WHERE clinician=%s AND language=%s',(user,r.language));record(user,r.language,user,'ClaimWithdrawn',{});flag_existing(user,r.language)
    frappe.db.sql("UPDATE tt_profile SET languages=%s WHERE user=%s AND kind='clinician'",(json.dumps(sorted(seen)),user))
    return claims()
def record(clinician,language,user,event,details):frappe.db.sql('INSERT INTO tt_care_language_event VALUES (%s,%s,%s,%s,%s,%s,UTC_TIMESTAMP(6))',(str(uuid.uuid4()),clinician,language,user,event,json.dumps(details)))
def flag_existing(clinician,language):
    for a in rows("SELECT id,policy_snapshot FROM tt_appointment WHERE clinician=%s AND state IN ('Booked','PendingConfirmation') AND start>UTC_TIMESTAMP(6)",(clinician,)):
        policy=json.loads(a.policy_snapshot or '{}')
        if policy.get('care_language') in (None,language):frappe.db.sql('INSERT IGNORE INTO tt_language_appointment_review VALUES (%s,%s,%s,UTC_TIMESTAMP(6))',(a.id,language,'Language authorization changed; logistics review required, no automatic cancellation'))
@command
def decide(clinician,language,decision,reason,evidence_ids=None):
    user=actor('Tele Tena Approver');reason=text(reason,1000)
    if decision not in ('Approved','Declined','Clarification required','Pending'):fail('Choose a language review decision.')
    one('SELECT user FROM tt_application WHERE user=%s',(clinician,))
    evidence_ids=evidence_ids or []
    if isinstance(evidence_ids,str):evidence_ids=json.loads(evidence_ids)
    if not isinstance(evidence_ids,list) or len(evidence_ids)>30:fail('Choose a bounded list of professional evidence.')
    for id in evidence_ids:
        if not rows("SELECT id FROM tt_professional_evidence WHERE id=%s AND user=%s AND purpose<>'Identification'",(id,clinician)):fail('Professional evidence is unavailable to this review.')
    claim=one('SELECT * FROM tt_care_language_claim WHERE clinician=%s AND language=%s AND active=1 FOR UPDATE',(clinician,language))
    if decision=='Approved' and not claim.proficiency:fail('Request an explicit proficiency self-assessment before approval.','language_assessment_required')
    frappe.db.sql('UPDATE tt_care_language_claim SET state=%s,reviewer=%s,reason=%s,modified=UTC_TIMESTAMP(6) WHERE clinician=%s AND language=%s',(decision,user,reason,clinician,language))
    record(clinician,language,user,'LanguageDecision',{'decision':decision,'reason':reason,'evidence':evidence_ids,'self_assessment':claim.proficiency});audit(clinician,'CareLanguageDecision',{'language':language,'decision':decision,'reason':reason})
    if decision!='Approved':flag_existing(clinician,language)
    return claims(clinician)
@command
def preference(language=''):
    p=profile('patient')
    if language and not valid(language):fail('Choose a consultation language from the catalog.')
    frappe.db.sql('UPDATE tt_profile SET preferred_care_language=%s WHERE user=%s',(language or None,p.user));return {'preferred_care_language':language or None}
