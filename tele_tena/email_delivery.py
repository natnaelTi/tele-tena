"""Bounded direct SMTP delivery; plaintext OTP never enters a persistent queue."""
import json
import smtplib
import ssl
import stat
from email.message import EmailMessage
from pathlib import Path

import frappe


class DeliveryUnavailable(Exception):
    pass


def configuration():
    path = Path(frappe.get_site_path('private', 'tele_tena_email.json'))
    if path.is_symlink() or not path.is_file() or stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise DeliveryUnavailable('email_not_configured')
    try:
        value = json.loads(path.read_text())
        assert value['host'] and value['sender'] and value['username'] and value['password']
        assert value['port'] in (465, 587)
        assert all('\n' not in value[k] and '\r' not in value[k] for k in ('host', 'sender', 'username'))
        return value
    except Exception:
        raise DeliveryUnavailable('email_not_configured') from None


def send_code(destination, code):
    settings = configuration()
    message = EmailMessage()
    message['From'] = settings['sender']
    message['To'] = destination
    message['Subject'] = 'Your TeleTena verification code'
    message.set_content(f'Your TeleTena code is {code}. It expires in 5 minutes. Never share it. If you did not request this code, ignore this email.')
    context = ssl.create_default_context()
    try:
        if settings['port'] == 465:
            client = smtplib.SMTP_SSL(settings['host'], 465, timeout=10, context=context)
        else:
            client = smtplib.SMTP(settings['host'], 587, timeout=10)
        with client:
            if settings['port'] == 587:
                client.ehlo()
                client.starttls(context=context)
                client.ehlo()
            client.login(settings['username'], settings['password'])
            rejected = client.send_message(message)
            if rejected:
                raise DeliveryUnavailable('email_rejected')
    except Exception:
        # No exception chaining: SMTP exceptions may contain message/credential context.
        raise DeliveryUnavailable('email_delivery_uncertain') from None
