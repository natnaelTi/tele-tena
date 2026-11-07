import hashlib,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from tele_tena.operations.proof import ProofRun,ProofBlocked
class Budget(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.root.chmod(0o700);self.run=ProofRun(self.root)
  c={'bugsink_dsn':'https://synthetic@project.bugsink.com/1','posthog_host':'https://eu.i.posthog.com','posthog_api_host':'https://eu.posthog.com','posthog_project_id':'335848','owner_alert_email':'owner@example.invalid','owner_account':'','live_test_authorized':False}
  digest=hashlib.sha256(Path('docs/operations/live-verification-plan-v1.md').read_bytes()).hexdigest();m={'approved':True,'authorization':{'run_id':'synthetic'},'public_plan_sha256':digest,'caps':{'errors':5},'usage':{'errors':0},'actions':{},'destinations':{'bugsink_host':'project.bugsink.com','bugsink_project_id':'1','posthog_ingest':c['posthog_host'],'posthog_api':c['posthog_api_host'],'posthog_project_id':'335848','email_recipient':c['owner_alert_email']}}
  self.run._write(self.run.config,c);self.run._write(self.run.manifest,m)
 def tearDown(self):self.tmp.cleanup()
 def test_durable_caps_retry_and_unknown_claim(self):
  self.run.reserve('first',{'errors':1});self.run.outcome('first','Unknown')
  with self.assertRaises(ProofBlocked):self.run.reserve('first',{'errors':1})
  self.run.reserve('second',{'errors':4})
  with self.assertRaises(ProofBlocked):self.run.reserve('third',{'errors':1})
  self.assertEqual(ProofRun(self.root).checked()[0]['usage']['errors'],5)
 def test_flag_restoration_and_no_destination_change(self):
  with self.assertRaises(ValueError):
   with self.run.live():
    self.assertTrue(json.loads(self.run.config.read_text())['live_test_authorized']);raise ValueError()
  self.assertFalse(json.loads(self.run.config.read_text())['live_test_authorized']);c=json.loads(self.run.config.read_text());c['owner_alert_email']='other@example.invalid';self.run._write(self.run.config,c)
  with self.assertRaises(ProofBlocked):self.run.reserve('no',{'errors':1})
 def test_changed_telegram_destination_is_rejected(self):
  m=json.loads(self.run.manifest.read_text());m['destinations']['telegram_chat']='synthetic-destination';self.run._write(self.run.manifest,m)
  c=json.loads(self.run.config.read_text());c['telegram_chat']='different-destination';self.run._write(self.run.config,c)
  with self.assertRaisesRegex(ProofBlocked,'destination_changed'):self.run.checked()
 def test_closed_immediate_phase_rejects_more_ingestion(self):
  m=json.loads(self.run.manifest.read_text());m['phase']='AwaitingSettledRecheck';self.run._write(self.run.manifest,m)
  with self.assertRaisesRegex(ProofBlocked,'immediate_phase_closed'):self.run.reserve('extra-error',{'errors':1})
  with self.assertRaisesRegex(ProofBlocked,'settled_checkpoint_only'):self.run.request('extra','bugsink_api','/api/canonical/0/events/lookup/')
 def test_completed_authorization_cannot_resume(self):
  m=json.loads(self.run.manifest.read_text());m['authorization']['status']='Completed';self.run._write(self.run.manifest,m)
  with self.assertRaisesRegex(ProofBlocked,'one_run_authorization_expired'):self.run.checked()
 def test_amendment_is_separate_and_bounded(self):
  m=json.loads(self.run.manifest.read_text());m['amendments']={'source_map_line_readback':{'approved':True,'limit':1}};self.run._write(self.run.manifest,m)
  self.run.reserve('line-check',{'source_map_line_readback':1})
  with self.assertRaisesRegex(ProofBlocked,'approved_limit_reached'):self.run.reserve('extra-line-check',{'source_map_line_readback':1})
 def test_extra_deletion_read_requires_separate_amendment(self):
  m=json.loads(self.run.manifest.read_text());m['phase']='AwaitingSettledRecheck';self.run._write(self.run.manifest,m)
  with self.assertRaisesRegex(ProofBlocked,'approved_limit_reached'):self.run.reserve('provider-delete-confirm-owner-amendment-test',{'deletion_readback_amendment':1})
  m=json.loads(self.run.manifest.read_text());m['amendments']={'deletion_readback':{'approved':True,'limit':1}};self.run._write(self.run.manifest,m)
  self.run.reserve('provider-delete-confirm-owner-amendment-test',{'deletion_readback_amendment':1})
  with self.assertRaisesRegex(ProofBlocked,'approved_limit_reached'):self.run.reserve('provider-delete-confirm-extra-test',{'deletion_readback_amendment':1})
 def test_unapproved_and_arbitrary_hosts_cannot_send(self):
  with self.assertRaises(ProofBlocked):self.run.request('no','unknown','/anything')
  m=json.loads(self.run.manifest.read_text());m['approved']=False;self.run._write(self.run.manifest,m)
  with self.assertRaises(ProofBlocked):self.run.reserve('no',{})
if __name__=='__main__':unittest.main()
