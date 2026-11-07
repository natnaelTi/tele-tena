"""Accessible multipart email composition; no remote assets or private payloads."""
from html import escape
from urllib.parse import urlsplit,urlunsplit
import frappe


class NoticeText(str):
    def __new__(cls, body, title='TeleTena Update', link='', locale='en'):
        obj=super().__new__(cls,body)
        obj.title=title;obj.link=link;obj.locale=locale
        return obj


def secure_link(destination):
    if not destination.startswith(('/patient/','/clinician/','/admin/')):
        raise ValueError('Unsupported authenticated destination')
    url=urlsplit(frappe.utils.get_url('/teletena'+destination))
    local=url.hostname in ('localhost','127.0.0.1') or (url.hostname or '').endswith('.localhost')
    return urlunsplit((url.scheme if local else 'https',url.netloc,url.path,'',''))


def render(body, title=None, link=None, locale=None, code=None):
    from tele_tena.localization import translate
    locale=locale or getattr(body,'locale','en')
    title=title or getattr(body,'title',None)
    if not isinstance(title,str):title='TeleTena Update'
    link=link if link is not None else getattr(body,'link','')
    # Only server-owned internal links enter the email CTA. No auth tokens.
    if link:
        parsed=urlsplit(link);origin=urlsplit(frappe.utils.get_url())
        if parsed.netloc!=origin.netloc or not parsed.path.startswith('/teletena/') or parsed.query or parsed.fragment:
            raise ValueError('Unsupported email destination')
    paragraphs=''.join('<p style="margin:0 0 18px;line-height:1.7">'+escape(part).replace('\n','<br>')+'</p>' for part in str(body).split('\n\n'))
    action=('<p style="margin:26px 0"><a href="'+escape(link,quote=True)+'" style="background:#166b83;color:#fff;border-radius:10px;padding:14px 22px;display:inline-block;text-decoration:none;font-weight:600">'+escape(translate('Open TeleTena',locale))+'</a></p>') if link else ''
    if code is not None:
        action='<p style="font-size:32px;letter-spacing:6px;font-weight:700;background:#eaf5f7;padding:20px;border-radius:12px;text-align:center">'+escape(code)+'</p>'
    from tele_tena.review import enabled
    disclosure=('<p style="margin:0;padding:12px 20px;background:#eaf5f7;color:#285363;font-size:12px">'+escape(translate('Demonstration environment — no real payments or clinical care',locale))+'</p>') if enabled() else ''
    return '''<!doctype html><html lang="'''+escape(locale)+'''"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;background:#eef5f8;color:#16343e;font-family:Inter,Arial,sans-serif"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:24px 12px"><table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px;background:#fff;border:1px solid #dce9ed;border-radius:18px;overflow:hidden">
<tr><td style="background:#103e56;padding:26px 30px;color:#fff"><p style="font-size:25px;font-weight:700;margin:0">TeleTena</p><p style="margin:4px 0 0;font-size:17px">ቴሌ ጤና</p></td></tr>
<tr><td>'''+disclosure+'''</td></tr><tr><td style="padding:30px;overflow-wrap:anywhere;word-break:break-word"><h1 style="font-size:25px;line-height:1.3;margin:0 0 22px">'''+escape(title)+'''</h1>'''+paragraphs+action+'''</td></tr>
<tr><td style="border-top:1px solid #e4edf0;padding:20px 30px;font-size:12px;line-height:1.7;color:#57717e">'''+escape(translate('For your privacy, detailed decisions, documents and consultation information are available only after you sign in.',locale))+'''</td></tr></table></td></tr></table></body></html>'''
