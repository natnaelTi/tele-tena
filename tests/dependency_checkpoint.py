"""Guard the shared-bench install plan against resolver replacements."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('checkpoint', Path(__file__).resolve().parents[1] / 'scripts/dependency_checkpoint.py')
checkpoint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checkpoint)


def report(*names):
    return {'install': [{'metadata': {'name': name}} for name in names]}


class DependencyPlan(unittest.TestCase):
    def test_additions(self):
        self.assertEqual(checkpoint.check_plan({'frappe': '16.2.1'}, report('tele_tena', 'livekit-api')),
                         ['tele-tena', 'livekit-api'])

    def test_reject_framework_or_transitive_replacement(self):
        for package in ('frappe', 'requests', 'livekit-protocol'):
            with self.assertRaises(ValueError):
                checkpoint.check_plan({package: '1'}, report('tele_tena', package))

    def test_normalized_names_and_missing_app(self):
        with self.assertRaises(ValueError):
            checkpoint.check_plan({'livekit-protocol': '1'}, report('tele_tena', 'Livekit_Protocol'))
        with self.assertRaises(ValueError):
            checkpoint.check_plan({}, report('unrelated'))



class UpdatePlan(unittest.TestCase):
    def test_intentional_update(self):
        self.assertEqual(checkpoint.check_plan({'tele-tena':'0.1.0','frappe':'16.2.1'}, report('tele_tena'), 'update'), ['tele-tena'])
    def test_modes_and_unrelated_replacements(self):
        for mode,before in [('install',{'tele-tena':'1'}),('update',{})]:
            with self.assertRaises(ValueError): checkpoint.check_plan(before,report('tele_tena'),mode)
        with self.assertRaises(ValueError): checkpoint.check_plan({'tele-tena':'1','requests':'2'},report('tele_tena','requests'),'update')
    def test_preserves_same_version_editable_identity(self):
        before={'frappe':{'version':'16.2.1','identity':{'editable':True,'path':'/bench/apps/frappe'}},'tele-tena':{'version':'0.1.0','identity':{'editable':True,'path':'/bench/apps/tele_tena'}}}
        after={**before,'tele-tena':{'version':'0.1.138','identity':before['tele-tena']['identity']}}
        checkpoint.check_preserved(before,after,'update')
        after['frappe']={'version':'16.2.1','identity':{'editable':True,'path':'/elsewhere'}}
        with self.assertRaises(ValueError): checkpoint.check_preserved(before,after,'update')
    def test_wrong_target_and_post_install_version(self):
        r={'install':[{'metadata':{'name':'tele_tena','version':'2'},'download_info':{'url':'file:///wrong','dir_info':{'editable':True}}}]}
        with self.assertRaises(ValueError): checkpoint.check_plan({'tele-tena':'1'},r,'update','/bench/apps/tele_tena')
        with self.assertRaises(ValueError): checkpoint.check_preserved({'frappe':{'version':'1','identity':None}}, {'frappe':{'version':'2','identity':None},'tele-tena':{'version':'1','identity':None}})

if __name__ == '__main__':
    unittest.main(verbosity=2)
