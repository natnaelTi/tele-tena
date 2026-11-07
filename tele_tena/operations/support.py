"""Private support with existing audit/outbox; no report body in telemetry."""
import base64,hashlib,json,uuid
from urllib.parse import quote
import frappe
from tele_tena.api.journey import actor,rows,one,text,fail,audit
from . import runtime as rt
CATEGORIES={'Technical','Booking','Payment','Application','Accessibility','Other'}
STATES={'New','Triaged','In Progress','Waiting for User','Resolved','Closed'}
def reviewers():
 return frappe.db.sql("SELECT DISTINCT p.parent FROM `tabHas Role` p JOIN tabUser u ON u.name=p.parent WHERE p.role='Tele Tena Approver' AND u.enabled=1 LIMIT 100",pluck=True)
def allowed(id):
 user=actor();r=one('SELECT * FROM tt_ops_support WHERE id=%s',(id,))
 if r.owner!=user:rt.reviewer()
 return r
def notice(report,kind,users):
 from tele_tena.communications import queue
 for user in users:queue(user,kind,'support',report['id'] if isinstance(report,dict) else report.id,'support:'+str(report['id'] if isinstance(report,dict) else report.id)+':'+kind+':'+str(report['modified'] if isinstance(report,dict) else report.modified),external=bool(report['followup']))
def submit(category,description,followup,retry_key,context,attachment=None):
 user=actor()
 if category not in CATEGORIES:fail('Choose a problem category.','support_category_invalid')
 description=text(description,3000);retry_key=text(retry_key,100)
 if type(followup) is not bool:fail('Review your follow-up preference.')
 if not isinstance(context,dict) or set(context)-{'route','step'}:fail('Support context is invalid.')
 safe={'route':rt.route_template(context.get('route','/unknown')),'step':context.get('step','unknown') if context.get('step') in ('profile','schedule','payment','room','review') else 'unknown','release':rt.release()}
 digest=hashlib.sha256(json.dumps([category,description,followup,safe,attachment],sort_keys=True).encode()).hexdigest()
 prior=rows('SELECT id,digest FROM tt_ops_support WHERE owner=%s AND retry_key=%s',(user,retry_key))
 if prior:
  if prior[0].digest!=digest:fail('This submission key was already used for different details.','retry_changed')
  return detail(prior[0].id)
 frappe.db.sql('SELECT name FROM tabUser WHERE name=%s FOR UPDATE',(user,))
 prior=rows('SELECT id,digest FROM tt_ops_support WHERE owner=%s AND retry_key=%s',(user,retry_key))
 if prior:
  if prior[0].digest!=digest:fail('This submission key was already used.','retry_changed')
  return detail(prior[0].id)
 if one('SELECT COUNT(*) n FROM tt_ops_support WHERE owner=%s AND created>DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 1 DAY)',(user,)).n>=10:fail('Daily problem-report limit reached. Try again later.','support_limit')
 id=str(uuid.uuid4());t=rt.now()
 frappe.db.sql("INSERT INTO tt_ops_support (id,owner,category,description,followup,state,priority,assignee,context,retry_key,digest,created,modified) VALUES (%s,%s,%s,%s,%s,'New','Normal',NULL,%s,%s,%s,%s,%s)",(id,user,category,description,int(followup),json.dumps(safe),retry_key,digest,t,t))
 if attachment:
  if not isinstance(attachment,dict) or set(attachment)!={'filename','content_base64'}:fail('Choose one screenshot.','support_file_invalid')
  from tele_tena.api.history_documents import validated
  name,mime,content=validated(attachment['filename'],attachment['content_base64'])
  if mime not in ('image/jpeg','image/png'):fail('Choose a JPEG or PNG screenshot up to 5 MB.','support_file_invalid')
  from . import storage
  key=storage.put(content,5*1024*1024,min(rt.config()['archive_bytes'],100*1024*1024),kind='support')
  frappe.db.sql('INSERT INTO tt_ops_file VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',(str(uuid.uuid4()),id,name,mime,hashlib.sha256(content).hexdigest(),len(content),key,t))
 audit(id,'SupportSubmitted',{'category':category});rt.safe_record('support.submitted',id,{'category':category});notice({'id':id,'modified':t,'followup':followup},'SupportReceived',[user]);rt.safe_record('support.acknowledged',id)
 return detail(id)
def detail(id):
 r=allowed(id);user=actor();is_reviewer=user=='Administrator' or 'Tele Tena Approver' in frappe.get_roles(user)
 audit(id,'SupportAccessed',{'reviewer':is_reviewer})
 result={k:r[k] for k in ('id','category','description','followup','state','priority','created','modified','context')};result['context']=json.loads(result['context'])
 if is_reviewer:result['assignee']=r.assignee
 result['replies']=rows('SELECT id,audience,body,created FROM tt_ops_reply WHERE report=%s '+('' if is_reviewer else "AND audience='User' ")+'ORDER BY created,id',(id,))
 result['attachments']=rows('SELECT id,filename,mime,size_bytes FROM tt_ops_file WHERE report=%s',(id,))
 return result
def listing():
 user=actor();is_reviewer=user=='Administrator' or 'Tele Tena Approver' in frappe.get_roles(user)
 return rows('SELECT id,category,state,priority,created,modified FROM tt_ops_support '+('' if is_reviewer else 'WHERE owner=%s ')+'ORDER BY modified DESC LIMIT 100',() if is_reviewer else (user,))
def reply(id,body,audience,retry_key,state=None,priority='Normal',assignee=None):
 r=allowed(id);user=actor();privileged=user=='Administrator' or 'Tele Tena Approver' in frappe.get_roles(user)
 body=text(body,3000);retry_key=text(retry_key,100)
 if audience not in ('Internal','User') or not privileged and (audience!='User' or state is not None or assignee is not None):raise frappe.PermissionError('Support action unavailable')
 if privileged:
  if state not in STATES or priority not in ('Low','Normal','High','Critical'):fail('Choose a supported status and priority.')
  if assignee and assignee!='Administrator' and assignee not in reviewers():fail('Choose an authorized reviewer.')
 digest=hashlib.sha256(json.dumps([body,audience,state,priority,assignee]).encode()).hexdigest();prior=rows('SELECT id,digest FROM tt_ops_reply WHERE report=%s AND author=%s AND retry_key=%s',(id,user,retry_key))
 if prior:
  if prior[0].digest!=digest:fail('This reply key was already used.','retry_changed')
  return detail(id)
 one('SELECT id FROM tt_ops_support WHERE id=%s FOR UPDATE',(id,))
 prior=rows('SELECT id,digest FROM tt_ops_reply WHERE report=%s AND author=%s AND retry_key=%s',(id,user,retry_key))
 if prior:
  if prior[0].digest!=digest:fail('This reply key was already used.','retry_changed')
  return detail(id)
 t=rt.now()
 frappe.db.sql('INSERT INTO tt_ops_reply VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',(str(uuid.uuid4()),id,user,audience,body,retry_key,digest,t))
 if privileged:frappe.db.sql('UPDATE tt_ops_support SET state=%s,priority=%s,assignee=%s,modified=%s WHERE id=%s',(state,priority,assignee,t,id))
 else:frappe.db.sql('UPDATE tt_ops_support SET modified=%s WHERE id=%s',(t,id))
 audit(id,'SupportUpdated',{'state':state,'audience':audience})
 if state in ('Triaged','Resolved'):rt.safe_record('support.triaged' if state=='Triaged' else 'support.resolved',id+':'+state,{'category':r.category})
 if state=='Resolved':frappe.db.sql('UPDATE tt_ops_support SET resolved_at=COALESCE(resolved_at,%s) WHERE id=%s',(t,id))
 if audience=='User':notice({'id':id,'modified':t,'followup':r.followup},'SupportUpdated',[r.owner] if privileged else reviewers())
 return detail(id)
def download(id):
 f=one('SELECT * FROM tt_ops_file WHERE id=%s',(id,));allowed(f.report);audit(f.report,'SupportFileAccessed',{'file':id})
 from .storage import read
 from werkzeug.wrappers import Response
 return Response(read(f.path,'support'),mimetype=f.mime,headers={'Cache-Control':'private, no-store','Content-Disposition':"attachment; filename*=UTF-8''"+quote(f.filename,safe=''),'X-Content-Type-Options':'nosniff','Content-Security-Policy':"sandbox; default-src 'none'"})
