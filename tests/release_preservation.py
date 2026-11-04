"""Only the explicitly authorized v148 role grant can differ; no data repairs."""
import copy,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('preservation',Path(__file__).resolve().parents[1]/'scripts/release_preservation.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Protection(unittest.TestCase):
 def pair(self):
  old={'site':'fixture.localhost','files':{'private/receipt':'receipt-hash'},'tables':{n:{'columns':['fixture'],'rows':[n]} for n in ('tabUser','tabHas Role','tt_audit','tt_wallet','__Auth')},'reviewer_default_v148':{'users':{'owner':{'full':'user-before','stable':'all-private-fields'}},'roles':{'existing':{'full':'role-before','stable':'same-role','parent':'owner','role':'Tele Tena Approver'}},'reviewer_default_audits':{}}}
  new=copy.deepcopy(old);new['tables']['tabUser']['rows']=['changed-metadata'];new['tables']['tabHas Role']['rows']+=['new-role'];new['tables']['tt_audit']['rows']+=['new-audit'];meta=new['reviewer_default_v148'];meta['users']['owner']['full']='user-after';meta['roles']['existing']['full']='role-after';meta['roles']['grant']={'full':'grant','stable':'grant','parent':'owner','role':'Tele Tena Financial Configuration'};meta['reviewer_default_audits']['new-audit']='owner';return old,new
 def test_strict_rejects_but_expected_grant_is_verified(self):
  a,b=self.pair()
  with self.assertRaises(AssertionError):m.verify_snapshot(a,b)
  self.assertEqual(m.verify_snapshot(a,b,True),1)
 def test_credentials_wallet_and_file_mutations_denied(self):
  for target in ['credentials','wallet','file']:
   a,b=self.pair()
   if target=='credentials':b['reviewer_default_v148']['users']['owner']['stable']='changed-password-or-setting'
   elif target=='wallet':b['tables']['tt_wallet']['rows']=['changed-money']
   else:b['files']['private/receipt']='changed-evidence'
   with self.assertRaises(AssertionError):m.verify_snapshot(a,b,True)
 def test_unrelated_or_duplicate_grants_and_audits_denied(self):
  for target in ['role','audit','not-reviewer','deleted-role']:
   a,b=self.pair()
   if target=='role':b['reviewer_default_v148']['roles']['grant']['role']='System Manager'
   elif target=='audit':b['tables']['tt_audit']['rows']+=['unrelated-event']
   elif target=='not-reviewer':a['reviewer_default_v148']['roles']['existing']['role']='Tele Tena Patient'
   else:del b['reviewer_default_v148']['roles']['existing']
   with self.assertRaises(AssertionError):m.verify_snapshot(a,b,True)
 def test_unchanged_older_snapshot_remains_strictly_compatible(self):
  a,_=self.pair();b=copy.deepcopy(a);del a['reviewer_default_v148'];self.assertEqual(m.verify_snapshot(a,b),0)
if __name__=='__main__':unittest.main()
