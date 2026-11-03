# Communications — Rendered Evidence

Runtime `02ed9209589732e9d4e3e3750c07c49592c2a327`. Synthetic accounts only.

- [Application notification](application-notification.png): submission/review acknowledgement in the existing bell/dialog composition. Applicants now have the same bell; review decisions stay separate.
- [Delivery settings, mobile](delivery-mobile.png): verified contacts and truthful per-channel delivery states using existing Account grouping; normal scrolling retained. Fixed help/navigation/popup elements can appear at viewport boundaries in a full-page capture.
- [Branded email, desktop](email-desktop.png) / [mobile](email-mobile.png): neutral acknowledgement, secure CTA, demonstration ribbon, privacy footer, no remote/tracking assets. Browser render, not physical mail-client receipt testing.
- [Clinician notifications, actual200%](clinician-notifications-200-percent.png):1440physical/720CSSpx, DPR2, visualViewport1; dialog scrolling and controls remain accessible.

Codex inspected contrast, hierarchy, card/button treatment, text wrapping and
scrolling against the established TeleTena shared settings/dialog language. Owner
visual acceptance remains pending. Private captures at390/768/1440 and zoom plus
logs are outside Git in `/home/frappe/teletena-communications-release/`.
Earlier screenshots/reports remain the before evidence; no historical evidence was
rewritten. This change adds delivery diagnostics/email composition rather than
redesigning the accepted workspace. The test provider accepts messages; it does not
establish real email/SMS delivery or human localization approval.
