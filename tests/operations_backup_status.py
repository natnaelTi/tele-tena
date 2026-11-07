import json,tempfile,gzip,tarfile,hashlib,os,unittest,sys
from pathlib import Path
from datetime import datetime,timezone,timedelta
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from tele_tena.operations.backup_status import observe,read,FILES
from verify_release_backup import verify
class BackupStatus(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name);self.p.chmod(0o700);self.start=datetime.now(timezone.utc)
  (self.p/FILES[0]).write_bytes(gzip.compress(b'CREATE TABLE synthetic_test (id int);'))
  for name in FILES[1:3]:
   with tarfile.open(self.p/name,'w'):pass
  (self.p/FILES[3]).write_text(json.dumps({'db_name':'synthetic'}))
  for f in self.p.iterdir():f.chmod(0o600)
  result=verify(self.p);f=self.p/'verified-manifest.json';f.write_text(json.dumps(result));f.chmod(0o600);observe(self.p,'synthetic.localhost',self.start,result)
 def tearDown(self):self.tmp.cleanup()
 def test_current_and_stale_use_capture_start_not_receipt_mtime(self):
  self.assertEqual(read(self.p,'synthetic.localhost')['status'],'Current')
  self.assertEqual(read(self.p,'synthetic.localhost',clock=self.start+timedelta(hours=25))['status'],'Stale')
 def test_absent_source_is_unavailable_and_legacy_bundle_unknown(self):
  self.assertEqual(read(None,'synthetic.localhost')['status'],'Unavailable');(self.p/'backup-observation.json').unlink();self.assertEqual(read(self.p,'synthetic.localhost')['status'],'Unknown')
 def test_missing_changed_or_cross_site_artifacts_never_healthy(self):
  self.assertEqual(read(self.p,'other.localhost')['status'],'Unknown')
  (self.p/FILES[0]).write_bytes(b'changed');self.assertEqual(read(self.p,'synthetic.localhost')['status'],'Unknown')
 def test_public_permissions_and_symlinks_denied(self):
  (self.p/FILES[0]).chmod(0o644);self.assertEqual(read(self.p,'synthetic.localhost')['status'],'Unknown')
 def test_future_timestamps_denied(self):
  self.assertEqual(read(self.p,'synthetic.localhost',clock=self.start-timedelta(seconds=1))['status'],'Unknown')
 def test_incomplete_backup_cannot_create_observation(self):
  (self.p/'backup-observation.json').unlink()
  with self.assertRaises(ValueError):observe(self.p,'synthetic.localhost',self.start,{})
  self.assertFalse((self.p/'backup-observation.json').exists())
if __name__=='__main__':unittest.main()
