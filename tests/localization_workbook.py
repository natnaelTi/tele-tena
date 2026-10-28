"""Synthetic workbook approvals only; never imports production dictionaries."""
import csv,io,hashlib,json,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as E
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/localization'))
import workbook as w
class Workbook(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.old=w.exchange.ROOT,w.exchange.DIRECTORY,w.exchange.CATALOG;w.exchange.ROOT=self.root;w.exchange.DIRECTORY=self.root;w.exchange.CATALOG=self.root/'catalog.json';(self.root/'extraction-exclusions.json').write_text('[]');self.baseline='0'*40
  self.row=dict(A='home',B='Home',C='መነሻ',D='Approved',E='Synthetic Test Reviewer',F='Mana',G='Draft',H='',I='',J='Navigation',K='Standard',L='[]',M='fixture.tsx:1',N=w.sha(b'Home'),O='provisional',P='')
  self.current={'home':{'key':'home','english':'Home','source_hash':w.sha(b'Home'),'context':'Navigation','source_location':'fixture.tsx:1','placeholders':'[]'}};w.exchange.CATALOG.write_text(json.dumps(self.current))
 def tearDown(self):w.exchange.ROOT,w.exchange.DIRECTORY,w.exchange.CATALOG=self.old;self.tmp.cleanup()
 def book(self):
  self.path=self.root/'input.xlsx';ns=w.NS['m'];rows=[{chr(65+i):h for i,h in enumerate(w.HEADERS)},self.row]
  def xml(data):
   root=E.Element('{'+ns+'}worksheet');sheet=E.SubElement(root,'{'+ns+'}sheetData')
   for i,values in enumerate(data,1):
    row=E.SubElement(sheet,'{'+ns+'}row',{'r':str(i)})
    for col,value in values.items():
     c=E.SubElement(row,'{'+ns+'}c',{'r':col+str(i),'t':'inlineStr'});E.SubElement(E.SubElement(c,'{'+ns+'}is'),'{'+ns+'}t').text=value
   return E.tostring(root)
  with zipfile.ZipFile(self.path,'w') as z:
   z.writestr('xl/workbook.xml','<workbook xmlns="'+ns+'" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Start Here" sheetId="1" r:id="r1"/><sheet name="Translations" sheetId="2" r:id="r2"/></sheets></workbook>');z.writestr('xl/_rels/workbook.xml.rels','<Relationships><Relationship Id="r1" Target="worksheets/sheet1.xml"/><Relationship Id="r2" Target="worksheets/sheet2.xml"/></Relationships>');z.writestr('xl/worksheets/sheet1.xml',xml([{'A':self.baseline}]));z.writestr('xl/worksheets/sheet2.xml',xml(rows))
 def runbook(self):
  self.book();before=self.path.read_bytes()
  with patch.object(w.subprocess,'check_output',side_effect=lambda args,**kw:json.dumps(self.current) if 'show' in args else self.baseline):report=w.reconcile(self.path,self.root/'out',self.baseline)
  self.assertEqual(self.path.read_bytes(),before);return report
 def test_independent_locale_approval_and_existing_preview(self):
  result=self.runbook();self.assertEqual(result['eligible_exports'],{'amharic':1,'afaan_oromo':0})
  exported=list(csv.DictReader(io.StringIO((self.root/'out/approved-amharic.csv').read_text())));self.assertEqual(exported[0]['amharic'],'መነሻ');self.assertEqual(exported[0]['afaan_oromo'],'');self.assertFalse(w.exchange.preview(self.root/'out/approved-amharic.csv')['errors']);self.assertFalse((self.root/'reviewed.json').exists())
 def test_oromo_approval_does_not_import_amharic_draft(self):
  self.row.update(D='Draft',E='',G='Approved',H='Synthetic Oromo Test Reviewer');r=self.runbook();self.assertEqual(r['eligible_exports'],{'amharic':0,'afaan_oromo':1});rows=list(csv.DictReader(io.StringIO((self.root/'out/approved-afaan_oromo.csv').read_text())));self.assertEqual(rows[0]['amharic'],'');self.assertEqual(rows[0]['afaan_oromo'],'Mana')
 def test_original_workbook_cannot_be_output_target(self):
  self.book();original=self.root/'TeleTena_Translation_Working_Copy.xlsx';self.path.rename(original);before=original.read_bytes()
  with self.assertRaises(ValueError):w.reconcile(original,self.root,self.baseline)
  self.assertEqual(original.read_bytes(),before)
 def test_draft_and_missing_attribution_cannot_become_approved(self):
  self.row['D']='Draft';self.row['E']='';r=self.runbook();self.assertEqual(r['eligible_exports']['amharic'],0)
  self.row['D']='Approved';r=self.runbook();self.assertEqual(r['eligible_exports']['amharic'],0)
 def test_source_changes_and_placeholder_multiplicity_are_blocked(self):
  self.row['N']='bad';r=self.runbook();self.assertTrue(r['fatal_source_errors']);self.assertEqual(r['eligible_exports']['amharic'],0)
  self.assertIn('placeholder_identity_or_multiplicity',w.token_issues('Hello {name} {name}','መልእክት {name}','amharic','UI',''))
 def test_tokens_numbers_markup_and_locale_alerts(self):
  cases=[('Use5 MB','Use10 MB','numeric_limits_or_formatting_changed'),('Open https://example.invalid','ክፈት','url_mismatch'),('<b>Care</b>','ክብካቤ','markup_mismatch')]
  for source,value,issue in cases:self.assertIn(issue,w.token_issues(source,value,'amharic','UI',''))
 def test_working_copy_preserves_review_states_and_namespace_compatibility(self):
  self.runbook();out=w.sheets(self.root/'out/TeleTena_Translation_Working_Copy.xlsx')['Translations']['rows'][1];self.assertEqual(out['D'],'Approved');self.assertEqual(out['G'],'Draft');self.assertIn('Q',out);self.assertEqual(out['N'],self.row['N'])
if __name__=='__main__':unittest.main()
