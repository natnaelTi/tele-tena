"""The elapsed-time checkpoint cannot issue calls early."""
import unittest,sys,io
from contextlib import redirect_stdout
from unittest.mock import patch
from datetime import datetime,timezone,timedelta
from scripts.operations_proof import native_resume
class Resume(unittest.TestCase):
 def test_not_due_does_not_start_worker_export_or_network(self):
  future=(datetime.now(timezone.utc)+timedelta(hours=25)).isoformat()
  with patch.object(sys,'argv',['native_resume','--root','/private/test','--output','/private/output','--delete-verified-tests']),patch.object(native_resume,'NativeRun') as run,patch.object(native_resume.subprocess,'run') as process:
   run.return_value.checked.return_value=({'recordings':[{'recheck_due_at':future}]},{})
   with redirect_stdout(io.StringIO()) as output:native_resume.main()
   self.assertIn('PENDING',output.getvalue());process.assert_not_called()
if __name__=='__main__':unittest.main()
