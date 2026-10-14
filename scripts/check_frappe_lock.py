"""Read-only check for the exact operator-reported caniuse-lite lock-only delta."""
import hashlib
from pathlib import Path
import subprocess
import sys

OLD='''  version "1.0.30001564"
  resolved "https://registry.yarnpkg.com/caniuse-lite/-/caniuse-lite-1.0.30001564.tgz#eaa8bbc58c0cbccdcb7b41186df39dd2ba591889"
  integrity sha512-DqAOf+rhof+6GVx1y+xzbFPeOumfQnhYzVnZD6LAXijR77yPtm9mfOcqOnT3mpnJiZVT+kwLAFnRlZcIz+c6bg=='''
NEW='''  version "1.0.30001765"
  resolved "https://registry.npmjs.org/caniuse-lite/-/caniuse-lite-1.0.30001765.tgz"
  integrity sha512-LWcNtSyZrakjECqmpP4qdg0MMGdN368D7X8XvvAqOcqMv0RxnlqVKZl2V6/mBR68oYMxOZPLw/gO7DuisMHUvQ=='''

def check(path,expected='8f6e24728b86b7c6427908ed6536289a41ea9cf4'):
 path=Path(path)
 def git(*args):return subprocess.check_output(['git','-C',str(path),*args],text=True).strip()
 if expected and git('rev-parse','HEAD')!=expected:raise ValueError('Different Frappe commit; investigate before proceeding')
 status=git('status','--porcelain')
 if not status:return 'clean'
 if status.strip() not in ('M yarn.lock','MM yarn.lock'):raise ValueError('Unreviewed framework changes; preserve and stop')
 baseline=subprocess.check_output(['git','-C',str(path),'show','HEAD:yarn.lock']).decode()
 if baseline.count(OLD)!=1 or (path/'yarn.lock').is_symlink() or (path/'yarn.lock').read_text()!=baseline.replace(OLD,NEW):raise ValueError('Lockfile differs from the exact reviewed caniuse-lite-only delta')
 return 'reviewed caniuse-lite-only delta; SHA256 '+hashlib.sha256((path/'yarn.lock').read_bytes()).hexdigest()

if __name__=='__main__':
 try:print('PASS:',check(sys.argv[1]))
 except (ValueError,OSError,subprocess.CalledProcessError) as e:raise SystemExit('FAIL: '+str(e))
