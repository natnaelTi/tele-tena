import importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('checkpoint',Path(__file__).resolve().parents[1]/'scripts/operations_archive_checkpoint.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PrivateCheckpoint(unittest.TestCase):
 def test_bound_config_volume_and_journal_are_required_and_verified(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);root.chmod(0o700);site=root/'sites'/'synthetic.localhost';site.mkdir(parents=True);volume=root/'replays';volume.mkdir(mode=0o700);file=volume/('replay-'+'a'*64);file.write_bytes(b'compressed-masked-fixture');file.chmod(0o600);cfg=root/'providers.json';cfg.write_text(json.dumps({'archive_directory':str(volume)}));cfg.chmod(0o600);(site/'site_config.json').write_text(json.dumps({'tele_tena_operations_config_file':str(cfg)}));out=root/'backup'
   self.assertEqual(m.snapshot(root,'synthetic.localhost',out)['archive_objects'],1);m.verify(out)
   with self.assertRaises(AssertionError):m.snapshot(root,'synthetic.localhost',out)
   (out/'archive-volume.tar').unlink()
   with self.assertRaises(FileNotFoundError):m.verify(out)
 def test_empty_unbound_state_is_explicit_not_missing_archive_success(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);root.chmod(0o700);site=root/'sites'/'synthetic.localhost';site.mkdir(parents=True);(site/'site_config.json').write_text('{}');out=root/'backup';self.assertEqual(m.snapshot(root,'synthetic.localhost',out),{'private_files':0,'archive_objects':0});self.assertIsNone(m.verify(out)['volume'])
if __name__=='__main__':unittest.main()
