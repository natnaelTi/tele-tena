import importlib.util,subprocess,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('lock',Path(__file__).resolve().parents[1]/'scripts/check_frappe_lock.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ExactLockDelta(unittest.TestCase):
 def test_clean_reviewed_and_unrelated(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)
   def git(*args):subprocess.run(['git','-C',d,*args],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   git('init');(p/'yarn.lock').write_text('caniuse-lite:\n'+m.OLD+'\n');git('add','yarn.lock');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','fixture')
   self.assertEqual(m.check(p,expected=None),'clean')
   (p/'yarn.lock').write_text('caniuse-lite:\n'+m.NEW+'\n');self.assertIn('reviewed',m.check(p,expected=None))
   (p/'yarn.lock').write_text('caniuse-lite:\n'+m.NEW+'\n#other change\n')
   with self.assertRaises(ValueError):m.check(p,expected=None)
   (p/'unreviewed.py').write_text('new file')
   with self.assertRaises(ValueError):m.check(p,expected=None)
