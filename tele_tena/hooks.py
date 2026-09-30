app_name = "tele_tena"
app_title = "Tele-tena"
app_publisher = "Tele-tena"
app_description = "Patient and clinician consultation platform"
app_email = ""
required_apps = ["erpnext"]

after_install = "tele_tena.schema.install"
after_request = ["tele_tena.privacy.no_store"]
