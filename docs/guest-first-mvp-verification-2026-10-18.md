# Guest-first MVP review —18 October 2026

This is the current **guest-first revision** report. Earlier dated reports retain
historical evidence, not the runtime identity for this preview. The sole acceptance
matrix remains [mvp-screen-acceptance.json](mvp-screen-acceptance.json), under
`guest_first_revision`. Owner acceptance is pending. Nothing was merged or deployed.

## Role-aware navigation follow-up —18October

This follow-up supersedes the earlier guest-card booking labels in the images
below. At runtime checkpoint55432b9, guest/non-patient cards contain only View
profile; the pane and full profile say Sign in to Book and preserve the selected
offering through auth. Authenticated patients retain Choose a time. The root route
waits for the server-verified cookie session and redirects to the existing role
destination; intent never grants another role. Public-page menus now use patient,
clinician/applicant or reviewer links plus the existing Account/Sign out menu.
Horizontal navigation is right aligned; direct-child CSS avoids corrupting the
nested account dropdown. Mobile navigation remains responsive.

`browser-role-navigation.cjs` passed against the real8017 backend:guest cards,
profile/pane actions,selected offering through password sign-in,three-role root
redirect/reload,curated390/768/1440 navigation,Escape/account menu,and authenticated
session invalidation on sign-out. `nav-zoom.log` passed actual browser200% for
guest/patient/clinician/reviewer. Rendered screenshots inspected at
[screenshots/role-navigation](screenshots/role-navigation/). Existing guest journey
browser also passed after its expected controls were updated. Locked production
build and lint pass;no API/schema/dependency/financial change or migration required.
Owner review remains pending;PR47 remains draft.

## Candidate and preview

- Branch `feat/guest-first-mvp`, dependent on PR46's
  `6c7e30ad911d6c4f143e7debed68c200cbbb1227`; PR43–46 ancestry retained.
- Rendered runtime checkpoint: `cd995539be4d4fd583358082f3bb324a8e4b6d94`.
  The final fallback-copy correction displays the actual “Private patient” identity
  for old profiles without an alias;it does not claim an alias will be generated.
  Evidence/documentation descendants are built from a clean checkout. The exact
  installed package identity is `tele_tena/public/review/release.json` (`source_commit`
  and asset SHA256 values); compare it with `git rev-parse HEAD` and preview status.
- Review URL **http://127.0.0.1:8017/teletena/**; site
  `teletena-mvp-presentation.localhost`; bench `/home/frappe/frappe/frappe-bench`.
  This retained local preview is Frappe15/Python3.12, **not** the compatibility bench.
- Compatibility tests use the isolated `/home/frappe/teletena-compat/bench`, exact
  Frappe16.2.1/ERPNext16.1.0/Python3.14.2, Node24.13.0, MariaDB10.6/Redis6.
  Its three explicitly disposable sites are the guest-first test, fresh and
  preservation fixtures. No Selfmade service, shared dependency or Amazon code changed.
- Production-built assets and same-origin cookies/CSRF; no Vite server. Public
  assets are755/644 even under umask077; private manifests remain600. No Nginx
  regeneration or trailing-slash-exception change.

## Implemented behavior

| Requirement | Functional evidence | Visual / owner state |
|---|---|---|
| GF01 public clinicians/services | Guest allowlist, approved published offerings, composable live filters, empty/reset/error states; health-query bar removed | A01/C01/C02 paired; new guest flow supersedes AI search; owner review pending |
| GF02 intent-aware access | New random-code patient onboarding→selected calendar→funding→booking/reload; returning email OTP/password; clinician intent, denied tampering; no account chooser | A04/A05/B01–B05/C06 screenshots; existing clinician B06/B07 completion evidence retained |
| GF03 honest availability | Shared continuous-capacity/presence/calendar projection, expiry/no-calendar/exhaustion/buffers;30s refresh, stale/error state | C02/C04 modal/profile comparison; mobile filter accordion; pulse respects reduced motion |
| GF04 guest request / offers | Memory-only draft→auth→explicit privacy→publish→eligible inbox→offer→shortfall/top-up→one appointment/reservation on retry→authorized preflight; popup/read persistence | D01/D02 condensed into one guest draft; D03/D09/D05 and clinician offer surfaces reuse existing system; actual shortfall and accepted-state screenshots |
| GF05 encounter sharing | New-account alias/text proposals only; explicit file selection; immutable text/file hashes, owner/treating-clinician access; other patients/partners/reviewers denied; audited revocation | B04/C07/H03; file history expandable; no claim that revocation erases earlier disclosure |
| GF06 policies / notices | Separate versioned review acknowledgements, care consent and optional marketing; durable pending/confirmed notices, unknown/rejected/retry handling; both consented adults get neutral individual notices | B05/H06; external notification preferences in Contact & sign-in, updates in the persistent menu |
| GF07 preserved MVP |66 workflow +12 couples regressions, financial owner checks, fresh/repeat migration, real RQ processing; unchanged hosted core evidence reused | Call composition unchanged; earlier paired evidence remains applicable; physical devices/native approval external |
| GF08 invitations | Existing practice links and explicit adult consent invitations preserved; safe return does not supersede an active invitation | Universal Invite expansion intentionally deferred for optional owner decision |

The detailed route/state/API/permission and evidence entries are in the existing
matrix. “Visually verified by Codex” means the named rendered comparison was
inspected with the documented new-flow exceptions; it does not mean owner approval
or an assertion of universal pixel equality.

## Checks actually run

Private raw logs: `/home/frappe/teletena-guest-first/` (directory700). No credentials,
OTPs, provider secrets, private site configs or database backups are committed.

| Check | Actual result / evidence |
|---|---|
| `tests/guest_first.py`, F16 |15/15 pass, `backend-final15.log`; public/private projection, actual reservation conflicts, file grants/revocation, pending/confirmed and uncertain-notice retries; final binary fix included |
| `tests/presentation.py`, F16 |66/66 pass at6574832, `presentation657.log`; persisted workflow, scope/permission, booking/offer concurrency and finance; subsequent backend change limited to binary snapshot copy, covered separately |
| `tests/contact_auth.py`, F16 |8/8 pass at6574832, `contact657.log`; random HMAC/single use, expiry, attempts/resend/rates/provider uncertainty, separate policy acknowledgements and onboarding locale |
| `tests/couples.py`, F16 |12/12 pass, `couples-final.log`; separate consent/recipients, joint reschedule/extension, concurrent single reservation, withdrawal/closure retry, neutral per-adult notices |
| `tests/history_uploads.py`, F16 |4/4 pass, `history657.log`; owner access/quota/type, verified adult onboarding, trusted source handling |
| Browser registration,8029 |Pass `browser-registration-files-fixed2.log`: real random OTP with loopback-only captured test delivery; wrong code/cooldown; resumed onboarding; private image upload→explicit selection→funded persisted booking/grant/download; clinician intent/draft recovery |
| Directory state/browser races |Pass `browser-directory-states2.log`: genuine responses delayed without altering their contents;newer filter wins;real empty/reset;simulated network failure/retry;mobile keyboard accordion preserves fields |
| Existing email OTP / password |Pass `browser-access657.log`, `browser-existing-197ce1c.log`; selected-offering return/reload; professional flow and tampered external return cannot grant roles |
| Invited-review configuration,8030 |Pass `browser-disabled2.log`; empty separate fresh fixture bound to review only for this test; both registrations/delivery methods unavailable, password alternative present; no retained-site policy changes |
| Volatile draft / failed sign-in |Pass `browser-draft.log`: actual wrong-password response;Back restores text;no URL/WebStorage health text;refresh intentionally clears unpublished draft |
| Private request / two-role offer browser,8029 |Pass `browser-offer-latest.log`; real persisted publication, live inbox/private quote, funding shortfall, acceptance/retry, one reservation, preflight authorization, cross-page clinician popup and read persistence |
| PWA |Pass `browser-pwa-latest.log`: existing controlled application retains its current module until explicit Refresh; updated module loaded; only static requests cached; offline page→online recovery. Draft/clinical workflows are protected from automatic update reload |
| Fresh native install / repeat migration |Pass `fresh3.log`: F16 v1.40 schema, ERPNext+TeleTena installed, two repeat migrations, empty new tables, empty guest directory, access defaults disabled; no seed. No DDL/bootstrap changes since that run |
| Existing800 upgrade |Two native migrations pass; `clean-preservation.log`:73 original operational/auth/permission tables,1,292 original rows unchanged on original columns, including passwords, balances and disclosure/consent. New columns/tables additive only |
| Retained presentation preservation |`private-preservation-final.log`:24 original private manifests/provider/key files byte-identical, configuration values identical. Complete before backup includes database, public/private files and private state; no reseed |
| Reconciliation |`reconcile-final-preview.log`:11 patients/8 clinicians; clean upgrade6/5; tested copy16/6, `reconcile-final-journeys.log`. Every owner reconciles and all journals balance; no repairs/deletions |
| Packaging / lint / privacy |Locked Node24 build passes; lint passes with68 existing warnings (not errors); compileall passes;9 review-package tests,8 dependency-checkpoint tests,2 backup/lock tests pass; service-worker static/privacy tests pass. Large-bundle warning retained |
| Staged package graph |`pip-final.log`: no broken requirements. No dependency declarations/lockfiles changed from PR46; completed shared repair not repeated |

Browser scripts are committed under `scripts/browser-guest-*.cjs`. Use installed
Playwright through `NODE_PATH=/home/frappe/teletena-browser-tools/node_modules`.
The OTP adapter is restricted to an explicitly named loopback test site; it mocks
only delivery, not verification/onboarding/booking APIs. After repeated browser
runs exhausted the fixture's default daily send budget, that **mock-only fixture**
used a documented cap100, within the existing configurable range. No rate rows,
code expiry, production limits or retained-site configuration were weakened.
Original fixture configuration is restored when test servers stop.

### Failures investigated rather than hidden

- Valid PNG encounter snapshot failed with a server417: Frappe16 decodes inspected
  bound queries as UTF-8. An ASCII PDF test missed this. `binary-before.log`
  reproduces `UnicodeDecodeError`; `c637893` keeps binary copying inside SQL using
  `INSERT … SELECT` under the existing transaction/owner locks.15 tests and the
  actual new-patient file/book browser pass. Failed attempts retain their owner
  files/funds; no false appointment or partial reservation is manufactured.
- A couples test selected `my_plans()[0]`, which can refer to a different retained
  encounter with the same creation second. It now checks the intended plan ID;
  completion/recipient/one-earning assertions remain unchanged.
- Outbox tests now count the intended appointment's neutral reference, not unrelated
  pending fixture messages. No production dispatch assertion or claim was relaxed.
- Rendered language checks exposed a delayed preference response overwriting an
  explicit selection.7fa63b5 preserves the later user choice. Screenshots now
  require translated headings to remain visible rather than checking overflow alone.
- Early capture failures were test-selector/context mistakes or the expected SMS
  fixture cap. The report names passing runs; failed logs are retained privately.

## Background processing and measurements

Preview has one owned native scheduler/worker, loopback queue Redis13917 and
short/default/long subscriptions. The shared scheduler keeps this site's regular
queue disabled; only the isolated one-site runtime processes it. Original bench
processes were preserved. The start/status tool validates ownership and refuses
conflicting ports rather than killing other processes.

An additional isolated F16 scheduler/worker on16480 **automatically** enqueued and
processed `booking_notifications.dispatch` and request expiry: `job-results.json`.
Five-second scheduler tick is a test-only enqueue cadence; withholding/expiry
policy windows and server clock were unchanged. One notice attempt reached
ProviderAccepted in the private test transport, one booking posting; **no delivery**.
The16480 processes were stopped and the fixture's scheduler setting restored.
Prior native earnings-release/dispute-hold/worker-restart evidence remains in the
existing journey report; this revision does not change accounting or its jobs.

One synthetic immediate-request run recorded publication→first offer102.997229s and
publication→acceptance108.102909s. Both participants had **not joined**: preflight is
not media connection. This is demonstration evidence, not pilot performance. The
metrics API includes open/expired/cancelled unmatched requests, separate3/5-minute
outcomes and booking→both-joined timing. Prepublication guest/auth timing is bounded,
client-reported and separately labelled; it is not dispatch time. No clinical text
is in these metrics. A3–5-minute match requires sufficient eligible available supply,
clinician response and patient choice; it remains an unvalidated target.

## Paired visual evidence and intentional deviations

See [screenshots/guest-first](screenshots/guest-first/). Reference served locally
from `/home/frappe/teletena-design-reference` on8044. Captures use equivalent
viewport dimensions, English and matching route/state; dynamic facts remain truthful.
A01/A04/D01/C02 include390/768/1440; C01/C04/C06/H01/H03/H06 include desktop/mobile.
Actual Chromium200% uses browser zoom (outer1440, inner720, DPR2, viewport scale1),
with CDP viewport captures to avoid Playwright's full-page crop at browser zoom.
Amharic/Ethiopic glyphs and Afaan Oromo wrapping are inspected, not native-approved.

Comparison notes:

- A01 retains the two audience panels, practical hero, brand/fonts and practice
  preview. The care query and concern chips are removed as directed; Find care is
  immediate. Ribbon, language and real registration-policy states remain.
- C02 retains clinician cards and price/action footers. Public navigation replaces
  patient navigation; structured filters occupy Refine your care, collapse before
  results on phones, and never require Apply. No fictional ratings/availability or
  inference/diagnosis explanation is copied from the prototype.
- C02 popup/C04 profile preserve identity, service facts and booking/trust hierarchy.
  Multiple real offerings are selectable; no fictional credential assertions or
  missing feedback statistics are invented. Public-profile gutters were corrected.
- C06 retains calendar beside generated times and contextual clinician/price.
  Explicit language and timezone share one compact row; all hours/dates remain
  server-authorized. A real schedule can supply more times than the prototype;
  the time list scrolls accessibly. No synthetic date buttons are introduced.
- D01/D02 are deliberately condensed into one bounded guest draft; no progress rail
  claims publication before auth/consent. The visible memory-loss/urgent-help notice
  and target wording are new approved states. D03/D09/D05 use real publication and
  offer state. Expired offers do not remain actionable or trigger misleading fallback.
- H03 retains settings/preview columns, alias editing and explicit name/history
  controls. Account-wide file history is expandable; per-booking recipient consent
  remains separate. H06 prototype is a notification feed; current preferences live
  in Contact & sign-in and durable messages in the persistent updates menu. This
  is an operational-placement extension, not a claim that a settings form is a feed.
- B05/policies are clearly review-only. Content versions/acknowledgements work;
  production legal policy content has not been invented or approved.
- Accepted desktop call stage/controls/layout and invitations were not redesigned.

Owner review remains necessary. Screenshots/CI are not owner visual acceptance.

## Reviewer walkthrough / restart

1. Signed out: homepage→Find care. Change service/language/format/availability;
   inspect profile popup, Escape/focus return and full profile. Choose a service.
2. Use an existing fictional patient via email→password. The exact chosen calendar
   opens, including after refresh. Select language/time, review alias/text/files,
   price and balance before confirming. Couples use their separate consent journey.
3. Signed out: Post a private request. Enter only fictional content, choose
   immediate/later preferences. Navigate to auth and back without refresh; the draft
   remains in memory. Refresh intentionally loses an unpublished guest draft.
4. After patient auth, inspect the exact disclosure and publish. In a separate
   approved-clinician session, go available if real capacity permits, respond with a
   private offer, then navigate elsewhere. Patient reviews/funds/accepts; clinician
   sees the existing popup and notification link. No appointment is created by a tour.
5. Confirmed immediate appointments route to preflight only inside their join
   window. Scheduled/pending appointments show their real next step. Existing
   Leave/End/notes/finalization/dispute/earnings rules remain in force.
6. Account→Privacy shows defaults and historical file grants; Contact & sign-in
   controls optional neutral external notices. Revocation is future-access control,
   not erasure of a past disclosure.

Private account details: the existing presentation manifest at
`/home/frappe/frappe/frappe-bench/sites/teletena-mvp-presentation.localhost/private/tele_tena_presentation_accounts.json`,
and the separately named `tt-demo-mvp-v2-accounts.json` beside it for v2 accounts.
Use the matching seed/records manifest to identify roles. Passwords are not printed.
No account was reseeded or had its password replaced.

See [local-preview.md](local-preview.md) for start/status/stop and reboot recovery.
The original bench alone does not launch8017. If offline, establish server status
and direct HTTP first; browser cache clearing is not the service fix.

## External / owner gates

- Owner acceptance of this revised guest journey and its documented visual changes.
- Live SMS/email receipt with configured provider and consenting recipients; API
  acceptance and local transports do not establish delivery. SMS remains Ethiopian
  mobile-only despite the international selector. No live notification was sent.
- Physical-device/network handover/assistive-technology checks and native-language
  review. Existing hosted fake-device End/token evidence is reused for unchanged
  room code, not presented as a new physical-device or automatic-SDK-refresh test.
- Approved production policy content and clinical retention/governance decisions;
  current acknowledgement and snapshot storage are review workflows, not compliance.
- Real clinical care, money custody/settlement and provider activation remain disabled.
  Universal Invite expansion, AI care search and other future modules remain backlog.

Selfmade's actual current commit was **not re-observed** in this local revision.
After owner acceptance, inspect it and prepare an incremental, backed-up, site-only
update preserving the repaired shared environment, Amazon patch, credentials,
demo data and `/teletena` Nginx exception. No remote update commands were executed.

Latest19 October schedule-presence/dropdown/status follow-up: see [current verification](automatic-request-availability-verification-2026-10-19.md). Earlier runtime identities remain historical evidence.
