import unittest
from unittest.mock import patch
from tele_tena.operations import providers
class Frames(unittest.TestCase):
 def test_browser_frames_and_debug_ids_are_trusted_manifest_only(self):
  name='app:///assets/index-Proof.js';payload={'exception':{'values':[{'type':'TypeError','value':'PRIVATE-CANARY','stacktrace':{'frames':[{'filename':name,'lineno':2,'colno':17,'vars':{'password':'PRIVATE-CANARY'}},{'filename':'https://private.invalid/private/file?token=PRIVATE-CANARY','lineno':1}]}}]},'tags':{'origin':'browser','route':'/patient/book/private?secret=PRIVATE-CANARY'}}
  with patch('tele_tena.operations.providers.javascript_assets',return_value={name:'12345678-1234-1234-1234-123456789abc'}):clean=providers.sanitized_error(payload)
  self.assertEqual(clean['platform'],'javascript');self.assertEqual(len(clean['exception']['values'][0]['stacktrace']['frames']),1);self.assertIn('debug_meta',clean);self.assertNotIn('PRIVATE-CANARY',str(clean));self.assertNotIn('vars',str(clean))
 def test_unknown_or_missing_asset_has_no_frames_or_source_map_metadata(self):
  with patch('tele_tena.operations.providers.javascript_assets',return_value={}):clean=providers.sanitized_error({'exception':{'values':[{'type':'TypeError','stacktrace':{'frames':[{'filename':'app:///assets/unknown.js','lineno':1}]}}]},'tags':{'origin':'browser'}})
  self.assertEqual(clean['exception']['values'][0]['stacktrace']['frames'],[]);self.assertNotIn('debug_meta',clean)
if __name__=='__main__':unittest.main()
