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
        "* * * * *": ["tele_tena.api.open_requests.expire_requests", "tele_tena.api.extensions.expire_extensions",
                       "tele_tena.api.vetting.flag_scope_appointments_for_review"],
        "0 * * * *": ["tele_tena.api.presentation.expire_reschedule_proposals"]},
}

# A dedicated namespace only; no catch-all routing or changes to other sites.
page_renderer = ["tele_tena.review_web.ReviewPage"]

# Generic Frappe list and document APIs must enforce the same ownership
# boundary as TeleTena's purpose-built clinic workflows.
permission_query_conditions = {
    "Tele Tena Clinic": "tele_tena.tele_tena.doctype.tele_tena_clinic.tele_tena_clinic.get_permission_query_conditions",
    "Tele Tena Clinic Affiliation": "tele_tena.tele_tena.doctype.tele_tena_clinic_affiliation.tele_tena_clinic_affiliation.get_permission_query_conditions",
    "Tele Tena Clinic Membership": "tele_tena.tele_tena.doctype.tele_tena_clinic_membership.tele_tena_clinic_membership.get_permission_query_conditions",
    "Tele Tena Clinic Encounter Access": "tele_tena.tele_tena.doctype.tele_tena_clinic_encounter_access.tele_tena_clinic_encounter_access.get_permission_query_conditions",
    "Tele Tena Vetting Scope Application": "tele_tena.tele_tena.doctype.tele_tena_vetting_scope_application.tele_tena_vetting_scope_application.get_permission_query_conditions",
    "Tele Tena Scope Evidence": "tele_tena.tele_tena.doctype.tele_tena_scope_evidence.tele_tena_scope_evidence.get_permission_query_conditions",
    "Tele Tena Vetting Appeal": "tele_tena.tele_tena.doctype.tele_tena_vetting_appeal.tele_tena_vetting_appeal.get_permission_query_conditions",
    "Tele Tena Scope Appointment Review": "tele_tena.tele_tena.doctype.tele_tena_scope_appointment_review.tele_tena_scope_appointment_review.get_permission_query_conditions",
}

has_permission = {
    "Tele Tena Clinic": "tele_tena.tele_tena.doctype.tele_tena_clinic.tele_tena_clinic.has_document_permission",
    "Tele Tena Clinic Affiliation": "tele_tena.tele_tena.doctype.tele_tena_clinic_affiliation.tele_tena_clinic_affiliation.has_document_permission",
    "Tele Tena Clinic Membership": "tele_tena.tele_tena.doctype.tele_tena_clinic_membership.tele_tena_clinic_membership.has_document_permission",
    "Tele Tena Clinic Encounter Access": "tele_tena.tele_tena.doctype.tele_tena_clinic_encounter_access.tele_tena_clinic_encounter_access.has_document_permission",
    "Tele Tena Scope Evidence": "tele_tena.tele_tena.doctype.tele_tena_scope_evidence.tele_tena_scope_evidence.has_document_permission",
    "Tele Tena Vetting Appeal": "tele_tena.tele_tena.doctype.tele_tena_vetting_appeal.tele_tena_vetting_appeal.has_document_permission",
    "Tele Tena Scope Appointment Review": "tele_tena.tele_tena.doctype.tele_tena_scope_appointment_review.tele_tena_scope_appointment_review.has_document_permission",
}
