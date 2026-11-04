"""Bounded server-side directory search; pending facilities remain owner-only."""
from tele_tena.localization import localized_throw
import json
import uuid
import frappe
from tele_tena.api.journey import actor,query,command,rows,text,integer,fail,audit


@query()
def search(kind,search='',country='',offset=0,limit=20,prefer_country='',profession=''):
    user=actor()
    if kind not in ('profession','specialty','domain','issuer','authority','facility'):fail('Unknown directory.')
    offset=integer(offset,0,1000000);limit=integer(limit,1,50);search=text(search,120,False);country=text(country,2,False)
    # Escape wildcard characters rather than allow unbounded wildcard queries.
    term='%'+search.replace('!','!!').replace('%','!%').replace('_','!_')+'%'
    where="kind=%s AND merged_into IS NULL AND (status IN ('Listed','Reviewed') OR submitted_by=%s) AND (label LIKE %s ESCAPE '!' OR aliases LIKE %s ESCAPE '!' OR group_label LIKE %s ESCAPE '!' OR description LIKE %s ESCAPE '!')"
    values=[kind,user,term,term,term,term]
    if kind=='facility':
        # Only explicit shared clinic identities are deduplicated. Never merge
        # organizations by a guessed similar name or infer affiliations.
        where+=" AND (clinic IS NULL OR NOT EXISTS (SELECT 1 FROM tt_reference peer WHERE peer.kind='facility' AND peer.clinic=tt_reference.clinic AND peer.merged_into IS NULL AND (peer.status IN ('Listed','Reviewed') OR peer.submitted_by=%s) AND (CASE WHEN peer.id LIKE 'clinic:%%' THEN 1 ELSE 0 END,peer.id)<(CASE WHEN tt_reference.id LIKE 'clinic:%%' THEN 1 ELSE 0 END,tt_reference.id)))";values.append(user)
    if country:where+=' AND country=%s';values.append(country)
    prefer_country=text(prefer_country,2,False)
    profession=text(profession,100,False)
    order="COALESCE(group_label,''),label,id" if kind=='domain' else "CASE WHEN country='ET' AND priority_et=1 THEN 0 ELSE 1 END,label,id"
    found=rows('SELECT id,label,country,region,entity_type,status,priority_et,priority_review_status,group_label,description FROM tt_reference WHERE '+where+' ORDER BY '+order+' LIMIT %s OFFSET %s',tuple(values+[limit+1,offset]))
    return {'items':found[:limit],'has_more':len(found)>limit,'offset':offset,'limit':limit}


@command
def add_facility(label,country,region,entity_type,identifier='',website=''):
    from tele_tena.api.professional import owner
    user=owner();label=text(label,160);country=text(country,2);region=text(region,140);entity_type=text(entity_type,80);identifier=text(identifier,120,False);website=text(website,300,False)
    if len(country)!=2 or not country.isalpha():fail('Choose a country.','country_invalid')
    if website and not website.startswith('https://'):fail('Use an HTTPS website.','website_invalid')
    frappe.db.sql('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    existing=rows("SELECT id FROM tt_reference WHERE kind='facility' AND LOWER(label)=LOWER(%s) AND country=%s AND LOWER(region)=LOWER(%s) AND (status IN ('Listed','Reviewed') OR submitted_by=%s) AND merged_into IS NULL",(label,country.upper(),region,user))
    if existing:return {'id':existing[0].id,'label':label,'existing':True}
    if rows("SELECT COUNT(*) AS total FROM tt_reference WHERE submitted_by=%s AND kind='facility' AND accessed=CURRENT_DATE",(user,))[0].total>=20:fail('You have reached the daily facility submission limit. Try again tomorrow.','facility_submission_limit')
    id='facility:'+str(uuid.uuid4())
    frappe.db.sql('''INSERT INTO tt_reference (id,kind,label,aliases,country,region,entity_type,source_id,source_url,accessed,permitted_use,status,submitted_by) VALUES (%s,'facility',%s,'[]',%s,%s,%s,%s,%s,CURRENT_DATE,'Applicant submitted; unverified','Pending',%s)''',(id,label,country.upper(),region,entity_type,identifier,website,user))
    return {'id':id,'label':label,'existing':False}


@query()
def pending_facilities():
    actor('Tele Tena Approver')
    return rows("SELECT id,label,country,region,entity_type,source_id,source_url,status FROM tt_reference WHERE kind='facility' AND status='Pending' ORDER BY label LIMIT 100")


@command
def review_facility(id,decision,reason,merge_into=''):
    user=actor('Tele Tena Approver');reason=text(reason,500)
    if decision not in ('Reviewed','Rejected','Merged'):fail('Choose a facility decision.')
    frappe.db.sql('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    found=rows("SELECT * FROM tt_reference WHERE id=%s AND kind='facility' FOR UPDATE",(id,))
    if not found:fail('Facility unavailable.')
    if decision=='Merged':
        target=rows("SELECT id FROM tt_reference WHERE id=%s AND kind='facility' AND status IN ('Reviewed','Listed') AND merged_into IS NULL",(merge_into,))
        if not target or merge_into==id:fail('Choose an existing reviewed facility.')
        # Keep source ID valid through alias resolution; historical submissions unchanged.
    elif decision=='Reviewed' and not found[0].clinic:
        # Native clinic entity remains separate from affiliation and staff privileges.
        # Reviewer creates only a review catalog draft, with no fabricated official registration.
        doc=frappe.new_doc('Tele Tena Clinic');doc.update({'clinic_name':found[0].label,'legal_name':found[0].label,'registration_reference':found[0].source_id or ('Directory submission '+id),'jurisdiction':found[0].country+' / '+found[0].region,'status':'Draft','submitted_by':user});
        previous=getattr(frappe.local,'tele_tena_clinic_review',False)
        try:
            frappe.local.tele_tena_clinic_review=True
            doc.insert()
        finally:frappe.local.tele_tena_clinic_review=previous
        frappe.db.sql('UPDATE tt_reference SET clinic=%s WHERE id=%s',(doc.name,id))
    frappe.db.sql('UPDATE tt_reference SET status=%s,merged_into=%s WHERE id=%s',(decision,merge_into if decision=='Merged' else None,id))
    audit(user,'FacilityDirectoryDecision',{'reference':id,'decision':decision,'reason':reason,'target':merge_into})
    return {'saved':True}


@query('POST')
def resolve(ids):
    user=actor()
    if isinstance(ids,str):ids=json.loads(ids)
    if not isinstance(ids,list) or len(ids)>100:fail('Select a bounded number of directory entries.')
    result=[]
    for id in ids:
        found=rows("SELECT id,label,country,status,merged_into FROM tt_reference WHERE id=%s AND (status IN ('Listed','Reviewed','Merged') OR submitted_by=%s)",(text(id,100),user))
        if found:result.append(found[0])
    return result


@command
def set_priority(id,enabled,source,reason):
    user=actor('Tele Tena Approver')
    if 'Tele Tena Medical Lead' not in frappe.get_roles(user):localized_throw('Medical Lead permission required',frappe.PermissionError)
    from tele_tena.api.journey import boolean
    source=text(source,500);reason=text(reason,1000)
    if not source.startswith('https://'):fail('Provide an HTTPS source for this curated selection.')
    found=rows("SELECT id FROM tt_reference WHERE id=%s AND country='ET' AND kind IN ('issuer','facility','authority') AND merged_into IS NULL FOR UPDATE",(id,))
    if not found:fail('Choose an eligible Ethiopian reference.')
    frappe.db.sql("UPDATE tt_reference SET priority_et=%s,priority_source=%s,priority_review_status='Reviewed' WHERE id=%s",(boolean(enabled),source,id))
    audit(user,'ReferencePriorityDecision',{'reference':id,'enabled':boolean(enabled),'source':source,'reason':reason})
    return {'saved':True}
