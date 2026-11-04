# Request Information Without Approval Evidence

## Cause and Behavior

The reviewer could select Request Information while a credential-verification
checkbox or partially filled scoring/source controls remained set. The backend
then required the approval evidence before it would record that non-approval
outcome. Reproduced against the real Frappe16 database as
`credential_provenance_required`; no live message was sent during reproduction.

Decisions are now handled separately:

- **Approve:** still requires the full mandatory checks, private license evidence,
  verification source/date/reference, complete scores/rationales, current credential
  dates and an independently approved service definition. No approval guard relaxed.
- **Request Information, Reject, Suspend, Expire:** require authorized reviewer,
  reviewable application, a nonempty reason and valid optional restrictions. They
  record the outcome, reason and current private evidence inventory, without
  certifying a credential or an unfinished scored assessment. Approval-only flags,
  source fields and scores from stale clients are not asserted in these decisions.
  Existing assessment history is immutable and not rewritten. The review UI keeps
  unfinished entries while changing the decision and explains what will be recorded.

Request Information persists the existing `Clarification` state and the reviewer's
exact requested-information reason. It produces the existing durable neutral system,
email and SMS notices, with preference/contact/provider/cap and retry protections.
The external message links to authenticated review; private findings are not placed
in SMS/email. Repeated identical notification events do not duplicate channel rows.

Both applicant and generally approved clinician homepages now load their service
follow-ups. A prominent More Information Requested card shows each affected
service, the private reviewer reason and Provide Requested Information. The card
refreshes while visible within15seconds and on focus. Its safe opaque application
reference opens that exact owner-authorized form, scrolls to it and preserves
other applications. The optional reply is saved/reloaded with existing
`applicant_response`; the clinician can upload the requested private evidence and
resubmit. Resubmission returns only that scope to review and removes its follow-up
card; it does not grant service approval. No name/contact/clinical text enters URLs.

Focused regression also found a missing local variable in the new legacy manual
grant notification path: the inserted Service Scope document is now retained before
reading its decision timestamp. Normal approval and legacy grant both pass again.

## Candidate and Verification

Runtime/install pin `83b88149121448c5555735a594460e34916c02ec`, branch
`feat/offline-telebirr-mvp`, draft [PR50](https://github.com/natnaelTi/tele-tena/pull/50)
dependent on PR49. Later evidence/documentation commits contain no runtime changes.
Preview: http://127.0.0.1:8017/teletena/ ; site
`teletena-mvp-presentation.localhost`, Frappe15.121.2/ERPNext15.121.6.

Private logs/fixtures/screens: `/home/frappe/teletena-scope-information-fix/`.

| Check | Actual Result |
| --- | --- |
| Real Frappe16 backend |9 pass:5 retained scope intake/review/permission/preservation tests plus4 focused decision/reply tests; all four non-approval outcomes with missing license/partial verification/scoring; approval denial; blank reason and unauthorized actors denied; notification deduplication; private upload/reply/resubmit without authorization grant |
| New clinician onboarding | Built browser, random private test OTP, private ID/CV/credential but deliberately no license; two separately Submitted scopes, no inferred approval |
| Reviewer → approved clinician handoff | Real independent sessions: general approval; Request Information with missing license, checked credential and partial score; saved Clarification; homepage card appears without reload; exact form link; reply save/reload; license upload; one scope Resubmitted while the other remains Submitted |
| Notification worker | Native isolated subscribed worker processes system/email/SMS decision channels using private mock adapters; once per durable decision key, no live receipt claim. Multiple actual human decisions during debugging retain their separate history |
| Responsive/keyboard |390/768/1440 rendered states inspected; actual200% evidence linked below; reduced motion and normal scrolling preserved |
| Build/localization/privacy | Locked production build and lint pass with existing nonblocking warnings; asset hashes/private credential scan pass;5 exchange and2 extraction tests pass. Ten-row source delta, full8,545-row CSV; reviewed translations unchanged, zero fabricated approvals |
| Local preservation | No schema/dependency/migration/configuration, patient preference, file, password, payment-mode or balance change. Read-only reconciliation:11 patient owners,2 clinician owners,22 accounts, zero projection/obligation/journal errors |

Primary preview services restarted using the scoped lifecycle helper; unrelated
Bench processes remain untouched. All mutated browser fixtures live only in the
retained isolated compatibility clone, not the presentation site's real/test users.
No demo reset, provider change, real transfer, remote deployment or merge occurred.
No fresh installation or unchanged hosted-call suite was repeated: schema and those
modules are unchanged. Current checks exercise changed approval/file/notification
boundaries; wider historical MVP evidence remains in the existing matrix.

## Owner Walkthrough and External Limits

1. Review a submitted scope with missing evidence. Leave partial assessment/source
   values if desired, enter the requested information, choose Request Information
   and Record Human Decision. Expect Saved and Clarification, without license errors.
2. Open that clinician's homepage. Follow More Information Requested → Provide
   Requested Information. Confirm the service and reason, save a reply, reload,
   upload the missing evidence and Submit for Review.
3. Review the resubmission. Approve still refuses missing mandatory evidence/checks.
4. Inspect the bell and Account → Notifications → Email & SMS Delivery Status.
   Disabled preferences, missing verified contacts, caps or provider/network failure
   remain truthful unavailable/uncertain outcomes, not fabricated delivery.

In particular, the previously diagnosed local SMTP connection timeout is an
external delivery limitation; this workflow correction does not repair the mail
server/network or claim inbox receipt. Physical-device calls, native-language
approval and owner visual acceptance remain separate. No new live message was sent.
See [screenshots](screenshots/scope-information/README.md) and the current
[Selfmade incremental guide](selfmade-translation-update.md); migration is unchanged.
