"""Normalize a licensed ROR v2 JSON (or CRC-checked ZIP) into a versioned bundle.
No site connection; writes a new output only. Registry inclusion is not accreditation.
Usage: python scripts/import_professional_references.py input.zip output.json.gz
"""
import argparse,gzip,json,zipfile
from pathlib import Path


def normalize(items):
    result=[]
    for item in items:
        if item.get('status')!='active':continue
        kinds=[]
        if 'education' in item.get('types',[]):kinds.append('issuer')
        if 'healthcare' in item.get('types',[]):kinds.append('facility')
        for kind in kinds:
            names=item['names'];label=next((n['value'] for n in names if 'ror_display' in n['types']),names[0]['value']);loc=(item.get('locations') or [{}])[0].get('geonames_details',{})
            result.append({'id':kind+':ror:'+item['id'].rsplit('/',1)[1],'kind':kind,'label':label,'aliases':[n['value'] for n in names if n['value']!=label],'country':loc.get('country_code',''),'region':loc.get('country_subdivision_name',''),'entity_type':'Education organization' if kind=='issuer' else 'Healthcare organization','source_id':item['id'],'source_url':item['id'],'accessed':'2026-10-22','permitted_use':'ROR CC0 1.0; directory inclusion is not accreditation'})
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);p.add_argument('output',type=Path);args=p.parse_args()
    if args.output.exists():raise SystemExit('Refusing to overwrite a versioned bundle')
    if zipfile.is_zipfile(args.input):
        with zipfile.ZipFile(args.input) as z:
            if z.testzip():raise SystemExit('Archive CRC check failed')
            data=json.loads(z.read(next(n for n in z.namelist() if n.endswith('.json'))))
    else:data=json.loads(args.input.read_text())
    with gzip.open(args.output,'wt') as f:json.dump(normalize(data),f,ensure_ascii=False)
