"""Read-only real Frappe catalog checks; no account, approval or language changes."""
import os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];os.chdir('/home/frappe/teletena-compat/bench/sites');sys.path.insert(0,str(ROOT))
import frappe
frappe.init(site='teletena-guest-first-test.localhost');frappe.connect();frappe.set_user('Guest')
from tele_tena.api.care_languages import catalog,display_catalog
class LanguageCatalog(unittest.TestCase):
 def test_priority_names_and_stable_server_paging(self):
  first=catalog()['items'];priority=[r for r in first if r.priority_group=='English and Ethiopian Languages']
  self.assertEqual({r.code for r in priority},{'aa','am','en','gez','om','sid','so','ti','wal'})
  self.assertEqual([r.english for r in priority],sorted(r.english for r in priority));self.assertEqual(first[:len(priority)],priority)
  all_items=[];offset=0
  while True:
   page=catalog(offset=offset);all_items+=page['items'];offset+=20
   if not page['has_more']:break
  self.assertEqual(len(all_items),len({r.code for r in all_items}));self.assertEqual(len(all_items),len(display_catalog()))
  self.assertTrue(all(len(r.english)>len(r.code) for r in all_items if r.code in ('ace','sid','wal')))
  self.assertEqual([r.code for r in catalog(offset=20)['items']],[r.code for r in all_items[20:40]])
 def test_search_only_matches_query_including_aliases(self):
  for search,expected in [('French','fr'),('aar','aa'),('eng','en')]:
   found=catalog(search)['items'];self.assertTrue(any(r.code==expected for r in found));self.assertFalse(any(r.code=='am' for r in found))
  self.assertEqual(catalog('a-language-that-does-not-exist')['items'],[])
 def test_public_projection_and_flag_provenance(self):
  for item in catalog()['items']:
   self.assertEqual(set(item),{'code','english','amharic','afaan_oromo','priority_group','region'})
   if item.region:self.assertTrue((ROOT/'frontend/public/flags'/(item.region.lower()+'.svg')).is_file())
  for item in display_catalog().values():
   if item['region']:self.assertTrue((ROOT/'frontend/public/flags'/(item['region'].lower()+'.svg')).is_file())
if __name__=='__main__':
 try:unittest.main()
 finally:frappe.destroy()
