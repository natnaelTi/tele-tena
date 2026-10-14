"""Best-effort country suggestion. Never authorization or OTP rate-limit identity."""
import ipaddress
from pathlib import Path
import frappe


def client_ip():
    request=getattr(frappe.local,'request',None)
    try:peer=ipaddress.ip_address(getattr(request,'remote_addr',''))
    except ValueError:return None
    try:trusted=[ipaddress.ip_network(value) for value in frappe.conf.get('tele_tena_country_trusted_proxies',[])]
    except ValueError:return None
    def is_trusted(ip):return any(ip in network for network in trusted)
    if is_trusted(peer):
        raw=request.headers.get('X-Forwarded-For','')
        if len(raw)>1024:return None
        try:chain=[ipaddress.ip_address(value.strip()) for value in raw.split(',') if value.strip()]
        except ValueError:return None
        if len(chain)>16:return None
        for hop in reversed(chain):
            if not is_trusted(peer):break
            peer=hop
    return str(peer) if peer.is_global else None


@frappe.whitelist(allow_guest=True)
def suggestion():
    ip=client_ip();country=None
    filename=frappe.conf.get('tele_tena_country_mmdb')
    if ip and filename and Path(filename).is_file():
        try:
            import maxminddb
            with maxminddb.open_database(filename) as database:
                entry=database.get(ip) or {};country=entry.get('country',{}).get('iso_code')
        except Exception:country=None
    if not isinstance(country,str) or len(country)!=2 or not country.isalpha():country=None
    return {'country':country.upper() if country else None,'source':'db-ip' if country else None,'fallback':'ET'}
