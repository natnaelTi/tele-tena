"""Allowlisted public projection; reviewer-only immutable content authoring."""
import json
import re
import uuid
import frappe
from tele_tena.api.journey import actor,command,query,rows,fail,text
from tele_tena.public_content_defaults import DOCUMENTS,CONTACT

def _key(key):
    if key not in {'contact',*DOCUMENTS}:fail('Choose a known content section.','content_key')
    return key

def _payload(key,value):
    if isinstance(value,str):
        try:value=json.loads(value)
        except (ValueError,TypeError):fail('Content must be a structured object.','content_invalid')
    if not isinstance(value,dict):fail('Content must be a structured object.','content_invalid')
    if key=='contact':
        allowed=set(CONTACT)
        if set(value)!=allowed or not isinstance(value.get('mock'),bool):fail('Complete the contact fields and fictional-contact setting.','content_invalid')
        clean={k:text(v,2000 if k=='address' else 240,False) for k,v in value.items() if k!='mock'}
        clean['mock']=value['mock']
        for field in ('email','privacy_email'):
            if clean[field] and (not re.fullmatch(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,63}',clean[field]) or '\r' in clean[field] or '\n' in clean[field]):fail('Enter a valid contact email address.','contact_email')
        if not clean['mock'] and any(clean[f].lower().endswith(('.example','.invalid','.test')) for f in ('email','privacy_email')):fail('Fictional addresses must stay marked as fictional.','contact_mock')
        if not clean['organization']:fail('Enter an organization label.','content_invalid')
        return clean
    if set(value)-{'title','body','audience','review_only'}:fail('Unexpected document field.','content_invalid')
    if value.get('audience',DOCUMENTS[key][1])!=DOCUMENTS[key][1]:fail('Document visibility is fixed by its policy purpose.','content_visibility')
    # No HTML execution, arbitrary policy keys, production-approval toggle or attachments.
    return {'title':text(value.get('title'),160),'body':text(value.get('body'),50000),'audience':DOCUMENTS[key][1],'review_only':True}

def _published(key):
    values=rows('''SELECT r.id,r.payload FROM tt_public_content_head h JOIN tt_public_content_revision r ON r.id=h.published_id WHERE h.content_key=%s''',(key,))
    if not values:return None
    return {'version':values[0].id,**json.loads(values[0].payload)}

@frappe.whitelist(allow_guest=True,methods=['GET'])
def public():
    contact=_published('contact') or {'version':'contact-review-fallback',**CONTACT}
    documents=[]
    for key,(_,audience,_) in DOCUMENTS.items():
        if audience=='public':
            item=_published(key)
            if item:documents.append({'key':key,**item})
    return {'contact':contact,'documents':documents,'review_only':True}

@query()
def manage():
    actor('Tele Tena Approver')
    items=[]
    for key in ['contact',*DOCUMENTS]:
        head=rows('SELECT * FROM tt_public_content_head WHERE content_key=%s',(key,))[0]
        revision=rows('SELECT * FROM tt_public_content_revision WHERE id=%s',(head.draft_id,))[0]
        history=rows('SELECT id,actor,created FROM tt_public_content_revision WHERE content_key=%s ORDER BY created DESC,id DESC LIMIT 30',(key,))
        items.append({'key':key,'revision':head.revision,'draft_id':head.draft_id,'published_id':head.published_id,'payload':json.loads(revision.payload),'history':history})
    return items

@command
def save_draft(key,payload,expected_revision):
    user=actor('Tele Tena Approver');key=_key(key);payload=_payload(key,payload)
    head=rows('SELECT * FROM tt_public_content_head WHERE content_key=%s FOR UPDATE',(key,))[0]
    if str(expected_revision)!=str(head.revision):fail('This section changed in another session. Reload before saving.','content_conflict')
    version=key+'-'+uuid.uuid4().hex
    frappe.db.sql('INSERT INTO tt_public_content_revision VALUES (%s,%s,%s,%s,UTC_TIMESTAMP(6))',(version,key,json.dumps(payload,ensure_ascii=False),user))
    frappe.db.sql('UPDATE tt_public_content_head SET draft_id=%s,revision=revision+1,updated=UTC_TIMESTAMP(6) WHERE content_key=%s',(version,key))
    frappe.db.sql('INSERT INTO tt_public_content_event VALUES (%s,%s,%s,%s,%s,UTC_TIMESTAMP(6))',(str(uuid.uuid4()),key,version,'Saved',user))
    return {'version':version,'revision':head.revision+1}

@command
def publish_review(key,version,expected_revision):
    user=actor('Tele Tena Approver');key=_key(key)
    head=rows('SELECT * FROM tt_public_content_head WHERE content_key=%s FOR UPDATE',(key,))[0]
    if str(expected_revision)!=str(head.revision) or head.draft_id!=version:fail('Save and review the current draft before publishing.','content_conflict')
    # Publishing is a review-mode visibility action, never a legal-approval claim.
    frappe.db.sql('UPDATE tt_public_content_head SET published_id=%s,revision=revision+1,updated=UTC_TIMESTAMP(6) WHERE content_key=%s',(version,key))
    frappe.db.sql('INSERT INTO tt_public_content_event VALUES (%s,%s,%s,%s,%s,UTC_TIMESTAMP(6))',(str(uuid.uuid4()),key,version,'PublishedReview',user))
    return {'version':version,'revision':head.revision+1,'review_only':True}
