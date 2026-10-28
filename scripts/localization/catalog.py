"""Deterministic owned-source extraction and review-only, versioned CSV exchange."""
import argparse,ast,csv,gzip,hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DIRECTORY=ROOT/'localization';CATALOG=DIRECTORY/'catalog.json'
COLUMNS=['key','context','english','amharic','afaan_oromo','source_location','placeholders','source_hash','review_status','translator_notes']
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def placeholders(s):return sorted(re.findall(r'\$?\{[^{}]+\}|%(?:\([^)]+\))?[sdif]',s))
def encode(s):return "'"+s if s and (s[0] in "'=+-@\t\r\n" or s[0].isspace() and s.lstrip().startswith(('=','+','-','@'))) else s
def decode(s):return s[1:] if len(s)>1 and s[0]=="'" and (s[1] in "'=+-@\t\r\n" or s[1].isspace() and s[1:].lstrip().startswith(('=','+','-','@'))) else s
def extract():
    raw=json.loads(subprocess.check_output(['node',str(ROOT/'scripts/localization/extract.cjs')],text=True));entries=raw['entries'];translations=raw['translations']
    for file in sorted((ROOT/'tele_tena').rglob('*.py')):
        if '/localization/' in str(file):continue
        tree=ast.parse(file.read_text())
        if file.name in ('notifications.py','booking_notifications.py','public_content_defaults.py','email_delivery.py','sms.py'):
            for node in ast.walk(tree):
                if isinstance(node,ast.Constant) and isinstance(node.value,str) and re.search('[A-Za-z]',node.value) and (' ' in node.value or re.fullmatch('[A-Z][a-z]+',node.value)) and not re.match(r'(?i)^(https?://|SELECT |INSERT |UPDATE |DELETE |CREATE |ALTER |\s*SELECT |\s*INSERT |\s*UPDATE )',node.value) and len(node.value)<50000:
                    entries.append({'english':node.value,'context':'Notification or default public copy / '+file.stem,'source_location':str(file.relative_to(ROOT))+':'+str(node.lineno)})
        for node in ast.walk(tree):
            if not isinstance(node,ast.Call) or not node.args:continue
            name=ast.unparse(node.func)
            if name not in ('fail','frappe.throw','ValueError','frappe._','text'):continue
            arg=node.args[0];english=arg.value if isinstance(arg,ast.Constant) and isinstance(arg.value,str) else ''.join(p.value if isinstance(p,ast.Constant) else '{'+ast.unparse(p.value)+'}' for p in arg.values) if isinstance(arg,ast.JoinedStr) else None
            if english:entries.append({'english':english,'context':'Backend validation / '+file.stem,'source_location':str(file.relative_to(ROOT))+':'+str(node.lineno)})
    # Shipped metadata only. Never query a database or export user submissions.
    for file in sorted((ROOT/'tele_tena/reference_data').glob('*.json.gz')):
        for r in json.loads(gzip.decompress(file.read_bytes())):
            if r['kind'] not in ('domain','profession','specialty'):continue
            for field in ('label','group_label','description'):
                if r.get(field):entries.append({'english':r[field],'context':'Configured '+r['kind']+' / '+r['id']+' / '+field,'source_location':str(file.relative_to(ROOT))})
    # Public shipped content and language names, not runtime account data.
    language_bundle=ROOT/'tele_tena/reference_data/care-languages-v1.json'
    for r in json.loads(language_bundle.read_text())['records']:
        entries.append({'english':r['english'],'context':'Care language / '+r['code'],'source_location':str(language_bundle.relative_to(ROOT))})
    for file in sorted((ROOT/'tele_tena/tele_tena/doctype').rglob('*.json')):
        d=json.loads(file.read_text())
        for f in d.get('fields',[]):
            for field in ('label','description'):
                if f.get(field):entries.append({'english':f[field],'context':d.get('name',file.stem)+' / '+f.get('fieldname',''),'source_location':str(file.relative_to(ROOT))})
    canonical={}
    for r in sorted(entries,key=lambda x:(x['source_location'],x['english'])):
        english=r['english'];context=r['context'];token=re.sub('[^a-z0-9]+','_',english.lower()).strip('_')[:70] or 'message';key='copy.'+re.sub('[^a-z0-9]+','_',context.lower()).strip('_')[:65]+'.'+token
        if key in canonical and canonical[key]['english']!=english:key+='_'+digest(english)[:8]
        if key not in canonical:
            am,om=translations.get(english,['','']);canonical[key]={'key':key,'context':context,'english':english,'amharic':am,'afaan_oromo':om,'source_location':r['source_location'],'placeholders':json.dumps(placeholders(english),ensure_ascii=False),'source_hash':digest(english),'review_status':'provisional' if am or om else 'missing','translator_notes':''}
        elif r['source_location'] not in canonical[key]['source_location']:canonical[key]['source_location']+='; '+r['source_location']
    for key,review in current().items():
        if key in canonical and review.get('source_hash')==canonical[key]['source_hash']:
            for locale in ('amharic','afaan_oromo'):
                if review.get(locale):canonical[key][locale]=review[locale]
            canonical[key]['review_status']='reviewed'
    DIRECTORY.mkdir(exist_ok=True);(DIRECTORY/'extraction-exclusions.json').write_text(json.dumps(raw.get('excluded',[]),ensure_ascii=False,indent=2)+'\n');old=json.loads(CATALOG.read_text()) if CATALOG.exists() else {};CATALOG.write_text(json.dumps(canonical,ensure_ascii=False,indent=2)+'\n')
    (DIRECTORY/'source-changes.json').write_text(json.dumps({'added':sorted(set(canonical)-set(old)),'stale':sorted(k for k in old if k not in canonical or old[k]['source_hash']!=canonical[k]['source_hash'])},indent=2)+'\n')
    return canonical

def export(destination):
    records=extract()
    with destination.open('w',encoding='utf-8',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=COLUMNS,lineterminator='\n');writer.writeheader()
        for key in sorted(records):writer.writerow({k:encode(str(records[key].get(k,''))) for k in COLUMNS})
    report={'source_entries':len(records),'missing_amharic':sum(not r['amharic'] for r in records.values()),'missing_afaan_oromo':sum(not r['afaan_oromo'] for r in records.values()),'approved':sum(r['review_status']=='reviewed' for r in records.values()),'private_records_exported':0}
    (DIRECTORY/'coverage.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

def current():
    file=DIRECTORY/'reviewed.json';return json.loads(file.read_text()) if file.exists() else {}
def install(records):
    content=json.dumps(records,ensure_ascii=False,indent=2,sort_keys=True)+'\n';version=digest(content);history=DIRECTORY/'versions';history.mkdir(exist_ok=True)
    previous=json.dumps(current(),ensure_ascii=False,indent=2,sort_keys=True)+'\n';(history/(digest(previous)+'.json')).write_text(previous)
    (history/(version+'.json')).write_text(content)
    for file in (DIRECTORY/'reviewed.json',ROOT/'frontend/src/localization/reviewed.json',ROOT/'tele_tena/localization/reviewed.json'):file.write_text(content)
    return version

def preview(source,apply=False):
    records=json.loads(CATALOG.read_text());seen=set();errors=[];updated=current();changes=[];missing=[];translations_by_english={}
    with source.open(encoding='utf-8-sig',newline='') as file:
        reader=csv.DictReader(file)
        if reader.fieldnames!=COLUMNS:raise ValueError('CSV columns do not match the documented dictionary schema')
        for raw in reader:
            r={k:decode(v or '') for k,v in raw.items()};key=r['key']
            if key in seen:errors.append({'key':key,'error':'duplicate key'});continue
            seen.add(key)
            if key not in records:errors.append({'key':key,'error':'unknown key'});continue
            base=records[key]
            if r['source_hash']!=base['source_hash'] or r['english']!=base['english']:errors.append({'key':key,'error':'stale English/source hash'});continue
            for locale in ('amharic','afaan_oromo'):
                value=r[locale]
                if not value:missing.append({'key':key,'locale':locale});continue
                if placeholders(value)!=placeholders(base['english']):errors.append({'key':key,'error':'placeholder mismatch','locale':locale});continue
                if r['review_status']!='reviewed':continue
                slot=(base['english'],locale)
                if slot in translations_by_english and translations_by_english[slot]!=value:errors.append({'key':key,'error':'same source copy has conflicting reviewed values; add an explicit contextual key in the caller first'});continue
                translations_by_english[slot]=value
                entry=updated.setdefault(key,{'english':base['english'],'source_hash':base['source_hash'],'context':base['context']})
                if entry.get(locale)!=value:changes.append({'key':key,'locale':locale});entry[locale]=value
    for key,entry in updated.items():
        for locale in ('amharic','afaan_oromo'):
            if entry.get(locale):
                slot=(entry['english'],locale)
                if slot in translations_by_english and translations_by_english[slot]!=entry[locale]:errors.append({'key':key,'error':'conflicts with an existing reviewed source; use an explicit context caller'})
                translations_by_english[slot]=entry[locale]
    stale_reviewed=[key for key,entry in updated.items() if key not in records or entry.get('source_hash')!=records[key]['source_hash']]
    report={'stale_reviewed':stale_reviewed,'errors':errors,'changes':changes,'missing_translations':missing,'missing_rows':sorted(set(records)-seen),'applied':False}
    if apply:
        if errors:raise ValueError('Import rejected; run preview and resolve validation errors')
        report.update(applied=True,version=install(updated))
    return report

def main():
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('export');p.add_argument('file',type=Path)
    for name in ('preview','import'):
        p=sub.add_parser(name);p.add_argument('file',type=Path);p.add_argument('--report',type=Path,required=True)
    p=sub.add_parser('rollback');p.add_argument('version');p.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    if args.command=='export':export(args.file)
    elif args.command=='rollback':
        if not re.fullmatch('[a-f0-9]{64}',args.version):raise ValueError('Invalid dictionary version')
        file=DIRECTORY/'versions'/(args.version+'.json');data=json.loads(file.read_text())
        if digest(file.read_text())!=args.version:raise ValueError('Version integrity check failed')
        print(json.dumps({'version':install(data) if args.apply else args.version,'applied':args.apply}))
    else:
        report=preview(args.file,args.command=='import');args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'errors':len(report['errors']),'changes':len(report['changes']),'missing':len(report['missing_translations']),'applied':report['applied']}));return 1 if report['errors'] else 0
    return 0
if __name__=='__main__':sys.exit(main())
