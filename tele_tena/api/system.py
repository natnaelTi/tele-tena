"""Minimal authenticated integration check; no clinical or financial data."""
import frappe
from tele_tena import __version__


@frappe.whitelist()
def status():
    if frappe.session.user == "Guest":
        frappe.throw("Authentication required", frappe.PermissionError)
    return {"application": "tele-tena", "version": __version__}
