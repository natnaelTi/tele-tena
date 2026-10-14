"""Guard invariants; optional real sanitized audit supplied privately in TEST_SHARED_AUDIT."""
import copy,importlib.util,json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import shared_repair_guard as guard
APP=Path('/home/smcs/frappe-bench/apps/ecommerce_integrations')
AUDIT={'bench_apps':['frappe','ecommerce_integrations'],'missing_bench_app_metadata':[],'unresolved_source_inputs':[],'app_declared_dependency_edges':[],'focused_requirement_edges':[],'installed_packages':{}}
for name,version in {'requests':'2.33.1','cryptography':'48.0.0','oauthlib':'3.3.1','websockets':'16.0','boto3':'1.28.85','botocore':'1.31.85','s3transfer':'0.7.0','urllib3':'2.6.3','click':'8.3.1','jmespath':'1.0.1','python-dateutil':'2.9.0.post0','frappe-bench':'5.29.0','ecommerce-integrations':'1.17.0'}.items():AUDIT['installed_packages'][name]={'version':version,'identity':{'editable':True,'path':str(APP)} if name=='ecommerce-integrations' else None}
for dep,spec in [('requests','~=2.32.5'),('cryptography','~=46.0.3'),('oauthlib','~=3.2.2'),('websockets','~=15.0.1')]:AUDIT['focused_requirement_edges'].append({'requires_from':'frappe','dependency':dep,'constraint':spec,'source':'distribution','direct_url_requirement':False})
if os.environ.get('TEST_SHARED_AUDIT'):AUDIT=json.loads(Path(os.environ['TEST_SHARED_AUDIT']).read_text())

def plan():
 requirements={'boto3':['botocore>=1.43.113,<1.44.0','s3transfer>=0.19.0,<0.20.0','jmespath>=0.7.1,<2'],'botocore':['urllib3>=1.25.4,!=2.2.0,<3','jmespath>=0.7.1,<2','python-dateutil>=2.1,<3'],'s3transfer':['botocore>=1.37.4,<2.0a.0'],'ecommerce-integrations':['boto3~=1.43.113']}
 items=[]
 for name,version in dict(guard.PINS,**{'ecommerce-integrations':'1.17.0'}).items():items.append({'metadata':{'name':name,'version':version,'requires_dist':requirements.get(name,[])},'is_direct':name=='ecommerce-integrations','download_info':{'url':APP.as_uri(),'dir_info':{'editable':True}} if name=='ecommerce-integrations' else {'url':'https://files.pythonhosted.org/fictional.whl'}})
 return {'install':items}
class Tests(unittest.TestCase):
 def setUp(self):self.before=copy.deepcopy(AUDIT['installed_packages']);self.report=plan()
 def test_exact_plan_and_post_preservation(self):
  approved=guard.check_plan(self.before,self.report,APP,AUDIT);after=copy.deepcopy(self.before);after.pop('frappe-bench');after.update(approved);guard.check_preserved(self.before,after,approved)
 def test_unrelated_replacement_rejected(self):
  self.report['install'].append({'metadata':{'name':'urllib3','version':'2.0.7'},'is_direct':False})
  with self.assertRaisesRegex(ValueError,'Unrelated'):guard.check_plan(self.before,self.report,APP,AUDIT)
 def test_sdk_mismatch_rejected(self):
  next(x for x in self.report['install'] if x['metadata']['name']=='botocore')['metadata']['version']='1.43.112'
  with self.assertRaises(ValueError):guard.check_plan(self.before,self.report,APP,AUDIT)
 def test_editable_swap_rejected(self):
  self.report['install'][-1]['download_info']['url']='file:///tmp/other-amazon'
  with self.assertRaisesRegex(ValueError,'identity'):guard.check_plan(self.before,self.report,APP,AUDIT)
 def test_protected_version_and_source_rejected(self):
  approved=guard.check_plan(self.before,self.report,APP,AUDIT);after=copy.deepcopy(self.before);after.pop('frappe-bench');after.update(approved);after['click']['version']='8.2.1'
  with self.assertRaises(ValueError):guard.check_preserved(self.before,after,approved)
  after['click']=copy.deepcopy(self.before['click']);name='pypika' if 'pypika' in after else 'click';after[name]['identity']={'editable':True,'path':'/tmp/source-swap'}
  with self.assertRaises(ValueError):guard.check_preserved(self.before,after,approved)
 def test_duplicate_cli_or_extra_package_rejected(self):
  approved=guard.check_plan(self.before,self.report,APP,AUDIT);after=copy.deepcopy(self.before);after.update(approved)
  with self.assertRaisesRegex(ValueError,'Duplicate'):guard.check_preserved(self.before,after,approved)
  after.pop('frappe-bench');after['unplanned']={'version':'1','identity':None}
  with self.assertRaisesRegex(ValueError,'Unplanned'):guard.check_preserved(self.before,after,approved)
 def test_new_conflicting_app_requirement_rejected(self):
  audit=copy.deepcopy(AUDIT);audit['app_declared_dependency_edges'].append({'requires_from':'another-app','dependency':'cryptography','constraint':'>=48','source':'pyproject.toml','direct_url_requirement':False})
  with self.assertRaisesRegex(ValueError,'another-app'):guard.check_plan(self.before,self.report,APP,audit)
 def test_missing_or_unparsed_apps_rejected(self):
  audit=copy.deepcopy(AUDIT);audit['missing_bench_app_metadata'].append('unknown-app')
  with self.assertRaises(ValueError):guard.check_plan(self.before,self.report,APP,audit)
 def test_http_signature_cryptography(self):
  import requests
  from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
  from http_message_signatures import HTTPMessageSigner,HTTPMessageVerifier,HTTPSignatureKeyResolver,algorithms
  key=Ed25519PrivateKey.generate()
  class Keys(HTTPSignatureKeyResolver):
   def resolve_private_key(self,key_id):return key
   def resolve_public_key(self,key_id):return key.public_key()
  request=requests.Request('POST','https://example.invalid/fictional-signature',data=b'fictional').prepare()
  HTTPMessageSigner(signature_algorithm=algorithms.ED25519,key_resolver=Keys()).sign(request,key_id='fictional')
  self.assertEqual(len(HTTPMessageVerifier(signature_algorithm=algorithms.ED25519,key_resolver=Keys()).verify(request)),1)
if __name__=='__main__':unittest.main(verbosity=2)
