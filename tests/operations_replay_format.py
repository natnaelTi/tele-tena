import gzip,json,unittest
from tele_tena.operations.replay_format import normalize,ReplayFormatError
class Format(unittest.TestCase):
 def setUp(self):
  self.sources=[{'source':'blob_v2','blob_key':'0'}];self.meta={'type':4,'timestamp':1,'data':{'width':100,'height':100,'href':'http://proof.invalid/ops-proof-v1/'}};self.full={'type':2,'timestamp':2,'data':{'node':{'type':0,'id':1,'childNodes':[]}}}
 def blob(self,events):return {'0':b'\n'.join(json.dumps(['safe-window',e]).encode() for e in events)}
 def test_normalize_compression_dedup_and_order(self):
  compressed={**self.full,'cv':'2024-10','data':gzip.compress(json.dumps(self.full['data']).encode()).decode('latin1')};data=normalize(self.sources,self.blob([compressed,self.meta,self.meta]));self.assertEqual([e['type'] for e in data['events']],[4,2]);self.assertEqual(data['windows'],1)
 def test_unimplemented_player_variants_and_multiple_windows_are_rejected(self):
  for source in (7,9,10,13,14):
   with self.assertRaisesRegex(ReplayFormatError,'incremental_version_unsupported'):normalize(self.sources,self.blob([self.meta,self.full,{'type':3,'timestamp':3,'data':{'source':source}}]))
  two=self.blob([self.meta,self.full]);two['0']+=b'\n'+b'\n'.join(json.dumps(['second-window',e]).encode() for e in (self.meta,self.full))
  with self.assertRaisesRegex(ReplayFormatError,'multi_window_player_unverified'):normalize(self.sources,two)
 def test_missing_malformed_unknown_and_unsafe_compression_are_rejected(self):
  for sources,blobs in [(self.sources,{}),(self.sources,{'0':b'{broken'}),([{'source':'realtime','blob_key':'0'}],self.blob([self.meta,self.full])),(self.sources,self.blob([self.full])),(self.sources,self.blob([{**self.meta,'timestamp':float('nan')},self.full])),(self.sources,self.blob([self.meta,{**self.full,'cv':'unknown'}]))]:
   with self.assertRaises(ReplayFormatError):normalize(sources,blobs)
if __name__=='__main__':unittest.main()
