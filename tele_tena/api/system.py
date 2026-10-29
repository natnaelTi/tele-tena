"""Minimal authenticated integration check; no clinical or financial data."""
from tele_tena.localization import localized_throw
import frappe
from tele_tena import __version__


@frappe.whitelist()
def status():
    if frappe.session.user == "Guest":
        localized_throw("Authentication required", frappe.PermissionError)
    return {"application": "tele-tena", "version": __version__, "site": frappe.local.site, "user": frappe.session.user}
