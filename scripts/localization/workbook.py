"""Local XLSX reconciliation; exports only independently human-approved locales.
Uses OOXML directly: no macros/formula evaluation, external services or site reads.
Original workbook is never modified. Artifacts belong outside public build output.
"""
import argparse,collections,csv,hashlib,io,json,os,re,subprocess,zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import catalog as exchange
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
HEADERS=['Key','English Source','Amharic Text','Amharic Review','Amharic Reviewer','Afaan Oromo Text','Afaan Oromo Review','Afaan Oromo Reviewer','Review Notes','Context','Suggested Review Priority','Placeholders','Source Location','Source Hash','Original Review Status','Original Translator Notes']
LOCALES={'amharic':('C','D','E'),'afaan_oromo':('F','G','H')}
STATES={'Draft','Missing','In Review','Needs Clarification','Approved'}
def sha(data):return hashlib.sha256(data).hexdigest()
def sheets(path):
 with zipfile.ZipFile(path) as z:
  if sum(n.file_size for n in z.infolist())>100_000_000:raise ValueError('Workbook exceeds100MB uncompressed limit')
  shared=[''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',NS)] if 'xl/sharedStrings.xml' in z.namelist() else []
  rels={r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))};out={}
  for s in ET.fromstring(z.read('xl/workbook.xml')).findall('m:sheets/m:sheet',NS):
   target=rels[s.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']];target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
   rows=[]
   for row in ET.fromstring(z.read(target)).findall('m:sheetData/m:row',NS):
    values={'_row':int(row.attrib['r'])};formulas=[]
    for c in row.findall('m:c',NS):
     col=re.sub('[0-9]','',c.attrib['r']);v=c.find('m:v',NS);raw=v.text if v is not None else '';inline=c.find('m:is',NS)
     values[col]=shared[int(raw)] if c.attrib.get('t')=='s' and raw else ''.join(inline.itertext()) if inline is not None else raw or ''
     if c.find('m:f',NS) is not None:formulas.append(col)
    values['_formulas']=formulas;rows.append(values)
   out[s.attrib['name']]={'path':target,'rows':rows}
  return out

def values(row,col):return exchange.decode(row.get(col,''))
def token_issues(source,value,locale,context,notes):
 issues=[]
 if not value.strip():return ['blank_translation']
 if exchange.placeholders(source)!=exchange.placeholders(value):issues.append('placeholder_identity_or_multiplicity')
 urls=lambda s:collections.Counter(re.findall(r'https?://[^\s<>"\]]+',s))
 if urls(source)!=urls(value):issues.append('url_mismatch')
 tags=lambda s:collections.Counter(re.findall(r'</?[A-Za-z][^>]*>',s))
 if tags(source)!=tags(value):issues.append('markup_mismatch')
 nums=lambda s:collections.Counter(re.findall(r'\d+(?:[.,]\d+)*(?:%)?',s))
 if nums(source)!=nums(value):issues.append('numeric_limits_or_formatting_changed')
 for brand in ('TeleTena','Telebirr','LiveKit'):
  if brand in source and brand not in value and not(brand=='TeleTena' and 'ቴሌ' in value and 'ጤና' in value):issues.append('product_name_review:'+brand)
 letters=re.findall('[A-Za-z]',value);ethiopic=re.findall('[\u1200-\u137f]',value)
 names='Care language /' in context or 'Configured ' in context or len(source.split())<=2
 if locale=='amharic' and len(letters)>15 and not ethiopic and not names:issues.append('locale_script_review')
 if locale=='afaan_oromo' and len(ethiopic)>4 and not ('ቴሌ' in value and len(ethiopic)<15):issues.append('locale_script_review')
 if source.count('\n\n')>=2 and value.count('\n\n')<source.count('\n\n'):issues.append('paragraph_structure_review')
 if len(source)>1000 and len(value)<len(source)*.35:issues.append('possible_truncation')
 if 'Existing Amharic' in notes and locale=='amharic':issues.append('supplied_locale_wording_review')
 if 'discount term' in notes or 'training evidence' in notes or 'specialist terminology' in notes:issues.append('clinical_financial_terminology_review')
 if 'policy' in notes.lower() or len(source)>2000:issues.append('policy_translation_review')
 if value!=value.strip():issues.append('outer_whitespace_review')
 return issues

def write_csv(path,columns,rows):
 with path.open('w',encoding='utf-8',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=columns,lineterminator='\n');writer.writeheader()
  for row in rows:writer.writerow({k:exchange.encode(str(row.get(k,''))) for k in columns})

def working_copy(original,destination,sheet_path,annotations,corrections):
 # Preserve every original OOXML ZIP entry except this worksheet; add Q:T notes.
 with zipfile.ZipFile(original) as source,zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as target:
  for info in source.infolist():
   data=source.read(info.filename)
   if info.filename==sheet_path:
    namespaces=dict(n for _,n in ET.iterparse(io.BytesIO(data),events=['start-ns']));
    for prefix,uri in namespaces.items():
     if not re.fullmatch(r'ns[0-9]+',prefix):ET.register_namespace(prefix,uri)
    root=ET.fromstring(data)
    for row in root.findall('m:sheetData/m:row',NS):
     index=int(row.attrib['r']);extra={'Q':'Amharic Validation','R':'Afaan Oromo Validation','S':'Source Reconciliation','T':'Mechanical Correction Log'} if index==1 else annotations.get(index,{})
     for col,text in extra.items():
      style=next((c.attrib.get('s','0') for c in row.findall('m:c',NS) if c.attrib['r']=='I'+str(index)),'0');cell=ET.SubElement(row,'{'+NS['m']+'}c',{'r':col+str(index),'t':'inlineStr','s':style});inline=ET.SubElement(cell,'{'+NS['m']+'}is');ET.SubElement(inline,'{'+NS['m']+'}t').text=text
     for col,text in corrections.get(index,{}).items():
      cell=next(c for c in row.findall('m:c',NS) if c.attrib['r']==col+str(index));cell.attrib['t']='inlineStr'
      for child in list(cell):cell.remove(child)
      inline=ET.SubElement(cell,'{'+NS['m']+'}is');ET.SubElement(inline,'{'+NS['m']+'}t').text=exchange.encode(text)
    cols=root.find('m:cols',NS)
    if cols is not None:ET.SubElement(cols,'{'+NS['m']+'}col',{'min':'17','max':'20','width':'48','customWidth':'1'})
    last=max(int(r.attrib['r']) for r in root.findall('m:sheetData/m:row',NS))
    dimension=root.find('m:dimension',NS)
    if dimension is not None:dimension.attrib['ref']='A1:T'+str(last)
    serialized=ET.tostring(root,encoding='unicode')
    for prefix,uri in namespaces.items():
     if prefix and ('xmlns:'+prefix+'=') not in serialized:root.set('xmlns:'+prefix,uri)
    data=ET.tostring(root,encoding='utf-8',xml_declaration=True)
   target.writestr(info,data)

def reconcile(original,output,baseline):
 output=Path(output);output.mkdir(mode=0o700,parents=True,exist_ok=True)
 if Path(original).resolve()==(output/'TeleTena_Translation_Working_Copy.xlsx').resolve():raise ValueError('Working output must never overwrite the supplied workbook')
 if output.resolve().is_relative_to((exchange.ROOT/'frontend').resolve()) or output.resolve().is_relative_to((exchange.ROOT/'tele_tena/public').resolve()):raise ValueError('Review drafts must remain outside public frontend/build trees')
 book=sheets(original);sheet=book['Translations'];rows=sheet['rows'];header=rows[0]
 if [header.get(chr(65+i)) for i in range(len(HEADERS))]!=HEADERS:raise ValueError('Unexpected workbook columns')
 start='\n'.join(v for r in book['Start Here']['rows'] for k,v in r.items() if not k.startswith('_'))
 if baseline not in start:raise ValueError('Workbook Start Here does not declare requested baseline')
 base=json.loads(subprocess.check_output(['git','show',baseline+':localization/catalog.json'],cwd=exchange.ROOT,text=True))
 current=json.loads(exchange.CATALOG.read_text());excluded=json.loads((exchange.DIRECTORY/'extraction-exclusions.json').read_text())
 excluded_values={e['english'] for e in excluded};seen=set();issues=[];delta=[];changes=[];annotations={};corrections={};exports={l:[] for l in LOCALES};by_locale={l:collections.Counter() for l in LOCALES};approved={l:0 for l in LOCALES};approval_audit=[];conflicts={l:collections.defaultdict(list) for l in LOCALES};fatal=[]
 for row in rows[1:]:
  key=row.get('A','');english=values(row,'B');source_hash=row.get('N','');context=row.get('J','');notes=row.get('I','');source_issues=[]
  if key in seen:source_issues.append('duplicate_key')
  seen.add(key)
  if key not in base:source_issues.append('unknown_baseline_key')
  elif base[key]['english']!=english or base[key]['source_hash']!=source_hash or sha(english.encode())!=source_hash:source_issues.append('baseline_source_mismatch')
  if row['_formulas']:source_issues.append('formula_cell_not_allowed')
  if key not in current:
   status='technical_extraction_excluded' if english in excluded_values else 'source_removed_review_required'
   delta.append({'key':key,'kind':status,'english':english,'source_hash':source_hash,'source_location':row.get('M','')})
  elif current[key]['source_hash']!=source_hash or current[key]['english']!=english:
   status='source_changed';source_issues.append(status);delta.append({'key':key,'kind':status,'english':english,'source_hash':source_hash,'source_location':row.get('M','')})
  else:status='source_unchanged'
  if source_issues:fatal.append({'key':key,'issues':source_issues})
  local_issues={};correction_notes=[]
  for locale,(text_col,state_col,reviewer_col) in LOCALES.items():
   value=values(row,text_col);state=row.get(state_col,'');reviewer=row.get(reviewer_col,'');by_locale[locale][state]+=1
   flags=token_issues(english,value,locale,context,notes)
   if state not in STATES:flags.append('unknown_review_state')
   if state=='Approved' and not reviewer.strip():flags.append('approved_without_reviewer')
   if status=='technical_extraction_excluded' and value!=english:
    corrections.setdefault(row['_row'],{})[text_col]=english
    changes.append({'key':key,'locale':locale,'before':value,'after':english,'reason':'Confirmed machine-only extraction; keep literal unchanged in working copy, excluded from runtime translation catalog. Original approval state retained.'})
    correction_notes.append(locale+': restored technical literal in working copy only')
   if value.strip() and status=='source_unchanged':conflicts[locale][english].append((key,value))
   if state=='Approved':
    approved[locale]+=1
    blockers=[f for f in flags if f not in ('clinical_financial_terminology_review','policy_translation_review','outer_whitespace_review')]
    if blockers or source_issues or status!='source_unchanged':flags.append('approved_row_blocked')
    else:
     out={k:current[key].get(k,'') for k in exchange.COLUMNS};out.update(amharic='',afaan_oromo='',review_status='reviewed');out[locale]=value;exports[locale].append(out);approval_audit.append({'key':key,'locale':locale,'reviewer':reviewer,'review_state':state,'workbook_row':row['_row'],'source_hash':source_hash})
   local_issues[locale]=flags
   for flag in flags:issues.append({'key':key,'locale':locale,'issue':flag,'english':english,'review_state':state,'source_location':row.get('M','')})
  annotations[row['_row']]={'Q':'; '.join(local_issues['amharic']),'R':'; '.join(local_issues['afaan_oromo']),'S':status+(' / '+','.join(source_issues) if source_issues else ''),'T':'; '.join(correction_notes)}
 for locale,groups in conflicts.items():
  for english,variants in groups.items():
   if len({value for _,value in variants})>1:
    for key,value in variants:issues.append({'key':key,'locale':locale,'issue':'same_english_fallback_conflict','english':english,'review_state':'See independent locale state','source_location':current.get(key,{}).get('source_location','')})
 for key in sorted(set(current)-seen):delta.append({'key':key,'kind':'new_source','english':current[key]['english'],'source_hash':current[key]['source_hash'],'source_location':current[key]['source_location']})
 missing=set(base)-seen
 if missing:fatal.append({'missing_baseline_keys':sorted(missing)})
 for locale,data in exports.items():write_csv(output/('approved-'+locale+'.csv'),exchange.COLUMNS,data)
 write_csv(output/'issues.csv',['key','locale','issue','english','review_state','source_location'],issues)
 write_csv(output/'source-delta.csv',['key','kind','english','source_hash','source_location'],delta)
 write_csv(output/'correction-log.csv',['key','locale','before','after','reason'],changes)
 working_copy(original,output/'TeleTena_Translation_Working_Copy.xlsx',sheet['path'],annotations,corrections)
 # Prove immutable source columns, attribution and per-locale review states survived.
 checked=sheets(output/'TeleTena_Translation_Working_Copy.xlsx')['Translations']['rows']
 for old,new in zip(rows,checked):
  for col in 'ABDEGHIJKLMNOP':assert old.get(col,'')==new.get(col,''),(old['_row'],col)
  for col in 'CF':assert new.get(col,'')==exchange.encode(corrections[old['_row']][col]) if col in corrections.get(old['_row'],{}) else new.get(col,'')==old.get(col,'')
 report={'workbook_sha256':sha(Path(original).read_bytes()),'baseline_commit':baseline,'current_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=exchange.ROOT,text=True).strip(),'baseline_rows':len(base),'workbook_rows':len(rows)-1,'current_catalog_rows':len(current),'source_delta':dict(collections.Counter(d['kind'] for d in delta)),'locale_states':{k:dict(v) for k,v in by_locale.items()},'approved_rows':approved,'eligible_exports':{k:len(v) for k,v in exports.items()},'issues_by_locale':{l:dict(collections.Counter(i['issue'] for i in issues if i['locale']==l)) for l in LOCALES},'fatal_source_errors':fatal,'mechanical_corrections':len(changes),'human_linguistic_corrections':0,'draft_preview_available':False,'import_performed':False,'approval_gate':'Blocked: no independently approved rows' if not any(approved.values()) else 'Validate per-locale CSV preview before import'}
 (output/'approval-audit.json').write_text(json.dumps({'workbook_sha256':sha(Path(original).read_bytes()),'approvals':approval_audit},ensure_ascii=False,indent=2)+'\n')
 (output/'validation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 for file in output.iterdir():
  if file.is_file():file.chmod(0o600)
 return report

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('workbook',type=Path);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--baseline',required=True);args=parser.parse_args()
 before=sha(args.workbook.read_bytes());report=reconcile(args.workbook,args.output,args.baseline);assert before==sha(args.workbook.read_bytes());print(json.dumps(report,ensure_ascii=False,indent=2));return 1 if report['fatal_source_errors'] else 0
if __name__=='__main__':raise SystemExit(main())
