"""Private system context for fixed User mutations after command authorization.

Callers must complete the ordinary actor/ownership/approval checks before entering
this context. Never expose it through a whitelisted method or generic DocType API.
"""
from contextlib import contextmanager
from copy import deepcopy
import frappe


@contextmanager
def authorized_user_change():
    original = frappe.session.user
    active_session = frappe.local.session
    session_snapshot = deepcopy(active_session)
    try:
        frappe.set_user('Administrator')
        yield
    finally:
        frappe.set_user(original)
        # frappe.set_user also replaces the active sid and nested session data.
        # Restore those request fields so the browser keeps its authenticated
        # session after this narrowly authorized system-user mutation.
        active_session.clear()
        active_session.update(session_snapshot)
