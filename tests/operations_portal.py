"""Rollback-only Frappe16 portal queries, authorization and evidence boundaries."""
from operations import *
from tele_tena.operations import portal
class Portal(unittest.TestCase):
 setUp=Operations.setUp
 tearDown=Operations.tearDown
 def test_every_query_and_assignment_requires_reviewer(self):
  for u in ['Guest',users['patient'],users['counselor']]:
   frappe.set_user(u)
   for fn in [ops.integration_status,ops.journey_insights,ops.support_queue,ops.archive_records,lambda:ops.support_assign('missing','Triaged','Normal')]:
    with self.assertRaises(frappe.PermissionError):fn()
 def test_binding_enablement_and_proof_are_independent_and_secret_free(self):
  frappe.set_user(users['reviewer'])
  with patch('tele_tena.operations.providers.settings',return_value={}),patch('tele_tena.operations.providers.archive_capability',return_value=False):
   value=ops.integration_status();self.assertTrue(all(not x['effective'] for x in value['items']));self.assertIn('Verified in Isolated Tests',json.dumps(value,default=str));self.assertTrue(all(x['current_build_verified'] is False for x in value['items']))
  c=rt.config()
  with patch('tele_tena.operations.providers.settings',return_value={'posthog_host':'https://eu.i.posthog.com','posthog_token':'CANARY-SECRET'}),patch('tele_tena.operations.providers.archive_capability',return_value=False):
   value=ops.integration_status();self.assertTrue(value['items'][0]['site_configured']);self.assertNotIn('CANARY-SECRET',json.dumps(value,default=str));self.assertEqual(value['items'][0]['enabled'],c['analytics'])
 def test_mobile_disabled_channel_is_not_effective_even_with_credentials(self):
  frappe.set_user(users['reviewer']);base=rt.config();private={'telegram_token':'synthetic-secret','telegram_chat':'synthetic-chat','owner_alert_email':'owner@ops-review.invalid'}
  with patch('tele_tena.operations.providers.settings',return_value=private),patch('tele_tena.operations.providers.archive_capability',return_value=False),patch('tele_tena.operations.runtime.config',return_value={**base,'alerts':True,'mobile_channel':'Disabled'}):
   mobile=next(x for x in ops.integration_status()['items'] if x['key']=='mobile');self.assertTrue(mobile['site_configured']);self.assertTrue(mobile['enabled']);self.assertFalse(mobile['effective'])
 def test_overview_counts_include_submitted_scopes_replies_and_assistance(self):
  frappe.set_user(users['reviewer']);d=ops.overview()
  self.assertEqual(d['scope_pending'],frappe.db.sql("SELECT COUNT(*) FROM `tabTele Tena Vetting Scope Application` WHERE status='Submitted'")[0][0])
  self.assertEqual(d['scope_replies'],frappe.db.sql("SELECT COUNT(*) FROM `tabTele Tena Vetting Scope Application` WHERE status='Resubmitted'")[0][0])
  self.assertEqual(d['assistance_requests'],frappe.db.sql("SELECT COUNT(*) FROM tt_assistance_case WHERE state='Open'")[0][0])
 def test_empty_filtered_journey_has_no_completion_percent(self):
  frappe.set_user(users['reviewer']);d=ops.journey_insights(locale='om',device='tablet',family='consultation',days=1)
  if d['observed_attempts']==0:self.assertIsNone(d['completion_percent']);self.assertEqual(d['sample_state'],'No Eligible Data')
  for params in [{'days':999},{'family':'private'},{'locale':'secret'},{'source':'SQL'},{'payment_mode':'all OR 1=1'}]:
   with self.assertRaises(frappe.ValidationError):ops.journey_insights(**params)
 def test_attempt_denominator_completion_window_and_synthetic_filter(self):
  from datetime import timedelta
  now=rt.now()
  ids=[uuid.uuid4().hex+uuid.uuid4().hex for _ in range(3)]
  dims=json.dumps({'synthetic':'yes','source':'server','locale':'om','device':'tablet','payment_mode':'Offline'})
  for i,id in enumerate(ids):
   t=now-timedelta(hours=30+i)
   frappe.db.sql('INSERT INTO tt_ops_attempt VALUES (%s,%s,%s,%s,%s,%s,%s)',(id,'request',t,t+timedelta(hours=1),['Completed','Saved','Resumed'][i],t+timedelta(hours=1) if i==0 else None,dims))
  frappe.set_user(users['reviewer']);d=ops.journey_insights('request',7,'om','tablet','Offline','server',1)
  self.assertEqual(d['observed_attempts'],3);self.assertEqual(d['completed_in_window'],1);self.assertEqual(d['interrupted'],2);self.assertEqual(d['completion_percent'],33.3)
  self.assertEqual(ops.journey_insights('request',7,'om','tablet','Offline','server',0)['observed_attempts'],0)
 def test_support_assignment_without_visible_reply_and_owner_boundary(self):
  frappe.set_user(users['patient']);r=ops.support_submit('Technical','Synthetic portal queue report',False,'portal-'+str(uuid.uuid4()),{'route':'/patient'})
  frappe.set_user(users['reviewer']);ops.support_assign(r['id'],'In Progress','High',users['reviewer']);q=ops.support_queue(ownership='mine');self.assertIn(r['id'],[x.id for x in q['items']]);self.assertNotIn('description',q['items'][0]);self.assertEqual(ops.support_detail(r['id'])['replies'],[]);ops.support_reply(r['id'],'Private follow-up note','Internal','portal-preserve',preserve_triage=True);self.assertEqual(ops.support_detail(r['id'])['priority'],'High');self.assertEqual(ops.support_detail(r['id'])['assignee'],users['reviewer'])
  with self.assertRaises(frappe.ValidationError):ops.support_assign(r['id'],'Resolved','High',users['reviewer'],expected={'state':'New','priority':'Normal','assignee':None})
  with self.assertRaises(frappe.ValidationError):ops.support_assign(r['id'],'Resolved','High',users['patient'])
  frappe.set_user(users['counselor'])
  with self.assertRaises(frappe.PermissionError):ops.support_detail(r['id'])
  frappe.set_user(users['patient']);self.assertNotIn('assignee',ops.support_detail(r['id']))
 def test_archive_records_filters_and_pagination_are_bounded(self):
  frappe.set_user(users['reviewer']);d=ops.archive_records();self.assertLessEqual(len(d['items']),30)
  for kw in [{'state':'Secret'},{'reference':'../private'},{'offset':-1}]:
   with self.assertRaises(frappe.ValidationError):ops.archive_records(**kw)
 def test_synthetic_report_requires_isolated_site_and_preserves_normal_compiler(self):
  frappe.set_user(users['reviewer']);period=str(rt.now().year)+'-Q'+str((rt.now().month-1)//3+1)
  with patch.dict(frappe.conf,{'tele_tena_ops_review_scenario':False}):
   with self.assertRaises(ValueError):ops.report_compile(period,1)
  normal=ops.report_compile(period);self.assertNotIn('data_scope',ops.report_detail(normal['id'])['data'])
  with patch.dict(frappe.conf,{'tele_tena_ops_review_scenario':True}):
   synthetic=ops.report_compile(period,1);self.assertEqual(ops.report_detail(synthetic['id'])['data']['data_scope'],'Isolated Synthetic Review Report');self.assertEqual(ops.report_compile(period,1)['id'],synthetic['id'])
if __name__=='__main__':unittest.main(defaultTest='Portal')
