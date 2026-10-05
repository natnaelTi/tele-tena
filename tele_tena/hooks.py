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
