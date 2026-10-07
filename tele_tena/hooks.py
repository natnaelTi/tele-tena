app_name = "tele_tena"
app_title = "Tele-tena"
app_publisher = "Tele-tena"
app_description = "Patient and clinician consultation platform"
app_email = ""
required_apps = ["erpnext"]

after_install = "tele_tena.schema.install"
after_request = ["tele_tena.privacy.no_store"]

scheduler_events = {
    "all": ["tele_tena.api.presentation.expire_pending_appointments"],
    "cron": {"*/5 * * * *": ["tele_tena.accounting.release_eligible_earnings"],
        "* * * * *": ["tele_tena.api.open_requests.expire_requests"]},
}

# A dedicated namespace only; no catch-all routing or changes to other sites.
page_renderer = ["tele_tena.review_web.ReviewPage"]

# Generic Frappe list and document APIs must enforce the same ownership
# boundary as TeleTena's purpose-built clinic workflows.
permission_query_conditions = {
    "Tele Tena Clinic": "tele_tena.tele_tena.doctype.tele_tena_clinic.tele_tena_clinic.get_permission_query_conditions",
    "Tele Tena Clinic Affiliation": "tele_tena.tele_tena.doctype.tele_tena_clinic_affiliation.tele_tena_clinic_affiliation.get_permission_query_conditions",
    "Tele Tena Vetting Scope Application": "tele_tena.tele_tena.doctype.tele_tena_vetting_scope_application.tele_tena_vetting_scope_application.get_permission_query_conditions",
}

has_permission = {
    "Tele Tena Clinic": "tele_tena.tele_tena.doctype.tele_tena_clinic.tele_tena_clinic.has_document_permission",
    "Tele Tena Clinic Affiliation": "tele_tena.tele_tena.doctype.tele_tena_clinic_affiliation.tele_tena_clinic_affiliation.has_document_permission",
}
