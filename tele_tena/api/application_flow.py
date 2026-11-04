"""Owner/reviewer application microflows; typed evidence and explicit email assistance."""
import base64,hashlib,json,uuid
import frappe
from tele_tena.api.journey import actor,rows,one,text,fail,command,query,audit,boolean

ITEMS={
 'license_document':{'label':'Professional License','purpose':'License','evidence_type':'License or registration'},
 'qualification_document':{'label':'Qualification Document','purpose':'Certification','evidence_type':'Qualification'},
 'training_document':{'label':'Scope Training Document','purpose':'Certification','evidence_type':'Scope training'},
 'cv':{'label':'CV','purpose':'CV'},
 'license_details':{'label':'License Details','fields':['registration_number','issuing_authority','jurisdiction','credential_valid_from','credential_expiry']},
 'training_details':{'label':'Relevant Training','fields':['relevant_training']},
 'explanation':{'label':'Supporting Explanation','fields':['applicant_response']},
}
LABELS={'Submitted':'In Review','Resubmitted':'Resubmitted for Review','Clarification':'Information Requested','Draft':'Draft','Approved':'Approved','Rejected':'Not Approved','Suspended':'Suspended','Expired':'Expired'}

def allowed(application):
 user=actor();app=one('SELECT name,clinician,status,service FROM `tabTele Tena Vetting Scope Application` WHERE name=%s',(application,))
 if app.clinician!=user and 'Tele Tena Approver' not in frappe.get_roles(user):fail('Application unavailable', 'application_unavailable')
 return app

def requested_items(value):
 if value is None:return ['explanation']
 if isinstance(value,str):
  try:value=json.loads(value)
  except ValueError:fail('Choose the information you need.','request_items_invalid')
 if not isinstance(value,list) or not value or len(value)>len(ITEMS) or any(k not in ITEMS for k in value) or len(set(value))!=len(value):fail('Choose the information you need.','request_items_invalid')
 return sorted(value)

def record_request(application,assessment,reason,items):
 items=requested_items(items)
 existing=rows("SELECT id,items,reason,reviewer FROM tt_scope_information_request WHERE application=%s AND state='Open'",(application,))
 if existing and json.loads(existing[0]['items'])==items and existing[0].reason==reason and existing[0].reviewer==actor():return existing[0].id
 frappe.db.sql("UPDATE tt_scope_information_request SET state='Superseded' WHERE application=%s AND state='Open'",(application,))
 id=str(uuid.uuid4());frappe.db.sql("INSERT INTO tt_scope_information_request (id,application,assessment,reviewer,reason,items,state,created) VALUES (%s,%s,%s,%s,%s,%s,'Open',UTC_TIMESTAMP(6))",(id,application,assessment,actor(),reason,json.dumps(items)))
 audit(application,'ScopeInformationRequested',{'request':id,'items':items,'assessment':assessment});return id

@query()
def tracker():
 user=actor();reviewer='Tele Tena Approver' in frappe.get_roles(user)
 result=rows('''SELECT a.name,a.clinician,a.service,a.status,a.submitted_at,a.modified,a.clarification_request,a.decision_reason,p.display_name,s.service_label
 FROM `tabTele Tena Vetting Scope Application` a JOIN tt_profile p ON p.user=a.clinician JOIN `tabTele Tena Service` s ON s.name=a.service '''+('' if reviewer else 'WHERE a.clinician=%s ')+"ORDER BY FIELD(a.status,'Clarification','Resubmitted','Submitted','Draft','Approved','Rejected','Suspended','Expired'),a.modified DESC,a.name",() if reviewer else (user,))
 for r in result:r.status_label=LABELS.get(r.status,r.status)
 return result

@query()
def detail(application):
 app=allowed(application)
 from tele_tena.api import vetting,professional
 item=next((r for r in vetting.my_scope_applications() if r.name==application),None)
 if not item:fail('Application unavailable','application_unavailable')
 requests=rows('SELECT id,assessment,reviewer,reason,items,state,created,origin FROM tt_scope_information_request WHERE application=%s ORDER BY created DESC,id',(application,))
 for r in requests:r['items']=[{'key':k,**ITEMS[k]} for k in json.loads(r['items'])]
 # Retain old free-text requests honestly. No invented typed requirement.
 if app.status=='Clarification' and not any(r.state=='Open' for r in requests):
  requests.insert(0,frappe._dict(id=None,reason=item.clarification_request or item.decision_reason,items=[{'key':'explanation',**ITEMS['explanation']}],state='Legacy',created=item.decided_at))
 responses=rows('SELECT id,request_id,actor,payload,created FROM tt_scope_information_response WHERE application=%s ORDER BY created DESC',(application,))
 for r in responses:r.payload=json.loads(r.payload)
 return {'application':item,'status_label':LABELS.get(app.status,app.status),'requests':requests,'responses':responses,'professional':professional.application(app.clinician),'items':ITEMS,'history':rows('SELECT name,decision,findings,restrictions,decided_at FROM `tabTele Tena Vetting Assessment` WHERE scope_application=%s ORDER BY creation DESC,name',(application,))}

def copy_scope_document(app,evidence_id,evidence_type):
 from tele_tena.api.history_documents import validated
 evidence=one('SELECT * FROM tt_professional_evidence WHERE id=%s AND user=%s',(evidence_id,app.clinician))
 if evidence.purpose=='Identification' or evidence.mime not in (('application/pdf','image/jpeg','image/png') if evidence_type=='License or registration' else ('application/pdf',)):fail('Use a private PDF for this service document.','scope_evidence_invalid')
 filename,mime,data=validated(evidence.filename,base64.b64encode(bytes(evidence.content)).decode())
 digest=hashlib.sha256(data).hexdigest()
 prior=rows('SELECT name FROM `tabTele Tena Scope Evidence` WHERE scope_application=%s AND evidence_type=%s AND content_sha256=%s',(app.name,evidence_type,digest))
 if prior:return prior[0].name
 revision=frappe.db.sql('SELECT COALESCE(MAX(revision),0)+1 FROM `tabTele Tena Scope Evidence` WHERE scope_application=%s AND evidence_type=%s',(app.name,evidence_type))[0][0]
 id=uuid.uuid4().hex;now=frappe.utils.now_datetime()
 frappe.db.sql('''INSERT INTO `tabTele Tena Scope Evidence` (name,owner,creation,modified,modified_by,docstatus,idx,scope_application,clinician,evidence_type,filename,revision,content_size,content_sha256,uploaded_by,uploaded_at)
 VALUES (%s,%s,%s,%s,%s,0,0,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',(id,app.clinician,now,now,actor(),app.name,app.clinician,evidence_type,filename,revision,len(data),digest,actor(),now))
 frappe.db.sql('INSERT INTO tt_scope_evidence_content VALUES (%s,FROM_BASE64(%s))',(id,base64.b64encode(data).decode()))
 audit(app.name,'RequestedEvidenceLinked',{'source':evidence_id,'scope_evidence':id,'type':evidence_type,'sha256':digest});return id

@command
def respond(application,request_id,fields=None,files=None):
 one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
 app=allowed(application);user=actor()
 if app.clinician!=user:fail('Use the recorded assistance workflow for another applicant.','application_unavailable')
 one('SELECT name FROM `tabTele Tena Vetting Scope Application` WHERE name=%s FOR UPDATE',(application,))
 fields=fields or {};files=files or {}
 if not isinstance(fields,dict) or not isinstance(files,dict):fail('Review the requested information.','information_invalid')
 if not request_id:
  digest=hashlib.sha256(json.dumps({'fields':fields,'files':files},sort_keys=True,separators=(',',':')).encode()).hexdigest()
  prior=rows('''SELECT r.id,r.digest FROM tt_scope_information_response r JOIN tt_scope_information_request q ON q.id=r.request_id WHERE r.application=%s AND q.origin='LegacyResponseCategorization' ORDER BY r.created DESC LIMIT 1''',(application,))
  if prior and prior[0].digest==digest:return {'submitted':True,'idempotent':True,'response':prior[0].id}
  if app.status!='Clarification' or rows("SELECT id FROM tt_scope_information_request WHERE application=%s AND state='Open'",(application,)):fail('Reload the current information request before responding.','information_closed')
  keys=['explanation']+list(files)
  if any(k not in ITEMS or not ITEMS[k].get('purpose') for k in files):fail('Choose the type of requested document.','information_invalid')
  original=one('SELECT reviewer,clarification_request,decision_reason FROM `tabTele Tena Vetting Scope Application` WHERE name=%s',(application,));request_id=str(uuid.uuid4())
  frappe.db.sql("INSERT INTO tt_scope_information_request (id,application,assessment,reviewer,reason,items,state,created,origin) VALUES (%s,%s,NULL,%s,%s,%s,'Open',UTC_TIMESTAMP(6),'LegacyResponseCategorization')",(request_id,application,original.reviewer or user,original.clarification_request or original.decision_reason,json.dumps(keys)))
  audit(application,'LegacyResponseCategorized',{'request':request_id,'document_types':list(files),'basis':'Clinician selected document types while responding to an existing free-text reviewer request; no historical typed requirement invented.'})
 req=one('SELECT * FROM tt_scope_information_request WHERE id=%s AND application=%s FOR UPDATE',(request_id,application))
 keys=json.loads(req['items']);field_keys={f for k in keys for f in ITEMS[k].get('fields',[])};file_keys={k for k in keys if ITEMS[k].get('purpose')}
 if set(fields)-field_keys or set(files)-file_keys:fail('Submit only the information requested for this application.','information_invalid')
 payload={'fields':fields,'files':files};digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 previous=rows('SELECT id,digest FROM tt_scope_information_response WHERE request_id=%s',(request_id,))
 if previous:
  if previous[0].digest!=digest:fail('This request already has a response. Reload to see its current status.','information_already_submitted')
  return {'submitted':True,'idempotent':True,'response':previous[0].id}
 if req.state!='Open' or app.status!='Clarification':fail('This request is no longer open. Reload to see the current application.','information_closed')
 from tele_tena.api import vetting,professional
 values=dict(one('SELECT * FROM `tabTele Tena Vetting Scope Application` WHERE name=%s',(app.name,)));values={k:values.get(k) for k in vetting.APPLICANT_FIELDS}
 for k in keys:
  if k=='explanation' and not str(fields.get('applicant_response','')).strip():fail('Add the requested explanation.','information_required')
  if k=='training_details' and not str(fields.get('relevant_training','')).strip():fail('Add the requested training details.','information_required')
  if k=='license_details' and any(not fields.get(f) for f in ('registration_number','issuing_authority','jurisdiction')):fail('Complete the requested license details.','information_required')
 values.update(fields);links=[]
 draft=rows('SELECT payload,revision FROM tt_professional_draft WHERE user=%s FOR UPDATE',(user,));profile=json.loads(draft[0].payload) if draft else None
 for k in file_keys:
  ids=files.get(k,[])
  if not isinstance(ids,list) or not 1<=len(ids)<=12 or len(set(ids))!=len(ids):fail('Attach the requested PDF document.','information_required')
  normalized=[]
  for id in ids:
   if not isinstance(id,str):fail('Choose an available private document.','scope_evidence_invalid')
   if id.startswith('scope:'):
    source=rows('''SELECT e.filename,c.content FROM `tabTele Tena Scope Evidence` e JOIN tt_scope_evidence_content c ON c.evidence=e.name WHERE e.name=%s AND e.scope_application=%s AND e.clinician=%s''',(id[6:],application,user))
    if not source:fail('This document is unavailable for your response.','scope_evidence_invalid')
    copied=professional._upload(user,ITEMS[k]['purpose'],source[0].filename,base64.b64encode(bytes(source[0].content)).decode())
    audit(application,'ExistingDocumentCategorized',{'source':id[6:],'purpose':ITEMS[k]['purpose'],'new_source':copied['id']});id=copied['id']
   normalized.append(id)
   e=rows('SELECT id,mime FROM tt_professional_evidence WHERE id=%s AND user=%s AND purpose=%s',(id,user,ITEMS[k]['purpose']))
   if not e or e[0].mime not in (('application/pdf','image/jpeg','image/png') if k=='license_document' else ('application/pdf',)):fail('Choose your own supported private file for the requested document.','scope_evidence_invalid')
   if ITEMS[k].get('evidence_type'):links.append(copy_scope_document(app,id,ITEMS[k]['evidence_type']))
  if profile is not None and k in ('license_document','cv'):
   field='license_files' if k=='license_document' else 'cv_files';profile[field]=list(dict.fromkeys(profile.get(field,[])+normalized))
 if profile is not None:professional.persist(user,profile,draft[0].revision,submit=False)
 vetting._save_scope_application(user,app.service,values,submit=True)
 id=str(uuid.uuid4());payload['linked_scope_evidence']=links
 frappe.db.sql('INSERT INTO tt_scope_information_response VALUES (%s,%s,%s,%s,%s,%s,UTC_TIMESTAMP(6))',(id,request_id,application,user,json.dumps(payload),digest))
 frappe.db.sql("UPDATE tt_scope_information_request SET state='Responded' WHERE id=%s",(request_id,))
 audit(application,'ScopeInformationResubmitted',{'request':request_id,'response':id,'linked_evidence':links})
 from tele_tena.communications import queue
 queue(user,'ScopeResubmitted','scope',application,'scope-response:'+id)
 return {'submitted':True,'response':id,'status':'Resubmitted'}

@command
def request_assistance(services,authorization):
 user=actor()
 from tele_tena.api.professional import owner
 if owner()!=user or not boolean(authorization):fail('Authorize assisted entry before requesting help.','assistance_authorization_required')
 if not isinstance(services,list) or not services or len(services)>30 or len(set(services))!=len(services):fail('Choose the service scopes you want to apply for.','scope_selection_invalid')
 for service in services:
  if not rows("SELECT name FROM `tabTele Tena Service` WHERE name=%s AND vetting_required=1 AND catalog_status IN ('Draft','Active')",(service,)):fail('Choose an available service.','scope_selection_invalid')
 one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
 existing=rows("SELECT id FROM tt_assistance_case WHERE clinician=%s AND state='Open'",(user,))
 if existing:return {'id':existing[0].id,'state':'Open','idempotent':True}
 id=str(uuid.uuid4());frappe.db.sql("INSERT INTO tt_assistance_case VALUES (%s,%s,%s,'Open',UTC_TIMESTAMP(6),UTC_TIMESTAMP(6))",(id,user,json.dumps(services)))
 audit(user,'EmailAssistanceRequested',{'case':id,'services':services,'authorization_version':'assisted-entry-request-v1'});return {'id':id,'state':'Open'}

@query()
def assistance_cases():
 user=actor();reviewer='Tele Tena Approver' in frappe.get_roles(user)
 return rows('SELECT c.*,COALESCE(p.display_name,u.full_name) display_name FROM tt_assistance_case c JOIN tabUser u ON u.name=c.clinician LEFT JOIN tt_profile p ON p.user=c.clinician '+('' if reviewer else 'WHERE c.clinician=%s ')+'ORDER BY c.modified DESC',() if reviewer else (user,))

def case_for(id):
 reviewer=actor('Tele Tena Approver');case=one('SELECT * FROM tt_assistance_case WHERE id=%s',(id,))
 if case.clinician==reviewer:fail('A reviewer cannot enter or decide their own assisted application.','assistance_unavailable')
 return case

@query()
def assistance_detail(case):
 c=case_for(case)
 from tele_tena.api import professional,policies
 data=professional.application(c.clinician)
 return {'case':c,'professional':data,'policies':policies.current(),'services':json.loads(c.services),'verified_contacts':rows('SELECT channel,contact FROM tt_contact_identity WHERE user=%s AND verified_at IS NOT NULL',(c.clinician,)),'service_labels':rows('SELECT name,service_label FROM `tabTele Tena Service` WHERE name IN %s',(tuple(json.loads(c.services)),))}

@command
def assisted_upload(case,purpose,filename,content_base64):
 c=case_for(case)
 if c.state!='Open':fail('This assistance case is already submitted.','assistance_closed')
 if purpose=='Identification' and not rows('SELECT clinician FROM tt_identity_reviewer WHERE clinician=%s AND reviewer=%s',(c.clinician,actor())):fail('An assigned identity reviewer is required.','identity_review_forbidden')
 from tele_tena.api.professional import _upload
 result=_upload(c.clinician,purpose,filename,content_base64)
 audit(c.clinician,'AssistedEvidenceUploaded',{'case':case,'evidence':result['id'],'purpose':purpose});return result

@command
def assisted_save(case,payload,revision):
 c=case_for(case)
 if c.state!='Open':fail('This assistance case is already submitted.','assistance_closed')
 from tele_tena.api import professional
 existing=professional.application(c.clinician)
 if not existing['identity_access']:
  original=rows('SELECT payload FROM tt_professional_draft WHERE user=%s',(c.clinician,));original=json.loads(original[0].payload) if original else {}
  for k in ('identity_files','identification_type'):
   if payload.get(k) and payload[k]!=original.get(k):fail('Identification requires an assigned credential reviewer.','identity_review_forbidden')
   if k in original:payload[k]=original[k]
 professional.persist(c.clinician,payload,revision,False)
 audit(c.clinician,'AssistedDraftSaved',{'case':case});return {'saved':True}

@command
def assisted_submit(case,authorization_file,source_reference,received_on,terms_version,privacy_version,attestations):
 one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
 c=case_for(case);one('SELECT id FROM tt_assistance_case WHERE id=%s FOR UPDATE',(case,))
 if c.state=='Submitted':return {'submitted':True,'idempotent':True}
 source_reference=text(source_reference,240)
 import re
 if not isinstance(received_on,str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',received_on):fail('Enter the date the authorization email was received.','assistance_date_invalid')
 try:received=frappe.utils.getdate(received_on)
 except (TypeError,ValueError):fail('Enter a valid received date.','assistance_date_invalid')
 if received>frappe.utils.getdate():fail('The received date cannot be in the future.','assistance_date_invalid')
 if not isinstance(attestations,dict) or set(attestations)!={'authorization','accuracy','adult','terms','privacy','registration_consent','care_languages'} or not all(type(v) is bool and v for v in attestations.values()):fail('Record each explicit statement supplied by the clinician.','assistance_attestation_required')
 evidence=rows("SELECT id,mime FROM tt_professional_evidence WHERE id=%s AND user=%s AND purpose='Authorization'",(authorization_file,c.clinician))
 if not evidence or evidence[0].mime!='application/pdf':fail('Attach the private PDF of the clinician’s email authorization and declarations.','assistance_authorization_required')
 if not rows("SELECT id FROM tt_audit WHERE subject=%s AND action='AssistedEvidenceUploaded' AND JSON_UNQUOTE(JSON_EXTRACT(evidence,'$.case'))=%s AND JSON_UNQUOTE(JSON_EXTRACT(evidence,'$.evidence'))=%s",(c.clinician,case,authorization_file)):fail('Upload the authorization for this specific assistance case.','assistance_authorization_required')
 from tele_tena.api import professional,policies,scope_intake
 current=policies.current()
 if terms_version!=current['terms_version'] or privacy_version!=current['privacy_version']:fail('The supplied policy versions changed. Obtain current acknowledgements.','policy_changed')
 draft=one('SELECT payload FROM tt_professional_draft WHERE user=%s',(c.clinician,));payload=json.loads(draft.payload)
 # The reviewer records an email-based declaration, never a forged owner UI click.
 payload['adult']=True;payload['declaration']=True;clean=professional.validate(payload,c.clinician,True)
 def label(k):
  return clean.get(k+'_other','') if clean.get(k)=='Other' else (rows('SELECT label FROM tt_reference WHERE id=%s',(clean.get(k),)) or [frappe._dict(label='')])[0].label
 name=' '.join(filter(None,[clean.get('prefix_other') if clean.get('prefix')=='Other' else clean.get('prefix'),clean['first_name'],clean['last_name']]))
 languages=rows('SELECT language,proficiency FROM tt_care_language_claim WHERE clinician=%s AND active=1',(c.clinician,))
 if not languages or any(not x.proficiency for x in languages):fail('Record the care languages and proficiency declared in the clinician’s email.','care_language_assessment_required')
 if not rows('SELECT user FROM tt_profile WHERE user=%s',(c.clinician,)):
  frappe.db.sql("INSERT INTO tt_profile (user,kind,display_name,history,share_name,share_history,public_id,languages,introduction) VALUES (%s,'clinician',%s,'',0,0,%s,%s,%s)",(c.clinician,name,str(uuid.uuid4()),json.dumps([x.language for x in languages]),clean.get('bio','')))
 from tele_tena.account_context import authorized_user_change
 with authorized_user_change():frappe.get_doc('User',c.clinician).add_roles('Tele Tena Applicant')
 professional.persist(c.clinician,clean,submit=True,declaration_version='professional-accuracy-email-v1')
 services=json.loads(c.services)
 frappe.db.sql("INSERT INTO tt_application (user,statement,status,requested_services,submitted_at) VALUES (%s,%s,'Pending',%s,UTC_TIMESTAMP(6)) ON DUPLICATE KEY UPDATE status='Pending',requested_services=VALUES(requested_services),submitted_at=UTC_TIMESTAMP(6)",(c.clinician,'Clinician-supplied application entered with recorded email authorization.',json.dumps(services)))
 claims={'professional_category':label('profession'),'qualification':clean['qualification_title'],'issuing_institution':label('issuer'),'registration_number':clean.get('license_number',''),'issuing_authority':label('authority'),'jurisdiction':clean.get('jurisdiction',''),'credential_valid_from':clean.get('valid_from',''),'credential_expiry':clean.get('valid_until',''),'experience_years':clean.get('experience_years') or '0'}
 frappe.db.sql("UPDATE tt_onboarding SET completed=UTC_TIMESTAMP(6),answers=%s WHERE user=%s",(json.dumps({'name':name,'adult':True,'consent':True,'professional':claims,'requested_services':services,'assistance_case':case}),c.clinician))
 scope_intake.submit_selected_scopes(c.clinician,services,assisted_actor=actor())
 id=str(uuid.uuid4());digest=hashlib.sha256(json.dumps(clean,sort_keys=True).encode()).hexdigest()
 frappe.db.sql('INSERT INTO tt_assisted_submission VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,UTC_TIMESTAMP(6))',(id,case,c.clinician,actor(),authorization_file,source_reference,received,terms_version,privacy_version,json.dumps(attestations),digest))
 frappe.db.sql("UPDATE tt_assistance_case SET state='Submitted',modified=UTC_TIMESTAMP(6) WHERE id=%s",(case,))
 audit(c.clinician,'EmailAssistedSubmission',{'case':case,'source':authorization_file,'source_reference':source_reference,'received_on':str(received),'declaration_version':'professional-accuracy-email-v1','terms_version':terms_version,'privacy_version':privacy_version,'actor':actor()})
 from tele_tena.communications import application_submitted
 application_submitted(c.clinician);return {'submitted':True,'case':case}

@query()
def document(id):
 e=one('SELECT scope_application,filename FROM `tabTele Tena Scope Evidence` WHERE name=%s',(id,));allowed(e.scope_application)
 data=one('SELECT content FROM tt_scope_evidence_content WHERE evidence=%s',(id,))
 from tele_tena.api.history_documents import validated
 from urllib.parse import quote
 from werkzeug.wrappers import Response
 name,mime,content=validated(e.filename,base64.b64encode(bytes(data.content)).decode())
 return Response(content,mimetype=mime,headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff','Content-Disposition':"attachment; filename*=UTF-8''"+quote(name,safe=''),'Content-Security-Policy':"sandbox; default-src 'none'"})

@query()
def assisted_languages(case):
 c=case_for(case)
 from tele_tena.api.care_languages import claims
 return claims(c.clinician)

@command
def assisted_save_languages(case,values,draft=True):
 c=case_for(case)
 if c.state!='Open':fail('This assistance case is already submitted.','assistance_closed')
 from tele_tena.api.care_languages import _save_claims
 result=_save_claims(c.clinician,values,draft);audit(c.clinician,'AssistedLanguagesRecorded',{'case':case});return result

@command
def assisted_add_facility(case,label,country,region,entity_type,identifier='',website=''):
 c=case_for(case)
 if c.state!='Open':fail('This assistance case is already submitted.','assistance_closed')
 from tele_tena.api.professional_directory import _add_facility
 result=_add_facility(c.clinician,label,country,region,entity_type,identifier,website)
 audit(c.clinician,'AssistedFacilityClaim',{'case':case,'facility':result['id'],'verified':False});return result

@query()
def assisted_resolve(case,ids):
 c=case_for(case)
 if not isinstance(ids,list) or len(ids)>100:fail('Select a bounded number of directory entries.','reference_invalid')
 return rows("SELECT id,label,country,status,merged_into FROM tt_reference WHERE id IN %s AND (status IN ('Listed','Reviewed','Merged') OR submitted_by=%s)",(tuple(ids) or ('',),c.clinician))
