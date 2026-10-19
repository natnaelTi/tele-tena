# Patient Notifications and Booking Follow-up — 19 October 2026

Current runtime and packaged source: `31a77c14c12a74c9b4e4632dad8cac988601836c`.
Later evidence/test-only commits do not change runtime assets. Branch `feat/guest-first-mvp`, draft PR #47, dependent on PR #46. No merge, reseed or remote deployment.

Preview: http://127.0.0.1:8017/teletena/ · site `teletena-mvp-presentation.localhost` · Bench `/home/frappe/frappe/frappe-bench` (Frappe15/Python3.12). Exact separate backend compatibility environment: Frappe16.2.1, ERPNext16.1.0, Python3.14.2, `/home/frappe/teletena-compat/bench`. Node24.13.0 production build. The original source/branches, provider settings and passwords are preserved.

## Behavior and Policy

- One patient bell replaces the navbar Appointment Updates dropdown, including the signed-in public directory. All/Unread, neutral event titles, useful links, durable owner-only read state, retry/empty states, Escape and focus return. Appointment-specific delivery history remains on Appointments.
- Events cover booking decisions, cancellation/expiry, upcoming reminders, call-ended/completion, explicitly shared summary/follow-up and account changes. Internal SystemUpdate events use an allowlisted neutral template; there is no public broadcast endpoint. Historical clinical records are not backfilled into notifications.
- Booking messages use verified contacts and existing private SMS/SMTP adapters, site flags, caps and explicit saved preferences. With no saved preference, operational email/SMS default on; existing opt-outs are preserved. Payer receipts require a real reservation journal and explicitly identify demonstration funds, not external payment collection. Cancellation/expiry receipt wording checks a real release journal.
- New manual-confirmation policy snapshots record a 180-second reminder threshold and a deadline from configured confirmation hours (default24, bounded1–168), capped at scheduled start. One email follow-up is queued after three minutes. Minute scheduling/provider availability means it is not an exact wall-clock delivery promise. No response follows the existing expiry/full reservation release, not a new financial penalty. Old accepted policies/deadlines are unchanged and excluded before batching.
- A separate 90-day/minimum-five-sample Booking Confirmation Response metric counts only actual presented, resolved prompts. A prompt can be acknowledged by the treating clinician's details view, read action, or explicit decision. Responsible decline counts; an unseen expiry is excluded. It does not change clinical competency, ratings, or ranking and is not evidence of provider delivery or human attention merely from enqueueing.
- Stable event keys, existing unique outbox keys, the booking gate and row locks serialize decisions/reminders. Durable Sending claims precede provider I/O. Unknown outcomes are not automatically retried. No clinical text appears in notification bodies or external messages. Couples notices resolve only recipient IDs belonging to independently consenting adults; private notes produce no summary notice.
- Browse by service shortcut navigation removed; service-grouped cards and dynamic filters remain. Shared headings, subtitles and section summaries display owner-requested Title Case without changing stored clinical text, technical enum values, or translation keys.

## Verification Actually Run

Private logs: `/home/frappe/teletena-guest-first/`; no passwords/tokens/provider bodies in reports.

| Check | Result / evidence |
|---|---|
| Complete native backup before v1.42 | DB, public/private archives and config verified; private `before-v142-notifications` |
| Main and F16 existing-site migration; repeat migration | Pass. Empty additive inbox/observation tables; no financial schema or historical backfill |
| Prior fresh-install site's v1.42 migration | Pass; this is an upgrade of the previously fresh site, not a newly performed v1.42 fresh installation |
| `tests/notifications.py` | 10 pass; owner denial/read, consented recipients, receipt channels/cap, explicit retry, Unknown single claim, reminder/decision/expiry idempotency, measured sample threshold |
| `tests/guest_first.py` | 15 pass; real backend public/private separation, disclosure/file permissions, booking intents and outbox |
| `tests/couples.py` | 12 pass; persisted participant/recipient consent, reschedule/extensions, one charge/earning; new recipient-notification assertions |
| Five relevant Presentation regressions | Pass: manual confirmation/cancel/expiry, room-closure/draft/finalize retries, note privacy/revisions, encounter disclosure and cancellation anonymity |
| Actual isolated scheduler/worker | Automatically enqueued/executed process_reminders and dispatch, default/short/long subscriptions, private Redis16480. One follow-up attempt ProviderAccepted using private transport, delivered=false. Controlled observation age181sec; server clock and accepted deadline unchanged. Repeated decline yields one booking journal and one release. Test preferences/schedule restored; owned test processes stopped |
| Real F16 browser notification pane | Pass read persistence after reload, 390/768/1440, Escape/focus, appointment-only delivery area, directory bell |
| Real separate patient/clinician offer browser | Pass actual acceptance → one cross-page popup → persisted read → authorized consultation link. General notices never trigger false accepted-offer popups |
| Main built browser | Pass patient bell/empty pane, Appointments delivery panel, public directory, removed shortcuts; 390/768/1440 |
| Actual Chromium200% | Pass; outer1440, inner720, DPR2, visualViewport.scale1. Pane reachable/scrollable, no horizontal overflow, Escape/focus; sign-out200 then authenticated identity/private inbox denied |
| Build / TypeScript / lint | Production build pass at exact source above; lint passes with warnings, no errors. Existing warning debt remains (including hooks/render purity); not represented as zero warnings |
| Main financial reconciliation | 11 patient owners /8 clinician owners, all journals balanced, no repairs. Isolated site:16 patient /6 clinician owners, all balanced |
| Preservation | Original24 private manifests/provider/key files byte-identical; semantic site config identical. No access-switch/provider credential changes |

Tests that assumed an empty environment were corrected to measure baseline deltas and the relevant owner's/appointment's records. Existing scheduler-created records were retained. The isolated browser404 was a test Gunicorn launch importing the original repository from its initial working directory; launching from the actual compatibility sites directory fixed the mismatch. Acceptance test was corrected to complete the real disclosure/price dialog and select its exact appointment among historical notifications. Logout checks use authenticated-endpoint denial, since Guest cannot call Frappe's authenticated identity endpoint. These were harness fixes, not weakened production guards.

## Rendered Evidence and Comparison

`docs/screenshots/patient-notifications/`: pane1440/768/390, actual200%, Appointments and directory; `disposable-read/` populated private inbox; `disposable-accepted-popup.png` retained clinician popup. Images were opened and inspected: compact unread cards, clear date/actions, readable mobile wrapping, reachable close controls and scrollable populated list. Empty and populated panes use the established shared dialog/button/bell system. Reference H04 governs notification preferences; C02 directory cards and previous paired directory evidence remain applicable. The newly requested universal inbox has no exact static reference screen; this is a documented minimal operational extension, not a claim of pixel identity. Title Case is the owner's explicit updated direction. Accepted call layout and LiveKit security code are unchanged.

Owner visual acceptance remains pending. Live consenting SMS/email delivery, physical-device calling and native Amharic/Afaan Oromo review were not performed. ProviderAccepted is never labeled delivered. Hosted LiveKit End/revocation evidence is reused because those modules did not change; no expensive hosted rerun was claimed.

## Review Walkthrough

1. Open the preview as a patient. Use the bell, All/Unread and Escape; Appointments holds booking delivery history.
2. Make a new booking on the isolated test configuration. Automatic confirmation yields confirmation/reservation messages; manual confirmation yields pending messages and an explicit deadline.
3. Present the pending booking as the clinician. After the three-minute threshold, the scheduler queues one follow-up email. Confirm/decline stops further reminders; expiry retains the accepted policy and releases the reservation once.
4. Finalize an encounter with private notes and optional selected shared recipients. Only consented selected recipients receive neutral update notices; notes never appear in the pane.
5. Confirm the directory still groups cards by service without the shortcut section, and shared headings use Title Case.

Keep draft PR #47 unmerged. The local preview-owned web/worker/scheduler remain running on queue13917. Temporary F16 browser server8029 and test routing/reminder processes are stopped after verification. Selfmade/shared dependency repair/Amazon patch are untouched.
