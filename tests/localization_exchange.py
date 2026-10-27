"""Source dictionary import checks use an isolated directory, never a site."""
import csv,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('catalog',Path(__file__).resolve().parents[1]/'scripts/localization/catalog.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Exchange(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.old=m.DIRECTORY,m.CATALOG,m.ROOT;m.DIRECTORY=Path(self.tmp.name);m.CATALOG=m.DIRECTORY/'catalog.json';m.ROOT=m.DIRECTORY
  for directory in ('frontend/src/localization','tele_tena/localization'):(m.ROOT/directory).mkdir(parents=True)
  self.row=dict.fromkeys(m.COLUMNS,'');self.row.update(key='booking.ready',context='Booking confirmation',english='Ready for {name}',source_hash=m.digest('Ready for {name}'),review_status='reviewed',amharic='ዝግጁ {name}')
  m.CATALOG.write_text(json.dumps({self.row['key']:self.row}));self.file=m.DIRECTORY/'review.csv'
 def tearDown(self):m.DIRECTORY,m.CATALOG,m.ROOT=self.old;self.tmp.cleanup()
 def write(self,rows):
  with self.file.open('w',newline='',encoding='utf-8') as f:
   writer=csv.DictWriter(f,fieldnames=m.COLUMNS);writer.writeheader();writer.writerows({k:m.encode(str(r[k])) for k in m.COLUMNS} for r in rows)
 def test_unicode_placeholder_newline_and_formula_roundtrip(self):
  for s in ['=SUM(A1)',' +1',"'actual",'አማርኛ\nAfaan Oromo','@contact','ordinary']:
   self.assertEqual(m.decode(m.encode(s)),s)
  self.write([self.row]);report=m.preview(self.file);self.assertFalse(report['errors']);self.assertEqual(len(report['changes']),1);self.assertFalse((m.DIRECTORY/'reviewed.json').exists())
 def test_bad_placeholder_stale_unknown_and_duplicate_rejected(self):
  for changed in [dict(self.row,amharic='Missing variable'),dict(self.row,source_hash='bad'),dict(self.row,key='unknown')]:
   self.write([changed]);self.assertTrue(m.preview(self.file)['errors'])
  self.write([self.row,self.row]);self.assertTrue(m.preview(self.file)['errors'])
 def test_apply_history_and_rollback_preserve_reviewed_values(self):
  self.write([self.row]);result=m.preview(self.file,True);self.assertTrue(result['applied']);self.assertEqual(m.current()[self.row['key']]['amharic'],self.row['amharic'])
  before=m.current();self.write([dict(self.row,source_hash='stale')])
  with self.assertRaises(ValueError):m.preview(self.file,True)
  self.assertEqual(m.current(),before)
  old=json.loads((m.DIRECTORY/'versions'/result['version']).with_suffix('.json').read_text());self.assertEqual(m.install(old),result['version'])
  self.assertEqual(json.loads((m.ROOT/'frontend/src/localization/reviewed.json').read_text()),m.current())
 def test_provisional_never_applied(self):
  self.write([dict(self.row,review_status='provisional')]);self.assertFalse(m.preview(self.file)['changes'])
if __name__=='__main__':unittest.main()
