"""Synthetic reviewed entries in memory only; never imports workbook draft text."""
import hashlib,unittest
from unittest.mock import patch
from tele_tena import localization
class Runtime(unittest.TestCase):
 def test_independent_locale_and_placeholder_fallback(self):
  source='Hello {name}';entry={'english':source,'source_hash':hashlib.sha256(source.encode()).hexdigest(),'amharic':'መልእክት {name}'}
  with patch.object(localization,'entries',return_value={'fixture':entry}):
   self.assertEqual(localization.translate(source,'am').format(name='Private Participant'),'መልእክት Private Participant');self.assertEqual(localization.translate(source,'om'),source);self.assertEqual(localization.translate(source,'fr'),source)
 def test_stale_source_is_never_served(self):
  with patch.object(localization,'entries',return_value={'fixture':{'english':'Hello','source_hash':'stale','amharic':'Draft'}}):self.assertEqual(localization.translate('Hello','am'),'Hello')
if __name__=='__main__':unittest.main()
