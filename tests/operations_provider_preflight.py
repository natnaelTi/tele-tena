"""Network-free private configuration and bounded discovery tests; synthetic secrets only."""
import importlib.util,json,os,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('preflight',Path(__file__).resolve().parents[1]/'scripts/operations_provider_preflight.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class Preflight(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.root.chmod(0o700);self.path=self.root/'providers.json'
  self.data={'schema':'teletena-operations-config-v1','owner_alert_email':'owner@example.invalid','owner_account':'','live_test_authorized':False,'posthog_host':'https://eu.i.posthog.com','posthog_api_host':'https://eu.posthog.com','posthog_project_id':'335848','posthog_token':'synthetic','posthog_read_key':'synthetic','bugsink_dsn':'https://synthetic@project.bugsink.com/1','telegram_token':'123:'+('x'*30),'telegram_chat':''};self.write()
 def tearDown(self):self.tmp.cleanup()
 def write(self):self.path.write_text(json.dumps(self.data));self.path.chmod(0o600)
 def test_private_valid_configuration_and_optional_scope_independence(self):
  data,_=module.load(self.path);result=module.validate(data);self.assertEqual(result['invalid_or_missing_fields'],[]);self.assertIn('bugsink_source_map_token',result['optional_missing_fields']);self.assertEqual(result['telegram_setup_missing_fields'],['telegram_chat'])
 def test_insecure_permissions_and_symlink_denied(self):
  self.path.chmod(0o644)
  with self.assertRaisesRegex(ValueError,'file_permissions_or_owner'):module.load(self.path)
  self.path.chmod(0o600);link=self.root/'alias.json';link.symlink_to(self.path)
  with self.assertRaises(ValueError):module.load(link)
 def test_region_project_ownership_and_live_flag_validation(self):
  self.data.update(posthog_api_host='https://us.posthog.com',owner_account='demo-reviewer',live_test_authorized=True,bugsink_project_id='2');self.assertEqual(set(module.validate(self.data)['invalid_or_missing_fields']),{'posthog_api_host','owner_account','live_test_authorized','bugsink_project_id'})
 def test_no_match_and_multiple_matches_never_modify(self):
  original=self.path.read_bytes()
  self.assertEqual(module.discover(self.path,self.data,original,lambda _: {'ok':True,'result':[]}),'No Matching Private Chat')
  items=[{'message':{'text':'TeleTena owner alert setup','chat':{'id':id,'type':'private'}}} for id in (1,2)]
  self.assertIn('Multiple',module.discover(self.path,self.data,original,lambda _: {'ok':True,'result':items}));self.assertEqual(self.path.read_bytes(),original)
 def test_exact_private_match_preserves_all_other_values(self):
  items=[{'message':{'text':'TeleTena owner alert setup','chat':{'id':9,'type':'group'}}},{'message':{'text':'Other private content','chat':{'id':8,'type':'private'}}},{'message':{'text':'TeleTena owner alert setup','chat':{'id':7,'type':'private'}}}]
  outcome=module.discover(self.path,self.data,self.path.read_bytes(),lambda _: {'ok':True,'result':items});self.assertIn('Saved',outcome);self.assertEqual(json.loads(self.path.read_text()),{**self.data,'telegram_chat':'7'});self.assertEqual(self.path.stat().st_mode&0o777,0o600)
 def test_existing_chat_skips_network_and_errors_are_neutral(self):
  self.data['telegram_chat']='7';self.assertEqual(module.discover(self.path,self.data,b'',lambda _: self.fail('must not fetch')),'Existing Chat Preserved');self.data['telegram_chat']=''
  def fail(_):raise RuntimeError('must-not-print-a-synthetic-token')
  self.assertEqual(module.discover(self.path,self.data,self.path.read_bytes(),fail),'Transport or Response Unavailable')
 def test_webhook_conflict_and_concurrent_change_preserved(self):
  before=self.path.read_bytes();self.assertIn('Unavailable',module.discover(self.path,self.data,before,lambda _: {'ok':False,'http_status':409}));self.assertEqual(self.path.read_bytes(),before)
  self.path.write_text(before.decode()+' ')
  self.assertIn('Concurrent',module.discover(self.path,self.data,before,lambda _: {'ok':True,'result':[{'message':{'text':'TeleTena owner alert setup','chat':{'id':7,'type':'private'}}}]}))
if __name__=='__main__':unittest.main()
