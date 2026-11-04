"""Recover missing explicitly selected scope requests; never grants approvals."""
import json
from tele_tena.api.journey import rows
from tele_tena.api.scope_intake import submit_selected_scopes


def execute():
    for application in rows('''SELECT a.user,a.requested_services FROM tt_application a
        JOIN tt_profile p ON p.user=a.user WHERE p.kind='clinician'
        AND a.requested_services IS NOT NULL'''):
        services = json.loads(application.requested_services or '[]')
        if isinstance(services,list):
            submit_selected_scopes(application.user,services,recovery=True)
