"""Reviewed source dictionary only. Never translate private records."""
import hashlib,json
from functools import lru_cache
from pathlib import Path
@lru_cache(maxsize=1)
def entries():
    return json.loads(Path(__file__).with_name('reviewed.json').read_text())
def translate(english,locale='en',key=None):
    if locale not in ('am','om'):return english
    candidates=[entries().get(key)] if key else entries().values()
    for entry in candidates:
        if entry and entry.get('english')==english and entry.get('source_hash')==hashlib.sha256(english.encode()).hexdigest():
            value=entry.get('amharic' if locale=='am' else 'afaan_oromo')
            if value:return value
    return english


def request_locale():
    import frappe
    request=getattr(frappe.local,'request',None)
    selected=request.headers.get('X-TeleTena-Locale') if request else None
    if selected in ('en','am','om'):return selected
    value=getattr(frappe.local,'lang','en')
    return value if value in ('en','am','om') else 'en'


def localized_throw(message,*args,**kwargs):
    """Localize app-owned error copy; preserve exception type and Frappe behavior."""
    import frappe
    locale=request_locale()
    if isinstance(message,str):message=translate(message,locale)
    if isinstance(kwargs.get('title'),str):kwargs['title']=translate(kwargs['title'],locale)
    return frappe.throw(message,*args,**kwargs)
