import unittest
from unittest.mock import patch
from tele_tena import email_delivery,email_templates
class Composition(unittest.TestCase):
 def test_plain_text_has_string_subject_and_branded_html_before_transport(self):
  with patch('tele_tena.email_delivery.configuration',return_value={'sender':'synthetic@example.invalid'}),patch('tele_tena.review.enabled',return_value=False),patch('tele_tena.localization.translate',side_effect=lambda value,locale:value),patch('tele_tena.email_delivery._send') as send:
   email_delivery.send_notice('owner@example.invalid','TeleTena Alert: synthetic verification no real incident. Open your authenticated Operations Overview.')
   self.assertEqual(send.call_count,1);message=send.call_args.args[0];self.assertEqual(str(message['Subject']),'TeleTena Update');self.assertIn('<h1',message.get_payload()[1].get_content());self.assertNotIn('built-in method',message.as_string())
 def test_notice_text_custom_title_and_escape_are_preserved(self):
  with patch('tele_tena.review.enabled',return_value=False),patch('tele_tena.localization.translate',side_effect=lambda value,locale:value):
   html=email_templates.render(email_templates.NoticeText('Safe <body>','Specific Title'));self.assertIn('Specific Title',html);self.assertIn('&lt;body&gt;',html)
if __name__=='__main__':unittest.main()
