"""Native configuration authorization shared by command and generic document APIs."""
from tele_tena.localization import localized_throw
import hashlib
import frappe


def approver():
    if frappe.session.user != 'Administrator' and 'Tele Tena Approver' not in frappe.get_roles():
        localized_throw('Approver required', frappe.PermissionError)


def scope_name(clinician, service):
    return hashlib.sha256((clinician + '\0' + service).encode()).hexdigest()
