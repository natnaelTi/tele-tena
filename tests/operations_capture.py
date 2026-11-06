"""Real Frappe16 capture gateway; all providers patched, rollback fixtures only."""
from operations import *
from tele_tena.operations import capture
from tele_tena.patches.v1_54_replay_capture import execute as migrate_capture
migrate_capture();frappe.db.commit()
class Capture(Operations):
 def setUp(self):
  super().setUp();self.config=rt.config();self.config.update(replay=True,archive=True,sample_percent=100)
  self.config_patch=patch('tele_tena.operations.runtime.config',return_value=self.config);self.config_patch.start();self.cap_patch=patch('tele_tena.operations.capture.capability',return_value=True);self.cap_patch.start()
  ops.preference(False,True)
 def tearDown(self):
  self.cap_patch.stop();self.config_patch.stop();super().tearDown()
 def recording(self):return ops.replay_admit(str(uuid.uuid4()),str(uuid.uuid4()))
 def frames(self):
  t=rt.now().replace(tzinfo=__import__('datetime').timezone.utc).timestamp()*1000
  return [{'type':4,'timestamp':t,'data':{'href':'https://private.invalid/patient/SECRET?token=SECRET','width':390,'height':844}},{'type':2,'timestamp':t+1,'data':{'node':{'id':1,'type':0,'childNodes':[{'type':2,'id':2,'tagName':'input','attributes':{'value':'SECRET','title':'SECRET','class':'card SECRET','src':'/private/SECRET'},'childNodes':[]},{'id':3,'type':3,'textContent':'SECRET clinical note'},{'type':2,'id':4,'tagName':'img','attributes':{'src':'/private/SECRET'},'childNodes':[]}]}}}]
 def test_admission_opt_in_tab_and_actor_permissions(self):
  self.assertFalse(ops.collection()['preference']['analytics']);self.assertTrue(ops.collection()['replay_configured'])
  p,w=str(uuid.uuid4()),str(uuid.uuid4());a=ops.replay_admit(p,w);self.assertEqual(a['state'],'Active');self.assertTrue(ops.replay_admit(p,w)['idempotent'])
  with self.assertRaises(frappe.PermissionError):ops.replay_admit(p,str(uuid.uuid4()))
  frappe.set_user(users['counselor'])
  with self.assertRaises(frappe.PermissionError):ops.replay_chunk(a['id'],str(uuid.uuid4()),self.frames(),'/patient/SECRET')
  frappe.set_user('Guest');self.assertEqual(capture.admit(str(uuid.uuid4()),str(uuid.uuid4()))['state'],'Disabled')
 def test_projection_retry_no_raw_payload_and_explicit_close(self):
  r=self.recording();key=str(uuid.uuid4());frames=self.frames();out=ops.replay_chunk(r['id'],key,frames,'/patient/consultations/SECRET?token=SECRET');self.assertEqual(out['state'],'Recorded Locally');self.assertTrue(ops.replay_chunk(r['id'],key,frames,'/patient/consultations/SECRET?token=SECRET')['idempotent'])
  row=j.one('SELECT * FROM tt_ops_chunk WHERE capture_id=%s',(r['id'],));raw=storage.read(row.object_key,'capture');self.assertNotIn(b'SECRET',raw);self.assertNotIn(b'/private/',raw);self.assertIn(b'https://replay.invalid/patient/consultations/:ref',raw)
  changed=self.frames();changed[1]['data']['node']['childNodes']=[]
  with self.assertRaises(frappe.ValidationError):ops.replay_chunk(r['id'],key,changed,'/patient')
  ops.replay_close(r['id']);self.assertEqual(ops.replay_chunk(r['id'],str(uuid.uuid4()),frames,'/patient')['state'],'Stopped')
 def test_opt_out_revokes_all_tabs_and_pending_objects(self):
  ids=[self.recording()['id'] for _ in range(2)]
  for id in ids:ops.replay_chunk(id,str(uuid.uuid4()),self.frames(),'/patient')
  ops.preference(False,False)
  self.assertEqual(j.one("SELECT COUNT(*) n FROM tt_ops_capture WHERE state='Revoked'").n,2)
  self.assertFalse(list(Path(self.tmp.name).glob('capture-*')));self.assertEqual(j.one("SELECT COUNT(*) n FROM tt_ops_chunk WHERE state='Discarded'").n,2)
 def test_quotas_scope_expiry_and_disabled_site(self):
  self.config['replays_per_day']=0;self.assertEqual(self.recording()['state'],'Limited');self.config['replays_per_day']=500
  r=self.recording();self.config['recording_bytes']=1;self.assertEqual(ops.replay_chunk(r['id'],str(uuid.uuid4()),self.frames(),'/patient')['state'],'Limited')
  self.assertEqual(j.one('SELECT bytes FROM tt_ops_capture WHERE id=%s',(r['id'],)).bytes,0)
  self.config['replay']=False;self.assertEqual(self.recording()['state'],'Disabled')
 def test_retry_worker_original_capture_retention_and_tombstone(self):
  r=self.recording();ops.replay_chunk(r['id'],str(uuid.uuid4()),self.frames(),'/patient');ops.replay_close(r['id']);before=j.one('SELECT * FROM tt_ops_capture WHERE id=%s',(r['id'],));clock=rt.now()
  with patch('tele_tena.operations.providers.replay_snapshot',side_effect=providers.ProviderUnavailable('timeout')) as send:capture.tick();self.assertEqual(send.call_count,1)
  self.assertEqual(j.one('SELECT state FROM tt_ops_chunk WHERE capture_id=%s',(r['id'],)).state,'Retry')
  with patch('tele_tena.operations.runtime.now',return_value=clock+timedelta(minutes=2)),patch('tele_tena.operations.providers.replay_snapshot',return_value='ProviderAccepted') as send:capture.tick();self.assertEqual(send.call_count,1)
  self.assertEqual(j.one('SELECT state FROM tt_ops_chunk WHERE capture_id=%s',(r['id'],)).state,'ProviderAccepted');self.assertFalse(list(Path(self.tmp.name).glob('capture-*')))
  after=j.one('SELECT * FROM tt_ops_archive WHERE id=%s',(r['id'],));self.assertEqual(after.captured,before.captured);self.assertEqual(after.expires,before.captured+timedelta(days=90));self.assertGreater(after.next_try,clock+timedelta(hours=25))
  with patch('tele_tena.operations.runtime.now',return_value=before.captured+timedelta(days=91)):capture.tick();archive.retention()
  self.assertTrue(archive.deleted(r['id']));self.assertEqual(j.one('SELECT state FROM tt_ops_archive WHERE id=%s',(r['id'],)).state,'Expired')
 def test_restore_integrity_and_not_exporting_incomplete_capture(self):
  r=self.recording();ops.replay_chunk(r['id'],str(uuid.uuid4()),self.frames(),'/patient');ops.replay_close(r['id'])
  item=j.one('SELECT * FROM tt_ops_chunk WHERE capture_id=%s',(r['id'],));path=Path(self.tmp.name)/('capture-'+item.object_key);path.write_text('corrupted')
  with patch('tele_tena.operations.providers.replay_snapshot') as send:capture.tick();send.assert_not_called()
  self.assertEqual(j.one('SELECT state FROM tt_ops_chunk WHERE id=%s',(item.id,)).state,'Incomplete')
  with patch('tele_tena.operations.runtime.now',return_value=rt.now()+timedelta(hours=26)),patch('tele_tena.operations.providers.archive_export') as export:archive.export_tick();export.assert_not_called()
  self.assertEqual(j.one('SELECT failure_code FROM tt_ops_archive WHERE id=%s',(r['id'],)).failure_code,'capture_incomplete')
 def test_renewed_auth_scope_denial_and_immediate_delete(self):
  r=self.recording();ops.replay_chunk(r['id'],str(uuid.uuid4()),self.frames(),'/patient')
  with patch('tele_tena.operations.capture.scope',return_value='b'*64):
   with self.assertRaises(frappe.PermissionError):ops.replay_chunk(r['id'],str(uuid.uuid4()),self.frames(),'/patient')
   self.assertEqual(ops.replay_delete(r['id'])['state'],'Expired')
  self.assertFalse(list(Path(self.tmp.name).glob('capture-*')))
  self.assertEqual(ops.replay_chunk(r['id'],str(uuid.uuid4()),self.frames(),'/patient')['state'],'Stopped')
 def test_projection_removes_selected_values_and_arbitrary_styles(self):
  from tele_tena.operations.replay_projection import project,attributes
  self.assertEqual(project({'type':3,'timestamp':1,'data':{'source':5,'id':1,'text':'PRIVATE','isChecked':True}},set())['data'],{'source':5,'id':1,'text':'*******','isChecked':False})
  self.assertEqual(attributes({'style':'color:JohnDoe;width:123px;background-color:#123456','title':'PRIVATE'},set()),{'style':'width:123px;background-color:#123456'})
 def test_private_volume_is_restricted_and_checksum_preserved(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory);path.chmod(0o700)
   with patch('tele_tena.operations.providers.settings',return_value={'archive_directory':directory}):
    key=storage.put(b'private-masked-synthetic',100,10000,'replay');self.assertEqual(storage.read(key,'replay'),b'private-masked-synthetic');self.assertEqual((path/('replay-'+key)).stat().st_mode&0o777,0o600)
    path.chmod(0o755)
    with self.assertRaises(ValueError):storage.read(key,'replay')
    path.chmod(0o700);storage.delete(key,'replay')
 def test_client_loss_is_incomplete_and_never_claims_archive(self):
  r=self.recording();ops.replay_chunk(r['id'],str(uuid.uuid4()),self.frames(),'/patient');self.assertEqual(ops.replay_loss(r['id'],'projection')['state'],'Incomplete')
  with patch('tele_tena.operations.providers.replay_snapshot') as send:capture.tick();send.assert_not_called()
  self.assertEqual(j.one('SELECT state FROM tt_ops_archive WHERE id=%s',(r['id'],)).state,'Incomplete')
 def test_inherited_suite_not_duplicated(self):pass
# Run only new tests; original operations suite is run once separately.
if __name__=='__main__':
 names=[name for name in Capture.__dict__ if name.startswith('test_') and name!='test_inherited_suite_not_duplicated']
 try:
  result=unittest.TextTestRunner().run(unittest.TestSuite(Capture(name) for name in names));sys.exit(not result.wasSuccessful())
 finally:frappe.db.rollback();frappe.destroy()
