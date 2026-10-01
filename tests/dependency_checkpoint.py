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


if __name__ == '__main__':
    unittest.main(verbosity=2)
