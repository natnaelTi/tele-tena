import json,unittest
from tele_tena.operations.posthog_export import export_recording,ExportError
from tele_tena.operations.replay_format import ReplayFormatError
class Export(unittest.TestCase):
 def test_all_segments_and_stable_manifest_required(self):
  id='12345678-1234-1234-1234-123456789abc';sources=[{'source':'blob_v2','blob_key':'0'}];blob=b'\n'.join(json.dumps(['window',e]).encode() for e in [{'type':4,'timestamp':1,'data':{'width':100,'height':100}},{'type':2,'timestamp':2,'data':{'node':{'type':0,'id':1,'childNodes':[]}}}]);calls=[]
  def fetch(path,maximum):
   calls.append(path)
   if path.endswith('/'+id+'/'):return 200,json.dumps({'id':id,'start_time':'2026-11-05T00:00:00Z'}).encode()
   if 'blob_key' in path:return 200,blob
   return 200,json.dumps({'sources':sources}).encode()
  result=export_recording(335848,id,fetch);self.assertEqual(len(calls),4);self.assertEqual(len(result['events']),2);self.assertEqual(result['source_keys'],['0']);self.assertIn('0',result['source_sha256'])
 def test_metadata_or_access_failure_is_not_playable_export(self):
  with self.assertRaises(ExportError):export_recording(335848,'12345678-1234-1234-1234-123456789abc',lambda *_:(403,b'{}'))

class ExportBounds(unittest.TestCase):
 def test_source_budget_rejects_before_partial_download(self):
  sources=[{'source':'blob_v2','blob_key':str(i)} for i in range(21)];id='12345678-1234-1234-1234-123456789abc';calls=[]
  def fetch(path,maximum):
   calls.append(path)
   return (200,json.dumps({'id':id,'start_time':'2026-11-06T00:00:00Z'}).encode()) if path.endswith('/'+id+'/') else (200,json.dumps({'sources':sources}).encode())
  with self.assertRaisesRegex(ExportError,'source_budget_exceeded'):export_recording(335848,id,fetch)
  self.assertEqual(len(calls),2)

if __name__=='__main__':unittest.main()
