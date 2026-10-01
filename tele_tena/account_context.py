"""Private system context for fixed User mutations after command authorization.

Callers must complete the ordinary actor/ownership/approval checks before entering
this context. Never expose it through a whitelisted method or generic DocType API.
"""
from contextlib import contextmanager
import frappe


@contextmanager
def authorized_user_change():
    original = frappe.session.user
    try:
        frappe.set_user('Administrator')
        yield
    finally:
        frappe.set_user(original)
