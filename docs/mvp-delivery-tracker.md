# TeleTena delivery tracker

## Active MVP correction — 2026-10-09

See [current source/build, actual checks and remaining gates](mvp-journey-verification-2026-10-09.md). Patient discovery/booking and retained private-offer acceptance have actual backend browser evidence. Care records now separate equal names across different patients. Reference-specific overview, queue, sharing/payment and earnings compositions are corrected. Full visual acceptance, coherent presentation data, couples, registration-enabled browser acceptance, current hosted calls, job cutover/reconciliation and fresh installation remain open. Earlier entries below are historical evidence for their recorded commits, not a current release pass.

## Current release priority — MVP handover — 2026-10-08

The active branch is `feat/mvp-release-handover`, based on preserved/pushed `feat/adult-relationship-links` at `1e8d161`. The authoritative bounded release scope is `mvp-release-scope.md`; `mvp-screen-acceptance.json` maps all 142 reference screens to 99 MVP screen/state concepts and 43 post-handover concepts. This is scope coverage, not 99 operationally accepted screens. Couples consultations are mandatory and remain missing beyond relationship links. No-show adjudication is deferred by explicit user decision. Critical current-release gaps are scheduler-driven routing/earnings evidence, full fresh/owner-level upgrade verification, non-diagnostic discovery/query continuity, complete couples permissions/calls/documentation and current-source MVP redesign acceptance. The older checkpoints below are historical per-slice evidence. No merge or remote deployment occurred.

## Current local checkpoint — optional adult relationship links — 2026-10-08

The active worktree is `feat/adult-relationship-links`, based on the local
`feat/clinic-shared-calendar` checkpoint at `5c62499`. It adds a patient-only,
mutually consented adult relationship link. The link shares only each party's
chosen display name and grants no appointments, clinical history, notes,
balances, or call access; couple/family appointments and multi-participant
consultations remain pending. The isolated site is
`tele-tena-pr12-fresh.localhost`. Before the additive migration, a full
database/config/file backup completed. Patch v1.30 was applied and invoked
twice to check idempotent table creation. Presentation tests passed 47/47 and
integration tests passed 24/24; the additional reviewer-role denial assertion
also passed in the focused relationship test. The production build and
artifact/privacy scan pass. A built-browser smoke test verified public
invitation routing, policy-aware signed-out copy, patient authentication and
the patient links page at 390 and 1440 px; screenshots are under
`docs/screenshots/adult-relationship-links/`. A two-context Playwright journey on the built app completed invitation, consent, acceptance, alias-limited visibility, and revocation; screenshots are retained. The packaged release manifest identifies the exact source SHA served by the running preview. Fresh-site installation, enabled-registration browser configuration, and 320/768/200%-zoom checks remain pending. The work is in draft PR #43,
stacked on open PR #42 (`feat/clinic-shared-calendar`). Neither PR is merged;
no remote site changed.

## Current local checkpoint — patient-shared clinic calendar — 2026-10-08

The active branch is `feat/clinic-shared-calendar`, in draft PR #42, stacked on
PR #41 → PR #40. PR #42 CI passed on Node 22.23.3/24.13.0 and Python
3.12/3.14.2. The isolated Frappe 15.121.2 review site at
`tele-tena-pr12-fresh.localhost` serves the production-built app at
`http://127.0.0.1:8017/teletena/`; the packaged frontend source SHA is recorded
in `docs/clinic-shared-calendar-verification.md`. Presentation tests passed
45/45, integration tests 24/24, and the built-browser calendar journey passed.
The screen map now records 9 locally verified screens, 78 implemented pending
verification, 51 designed, 3 implementation in progress, and 1 externally
blocked. This slice is read-only patient-shared scheduling; it does not finish
clinic operations or the broader roadmap. Fresh-site/Frappe 16 checks and the
many designed roadmap journeys remain open. No PR was merged and Selfmade was
not changed.


## Current local checkpoint — appointment-scoped acquisition — 2026-10-08

The active feature branch is `feat/relationship-acquisition-attribution`,
stacked on `test/progressive-request-wave-acceptance` (draft PR #38) → PR #37 →
PR #36. Patch v1.26 adds an appointment `acquisition_source`; a valid opaque
clinician-share token is checked again inside the booking transaction. Direct
booking and accepted open requests store their own source values. Existing rows
default to `unknown`; nothing is written to patient profiles. The upgrade was
applied to isolated site `tele-tena-pr12-fresh.localhost` after a successful
site/database/private-files backup, under site maintenance mode, then the site
was returned to service. The migration changed only the additive column.

The focused clinician-link backend test passes, including rejection of a wrong
token, persisted source, same-payload retry, and rejection of a changed-token
retry. The migration repeat/preservation test passes. The complete Frappe
presentation suite passes 42/42 and integration suite passes 24/24 on the
isolated review site. Production assets built for this branch pass the asset
scope scan, and the packaged share-link route test passes. Fresh-site
installation remains pending; no remote site is changed. See
`docs/acquisition-attribution-verification.md`.

## Current local checkpoint — progressive request waves — 2026-10-08

The active branch is `test/progressive-request-wave-acceptance`, stacked on
`fix/open-request-visible-inbox` (draft PR #37), which depends on PR #36. It
adds a persisted-backend regression for the existing progressive dispatcher.
Against the isolated Frappe 15 site, the focused test passed: three manually
approved synthetic clinicians had matching offerings and schedules; one-recipient
waves advanced at test-only delays of 10 and 20 seconds; each wave reached a
distinct clinician; a repeated reconciliation added no duplicate recipients or
notifications. The full Frappe 15 presentation suite passed 41/41 with this
test included. It calls `dispatch_open_requests()` directly, so it does not yet
prove execution through the asynchronous Bench worker or demonstrate a full
clinician-offer-to-completed-consultation journey.

The production-built preview remains `http://127.0.0.1:8017/teletena/` on
`tele-tena-pr12-fresh.localhost`. The release manifest is regenerated from the
current checkout by `scripts/build_review.py`; its source SHA is authoritative.
The site scheduler is enabled. The shared Bench worker and scheduler processes
are running, but this turn has not verified a queued routing or earnings job
on them. Fresh-site install verification remains pending. Existing data and
credentials are preserved.

## Prior checkpoint — rendered immediate-request inbox — 2026-10-08

The active continuation is `fix/open-request-visible-inbox`, based on the
current PR #36 head (`fix/legacy-wallet-projection-audit`). Its focused change
adds a two-browser acceptance check for the clinician's rendered inbox, in
addition to persisted recipient/fetch events. On the built preview at
`http://127.0.0.1:8017/teletena/` (isolated site
`tele-tena-pr12-fresh.localhost`), the patient published an immediate request,
one eligible clinician was recorded, the inbox API and rendered card contained
the request, and the patient's account email was absent. The test cancelled
its synthetic request and restored clinician presence without creating an
offer, appointment, or financial posting. Screenshots are in
`docs/screenshots/open-request-routed/`; the executable journey is
`scripts/browser-open-request-routed-inbox.cjs`.

PR #37 is draft and depends on PR #36. The production asset build,
asset/privacy scan, and two-context browser journey passed; the newer doc-only
checkpoint build SHA and PR #37 CI are recorded below. Fresh-site v1.7/expanded-
catalog verification requested in the broader product checkpoint remains
pending; no fresh-site credentials or successful helper completion are
available at this checkpoint. This verifies only the routed inbox slice, not
offer acceptance or the full A–I scope. Live SMS, physical devices, and
native-language review remain external validation items.

Follow-up verification on this branch: `tests/integration.py` passed 24/24 and
`tests/presentation.py` passed 40/40 on `tele-tena-pr12-fresh.localhost`; PR #37
CI passed both frontend Node versions (22.23.3 and 24.13.0) and Python syntax
checks (3.12 and 3.14.2). The source/build SHA at that run was
`0339c1483043c1e047d1e7f509b67c6bc3a3ebd1`. The active preview returned HTTP
200 from the packaged `/teletena/` route. These backend suites include the
continuous immediate-start boundary, request eligibility, private competing
offers, concurrent acceptance, and payment reservation regressions; they do not
verify the full downstream consultation and earnings journey in two browsers.

## Current local operational checkpoint — legacy finance projection — 2026-10-08

The active checkout is `fix/legacy-wallet-projection-audit` at the current
feature head (the asset manifest is rebuilt after the final commit), based on PR #35's current head
`1d2a65ecfb450d938cb36a82f74fb80e9202e961` and dependent on PR #35/#34. The
preview is again serving `http://127.0.0.1:8017/teletena/` from isolated site
`tele-tena-pr12-fresh.localhost`; production asset manifest source is the
feature commit above. Its `/teletena/` WSGI process was reloaded after building.

The isolated site was backed up before v1.24 and again before v1.25. At each
cutover its scheduler was disabled with no pending jobs and maintenance mode
blocked web writes. The site scheduler was restored afterward; no shared worker
or unrelated Bench service was restarted. v1.24 added 14 exact, journal-proven
completion activity rows; comparison confirmed all 91 pre-existing rows were
unchanged. v1.25 added 3 journal-proven refund rows; comparison confirmed all
105 pre-existing rows were unchanged. Repeated migration and finance snapshot
checks passed. All 9 patient wallets now match their subledger and activity
projection; all journals balance and no unknown event kinds remain. Three
`ReviewRequired` cases remain held pending an authorized decision; the refresh
preserved their earlier evidence and did not auto-accept them. The Review Patient
wallet matches.

The `/admin/financial-disputes` reviewer page now also exposes the authorized
wallet reconciliation queue, recorded balances/evidence, opaque case references,
and a reason-required acceptance action backed by a locked server command. The
queue does not expose patient account identifiers. This action
authorizes continued use of an unchanged wallet/subledger snapshot; it does not
settle or repair the historical difference. Existing held records were not
accepted during UI verification. See `financial-reconciliation-review-ui.md`.

`tests/presentation.py` passes 40/40; `tests/integration.py` passes 24/24.
Production asset secret/scope verification passed. Built-browser review passed
sign-in/out, deep-link reload, private consultation access, PWA scope/cache,
offline fallback, 390/768/1440 layouts, and a controlled update prompt. That
update test simulates a waiting worker; it is not an existing-device PWA update
or physical-device test. Fresh-site install/browser verification remains
pending a disposable database credential setup. The broad approved A–I product
scope remains incomplete; this checkpoint is only the focused finance repair.
See `legacy-wallet-projection-fix.md`.

## Historical note — pre-migration legacy wallet audit — 2026-10-08

The original read-only audit identified the missing legacy `Consumption`
activity row on old consultation finalization. This note predates v1.24; use the
current checkpoint above for migration and preview status.

The owner audit traced a missing legacy `Consumption` activity row on old
consultation finalization. A new completion/refund event is logged in the same
transaction as its balanced subledger journal, and patch v1.24 can append only
historical completion activity proved by the matching immutable earning and
journal. Wallets and old events are not overwritten. Synthetic evidence shows
four owners whose reserved difference matches finalized gross earnings; three
other owners retain an unexplained 600-minor-unit available/reserved residual
each and remain held. See `legacy-wallet-projection-fix.md` for the current
migration result and verification.

The whole approved screen map and batches A–I remain incomplete. This is one
finance correction slice, not full-product acceptance.

## Historical test-fixture checkpoint — before discovery-filter branch — 2026-10-08

The current continuation is `fix/immediate-readiness-window` (exact source
SHA is the current Git head; packaged preview manifest still points to the
preceding frontend-only SHA `5c1a976175f23029f8ee63efc3eaeee5a3383466`). The
production-built preview at `http://127.0.0.1:8017/teletena/` remains on the
isolated `tele-tena-pr12-fresh.localhost` site. `tests/presentation.py` passes
38/38 and `tests/integration.py` passes 24/24. The latter required a test-only
enabled-registration configuration for its SMS/signup cases because the
retained site correctly has phone access disabled; mocked delivery was used,
and no site flags or live provider settings changed. See
`vetting-routing-verification.md` for the correction and fresh-install status.
The packaged browser suite passed guest deep-link redirect, password access,
consultation reload, responsive widths, PWA scope/cache, offline fallback and
the explicit update interaction. Invited-review browser policy also passed.
The wide A–I scope remains partial/pending as shown in the screen-level map;
this verification fix does not change those statuses.

## Current local continuation — immediate request readiness diagnosis — 2026-10-08

The Review Patient’s latest retained immediate request reached `Matched` with
one accepted offer; it was routed to a different eligible clinician. The Review
Clinician had no recipient row. At publication, the clinician's configured
weekly interval began at 08:00 Africa/Addis_Ababa, after the immediate-start
window, so the service could not fit its full duration. This is distinct from
the request-availability toggle. `request-inbox-eligibility.md` supersedes older
notes on this fixture's missing language/policy configuration.

Readiness and publication now use the same site-configurable 5–60 minute start
window (30-minute default). A live but stale presence lease no longer renders
as Available after scope, policy or capacity setup changes make the clinician
ineligible. Patient request summaries include publication-time eligible supply
and explain when no clinician can meet all constraints; scheduling later
prefills the request choices and disclosure instead of broadening requirements.
The focused regression and the Frappe 15 presentation suite pass 38/38 on the
isolated site. Its enabled scheduler and worker logged successful site-qualified
executions of the request expiry/routing reconciler and earnings release
handler. A later real two-context request inside the clinician's immediate
window recorded one eligible recipient, `NotificationEnqueued`, and
`InboxFetched` for the Review Clinician. The last DOM assertion used an
attribute the inbox card does not render, so visible-card acceptance is still
pending; the request was cancelled and presence paused. The patient zero-supply
browser path passes publication → explanation → preserved schedule-later inputs
→ cancellation and persisted-state reread. See
`open-request-no-supply-verification.md` and
`request-inbox-routing-browser-verification.md`. Offer submission/acceptance,
due-wave widening outcome and complete open-request acceptance remain pending.

## Current continuation — owner-scoped transaction details — 2026-10-08

Branch `feat/financial-transaction-details` is a focused dependent slice from
the current PR #31 branch. It adds persisted detail routes for patient payment
activity and clinician earnings/payout entries. The backend derives ownership
from the authenticated account, returns no counterparty/account identifiers,
and uses a generic denial for foreign or unknown references. Patient legacy
simulation rows remain explicitly distinct from balanced subledger journals.
The production frontend build, Python compile, and new Frappe owner/privacy
assertions pass. The initial broad presentation run caught a wallet/subledger
projection mismatch in the new test fixture; its reservation and release now
update both projections together. `tests/presentation.py` then passed 36/36.
Built-browser route acceptance passed for a patient reservation detail and a
clinician released earning, including refresh and generic unknown-record
denial. Patient screenshots at 320/390/768/1440 and clinician screenshots at
390/1440 CSS px are in `docs/screenshots/financial-activity/`. Actual 200% zoom
remains pending, so inventory item G03 stays
`Implemented, verification pending`. See
`docs/financial-activity-verification.md`.

## Current local continuation — private offer review — 2026-10-08

Branch `feat/patient-request-offer-detail` is the head of draft PR #31 and is
based on draft PR #30 (`feat/patient-request-detail-route`, head
`a2f017dc2e5684d9fb9277a6e83c9420e5043808`). Dependency ancestry continues
through PR #29 and #28. No PR is merged. The local review remains
`http://127.0.0.1:8017/teletena/` on site `tele-tena-pr12-fresh.localhost` in
the original Frappe bench's isolated review site; it is production-built, not
Vite. The feature branch's current head is tracked on PR #31; the packaged
asset manifest source is `f9d01703a3e46edbf80fe674f3fd4753256f22b5`. Gunicorn master PID 287561 serves
the current build with worker PIDs 326665 and 326666. The offer review route
uses the owner-scoped `my_request_detail` query
and existing atomic `respond_offer` command. The real browser route showed a
persisted accepted offer, immutable sharing snapshot, total price and
appointment link. Browser coverage does not claim the active-offer acceptance
button was used; direct accept, expired-offer, and no-funds cases through this
new route remain pending. Visual screenshots are under
`docs/screenshots/request-details/`. No migration, reseed, or remote deployment
was performed. The rest of the approved 142-screen and A–I scope remains
incomplete; the per-screen map retains verification-pending/designed statuses.

## Current local continuation — patient request detail — 2026-10-08

The current branch is `feat/patient-request-detail-route` at
`29d267de5f510799f44db9506d91b4412a519a23`. Draft PR #30 targets PR #29's
`feat/request-inbox-eligibility-refresh` branch; #29 is draft and depends on
PR #28. Do not merge this stack independently. The production-built preview is
`http://127.0.0.1:8017/teletena/`, site `tele-tena-pr12-fresh.localhost`, in
`/home/frappe/frappe/frappe-bench`; it is not Vite. Its asset manifest records
frontend source `662d5ec6ae869a568a0105285cd36ad23a03315f`. Backend request
detail code is present from `1a9eeeaa9a83808e4725150aa9e6bdae64354832` and
unchanged since that API addition. The preview is served by Gunicorn master
PID 287561 and its two worker children 323887/323888; the service is bound to
127.0.0.1:8017. No migration, reseed or source change to another bench/site was
performed for this slice.

The patient-owned request detail screen and list/dashboard links are
implemented. Frappe 15 `tests/presentation.py` passed 34/34. The packaged
browser journey passed sign-in, detail route, reload, return to list and list
link navigation, then generic unavailable behavior for an unknown ID. Layout
overflow checks passed at 320/390/768/1440 CSS px, and Amharic/Afaan Oromo
headings rendered. Screenshots and details are in
[`patient-request-detail-verification.md`](patient-request-detail-verification.md).
PR #30 CI passed on Node 22.23.3/24.13.0 and Python syntax 3.12/3.14.2.
The worktree is clean. This route slice does not verify SMS delivery, physical
devices, native-language quality, pilot match performance, earnings release,
or the remainder of approved batches A–I.

## Current local continuation — immediate request reproduction — 2026-10-08

The integrated preview is `http://127.0.0.1:8017/teletena/` on
`tele-tena-pr12-fresh.localhost`, served from `/home/frappe/frappe/frappe-bench`
as a production-built Frappe application. Current branch HEAD is
`31260d6b2c55faab604787e25c6ce894ac21af7e` (documentation and evidence only).
The backend Python implementation loaded by the preview is unchanged from
`9385fe6d4301d8ec3ad8fa8b483223fc86ecb52e`. The readiness UI fix was authored
in `3a532274c184792ce6a93365b826617acb2a5f5b`; the packaged frontend manifest
identifies build source `75ef08be1a726b5515584771668a3120b3dc2500`. The
identified preview Gunicorn master was reloaded after that build. This is not a
Vite preview.

The persisted synthetic Review Clinician setup did not initially meet the
immediate-request rules: no care language was saved, the reviewer-controlled
immediate policy for the legacy review service was off, and the recurring
schedule began at 08:00 Addis time while the reproduction ran at 03:17. After
these were configured through their authorized application workflows and a
temporary date-specific interval was added, a separate patient session
published an immediate request, the clinician received it and submitted a
published-price offer, and the patient accepted. Exactly one appointment and
one ETB 600 reservation were created. The temporary availability override was
removed without changing the original recurrence or the booked appointment.
The clinician workspace now names `no_immediate_capacity` explicitly and links
directly to the availability editor; an authenticated built-browser regression
checks this state in English, Amharic, and Afaan Oromo at responsive widths.
Detailed evidence and screenshots are in
[`vetting-routing-verification.md`](vetting-routing-verification.md).

At this head, the packaged clinician readiness browser regression passes and
the Frappe 15 `tests/presentation.py` suite passes 33/33. GitHub checks on PR
#29 pass for Node 22.23.3 and 24.13.0 plus Python syntax on 3.12 and 3.14.2.
The disposable registration-browser check did not complete on this head: its
named site already exists, and the harness correctly refuses to overwrite it.
The retained site's repeat migration and data fingerprint check passed on the
preceding schema-bearing checkout; a new unique-site installation with both
registration configurations is still required. See the current verification
section in `vetting-routing-verification.md`.

Before schema work on the already-existing isolated
`tele-tena-clinic-access-fresh.localhost`, a full database/config/file backup
was completed. Repeat migration passed twice on the current checkout and
`tests/presentation.py` passed 33/33. The installer correctly refused to
overwrite this existing site, so a fresh installation at this exact head is
still pending. The site-level scheduler flag is enabled and bench-wide
`frappe schedule`/worker processes are running; isolated scheduled-wave and
earnings-release execution is not verified. Broader scope A–I remains
incomplete; see the status matrix and historical checkpoints below.

## Current continuation — scope credential lifecycle — 2026-10-08

Active branch `feat/scope-reverification` is a dependent follow-up to the
vetting reconsideration work. It adds separate, evidence-backed credential
renewal and reviewer-only operational flags for future appointments when a
scope is no longer eligible. The flag cannot reveal patient records or mutate
booking/financial state. Frappe 15 and the separate Frappe 16.2.1 / ERPNext
16.1.0 / Python 3.14.2 compatibility site each passed the 30-case presentation
suite and repeat migration through v1.21; Frappe 16 `pip check` is clean. CI
passed frontend on Node 22 and 24 and Python syntax on 3.12 and 3.14.2. The
packaged `/teletena/admin/vetting` reviewer empty-state rendered without browser
errors; see the screenshot in the verification report. The disposable Frappe 15
site's installed schema and repeat migration were checked, and the production
browser journey passed for registration/onboarding, booking, tours and responsive
screens. A clean-site creation at the final frontend-only commit, Frappe 16
browser verification, populated reviewer queue and isolated scheduler execution
remain pending. The shared review-site scheduler is enabled and one shared-bench
worker is online, but execution of the new hook is unverified. Automatic
date-expiry discovery is not claimed until an isolated worker check passes. This
is still a narrow vetting lifecycle slice; the approved A–I scope and screen
inventory are not complete. See
[`scope-lifecycle-verification.md`](scope-lifecycle-verification.md).

## Current active continuation — consultation extensions — 2026-10-08

The active feature branch is `feat/consultation-extensions`, based on the
private-scope-evidence head and therefore dependent on PR #23. The matching
production-built preview is `http://127.0.0.1:8017/teletena/`, isolated site
`tele-tena-pr12-fresh.localhost` in `/home/frappe/frappe/frappe-bench`.
`tele_tena/public/review/release.json` identifies the packaged frontend source
SHA; this is not a Vite server. The extension backend has passed the 29-case
presentation suite on Frappe 15.121.2 / ERPNext 15.121.6 / Python 3.12.3 and
Frappe 16.2.1 / ERPNext 16.1.0 / Python 3.14.2 after additive v1.17 migration
and repeat migration. The Frappe 16 test site was backed up before migration.
Rendered call-panel browser interaction, fresh-empty-site install for v1.17,
and actual scheduler worker execution are still pending; the retained local
review site's scheduler remains disabled. No hosted site was changed.

## Historical integrated checkout — 2026-10-07

The active local checkout is `feat/mutual-rescheduling`; the exact source SHA
is exposed by the current production asset manifest and the Git branch head.
Draft PR #22
([review](https://github.com/natnaelTi/tele-tena/pull/22)) depends on draft
PR #21 and remains unmerged. The local production-built preview is
`http://127.0.0.1:8017/teletena/`, site
`tele-tena-pr12-fresh.localhost`, from
`/home/frappe/frappe/frappe-bench/apps/tele_tena`; the asset manifest is the
authority for the currently served frontend source SHA. The preview is Frappe
15.121.2 / ERPNext 15.121.6 / Python 3.12.3 and does not use Vite. The original
`erp.localhost` and Selfmade installation were not migrated or changed.

The mutual-rescheduling and availability slice, account composition correction,
and browser-harness diagnostic improvements are in this branch. Focused
Frappe 15 presentation regressions passed 27/27, including the authorized-role
grant session-preservation regression. A separate fresh-site install passed
schema, repeat migration, guest-denial, and disabled-by-default assertions. The
registration-enabled browser journey then passed against that fresh site,
including patient onboarding completion and clinician application entry; the
invited-review mode independently passed with phone access and public signup
disabled. See `mutual-rescheduling-verification.md` for the root cause,
intermediate harness failures, evidence and compatibility limits. The retained
disposable site is `tele-tena-clinic-access-fresh.localhost`; its temporary DBA
credential was removed. The packaging/preview checks remain tied to the source
SHA recorded in `tele_tena/public/review/release.json`, not the backend head.

This is an incremental implementation checkpoint, not completion of batches
A–I or the 142-screen acceptance map. Clinic resources, couples consent, labs,
subscriptions, second opinions, medical tourism, extensions, and several other
contracted workflows remain pending or partial in the per-screen map. The
isolated preview scheduler is disabled; no scheduled routing or earnings
release is claimed from this checkout.

## Current clinic and authentication verification — 2026-10-07

Current branch `feat/clinic-affiliation-review` is a focused dependent slice
on `feat/previous-clinicians`; its latest pushed head is shown by PR #18. The
reviewed backend/product code and packaged frontend source are at
`8e3a298bdc3f2624cdf0fb5d256fc469177fea36`; subsequent branch commits update
tests and verification documents only. This is not the complete
approved A–I product scope. The matching built preview is
`http://127.0.0.1:8017/teletena/`, served from
`/home/frappe/frappe/frappe-bench`, site
`tele-tena-pr12-fresh.localhost`, Frappe 15.121.2 / ERPNext 15.121.6 / Python
3.12.3 / Node 22.23.3. The running backend imported the branch's matching
product code and the production asset manifest records source `8e3a298`; the
app is not served by Vite.
The retained `erp.localhost` site has not been migrated or reseeded. The review
site remains invited-review configuration; phone OTP and public registration
are disabled there.

Clinic registration and clinician affiliation now have persistent native
DocTypes, applicant-owned submission/resubmission, separate human decisions,
audited reasoned transitions, and generic DocType permission checks. A real
Playwright journey against the built Frappe app passed clinician clinic
submission → reviewer verification → clinician affiliation request → separate
reviewer decision. `tests/presentation.py` passed 22/22. The contact-auth
regressions passed 7/7 after separating test configuration from the retained
invited-review site: SMTP configuration and registration policy are mocked
only for that enabled-registration state-machine suite; no mail was sent and
the site's flags were not changed. Screenshots are in
`docs/screenshots/clinic-review/`.

The Frappe integration suite also passed 24/24 after aligning its HTTP origin
with the built port 8017 and replacing stale calls to the retired guest-phone
API with the current `contact_auth` API. The disposable site's phone and public
registration flags were temporarily enabled for that run and restored in
cleanup; the preview is again invited-only. SMS transport was mocked and no
live message was sent.

This is partial clinic onboarding/review, not clinic operations. Memberships,
staff invitations, shared calendars/resources, clinic billing and encounter
grants remain pending. Responsive clinic/admin review, real SMTP/SMS, mobile
devices, native-language review, and Frappe 16 compatibility for this added
schema are not verified. Other A–I scope remains at the per-screen status in
`operational-screen-map.json`; the map is not an implementation claim.

Scheduler status on this disposable site is disabled and no worker is running.
The integration suite covers scheduling/dispatch command behavior but does not
prove queued earnings release or routing executes. Do not demonstrate those
scheduled transitions until an isolated queue and worker are configured; the
shared bench queue must not be drained accidentally.

## Returning-care checkpoint — 2026-10-07

The current dependent branch is `feat/previous-clinicians` at
`fb58ab13815bd3cc16b9e12675c6f6e2474967a1`. Draft PR #17 targets the open
PR #16 branch `feat/teletena-operational-completion` at `503a39df2993cbced46ea067cef97917bac8bcf8`;
neither PR is merged. The patient-home returning-clinician slice is implemented
but Frappe integration and browser verification are pending. PR #17 CI passed
frontend builds on Node 22/24 and Python syntax jobs on Python 3.12/3.14.2.

No valid `/teletena/` preview for this source currently runs. Port 8000 is the
retained Frappe 15 `erp.localhost` bench using its pre-existing checkout; port
8017 is the separate Frappe 16 compatibility test WSGI process at
`/home/frappe/teletena-compat/bench` and is not this branch's matching preview.
Neither service was restarted or migrated. The disposable integration site and
its temporary DB credential are absent. Do not review either URL as this
branch's built application.

## Current implementation checkpoint — 2026-10-07

The active local branch is `feat/teletena-operational-completion` at the PR #15
base commit `3e0965c5fdf6485d945756b382c0a3c008450058`; it preserves PR #14 →
#13 → #12 ancestry. PR #15 is open/draft and has passing frontend/syntax CI but
no executed Frappe integration suite. PR #11 remains open separately. PRs #7–#10
are merged; Selfmade remains unchanged. The WSL Frappe 15 `erp.localhost` site was
backed up before schema work and has not been migrated by this branch.

The expanded approved scope is tracked across A–I in `operational-design-integration.md`.
The 142-screen acceptance map is `operational-screen-map.json`; its status values
are evidence states and are not inferred from a rendered page alone. Current
financial work adds a versioned reconciliation audit/hold; it is not yet run on
a disposable site. The production-built review route has not yet been established
for this source SHA.

Consolidated 2026-10-02: PRs #7, #8, #9 and #10 are merged into `main` at `4cc0be9a0a96c3b209d07b47fd5e7c46ab4c31a2`. The Selfmade site remains pinned to its separately installed commit; merging did not deploy or enable hosted phone access. Earlier PRs #3/#4 are merged through preserved ancestry; PR #5 was superseded. The hosted LiveKit Cloud End/rejoin/cached-token assertions passed with automated two-browser fake-media. Status describes demonstration evidence, not production readiness. Presentation release implementation and verification are tracked in `docs/presentation-readiness-verification.md`; [the next design inventory](design-update-inventory.md) maps every current route and component.

**Status meanings:** `implemented` means code and listed checks cover the
demonstration behavior; `partial` means a narrower slice exists or has a known
validation gap; `pending` means agreed scope is not implemented; `blocked` means
do not release/claim the feature until the stated blocker is resolved.

Hosted review update: site-bound phone OTP, patient registration and clinician
application switches are implemented with a rolling 24-hour site SMS attempt
cap. Frappe's generic public signup remains off; reviewer password login stays
available. SMS Ethiopia account authentication, whitelist, carrier receipt and
actual code verification on the remote server still require the controlled live
test in `selfmade-phone-access-update.md`. Provider acceptance is not delivery.

| Agreed MVP requirement | Status | Evidence / remaining work |
|---|---|---|
| Adults 18+, patient and clinician profiles, private synthetic history, distinct account/disclosure identity | partial | Milestone 1 profiles; phone signup requires an adult attestation, while the attestation is not independent age verification. Existing development accounts continue to work. |
| Phone/email possession codes, expiry, single use, rate/abuse controls and separated onboarding | partial | `contact_auth.py`, `email_delivery.py`, v1_5 migration, 7 contact-auth and 24 integration regressions. SMS/email send adapters are mocked. SMTP and SMS credentials/consenting recipients are not configured or live-tested. Professional evidence intake is narrative only; code proves contact possession, not credential verification. |

| Clinician approval and per-service approval | implemented | Manual approver flow and native Service Scope DocType; PR #2 review verification and MariaDB integration tests. |
| Independent clinicians, clinic affiliations and operational staff memberships without implied record access | partial | Native clinic and affiliation DocTypes retain separate human review; commit `05115ca` adds role-limited invitations, exact verified-email acceptance, revocation audit, generic DocType permissions and an in-workspace portal. `tests/presentation.py` passed 23/23 on Frappe 15.121.2. The built-browser flow passed clinic submission → reviewer verification → manager invite → verified invitee acceptance → reasoned revocation; screenshots are in `docs/screenshots/clinic-membership/`. A temporary synthetic email-verified fixture was removed after the run. Invitations are not emailed. Scheduling/Billing labels have no implemented operations, and Clinic Manager authority is limited to membership administration. Clinic calendars/resources, billing and encounter grants remain pending. The browser checked 320/390/768/1440 CSS px with no horizontal overflow; actual 200% zoom, native-language review, Frappe 16 compatibility and a clean fresh-install run for this addition remain pending. |
| Service definitions, approved clinician offerings, published ETB price and fixed duration | partial | Native Service and Service Scope; scoped publication/discovery/booking and stale-ID regression checks. Multiple named offerings per scope are implemented by v1.23 with idempotent creation/edit, owner/scope enforcement, patient discovery and migration preservation tests (33/33 presentation suite). Broader catalog attributes and clinical taxonomy remain pending. See `multiple-offerings.md`. |
| Natural-language request suggestions, eligible clinician matching, editable filters, relevance feedback; eligibility before ranking | partial | Discovery now filters persisted approved offerings by service, clinician-declared care language, supported format, and server-generated open calendar slots in the next 14 days. The packaged browser check verifies these controls and carries the search text and selected constraints into the private-request draft. See `discovery-filter-verification.md`. Natural-language service suggestions, relevance feedback, and proximity ranking remain absent. |
| Previous clinicians and repeat care discovery | partial | Dependent slice `feat/previous-clinicians` adds a patient-only dashboard query sourced solely from that patient's Completed appointments and currently approved/publicly bookable clinician offerings, plus profile links and loading/empty/error states. The query returns an opaque profile key and never links other patients' masked encounters. Frappe DB permission and browser verification remain pending because the disposable integration site is not provisioned. |
| Private open patient requests and clinician offers, isolated from competing clinicians | partial | Persisted private requests/offers, bounded waves, hard eligibility, owner-scoped history, atomic acceptance and capacity revalidation are implemented. The earlier empty inbox was explained by the Review Clinician's 08:00 Addis interval being outside the immediate window at request publication. A new two-context built-browser journey now verifies the same clinician is a recipient, fetches the inbox, and sees the request card when the full session fits; the patient email is omitted. The synthetic request was cancelled, with no offer or balance change. Frappe presentation tests cover immediate starts between grid boundaries. Scheduler-backed widening, offer acceptance, and full journey to completed consultation/earnings remain pending; the under-three-minute target is not guaranteed. See `request-inbox-eligibility.md` and `request-inbox-routing-browser-verification.md`. |
| Progressive explainable routing, service catalog and clinician vetting | partial | Additive linked native category/approach/topic/format/attribute and per-scope application/assessment DocTypes; catalog remains draft/inactive pending clinical review. Applicant drafts, reviewer assignment, clarification/resubmission, per-scope decisions, private clinician CVs and immutable per-scope private evidence revisions exist. PR #25 adds immutable per-decision reconsideration, with `Upheld` or `Reopened`; the current dependent branch adds a separate credential re-verification application linked to the previously approved scope. Credential expiry is enforced against the configured Frappe site date across service-scope eligibility; fresh private license evidence and a new human decision are required to restore expired-scope eligibility. Rejected renewal evidence does not revoke a still-valid prior credential. Backend presentation suite passes 30/30 on Frappe 15 for this stack. The appeal browser journey is captured in `docs/screenshots/vetting-appeals/`; renewal browser acceptance remains pending. Fresh empty-site v1.19, Frappe 16 migration/browser rerun, verified credential sources, proposed rubric v1.0 approval, jurisdiction-specific expiry policy, full credential/accessibility validation, affiliation verification and transparent eligibility-first ranking remain pending. Structured trust indicators exist but broader browser/metric review remains. See `scope-evidence-storage.md`, `session-experience-metric.md`, `vetting-appeals.md`, and `scope-reverification.md`. |
| Free patient discovery/booking and bring-your-own-patient links | partial | Direct booking and opaque clinician links already share the same authorized slot/price/privacy flow. Patch v1.26 records acquisition per appointment as `direct_booking`, `clinician_share`, or `open_request`; the clinician-link token is revalidated in the atomic booking transaction, and old appointments remain `unknown`. Backend/migration checks are in progress; production-built link booking browser verification and operational referral reporting remain pending. |
| Automatic/manual booking confirmation, slot holds/expiry and mutual rescheduling | partial | Recurring server-generated slots, configurable automatic/manual confirmation, atomic slot/fund holds and 24-hour demonstration expiry/release are implemented and regression tested. This branch adds mutual time proposals with counterpart consent, idempotent retry, generated-slot revalidation, preserved original hold until acceptance, expiry/withdraw/decline and no financial reposting. Frappe presentation regression and the independent patient→clinician→patient packaged-browser acceptance pass. Demo proposal expiry defaults to 48 hours, configurable per site. Fresh-install and full responsive/accessibility acceptance remain pending. |
| Global disclosure defaults, request override and exact per-request preview | implemented | Separate defaults/override, immutable booking snapshot, privacy and profile-edit regression tests. |
| Public review identity separate from account and clinical disclosure identity | partial | No public identity or comments are collected. A patient may submit one 1–5 session-experience rating only after their own encounter is ended and finalized; clinician profiles show a rolling 365-day mean only at five or more responses. Migration/API/browser verification remains pending; free-text comments and moderation are not implemented. See `session-experience-metric.md`. |
| Couples participation with individual consent and optional mutual relationship link | pending | No shared appointment, separate participant permissions, or consent workflow. Payment/partner relationship must not grant record access. |
| Authorized human voice/video, audio-only, mute/camera, Leave and clinician End | partial | Hosted Cloud browser test passed for independent Chromium contexts with fake devices, Leave/rejoin/End and original/refreshed token rejection for both identities, including a departed participant. End test root cause was a stale “Refresh” click after polling; fixed without removing assertions. Human/device testing remains. This remains a demo, not clinical readiness. |
| No recording/transcription by default; no automatic charge/release from connection time | implemented | No recorder/transcriber/agent/automatic extension charge/release path in PR #3; keep this invariant in all call work. |
| Clinician notes, patient-authorized summary, email link to authenticated summary, follow-up booking | partial | Private versioned clinician notes, separately published summary revisions, direct API privacy and same-clinician follow-up booking are implemented/tested. Email notification/link is not implemented. |
| Completed-session ratings/reviews | implemented; focused local verification passed | One immutable 1–5 session-experience response is allowed after clinician finalization; same-rating retry is idempotent, changed retry is rejected, and public aggregates are sample-suppressed separately from clinical competence. `tests/presentation.py` 23/23 and `tests/trust_metrics.py` 4/4 passed; built `/teletena/` patient submission/reload showed one persisted rating and omitted private notes. UI translation-key rendering was fixed in `1e2f8c00f6d354e27f99ac1d924e5476abc4cbe4`. No free-text review/moderation, clinical outcome metric, native translation approval, or real media exchange in this fixture. See `session-experience-metric.md`. |
| Cancellation rules differ by actor; bounded clinician policy, immutable accepted snapshot, disputes/earnings hold | partial | Authorized pre-start cancellation, accepted demo policy snapshot and exact-once full simulated reservation release are implemented. This is one explicit demo policy, not the requested actor-specific production policy or disputes/earnings hold. |
| Simulated patient deposit and atomic available/reserved booking balance | implemented | Labeled development-only simulation, integer minor units, MariaDB atomicity and rollback tests. Not real-money funding. |
| Balanced demonstration subledger, clinician pending/available earnings, authorized extensions and explicit consent/funds reservation | partial | v1.7 adds an immutable balanced demonstration journal distinct from the old `tt_ledger` activity log; booking, explicit finalization, dispute holds, scheduled release, payout reservations, and v1.17 prefunded consent-based extension blocks are implemented. The Frappe 15 suite passes 29/29, including extension reservation, explicit start/finalization exactly once, release on End, scheduled expiry idempotency, and prevention of cancellation during an active call from stranding extension funds. The live call panel still needs rendered-browser acceptance; Frappe 16 and fresh-empty-site migration checks for v1.17 remain pending. This is not ERPNext accounting or real-money readiness. See `consultation-extensions.md`. |
| Simulated payouts and snapshotted withholding | partial | Zero-fee policy and dispute window are captured per booking; release is retry-safe; clinician payout request/cancel reserves/releases available funds exactly once. No external transfer, processing or paid state exists. Post-release refund and dispute workflows are deliberately unsupported pending authorized resolution. |
| Refund unused funds using verified supported route | partial | Demo pre-start release restores simulated balance exactly once; no real refund rails or production refund policy exist. |
| ERPNext accounting/reporting integration and production reconciliation | pending | The demonstration journal has durable references, balance checks and a migration preservation check, but no ERPNext posting, real custody or production reconciliation exists. |
| English, Amharic and Afaan Oromo UI translation | partial | Existing journey keys in all three languages; Amharic/Afaan Oromo strings are provisional and need native review. OTP adds keys under Phase 1. |
| Responsive accessible patient, clinician and administrator journeys/design system | partial | New routes/layouts, original local brand, tokens/components, hosted Playwright 1.63 Chromium and connected booking/onboarding journeys. Synthetic screens captured/inspected at 390/768/1440 plus 320 and 200% zoom; no horizontal overflow. New narrative is partly English in Amharic/Oromo pending translation review. Human device/assistive-tech review remains. |
| Role-specific tours with persisted dismissal/replay and permission-aware steps | implemented | Per-user/role/version progress, patient/clinician/applicant/approver tours, route-safety handling, dismiss persistence, replay, route transitions and missing-target recovery passed API/browser checks; screenshots at 320/390/768/1440 are in `/tmp/tele-tena-presentation-review/`. |
| Presentation release: recurrence scheduling, bookings, lifecycle, notes, detail pages, private resumes, directory, PWA and tours | partial | Existing API/React flows are connected. The availability save defect was reproduced as `start_local`/`end_local` versus API `start`/`end`; focused hotfix is PR #11 (open). The Frappe 16 browser save/reload/booking journey passes again after the fix. Broader layout/e2e work on this branch remains under review; see `presentation-readiness-verification.md`. |
| Production safety/escalation, credential verification, hosting and regulated financial/provider readiness | pending | Product contract marks these unresolved/deferred. Demo uses synthetic accounts/data and is not production clinical readiness. |

## Current delivery and remaining sequence

1. Contact verification and onboarding are implemented. The email OTP state-machine suite passed 7/7 with a mocked provider and enabled-registration fixture; the retained review site remains invitation-only. Live delivery awaits secure local configuration and a consenting recipient. Do not treat codes as SMS/email delivery proof or professional approval.
2. The TeleTena design and focused React journeys are implemented on merged main through PR #6 (`7222836`). This presentation feature branch extends that baseline; its new visual and behavioral evidence is in `docs/presentation-readiness-verification.md`.
3. Discovery, previous clinicians, private requests and offers.
4. Mutual rescheduling, actor-specific production cancellation policy, no-show actions, and production refund rules. This branch adds only an explicit pre-start demonstration cancellation/release policy.
5. Couples consent and sensitive-summary notification/email delivery. This branch adds private notes, separately approved summaries and same-clinician follow-up booking.
6. Ratings, responsiveness, pending earnings, simulated withdrawals and explicitly authorized extensions.
7. Any change to calls must retain LiveKit Cloud revocation, both identity aliases, cutoff/concurrency behavior and the full hosted End regression. PR #3’s source branch remains preserved while consolidation is reviewed.

Demonstration funding is not real-money readiness. `tt_ledger` remains the simulation activity log, while v1.7 `tt_journal` is a separate balanced demonstration subledger; neither is ERPNext posting or settlement. Live SMS, SMTP, credential verification, physical-device call testing and production readiness remain outstanding.

Current release-check note: the additive repeat-migration check now snapshots
the v1.7 account, journal, earning, dispute and payout tables and passed on the
disposable site. The stronger wallet-to-journal reconciliation check exposed a
synthetic seeded patient mismatch after an old loopback test worker had written
legacy events without subledger postings. The records were preserved and no
release claim is based on reconciling that account; a fresh isolated site is
needed for clean financial cutover verification.

### Expanded product scope status (2026-10-07)

| Approved area | Current status | Evidence / remaining work |
|---|---|---|
| Extracted design, React design system, all 142 screens | partial | Existing React flows remain authoritative and the visual tokens now begin moving toward the extracted Inter/blue–teal reference. Screen-level map covers 142 concepts. Most routes still need direct visual and connected interaction review; prototype-only states are not accepted. |
| Clinician vetting and service catalog | partial | Native per-scope applications/decisions, private evidence revisions, expiry/reverification, reconsideration, an immutable proposed rubric registry, digest-bound assessment snapshots, and credential-verification provenance are implemented. On Frappe 15.121.2, `tests/presentation.py` passes 45/45 and `tests/integration.py` 24/24. New credential verification requires source, check date, registry reference, and license evidence from the same scope; applicant and patient API views omit the snapshot. Historical assessments are preserved with provenance blank rather than fabricated. A synthetic applicant/reviewer browser flow rendered provenance controls at 390/1440px without recording a decision. The rubric remains a proposal pending Medical Lead approval; external registry checks, affiliation verification, fresh-install verification and clinical terminology approval remain. This is not Frappe 16 or real-world credential verification evidence. See `vetting-rubric-verification.md`. |
| Open requests, private offers and progressive routing | partial | Persisted request/offer state, hard eligibility, presence leases, bounded waves, owned paginated history, atomic offer acceptance and progress metrics are implemented. Built-browser acceptance verified publication → eligible recipient → clinician inbox API → rendered request card with account email omitted; synthetic request cancelled afterward. Frappe presentation test now directly exercises three due waves with distinct eligible clinicians and retry deduplication. The test-only accelerated timing does not establish production cadence or asynchronous worker execution. Offer submission/acceptance through consultation completion, privacy/abuse audit and pilot performance remain pending. The under-three-minute target is not guaranteed. See `request-inbox-eligibility.md`, `request-inbox-routing-browser-verification.md` and `vetting-routing-verification.md`. |
| Owner-level legacy financial reconciliation | implementation in progress | New v1.13 migration records legacy-event, wallet-snapshot, subledger and exact opening-boundary differences without changing existing records. Mismatched owners are held until an authorized reasoned snapshot decision. Fresh/upgrade/repeat tests on a disposable site remain pending. |
| Extensions and dispute/refund policy | pending | No prefunded explicit extension workflow. Refunds/disputes after release or payout state remain gated for authorized operations; no negative balance or history edits are allowed. |
| Clinic operations and record grants | partial | Verified clinic registration/affiliation and limited memberships are implemented. A patient can grant a clinic scheduling-only access to one future booked encounter and separately grant published summaries from one completed encounter to Care Coordination. The latest clinic-summary browser journey read a persisted patient-authorized summary while omitting private fields; Frappe 15 presentation/integration suites passed 45/45 and 24/24. This branch adds a read-only weekly `/clinic/calendar` projection over the same future schedule grants, with server-validated timezone bounds and role-specific navigation; its Frappe 15 authorization/timezone/privacy regression passes. The built `/teletena/` browser journey and full suites now pass on the retained isolated review site; fresh-site installation/Frappe 16 checks remain pending. Clinic resources, room/shift scheduling, clinic booking, clinic billing, broader staff operations, and broad clinical-record access remain unimplemented; membership alone grants none. See `clinic-encounter-access.md`, `clinic-shared-summary-access.md`, and `clinic-shared-calendar.md`. |
| Adult couples/family care | pending | Separate participant identity, invitations, per-person consent/disclosure, multi-party call permissions and recipient-specific documentation are absent. |
| Laboratory and diagnostics | pending | The v1.12 inactive typed-attribute example is a schema illustration only. Partners, orders, specimen custody, processing, result review/correction/release and integration are absent. |
| Subscriptions | pending | No durable plan entitlements or provider event workflow. Basic records must remain outside any subscription gate. |
| Second opinions and medical travel | pending | No case-sharing, jurisdiction workflow, conditional estimate/proposal or coordination records. |
| Administration and operations | partial | Clinician/scope review, financial disputes and request administration exist in slices. Clinic/lab/metrics/support and scoped financial operations remain. |

Status distinction: “implemented” describes behavior covered by code and listed
checks; “verified” requires the named current-environment run; “external” means
live provider, clinical, legal or partner acceptance is still needed.

## Selfmade review packaging

Deployment packaging and compatible Frappe 16 work were merged through PRs #7–#10.
Selfmade was separately reported installed at `bba5ed9f15bd0b140967618ed2bd982c31a76c1b`;
the operator later reported actual app SHA `8f7ab9cd8d5e779d17b632dc9afdae3e700ab3c6`.
No update is implied by local feature work. The current availability hotfix PR #11 is
open and independent of the wider presentation improvement branch.

### Immediate service policy follow-up (2026-10-08)

The dependent `feat/immediate-service-policy-review` branch adds an approver-
only audit command for enabling or pausing service-level immediate-care policy,
with lifecycle checks, idempotency, rationale, and generic DocType write
protection. On the backed-up Frappe 15 isolated site, v1.22 migration and repeat
migration passed; `tests/presentation.py` passed 31/31. Frontend lint/build
passed (existing lint warnings and bundle-size notice remain). The rendered
packaged reviewer page is captured at
`docs/screenshots/immediate-policy/reviewer-services-1440.png`. The preview's
synthetic Review Clinician data remains unchanged and still has no persisted
care language; its service policy remains off. No successful routed offer is
claimed.

### Service-definition editor checkpoint (2026-10-08)

The reviewer catalog now has its own `/teletena/admin/services` workspace and
server commands over the existing native service and versioned-attribute
DocTypes. Only inactive, unreviewed Draft definitions can be changed there;
keys are stable, type/range/format/workflow rules are allowlisted, and private
or sensitive fields cannot drive public filters or matching. Requesting clinical
terminology review locks the draft; the API cannot approve terminology or
activate a service. The old two-field create form was removed from the service-
scope review screen. The focused Frappe regression passed 1/1 and the full Frappe 15 presentation
suite passed 37/37 on the isolated `tele-tena-pr12-fresh.localhost`. The packaged
reviewer journey passed create/reload/review-lock at 390/768/1440px with no
horizontal overflow. This is not Frappe 16, fresh-install, or full inventory
acceptance. Catalog activation,
medical-lead terminology/source approval, runtime dynamic intake validation and
native-language review remain outstanding. See `service-catalog-data-dictionary.md`, `service-catalog-editor-verification.md`,
and screen I08 in `operational-screen-map.json`.

### Versioned human-led rubric checkpoint (2026-10-08)

On `feat/vetting-rubric-assessment-engine` (dependent on the progressive
routing/acquisition stack), v1.28 adds an append-only proposed rubric registry
with definition digests and a distinct `Tele Tena Medical Lead` role. Reviewers
may propose immutable versions; only a medical lead may approve. Scope
applications pin their version and assessment records snapshot the definition,
digest, scores, rationale and application-scoped evidence revisions. Integrity
failure denies use. The rubric remains proposed until an actual medical lead
review; no score grants scope approval. A site-specific backup preceded the
additive migration on `tele-tena-pr12-fresh.localhost`; first and repeat
migrations passed. Frappe 15 presentation tests pass **44/44** and integration
tests **24/24**. Frontend TypeScript/Vite production build passes; lint exits 0
with existing warnings. The packaged `/teletena/admin/vetting` rubric manager
was opened with the synthetic approver account; the full proposed definition
and digest rendered at 390, 768 and 1440px, and direct access to
`/teletena/admin/rubrics` was denied to that role. Captures are in
`docs/screenshots/vetting-rubric/`. A clean
fresh-site install has not been verified for v1.28. Clinical/credential authority, primary
source verification, translation review and complete product scope remain
external or pending. See `vetting-rubric-v1.md`, and screens I04/I09 in
`operational-screen-map.json`.


## Patient-authorized clinic summary access — 2026-10-08

A new dependent slice on the vetting-rubric branch separates the earlier
scheduling-only grant from a patient-controlled grant for published summaries
of one completed encounter. `Care Coordination` is a distinct clinic membership
role; clinic ownership, management, billing, scheduling, affiliation or general
administrator access do not reveal clinical records. Reads recheck active
membership, verified clinic and treating-clinician affiliation, active grant,
completed appointment and currently published summary revisions. Direct DocType
reads remain denied. Patient revocation closes subsequent reads and preserves
the audit history.

On Frappe 15.121.2, `tests/presentation.py` passes 45/45 and
`tests/integration.py` 24/24 after this addition. The presentation regression
checks patient ownership/consent, idempotent grant, published-summary-only
projection, private-note exclusion, manager/Billing denial, Care Coordination
access, membership/affiliation revocation, and patient revoke. Frontend TypeScript
production build passed; lint exited 0 with existing warnings. Draft PR #41 is
open against PR #40; it is not merged or deployed. The clinic staff
invitation/acceptance and summary-empty-state browser flow passed earlier at
320/390/768/1440 CSS px. On 2026-10-08, the production-built Frappe journey also
passed fresh patient consent → persisted summary grant → a separate Care
Coordination account reading the published summary. Its response omitted
patient identity, contact fields, private notes, request text, and disclosure
data. Screenshots are under `/tmp/tele-tena-clinic-summary-browser/`; earlier
clinic staff screenshots are in `docs/screenshots/clinic-staff-workspace/`.

That browser run exposed and fixed an API projection bug: an active summary
grant intentionally has no expiry, but the patient's grant-history query
compared `None` with the current timestamp. Summary grants now remain Active
without an expiry comparison; scheduling grants still expire normally. The
focused regression and full 45-test presentation and 24-test integration suites
passed on Frappe 15.121.2. The browser harness initially waited for a closed
native select option to become visible; it now waits for the option to be
attached and selects it normally. Clean fresh-site installation and Frappe 16
validation of this addition remain pending.


## Patient-shared clinic calendar — 2026-10-08

The dependent `feat/clinic-shared-calendar` branch builds on draft PR #41, which
itself depends on PR #40. It adds a read-only weekly clinic schedule view over
existing patient-consented future appointment grants. Verified clinic owners,
Clinic Managers and Scheduling members are eligible; Care Coordination,
Billing and unrelated accounts are denied by the calendar query. The query
validates Monday week starts and IANA timezones server-side, uses local-midnight
UTC boundaries for daylight-saving correctness, and returns only disclosure-safe
calendar fields without appointment or grant identifiers. No migration is
needed.

The focused `Presentation.test_patient_clinic_grant_is_scheduling_only_revocable_and_membership_scoped` regression passed on `tele-tena-pr12-fresh.localhost` after adding week filtering, privacy shape, timezone validation, and role-denial assertions. Current branch `feat/clinic-shared-calendar` builds to source `deac339f353b3c5ca1e9042cebbe609cc789d0a4`; the built `/teletena/` browser journey passed, and full Frappe 15 suites passed (45 presentation, 24 integration). Browser coverage includes owner route/API, empty state, week navigation, timezone validation, 320/390/768/1440 widths and patient API denial. The current browser fixture has no shared appointment in its week; populated response privacy and role matrix are covered by backend tests. Screenshot evidence is in `docs/screenshots/clinic-shared-calendar/`. Frontend build passes with the existing large LiveKit bundle warning. Fresh-site/Frappe 16 checks remain pending. The route covers shared appointment viewing only; it is not clinic resource or booking management.


### 9 October — continued connected MVP correction

Current packaged source `0c69dfc2e665deba7208ea39839c766a001a91e6` on PR #44.
Added persisted confirmed/pending booking handoff, request stages, profile booking
panel, own approved-scope offering editor, private offer outcome routes and tour
entries. Actual browser and focused backend results, discrepancies and screenshots
are in [the current verification report](mvp-journey-verification-2026-10-09.md).
Visual acceptance, couples, enabled-registration onboarding, presentation dataset,
scheduler/cutover, fresh/upgrade reconciliation and current hosted-call release
checks remain open. No handover acceptance, merge or remote deployment.

### Documentation continuation — 9 October 2026

Packaged source `a05ed13d53b690939343bc5e1a18ade5b178e54e`, same isolated 8017 preview.
E02/E11/E13 now have paired comparison notes and real persisted documentation
journey evidence. Posting-derived reservation display, finalized document visibility,
unsaved summary preview, revision amendment and cross-appointment draft isolation
are corrected. See the active journey report for actual tests and shared-fixture
test failures. All 99 MVP reference routes have rendered structural mappings; this
is not 99 application acceptance passes. Couples, private-note sharing, clean
presentation data, current scheduler/financial/fresh-install and hosted-call release
checks remain gates. No merge, remote deployment or real-money activation.
