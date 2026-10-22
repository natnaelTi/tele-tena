"""Structured applicant claims. Never grants scopes, clinical access or verification."""
import base64
import hashlib
import json
import re
import uuid
from urllib.parse import quote
import frappe
from tele_tena.api.journey import actor,command,query,rows,text,fail,audit

DECLARATION='professional-accuracy-v1'
RATING_DEFINITIONS={1:'Training or introductory exposure',2:'Practice with supervision',3:'Independent practice within professional scope',4:'Advanced practice with substantial relevant experience',5:'Supervises or trains others within professional scope'}


def word_count(value):
    """A word is a non-empty Unicode-whitespace-delimited token; hyphens stay inside it."""
    return len([part for part in re.split(r'[\u0009-\u000d\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+',value) if part])


def validate_bio(value):
    value=text(value,4000,False)
    if word_count(value)>50:fail('Keep your bio to 50 words or fewer. Your original text has not been shortened.','bio_word_limit')
    return value


def owner():
    user=actor()
    p=rows('SELECT kind FROM tt_profile WHERE user=%s',(user,))
    draft=rows('SELECT kind,completed FROM tt_onboarding WHERE user=%s',(user,))
    from tele_tena.review import registration_enabled
    if (p and p[0].kind=='clinician') or (draft and not draft[0].completed and not p and registration_enabled('clinician')):return user
    frappe.throw('Professional application access required',frappe.PermissionError)


def may_review(user,clinician):
    if user==clinician:return True
    return 'Tele Tena Approver' in frappe.get_roles(user) and bool(rows('SELECT user FROM tt_application WHERE user=%s',(clinician,)))


def reference(id,kind,user):
    value=rows('SELECT id,label,country,status FROM tt_reference WHERE id=%s AND kind=%s AND (status IN (\'Listed\',\'Reviewed\',\'Merged\') OR submitted_by=%s)',(id,kind,user))
    if not value:fail('Choose a current directory entry or use Other.','reference_invalid')
    return value[0]


def validate(value,user,submit=False):
    if not isinstance(value,dict):fail('Review the professional application fields.','professional_fields')
    keys={'prefix','prefix_other','first_name','last_name','profession','profession_other','specialties','bio','identification_type','identity_files','qualification_area','qualification_area_other','qualification_title','issuer','issuer_other','issuer_country','certifications','license_number','authority','authority_other','jurisdiction','valid_from','valid_until','non_expiring','license_files','competencies','independent','clinics','declaration','adult','experience_years','cv_files','practice_country'}
    if set(value)-keys:fail('Application contains unsupported fields.','professional_fields')
    result={}
    for key in keys-{'specialties','identity_files','certifications','license_files','competencies','clinics','non_expiring','independent','declaration','adult','cv_files'}:
        if key in value:result[key]=text(str(value[key]),4000 if key=='bio' else {'profession_other':80,'qualification_title':240,'issuer_other':240,'authority_other':240,'license_number':100,'jurisdiction':120}.get(key,240),False)
    if result.get('experience_years'):
        from tele_tena.api.journey import integer
        result['experience_years']=str(integer(result['experience_years'],0,60))
    result['bio']=validate_bio(result.get('bio','')) if submit else text(result.get('bio',''),4000,False)
    for key in ('non_expiring','independent','declaration','adult'):result[key]=value.get(key) is True
    if result.get('prefix') not in (None,'','Dr','Mr','Ms','Mrs','Mx','Prof','Other'):fail('Choose a prefix or Other.','prefix_invalid')
    for key,kind in [('profession','profession'),('issuer','issuer'),('authority','authority')]:
        if result.get(key) and result[key]!='Other':reference(result[key],kind,user)
        if submit and result.get(key)=='Other' and not result.get(key+'_other'):fail('Enter the name for Other.','reference_other_required')
    for key in ('specialties','clinics'):
        values=value.get(key,[])
        if not isinstance(values,list) or len(values)>100 or len(set(values))!=len(values):fail('Review selected entries.','reference_invalid')
        for id in values:reference(id,'specialty' if key=='specialties' else 'facility',user)
        result[key]=values
    if submit and result.get('qualification_area') and result['qualification_area'] not in result['specialties']+['Other']:fail('Choose a selected specialty area or Other.','qualification_area_invalid')
    if submit and result.get('qualification_area')=='Other' and not result.get('qualification_area_other'):fail('Enter the qualification’s related area, or leave the optional area unselected.','qualification_area_other_required')
    if submit and result.get('issuer')=='Other' and not re.fullmatch('[A-Z]{2}',result.get('issuer_country','')):fail('Choose the institution country.','issuer_country_required')
    if result['non_expiring'] and result.get('valid_until'):fail('Clear Valid Until for a non-expiring credential.','credential_date_range')
    for key in ('valid_from','valid_until'):
        if result.get(key):
            try:result[key]=frappe.utils.getdate(result[key]).isoformat()
            except Exception:fail('Enter a valid credential date.','credential_date_invalid')
    if result.get('valid_from') and result.get('valid_until') and result['valid_until']<result['valid_from']:fail('Valid Until must be on or after Valid From.','credential_date_range')
    if result.get('identification_type') not in (None,'','National ID',"Driver’s License",'Passport'):fail('Choose an identification type.','identification_type_invalid')
    file_references=0
    def files(values,purpose):
        nonlocal file_references
        if not isinstance(values,list) or len(values)>100 or len(set(values))!=len(values):fail('Review supporting files.','evidence_invalid')
        file_references+=len(values)
        if file_references>2000:fail('An application can reference up to 2,000 supporting files.','evidence_reference_limit')
        for id in values:
            if not rows('SELECT id FROM tt_professional_evidence WHERE id=%s AND user=%s AND purpose=%s',(id,user,purpose)):fail('Supporting file is unavailable to this application.','evidence_invalid')
        return values
    for key,purpose in [('identity_files','Identification'),('license_files','License'),('cv_files','CV')]:result[key]=files(value.get(key,[]),purpose)
    certs=value.get('certifications',[])
    if not isinstance(certs,list) or len(certs)>200:fail('Up to 200 certifications may be saved per application.','certifications_limit')
    result['certifications']=[];seen=set()
    for item in certs:
        if not isinstance(item,dict) or set(item)-{'id','title','description','issuer','issuer_other','country','issued','expires','files'}:fail('Review certification fields.','certification_invalid')
        cert={k:text(str(v),1000 if k=='description' else 240,False) for k,v in item.items() if k!='files'}
        if not re.fullmatch(r'[a-f0-9-]{36}',cert.get('id','')) or cert['id'] in seen:fail('Certification row is invalid.','certification_invalid')
        seen.add(cert['id']);cert['files']=files(item.get('files',[]),'Certification')
        if submit and not cert.get('title'):fail('Enter a title for every certification, or remove its empty row.','certification_title_required')
        if cert.get('issuer') and cert['issuer']!='Other':reference(cert['issuer'],'issuer',user)
        if submit and cert.get('issuer')=='Other' and not (cert.get('issuer_other') and cert.get('country')):fail('Enter the certification issuer and country.','issuer_country_required')
        for k in ('issued','expires'):
            if cert.get(k):
                try:cert[k]=frappe.utils.getdate(cert[k]).isoformat()
                except Exception:fail('Enter valid certification dates.','credential_date_invalid')
        if cert.get('issued') and cert.get('expires') and cert['expires']<cert['issued']:fail('Certification expiry must follow its issue date.','credential_date_range')
        result['certifications'].append(cert)
    domains=value.get('competencies',[])
    if not isinstance(domains,list) or len(domains)>100:fail('Review selected competency domains.','competency_invalid')
    result['competencies']=[];seen=set()
    for item in domains:
        if not isinstance(item,dict) or set(item)-{'domain','rating','explanation','files'}:fail('Review competency fields.','competency_invalid')
        reference(item.get('domain'),'domain',user)
        if item['domain'] in seen or type(item.get('rating')) is not int or item['rating'] not in (RATING_DEFINITIONS if submit else {0,*RATING_DEFINITIONS}):fail('Select a rating for every selected domain.','competency_rating_required')
        seen.add(item['domain']);result['competencies'].append({'domain':item['domain'],'rating':item['rating'],'explanation':text(item.get('explanation',''),1000,False),'files':files(item.get('files',[]),'Competency')})
    if submit:
        for key,label in [('first_name','First Name'),('last_name','Last Name'),('profession','Profession'),('qualification_title','Awarded Qualification Title'),('issuer','Issuing Institution')]:
            if not result.get(key):fail('Complete '+label+' before submitting.','professional_required')
        if result.get('prefix')=='Other' and not result.get('prefix_other'):fail('Enter your preferred prefix.','prefix_invalid')
        full_name=' '.join(filter(None,[result.get('prefix_other') if result.get('prefix')=='Other' else result.get('prefix'),result['first_name'],result['last_name']]))
        if len(full_name)>120:fail('Keep your combined professional name to 120 characters or fewer.','professional_name_invalid')
        if not result['adult']:fail('Professional registration remains restricted to adults.','adult_required')
        if not result['declaration']:fail('Confirm your application declaration before submitting.','declaration_required')
    return result


@query()
def application(clinician=None):
    user=actor();clinician=clinician or owner()
    if not may_review(user,clinician):frappe.throw('Application unavailable',frappe.PermissionError)
    saved=rows('SELECT payload,revision,legacy_name FROM tt_professional_draft WHERE user=%s',(clinician,))
    evidence=rows('SELECT id,purpose,filename,mime,content_size,content_sha256,created FROM tt_professional_evidence WHERE user=%s ORDER BY created',(clinician,))
    identity_access=user==clinician or bool(rows('SELECT clinician FROM tt_identity_reviewer WHERE clinician=%s AND reviewer=%s',(clinician,user)))
    evidence=[e for e in evidence if e.purpose!='Identification' or identity_access]
    legacy=rows("SELECT answers FROM tt_onboarding WHERE user=%s AND kind='clinician'",(clinician,))
    legacy=json.loads(legacy[0].answers) if legacy else {}
    public=rows("SELECT display_name,introduction FROM tt_profile WHERE user=%s AND kind='clinician'",(clinician,))
    payload=json.loads(saved[0].payload) if saved else {'bio':public[0].introduction or ''} if public else {}
    if not saved:
        claims=legacy.get('professional',{})
        if isinstance(claims,dict):
            for target,key in [('qualification_title','qualification'),('license_number','registration_number'),('jurisdiction','jurisdiction'),('valid_from','credential_valid_from'),('valid_until','credential_expiry'),('experience_years','experience_years')]:
                if claims.get(key) is not None:payload[target]=str(claims[key])
            for target,key in [('issuer','issuing_institution'),('authority','issuing_authority')]:
                if claims.get(key):payload[target]='Other';payload[target+'_other']=claims[key]
            if claims.get('professional_category'):
                matched=rows("SELECT id FROM tt_reference WHERE kind='profession' AND label=%s AND merged_into IS NULL",(claims['professional_category'],))
                payload['profession']=matched[0].id if matched else 'Other'
                if not matched:payload['profession_other']=claims['professional_category']

    if not identity_access:payload.pop('identity_files',None);payload.pop('identification_type',None)
    submissions=rows('SELECT id,payload,digest,created,declaration_version,reference_snapshot FROM tt_professional_submission WHERE user=%s ORDER BY created DESC LIMIT 30',(clinician,))
    for row in submissions:
        row.payload=json.loads(row.payload)
        if not identity_access:row.payload.pop('identity_files',None);row.payload.pop('identification_type',None)
    # Only selected reference labels leave this private endpoint; never the whole registry.
    selected=set()
    for key in ('profession','issuer','authority'):selected.add(payload.get(key,''))
    for key in ('specialties','clinics'):selected.update(payload.get(key,[]))
    selected.update(c.get('domain','') for c in payload.get('competencies',[]))
    selected.update(c.get('issuer','') for c in payload.get('certifications',[]))
    reference_rows=rows('SELECT id,label,country FROM tt_reference WHERE id IN ('+','.join(['%s']*len(selected))+')',tuple(selected)) if selected else []
    reference_labels={r.id:r.label for r in reference_rows}
    legacy_cv=rows('SELECT filename,content_size,revision FROM tt_resume_evidence WHERE clinician=%s',(clinician,))
    return {'legacy_cv':dict(legacy_cv[0]) if legacy_cv else None,'reference_countries':{r.id:r.country for r in reference_rows},'reference_labels':reference_labels,'legacy':{'name':saved[0].legacy_name if saved and saved[0].legacy_name is not None else legacy.get('name') or (public[0].display_name if public else ''),'professional':legacy.get('professional',{}),'statement':legacy.get('statement','')},'payload':payload,'revision':saved[0].revision if saved else 0,'evidence':evidence,'identity_access':identity_access,'submissions':submissions,'rating_definitions':RATING_DEFINITIONS,'declaration_version':DECLARATION}


def persist(user,payload,revision=None,submit=False):
    old=rows('SELECT revision FROM tt_professional_draft WHERE user=%s FOR UPDATE',(user,))
    if revision is not None and int(revision)!=(old[0].revision if old else 0):fail('This application changed in another tab. Reload before saving; your entries remain here.','professional_conflict')
    clean=validate(payload,user,submit)
    encoded=json.dumps(clean,ensure_ascii=False,sort_keys=True,separators=(',',':'));digest=hashlib.sha256(encoded.encode()).hexdigest()
    original=rows("SELECT display_name FROM tt_profile WHERE user=%s AND kind='clinician'",(user,))
    original_name=original[0].display_name if original else None
    if old:frappe.db.sql('UPDATE tt_professional_draft SET payload=%s,revision=revision+1,modified=UTC_TIMESTAMP(6),legacy_name=COALESCE(legacy_name,%s) WHERE user=%s',(encoded,original_name,user))
    else:frappe.db.sql('INSERT INTO tt_professional_draft (user,payload,revision,modified,legacy_name) VALUES (%s,%s,1,UTC_TIMESTAMP(6),%s)',(user,encoded,original_name))
    if submit:
        already_submitted=bool(rows('SELECT id FROM tt_professional_submission WHERE user=%s AND digest=%s',(user,digest)))
        selected={clean.get(k) for k in ('profession','issuer','authority')}|set(clean.get('specialties',[]))|set(clean.get('clinics',[]))|{c.get('domain') for c in clean.get('competencies',[])}|{c.get('issuer') for c in clean.get('certifications',[])}
        selected.discard(None);selected.discard('');selected.discard('Other')
        snapshot=rows('SELECT id,label,country,region,entity_type,source_id,source_url,accessed,permitted_use,status FROM tt_reference WHERE id IN ('+','.join(['%s']*len(selected))+')',tuple(selected)) if selected else []
        frappe.db.sql('INSERT IGNORE INTO tt_professional_submission (id,user,payload,digest,created,declaration_version,reference_snapshot) VALUES (%s,%s,%s,%s,UTC_TIMESTAMP(6),%s,%s)',(str(uuid.uuid4()),user,encoded,digest,DECLARATION,json.dumps(snapshot,default=str,ensure_ascii=False)))
        # Only structured name + explicitly public bio. Never copies qualifications or ID into public fields.
        name=' '.join(filter(None,[clean.get('prefix_other') if clean.get('prefix')=='Other' else clean.get('prefix'),clean['first_name'],clean['last_name']]))
        name=text(name,120)
        frappe.db.sql('UPDATE tt_profile SET display_name=%s,introduction=%s WHERE user=%s',(name,clean.get('bio',''),user))
        if not already_submitted:audit(user,'ProfessionalDeclaration',{'version':DECLARATION,'digest':digest})
    return clean


@command
def save(payload,revision,submit=False):
    user=owner()
    # Submission of these claims never changes general or individual scope decisions.
    from tele_tena.api.journey import boolean
    persist(user,payload,revision,boolean(submit))
    return {'saved':True,**application(user)}


@command
def upload(purpose,filename,content_base64):
    user=owner()
    if purpose not in ('Identification','Certification','License','Competency','CV'):fail('Choose the evidence category.','evidence_invalid')
    from tele_tena.api.history_documents import validated
    filename,mime,content=validated(filename,content_base64)
    if purpose=='CV' and mime!='application/pdf':fail('Upload your CV as a PDF.','evidence_invalid')
    frappe.db.sql('SELECT name FROM tabUser WHERE name=%s FOR UPDATE',(user,))
    digest=hashlib.sha256(content).hexdigest();old=rows('SELECT id FROM tt_professional_evidence WHERE user=%s AND purpose=%s AND content_sha256=%s',(user,purpose,digest))
    if old:return {'id':old[0].id}
    used=frappe.db.sql('SELECT COUNT(*),COALESCE(SUM(content_size),0) FROM tt_professional_evidence WHERE user=%s',(user,))[0]
    if used[0]>=1000 or used[1]+len(content)>250*1024*1024:fail('Professional evidence storage limit reached. Contact support for a reviewed retention plan.','evidence_quota')
    id=str(uuid.uuid4());frappe.db.sql('INSERT INTO tt_professional_evidence VALUES (%s,%s,%s,%s,%s,FROM_BASE64(%s),%s,%s,UTC_TIMESTAMP(6))',(id,user,purpose,filename,mime,base64.b64encode(content).decode(),digest,len(content)))
    return {'id':id}


@query()
def download(id):
    user=actor();found=rows('SELECT user,purpose,filename,mime,content FROM tt_professional_evidence WHERE id=%s',(id,))
    if not found:frappe.throw('Evidence unavailable',frappe.PermissionError)
    d=found[0]
    allowed=may_review(user,d.user)
    if d.purpose=='Identification' and user!=d.user:allowed=bool(rows('SELECT clinician FROM tt_identity_reviewer WHERE clinician=%s AND reviewer=%s',(d.user,user))) and 'Tele Tena Approver' in frappe.get_roles(user)
    if not allowed:frappe.throw('Evidence unavailable',frappe.PermissionError)
    from werkzeug.wrappers import Response
    return Response(bytes(d.content),mimetype=d.mime,headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff','Content-Disposition':"attachment; filename*=UTF-8''"+quote(d.filename,safe=''),'Content-Security-Policy':"sandbox; default-src 'none'"})


@command
def assign_identity_reviewer(clinician,reviewer,reason):
    lead=actor('Tele Tena Medical Lead');actor('Tele Tena Approver')
    if 'Tele Tena Approver' not in frappe.get_roles(reviewer) or not rows('SELECT user FROM tt_application WHERE user=%s',(clinician,)):fail('Choose an application and an authorized credential reviewer.','reviewer_invalid')
    reason=text(reason,500)
    frappe.db.sql('INSERT INTO tt_identity_reviewer VALUES (%s,%s,%s,%s,UTC_TIMESTAMP(6)) ON DUPLICATE KEY UPDATE assigned_by=VALUES(assigned_by),reason=VALUES(reason),created=VALUES(created)',(clinician,reviewer,lead,reason))
    audit(clinician,'IdentityReviewerAssigned',{'reviewer':reviewer})
    return {'assigned':True}


def retained_cv_ids(user):
    saved=rows('SELECT payload FROM tt_professional_draft WHERE user=%s',(user,))
    snapshots=rows('SELECT payload FROM tt_professional_submission WHERE user=%s ORDER BY created DESC,id DESC',(user,))
    ids=[]
    for row in saved+snapshots:
        for id in json.loads(row.payload).get('cv_files',[]):
            if id not in ids and rows("SELECT id FROM tt_professional_evidence WHERE id=%s AND user=%s AND purpose='CV'",(id,user)):ids.append(id)
    return ids


def cv_available(user):
    return bool(retained_cv_ids(user))


def submitted_legacy_claims(user):
    found=rows('SELECT payload FROM tt_professional_submission WHERE user=%s ORDER BY created DESC,id DESC LIMIT 1',(user,))
    if not found:return {}
    value=json.loads(found[0].payload)
    def label(key):
        id=value.get(key)
        if id=='Other':return value.get(key+'_other','')
        r=rows('SELECT label FROM tt_reference WHERE id=%s',(id,))
        return r[0].label if r else ''
    return {'professional_category':label('profession'),'qualification':value.get('qualification_title',''),'issuing_institution':label('issuer'),'registration_number':value.get('license_number',''),'issuing_authority':label('authority'),'jurisdiction':value.get('jurisdiction',''),'credential_valid_from':value.get('valid_from',''),'credential_expiry':value.get('valid_until',''),'experience_years':value.get('experience_years') or 0}


@command
def revoke_identity_reviewer(clinician,reviewer,reason):
    actor('Tele Tena Medical Lead');actor('Tele Tena Approver');reason=text(reason,500)
    frappe.db.sql('DELETE FROM tt_identity_reviewer WHERE clinician=%s AND reviewer=%s',(clinician,reviewer))
    audit(clinician,'IdentityReviewerRevoked',{'reviewer':reviewer,'reason':reason})
    return {'revoked':True}


@query()
def submission(id):
    user=actor();found=rows('SELECT id,user,payload,digest,created,declaration_version,reference_snapshot FROM tt_professional_submission WHERE id=%s',(id,))
    if not found or not may_review(user,found[0].user):frappe.throw('Submitted application unavailable',frappe.PermissionError)
    row=found[0];payload=json.loads(row.payload)
    identity=user==row.user or ('Tele Tena Approver' in frappe.get_roles(user) and bool(rows('SELECT clinician FROM tt_identity_reviewer WHERE clinician=%s AND reviewer=%s',(row.user,user))))
    if not identity:payload.pop('identity_files',None);payload.pop('identification_type',None)
    ids=set()
    for key in ('identity_files','license_files','cv_files'):ids.update(payload.get(key,[]))
    for item in payload.get('certifications',[])+payload.get('competencies',[]):ids.update(item.get('files',[]))
    evidence=rows('SELECT id,purpose,filename FROM tt_professional_evidence WHERE user=%s AND id IN ('+','.join(['%s']*len(ids))+')',(row.user,*ids)) if ids else []
    references=json.loads(row.reference_snapshot or '[]')
    return {'payload':payload,'reference_labels':{r['id']:r['label'] for r in references},'reference_countries':{r['id']:r.get('country','') for r in references},'evidence':evidence,'identity_access':identity,'id':row.id,'created':row.created,'declaration_version':row.declaration_version}


@command
def attach_scope_license(application,id):
    user=owner()
    from tele_tena.api.vetting import _authorized_scope_application,upload_scope_evidence
    scope=_authorized_scope_application(application,user)
    if scope.clinician!=user:frappe.throw('Scope evidence unavailable',frappe.PermissionError)
    document=rows("SELECT filename,mime,content,content_sha256 FROM tt_professional_evidence WHERE id=%s AND user=%s AND purpose='License'",(id,user))
    if not document or document[0].mime!='application/pdf':fail('Choose a private license PDF from your professional profile. Identification files cannot be attached to scope applications.','scope_license_pdf_required')
    rows('SELECT name FROM `tabTele Tena Vetting Scope Application` WHERE name=%s AND clinician=%s FOR UPDATE',(application,user))
    prior=rows("SELECT name FROM `tabTele Tena Scope Evidence` WHERE scope_application=%s AND evidence_type='License or registration' AND content_sha256=%s FOR UPDATE",(scope.name,document[0].content_sha256))
    if prior:return {'id':prior[0].name,'already_attached':True}
    result=upload_scope_evidence(application,'License or registration',document[0].filename,base64.b64encode(bytes(document[0].content)).decode())
    audit(user,'ProfessionalLicenseAttached',{'application':application,'source_evidence':id,'sha256':document[0].content_sha256})
    return result
