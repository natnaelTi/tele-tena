import gzip,importlib.util,json,tempfile,tarfile,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('backup',Path(__file__).resolve().parents[1]/'scripts/verify_release_backup.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
class RequiredArchives(unittest.TestCase):
 def test_absent_empty_and_corrupt(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)
   with self.assertRaises(ValueError):b.verify(p)
   with gzip.open(p/'database.sql.gz','wb') as f:f.write(b'CREATE TABLE example (id int);')
   (p/'site-config.json').write_text(json.dumps({'db_name':'fictional'}))
   with self.assertRaises(ValueError):b.verify(p)
   for name in ['public-files.tar','private-files.tar']:
    with tarfile.open(p/name,'w'):pass
   self.assertEqual(len(b.verify(p)),4)
   (p/'private-files.tar').write_bytes(b'corrupt')
   with self.assertRaises(tarfile.TarError):b.verify(p)
