"""Regression coverage for clear technical exclusions without deleting visible copy."""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Extraction(unittest.TestCase):
 def test_clear_technical_rows_excluded_but_visible_copy_retained(self):
  data=json.loads((ROOT/'localization/catalog.json').read_text())
  self.assertNotIn('copy.accountmenu.escape',data)
  self.assertNotIn('copy.admin.button_quiet',data)
  for english in ['End for everyone','ETB','TeleTena','View Payment','English and Ethiopian Languages','Search Care Languages']:
   self.assertTrue(any(r['english']==english for r in data.values()),english)
 def test_exclusions_are_source_attributed_and_no_reviewed_values_lost(self):
  removed=json.loads((ROOT/'localization/extraction-exclusions.json').read_text());self.assertTrue(removed)
  self.assertTrue(all(e['source_location'].startswith(('frontend/src/','tele_tena/')) and e['reason'] for e in removed))
  for key,entry in json.loads((ROOT/'localization/reviewed.json').read_text()).items():
   self.assertEqual(json.loads((ROOT/'localization/catalog.json').read_text())[key]['source_hash'],entry['source_hash'])
if __name__=='__main__':unittest.main()
