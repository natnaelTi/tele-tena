"""Read-only reviewed-dictionary identity/coverage gate; no draft-loading option."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def inspect():
 files=[ROOT/p for p in ('localization/reviewed.json','frontend/src/localization/reviewed.json','tele_tena/localization/reviewed.json')];data=json.loads(files[0].read_text());assert all(json.loads(f.read_text())==data for f in files),'Reviewed dictionaries differ'
 for entry in data.values():assert entry['source_hash']==hashlib.sha256(entry['english'].encode()).hexdigest(),'Reviewed source hash mismatch'
 catalog=json.loads((ROOT/'localization/catalog.json').read_text());english={r['english'] for r in catalog.values()}
 counts={};missing={}
 for locale in ('amharic','afaan_oromo'):
  approved={r['english'] for r in data.values() if r.get(locale) and r['english'] in english};counts[locale]=len(approved);missing[locale]=len(english-approved)
 return {'sha256':hashlib.sha256((json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()).hexdigest(),'catalog_entries':len(catalog),'unique_english':len(english),'reviewed_unique_english':counts,'missing_unique_english':missing,'complete':all(v==0 for v in missing.values())}
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--require-complete',action='store_true');args=parser.parse_args();report=inspect();print(json.dumps(report,indent=2));return 1 if args.require_complete and not report['complete'] else 0
if __name__=='__main__':raise SystemExit(main())
