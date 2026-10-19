# Request Sharing and Presence Follow-Up —19 October 2026

Built source: `cc5886f3a5378bb7964aff1fe9042d495c183ef6`.
Runtime backend change: `ebb76ad560d9e4abb10d1e5664f5c64a563b24c6`;
there are no backend differences between these commits. The later commit corrects
onboarding copy and records browser checks. No schema/dependency/configuration
changes or preference backfills. Draft PR47 retains PR46 ancestry.

Review URL: http://127.0.0.1:8017/teletena/ · site
`teletena-mvp-presentation.localhost` · Bench `/home/frappe/frappe/frappe-bench`
(Frappe15/Python3.12). Scoped web277161, worker277150, scheduler277157 and
loopback queue13917 are running; unrelated Bench services remain untouched.
Backend validation used the separate compatibility Bench's Frappe16.2.1,
ERPNext16.1.0/Python3.14.2 site `teletena-guest-first-test.localhost`.

| Requirement | Result |
|---|---|
| New patients default name/history on | Server onboarding and profile creation defaults; UI proposes both on. Explicit false survives completion and subsequent edits. Existing accounts/drafts keep explicit choices. |
| Remove redundant publication review | Both saved preferences on: Describe → Preferences → Publish, with concise disclosure notice and optional sharing editor. Either off: privacy step remains. |
| Compact offer acceptance | Price/time/format and funding confirmation remain. Both preferences on: sharing editor/preview collapsed; either off: open. Server preview and immutable consent snapshot remain mandatory to the API. |
| Protect record sharing | Request recipients receive request/name only. Text history goes to the selected treating clinician after affirmative acceptance. Individual uploaded files retain explicit selection and scoped grants; no previously owner-only file is auto-broadcast. |
| Requests-page availability | Same shared status/start/pause/setup card as Today, inside Requests & Offers. |
| Preserve enabled intent | `started` is durable intent. Capacity loss and lease expiry no longer clear it. A fresh authenticated heartbeat revalidates capacity before making presence effective again. Manual `paused` remains paused. |

## Checks Actually Run

- Frontend lint passed (existing warnings), production TypeScript/Vite build and
  locked packaged build passed. All41 generated file hashes verified; main URL,
  patient/clinician deep links and release manifest returned HTTP200.
- Four persisted Frappe16 tests passed: new defaults/existing opt-out preservation;
  manual start across lease/capacity loss and pause priority; policy acceptance/no
  implicit role grant; invalid/cross-owner file rejection. Savepoint rollback,
  no external mail.
- Four existing Frappe16 regressions passed: owner-only request details; competing
  private offers/insufficient funds/atomic match; continuous immediate-start grid
  boundary; two patients cannot claim one clinician slot.
- Real backend browser sessions: one separately provisioned fictional patient with
  default-on preferences publishes directly from Preferences; eligible clinician
  sees request and submits private offer; patient opens compact acceptance, edits
  sharing, and cannot accept without sufficient balance. Existing opt-out patient
  still sees Review privacy. The test request was cancelled through its API/UI;
  no funding, booking or provider delivery was performed in this browser check.
- Retained preview read-only browser: patient/clinician1440/768/390, draft/back
  preservation, offer history/deep links, Amharic/Afaan Oromo layout. No main-site
  publication, preferences or funds changed.
- Owner reconciliation: isolated17patient/6clinician owners all balanced; no
  repairs. Main24original private files byte-identical and site settings unchanged.
- Initial browser harness used outdated time-field labels; corrected to actual
  labels before publication. Later cleanup was obscured by the optional tour
  invitation on mobile; dismissed using its real control and resumed the same
  persisted request, without recreating it. Cancellation then passed.

## Rendered Evidence

Visually inspected compact1440/390 offer confirmations and the Requests card;
price, sharing controls and funding action remain readable/reachable. Mobile
confirmation keeps natural scrolling. Reference D03/D05/D09/F02/F03/F04/F14/F15
components are retained; this owner's shorter sharing journey supersedes the
prototype's separate disclosure step. These checks do not imply owner acceptance.

- `screenshots/request-sharing/publish-defaults-1440.png`
- `screenshots/request-sharing/compact-accept-1440.png`
- `screenshots/request-sharing/compact-accept-768.png`
- `screenshots/request-sharing/compact-accept-390.png`
- `screenshots/request-sharing/sharing-editor-390.png`
- `screenshots/request-sharing/clinician-card-1440.png`
- `screenshots/request-workspace/preview/counselor-{1440,768,390}.png`

The scoped browser script is `scripts/browser-request-sharing.cjs`; it requires
private `TELE_TENA_SHARING_EVIDENCE_ROOT` (trailing slash) containing the scenario
and a deliberately provisioned default-on test patient account, plus
`TELE_TENA_REVIEW_SITE_PATH` ending in the named disposable site. It never obtains
codes, enables registration or funds a wallet. Private credentials stay outside Git.

## Limits

Desired availability persists; effective Available still needs a reachable active
session, approved published service, actual feasible capacity and a fresh lease.
Closing the browser does not advertise unattended readiness. Existing opt-outs
are not reset. History-file selection is not replaced by global blanket access.
No new fresh-install/migration, actual200% zoom, hosted-call, physical-device,
live SMS/email or native-language-approval claims are made for this patch; unchanged
prior evidence remains separate. No merge, remote deployment, reseed or money/access
switch changes. Owner visual acceptance remains pending.
