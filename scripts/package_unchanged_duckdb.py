"""Read-only installed DuckDB binary export; no customer data or package changes."""
import argparse,hashlib,importlib.metadata as md,os,sys,tempfile
from pathlib import Path
import duckdb
from wheel.wheelfile import WheelFile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--destination',type=Path,required=True);a=p.parse_args()
if sys.version_info[:2]!=(3,14) or duckdb.__version__!='1.3.2':raise SystemExit('STOP: expected existing working Python3.14/DuckDB1.3.2')
d=md.distribution('duckdb');tag=next(line[5:] for line in d.read_text('WHEEL').splitlines() if line.startswith('Tag: '));a.destination.mkdir(mode=0o700,exist_ok=False)
filename=a.destination/f'duckdb-1.3.2-{tag}.whl'
with WheelFile(filename,'w') as wheel:
 for entry in d.files or []:
  rel=Path(str(entry));top=rel.parts[0]
  if rel.name.startswith('RECORD') or '__pycache__' in rel.parts:continue
  if rel.is_absolute() or '..' in rel.parts or not (top in ('duckdb','duckdb.libs','duckdb-stubs','adbc_driver_duckdb') or top.startswith('_duckdb.') or top.startswith('duckdb-1.3.2.dist-info')):raise SystemExit('STOP: unexpected package path; no unrelated files copied')
  source=Path(d.locate_file(entry));assert source.is_file() and not source.is_symlink()
  wheel.write(source,str(rel))
os.chmod(filename,0o600);digest=hashlib.sha256(filename.read_bytes()).hexdigest();manifest=a.destination/'SHA256SUMS';manifest.write_text(digest+'  '+filename.name+'\n');manifest.chmod(0o600)
print('PASS: working unchanged DuckDB1.3.2 static wheel exported privately; no production packages/files/data modified. '+str(filename))
