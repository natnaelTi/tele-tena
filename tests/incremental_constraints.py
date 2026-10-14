"""No-provider, no-write file and Ethiopian-number boundary regressions."""
import base64
import io
import os
from pathlib import Path
import sys
import unittest

bench=Path(os.environ['TELE_TENA_TEST_BENCH']);site=os.environ['TELE_TENA_TEST_SITE']
assert site.startswith('teletena-') and site.endswith('.localhost')
os.chdir(bench/'sites');sys.path.insert(0,str(bench/'apps/tele_tena'))
import frappe
frappe.init(site=site);frappe.connect()
from tele_tena.api.history_documents import validated
from tele_tena.api.phone_auth import normalize_phone

class Constraints(unittest.TestCase):
    def test_country_selection_does_not_expand_sms(self):
        self.assertEqual(normalize_phone('0911223344'),'+251911223344')
        self.assertEqual(normalize_phone('+251 911 223344'),'+251911223344')
        for number in ('+12025550123','+447700900123','+254712345678'):
            with self.assertRaises(frappe.ValidationError):normalize_phone(number)
    def test_pdf_and_image_server_constraints(self):
        from frappe.utils.pdf import PdfWriter
        from PIL import Image
        for kind in ('encrypted','scripted'):
            writer=PdfWriter();writer.add_blank_page(width=100,height=100)
            if kind=='encrypted':writer.encrypt('fictional-test-only')
            else:writer.add_js('app.alert("fictional");')
            stream=io.BytesIO();writer.write(stream)
            with self.subTest(kind=kind):
                with self.assertRaises(frappe.ValidationError):validated(kind+'.pdf',base64.b64encode(stream.getvalue()).decode())
        for format,extension in [('JPEG','jpg'),('PNG','png')]:
            stream=io.BytesIO();Image.new('RGB',(8,8)).save(stream,format=format)
            filename,mime,content=validated('fictional.'+extension,base64.b64encode(stream.getvalue()).decode())
            self.assertEqual(content,stream.getvalue());self.assertEqual(mime,'image/'+('jpeg' if extension=='jpg' else 'png'))
            other='png' if extension=='jpg' else 'jpg'
            with self.assertRaises(frappe.ValidationError):validated('mismatch.'+other,base64.b64encode(stream.getvalue()).decode())

if __name__=='__main__':
    try:
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Constraints));sys.exit(0 if result.wasSuccessful() else 1)
    finally:frappe.db.rollback();frappe.destroy()
