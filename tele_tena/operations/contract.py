"""Versioned privacy allowlist shared by ingress, exports and provider adapters."""
import re
VERSION='operations-v1.1'
EVENTS={
 'application.started':'browser','application.resumed':'browser','application.step_completed':'server','application.saved':'server','application.submitted':'server','application.scope_created':'server','application.assistance_requested':'server','application.clarification_opened':'browser','application.reply_started':'browser','application.resubmitted':'server','application.professional_decision':'server','application.scope_decision':'server','application.language_decision':'server',
 'upload.attempted':'browser','upload.succeeded':'server','upload.failed':'browser','validation.failed':'browser',
 'booking.offering_selected':'browser','booking.auth_returned':'browser','booking.scheduling_attempted':'browser','booking.created':'server','booking.confirmed':'server','booking.cancelled':'server','booking.expired':'server',
 'payment.submitted':'server','payment.verified':'server','payment.followup':'server',
 'request.draft_progressed':'browser','request.published':'server','request.offer_received':'server','request.offer_accepted':'server','request.offer_declined':'server','request.appointment_created':'server','request.consultation_handoff':'browser',
 'consultation.join_attempted':'browser','consultation.join_authorized':'server','consultation.quality':'browser','consultation.connected':'browser','consultation.connection_failed':'browser','consultation.left':'browser','consultation.rejoined':'browser','consultation.ended':'server','consultation.documentation_completed':'server',
 'support.submitted':'server','support.acknowledged':'server','support.triaged':'server','support.resolved':'server','operations.error_observed':'server','operations.failure':'server','operations.recovery':'server',
}
PROPERTIES={'quality':{'excellent','good','poor','lost','unknown'},'step':{'0','1','2','3','4','5','6','7','profile','qualifications','license','competencies','affiliations','authorization','review','schedule','payment','preflight','room','notes'},'document':{'CV','License','Identification','Certification','Authorization','History','Receipt','Other'},'outcome':{'saved','resumed','failed','blocked','completed','pending','Approved','Rejected','Clarification','Suspended','Expired','Pending','Submitted','Resubmitted','Booked','AwaitingPayment','Verified','CorrectionRequired','ReconciliationRequired','approve','decline','accept','confirm','reject'},'error_code':{'validation','permission','network','timeout','unavailable','conflict','invalid_file','quota','unexpected'},'category':{'Technical','Booking','Payment','Application','Accessibility','Other'},'synthetic':{'yes','no','unknown'}}
ROUTES=[('/','/'),('/find-care','/find-care'),('/clinicians','/clinicians'),('/sign-in','/sign-in'),('/onboarding','/onboarding'),('/patient','/patient'),('/clinician','/clinician'),('/admin','/admin')]
# Only known application routes. Every suffix/reference is discarded.
PATHS=('discovery','requests','appointments','consultations','care','account','book','direct-payments','payments','earnings','availability','services','vetting','applications','assisted','scopes','languages','operations','support','insights','health','archive','reports','couples','offers')
def route_template(value):
 if not isinstance(value,str):return '/unknown'
 value=value.split('?',1)[0].split('#',1)[0]
 if value.startswith('/teletena'):value=value[9:] or '/'
 bits=value.strip('/').split('/')
 if not value.strip('/'):return '/'
 if bits[0]=='consultation':return '/consultation/:ref/room'
 if bits[0] in ('patient','clinician','admin'):
  if len(bits)==1:return '/'+bits[0]
  if bits[1] not in PATHS:return '/unknown'
  return '/'+bits[0]+'/'+bits[1]+('/:ref' if len(bits)>2 else '')
 if bits[0] in ('care','services','find-care','clinicians','sign-in','onboarding','how-it-works','contact','terms','privacy','policies','request'):
  return '/'+bits[0]+('/:ref' if len(bits)>1 else '')
 return '/unknown'
def properties(value):
 if not isinstance(value,dict) or len(value)>8 or any(k not in PROPERTIES or str(v) not in PROPERTIES[k] for k,v in value.items()):raise ValueError('unsafe_properties')
 return {k:str(v) for k,v in value.items()}
def uuid(value):return isinstance(value,str) and bool(re.fullmatch(r'[a-f0-9-]{36}',value))
