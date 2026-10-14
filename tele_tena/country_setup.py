"""Explicit CLI setup; offline country data, no visitor IP sent to a provider."""
from pathlib import Path
import ipaddress
import os
import frappe


def configure(database_path=None,trusted_proxies=None):
    from tele_tena.review import cli
    cli(require_enabled=False)
    database_path=database_path or input('Absolute path to a DB-IP Country MMDB file: ').strip()
    path=Path(database_path).resolve()
    if not path.is_file():raise ValueError('Country database file is unavailable')
    try:import maxminddb
    except ImportError:raise ValueError('The optional MaxMind reader is absent; review its installation separately. No dependencies were installed.') from None
    with maxminddb.open_database(str(path)) as reader:
        if not reader.get('8.8.8.8'):raise ValueError('Country database could not be read')
    raw=trusted_proxies if trusted_proxies is not None else input('Trusted reverse-proxy CIDRs, comma separated; leave empty for direct HTTP: ').strip()
    networks=[str(ipaddress.ip_network(value.strip())) for value in raw.split(',') if value.strip()]
    from frappe.installer import update_site_config
    update_site_config('tele_tena_country_mmdb',str(path))
    update_site_config('tele_tena_country_trusted_proxies',networks)
    return {'configured':True,'site':frappe.local.site,'trusted_proxy_count':len(networks),'visitor_ip_leaves_server':False}
