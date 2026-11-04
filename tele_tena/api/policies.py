"""Review-mode version display. Not approved production legal policy content."""
import uuid
import frappe
from tele_tena.api.journey import fail
TERMS='terms-draft-2026-10-20-v1';PRIVACY='privacy-draft-2026-10-20-v1'

@frappe.whitelist(allow_guest=True,methods=['GET'])
def current(locale='en'):
    from tele_tena.api.public_content import public
    if locale not in ('en','am','om'):fail('Choose an available language')
    from tele_tena.localization import translate
    from tele_tena.public_content_defaults import DOCUMENTS
    content=public()
    localized=[]
    for document in content['documents']:
        item=dict(document);default=DOCUMENTS.get(item['key'])
        # Translate only exact application-owned defaults, never edited records.
        if default and item.get('title')==default[0]:item['title']=translate(default[0],locale)
        if default and item.get('body')==default[2]:item['body']=translate(default[2],locale)
        localized.append(item)
    content={**content,'documents':localized}
    versions={item['key']:item['version'] for item in content['documents']}
    return {'review_only':True,'terms_version':versions.get('terms',TERMS),'privacy_version':versions.get('privacy',PRIVACY),'documents':content['documents'],
      'notice':'Policy content is under review. This demonstration is not real clinical care or real payments. Approved production Terms and Privacy content is not yet available.',
      'sharing_notice':'Only the identity, text and individual files you affirmatively approve for this encounter are shared with its treating clinician. Previously viewed material cannot be recalled.'}

def record(user,answers):
    if answers.get('terms_accepted') is not True or answers.get('privacy_acknowledged') is not True:
        fail('Review the separate Terms and Privacy acknowledgements.','policy_ack_required')
    frappe.db.sql("SELECT content_key FROM tt_public_content_head WHERE content_key IN ('terms','privacy') ORDER BY content_key FOR UPDATE")
    versions=current()
    terms=versions['terms_version'];privacy=versions['privacy_version']
    if answers.get('terms_version')!=terms or answers.get('privacy_version')!=privacy:fail('Policy versions changed;review them again.','policy_changed')
    frappe.db.sql('''INSERT IGNORE INTO tt_policy_acceptance VALUES (%s,%s,%s,%s,1,1,%s,%s,1,UTC_TIMESTAMP(6))''',
      (str(uuid.uuid4()),user,terms,privacy,int(answers.get('consent') is True),int(answers.get('marketing') is True)))
