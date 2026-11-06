"""Network-free amendment isolation; no provider credentials needed."""
from operations_proof_budget import Budget
from scripts.operations_proof.native_v2 import NativeRun
from tele_tena.operations.proof import ProofBlocked
import json,hashlib
from pathlib import Path

class NativeBudget(Budget):
 def setUp(self):
  super().setUp()
  original=json.loads(self.run.manifest.read_text());original['authorization']['status']='Completed';original['amendments']={'native_gateway':{'approved':True}};self.run._write(self.run.manifest,original)
  m=json.loads(json.dumps(original));m['authorization']={'status':'Approved'};m['caps']={'replays':1,'snapshot_upload_requests':6,'recording_bytes':5242880,'posthog_admin_gets':16,'recording_deletes':1,'deletion_confirmation_gets':1};m['usage']={};m['actions']={};m['recordings']=[];m['native_plan_sha256']=hashlib.sha256(Path('docs/operations/live-verification-amendment-v2-proposal.md').read_bytes()).hexdigest()
  self.native=NativeRun(self.root);self.native._write(self.native.manifest,m)
 # Do not inherit original-run tests; this class exercises only amendment boundaries.
 def runTest(self):pass
 def test_native_counter_does_not_reopen_original(self):
  self.native.reserve('native-recording-test',{'replays':1})
  original=self.native._read(self.root/'live-verification-plan-v1.json');self.assertEqual(original['authorization']['status'],'Completed');self.assertEqual(original['usage']['replays'],1)
  with self.assertRaises(ProofBlocked):self.native.reserve('native-recording-extra',{'replays':1})
 def test_native_cannot_send_errors_or_other_provider(self):
  with self.assertRaises(ProofBlocked):self.native.reserve('error',{'errors':1})
  with self.assertRaises(ProofBlocked):self.native.request('error','bugsink_ingest','/store/')
 def test_native_ingestion_requires_snapshot_and_exact_cost(self):
  with self.assertRaises(ProofBlocked):self.native.request('bad','posthog_ingest','/s/',method='POST',payload={'event':'unapproved'},costs={})
 def test_native_cannot_read_unrelated_recordings(self):
  with self.assertRaises(ProofBlocked):self.native.request('read','posthog_api','/api/projects/335848/session_recordings/unrelated/')

# Explicit load avoids rerunning inherited V1 tests against closed fixtures.
def load_tests(loader,tests,pattern):
 import unittest
 return unittest.TestSuite(NativeBudget(name) for name in ('test_native_counter_does_not_reopen_original','test_native_cannot_send_errors_or_other_provider','test_native_cannot_read_unrelated_recordings','test_native_ingestion_requires_snapshot_and_exact_cost'))
if __name__=='__main__':
 import unittest
 unittest.main()
