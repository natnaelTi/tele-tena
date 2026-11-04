# Assisted Entry and Direct-Payment Follow-Up — 4 November 2026

Runtime/install pin `0d1a3c37e68f4154f96bb809f6a3b60c11acd567`, branch
`feat/application-tracker-assisted-entry`, draft [PR51](https://github.com/natnaelTi/tele-tena/pull/51)
dependent on PR50. Later documentation/screenshots/review-exchange artifacts do not
change runtime. Local preview http://127.0.0.1:8017/teletena/ on
`teletena-mvp-presentation.localhost`. Nothing remotely deployed or merged.

## Attachment Isolation and Assisted-Entry UX

The reported Selfmade mirroring was **not reproduced on the prior local build**:
CV upload followed by the License section showed zero selected CVs/licenses there.
We therefore do not claim a confirmed diagnosis of that remote instance. The
reusable form did reuse field/component identities across steps. Each evidence
slot now has a stable purpose/credential-row key; the step and assistance case are
also independently keyed. Pending uploads block section navigation/save, avoiding
an attachment callback crossing an active section transition. Existing functional
state updates keep selected ID arrays distinct. Server validation continues to
reject CV IDs in License, Identification or Credential fields; it never infers a
license from a CV or automatically shares one credential's selection with another.
No old evidence is rewritten or deleted to repair a presentation symptom.

The reviewer now sees one editing panel beside numbered section navigation, a
compact expandable applicant/contact/service summary, contextual instructions,
Back, Save Assisted Draft and Save and Continue. Mobile stacks the navigation and
form; keyboard transitions focus the new section heading and preserve normal
scrolling/reduced-motion behavior. Saved values and historical evidence remain.
Recorded email authorization, separate declarations/policy versions and independent
general/scope/language approvals are unchanged.

## Offline Payments and Wallet Disputes

The existing Request Payment Reconciliation command appends a direct-payment
follow-up; it never created a platform wallet-dispute case. Its notifier previously
sent this event only to the patient. It now records system notifications and
idempotent email/SMS outbox rows for **both payer and receiving clinician**, with
preferences, verified-contact/provider availability and caps still enforced.
The clinician gets the existing automatic actionable popup on any workspace page.
External content remains neutral and contains no receipt/private reason/clinical text.

The page explicitly calls this a **Follow Up With the Clinician About Payment** and
explains that it opens no platform wallet dispute or automatic refund. The timeline
labels the durable event Payment Follow-Up Requested. Refund-required/reported/
received states and the original external-payment evidence remain auditable.

In Offline mode, the ordinary reviewer navigation no longer offers Financial
Disputes. The capability projection reports wallet_disputes=false. Direct-payment
appointments never expose the patient wallet-dispute action; the actual wallet
command rejects them server-side even if called manually. The clinician's legacy
`dispute` action is rejected; the direct follow-up uses `reconcile`, not a wallet
adjudication. A stale old client receives a safe rejection and must update.

**Historical wallet obligations are preserved:** a current site-mode change cannot
silently rewrite old transaction rules or prevent resolution of existing holds.
Authorized administrators can use Payment Mode → Review Historical Wallet
Obligations; its deep link is clearly titled Historical Wallet Review in Offline
mode. Original wallet appointments retain their original dispute rules. No new
Offline payment can become a wallet dispute; the direct follow-up does not create
a reviewer case or notify unrelated reviewers. This distinction implements the
owner's latest direction without deleting or stranding earlier wallet obligations.

## Current Verification

| Check | Actual Result |
| --- | --- |
| Application/backend |17 Frappe16 tests pass, including existing owner-selected CV, independent license removal/save/reload, wrong-purpose rejection and retained assisted/typed-response permissions/history |
| Payment boundaries |2 focused Frappe16 tests pass: past appointment/unverified receipt, one follow-up across retry, two system/four external rows, no wallet dispute/journal effect, direct dispute denial, unrelated reviewer receipt denial, Wallet/Offline capability and original wallet rules |
| Retained direct-payment suite |21 pass, including receipt corrections/late proof, retry/ownership, wallet shortfall, couples and no duplicate earnings on finalization |
| Real built attachment browser |CV, License and two credential rows upload independently; remove license without changing CV; remove one credential file without changing sibling; save/reload preserves all; zero page exceptions |
| Complete assisted browser |New email test OTP → request help → separate reviewer → profile/language/CV/license → recorded email authorization → two pending scopes, no inferred approval; passes after layout change |
| Real built expired-payment browser |Retained isolated past unverified receipt → patient follow-up → current timeline acknowledgement → clinician already on Requests gets exact payment-link popup without reload; Offline reviewer menu omits disputes; historical-only deep link remains |
| Native worker |Two system notices; both email rows ProviderAccepted exactly once by private test transport; both SMS rows truthfully Unavailable/zero attempts because these test accounts lack eligible verified SMS delivery. No live receipt claim |
| Visual/keyboard |390/768/1440 screenshots inspected; actual Chromium200%,1440physical/720CSS/DPR2, reduced motion; keyboard section entry/save-and-continue and normal scrolling |
| Build/lint/privacy/localization |Locked production build, lint with pre-existing nonblocking warnings, asset/hash/private credential scan pass;5 exchange +2 extraction tests pass;21-row source delta, full8,758-row exchange; no draft approval/import |
| Finance preservation |Read-only main-site11 patient owners/2 clinician owners/22 accounts; zero projection/obligation/journal mismatches. No migration, schema, settings, balance, password, provider or historical-evidence mutation needed |

Evidence is privately retained at `/home/frappe/teletena-assisted-polish/`.
[Screenshots and before/current comparison](screenshots/assisted-polish/README.md).
Browser mutations are restricted to existing isolated synthetic accounts/receipts
and newly registered test applicants, never the main site's demonstration history.
No scenarios were reset. Native v1.52 upgrade/repeat preservation is inherited from
[the preceding revision](application-workflow-revision-2026-11-04.md); this patch has
no additional schema or package dependencies. Unchanged hosted calls and wider MVP
acceptance reuse their existing evidence rather than claiming a new full-suite run.

## Owner Review / Deployment

1. Reviewer → Applications → Email-Assisted Applications. Check the CV in section2,
   a different license in section3 and separate credential files. Remove one
   selection, switch back, save/reload; other selections must remain unchanged.
2. Offline payment with an expired appointment and unverified receipt: patient
   opens payment → Follow Up With the Clinician About Payment → enter reason →
   Request Payment Reconciliation. Expect a saved follow-up and clinician notice,
   not a reviewer wallet-dispute case. Review actual delivery status/preferences.
3. Reviewer: ordinary Financial Disputes menu is absent in Offline mode. Use the
   explicitly historical link only for earlier wallet obligations. Current direct
   payments remain private to payer/receiving clinician.

Selfmade has not been inspected or changed remotely. Owner retest on its actual
served build remains necessary, particularly for the originally reported mirrored
attachment symptom. Live SMS/email delivery, physical-device calls, native-language
approval and owner visual acceptance are not established by these tests. Existing
local SMTP reachability limitations remain. The new dictionary delta is unreviewed;
no human approval or production localization completion is invented.

Updated incremental installation/backup/recovery procedure:
[selfmade-translation-update.md](selfmade-translation-update.md). Preserve the actual
remote baseline, provider configuration, payment mode, Nginx exception, shared
packages/Amazon patch, files, accounts and balances. Do not reseed or reset passwords.
