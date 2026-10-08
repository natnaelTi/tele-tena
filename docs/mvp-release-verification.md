# MVP release verification — current bounded release

This is the current release acceptance record. Older per-slice reports remain
preserved and must not be read as a complete current-candidate pass.
Scope: [mvp-release-scope.md](mvp-release-scope.md).
Screen matrix: [mvp-screen-acceptance.json](mvp-screen-acceptance.json).
Status: **not ready for handover**.

## Source and runtime

- Release branch: `feat/mvp-release-handover`, dependent on preserved draft PR #43.
- Behavioral commit checked this batch:
  `42574c4fc3dee4ffc83db709d0f0105b31f08ab9`.
- Current packaged source: inspect `tele_tena/public/review/release.json`;
  documentation-only commits are repackaged from the clean final checkout.
- Preview: `http://127.0.0.1:8017/teletena/`.
- Bench: `/home/frappe/frappe/frappe-bench`.
- Site: `tele-tena-pr12-fresh.localhost`.
- Frontend: production-built assets served by Frappe, no Vite runtime.
- Current web entrypoint: Gunicorn `scripts.review_test_wsgi:application`,
  explicit local site binding, two workers, loopback-only port 8017. This
  entrypoint binds the site/static assets; it does not bypass authentication or
  mock SMS, clinical APIs, funds or LiveKit.
- The previous temporary Werkzeug preview was replaced; only the identified
  port-8017 process was stopped. Original bench web/background processes and
  Selfmade were not restarted or modified.
- Full isolated-site config/database/public/private-file backup completed to
  site-private `backups/20261009_015426-*`. No migrations occurred this batch.

## Checks actually run this batch

| Check | Result and scope |
|---|---|
| All reference screen IDs retained in MVP matrix | Pass: 142 entries, 99 MVP concepts and 43 post-handover; couples included, K/L/M deferred. Counts are not completion percentages |
| `npm --prefix frontend run build` | Pass: TypeScript and Vite; existing >500kB bundle warning remains |
| `npm --prefix frontend run lint` | Exit 0; existing hook/purity warnings remain |
| `scripts/build_review.py` | Pass: exact clean source packaged |
| `scripts/check_review_assets.py --site-private …/private` | Pass before care-query change; final candidate scan rerun recorded below when completed |
| Gunicorn built root/sign-in/discovery deep links | HTTP 200; served manifest matched source commit `6361ee5` before the care-query batch |
| Guest relationship private endpoint | HTTP 403 |
| `scripts/browser-mvp-care-query.cjs` | Pass on actual built app, synthetic existing patient, 390px: landing→password sign-in→discovery; patient-home search; query absent from request URLs, browser history state, localStorage and sessionStorage; clear on sign-out; no funds/record mutation |
| `node --check scripts/browser-mvp-care-query.cjs`, JSON validation and `git diff --check` | Pass |

The initial care-query browser test expected Home after sign-out/sign-in, but
sign-in intentionally returns to the prior safe Discovery route. The assertion
was corrected to accept that route and require the care query to be empty.
No product authorization or state assertion was removed. OTP and new-user
onboarding query continuity are not claimed tested; only their code return path
has changed. Query intent is volatile, deliberately lost on full reload, never
sent to matching/analytics or stored as a patient record. Category interpretation
remains a separate missing behavior; this change is not a natural-language matcher.

## Background-processing gate

Inspection: isolated-site scheduler enabled; one shared worker/scheduler process
is online, started on 2026-10-06. Short/default/long queues were empty at inspection.
These facts do not establish current-code routing/earnings execution. Do not
restart shared services for acceptance. Establish isolated current-code processing
and observe real dispatched jobs before marking that release gate passed.

## Remaining release work

- Two-adult couples participant model, separate consent/disclosure, eligible
  booking/requests, three-person call authorization/End revocation and explicit
  documentation recipients. Relationship links alone do not satisfy this gate.
- Non-diagnostic category suggestions/relevance feedback and care-query continuity
  through enabled-registration OTP and persisted new-user onboarding.
- Current complete booking/request/offer/concurrency, auth/private-file/notes and
  hosted LiveKit regressions; scheduler-driven routing and earning release.
- Fresh installation, representative legacy migration/opening-boundary audit,
  per-owner reconciliation and repeat preservation, without deleting mismatches.
- Approved redesign acceptance for each MVP route/state and requested widths,
  actual 200% zoom, keyboard and all three language layouts; inherited screenshots
  remain historical evidence and do not complete this release matrix.
- Final reviewer walkthrough, private synthetic accounts, exact release PR/SHA,
  environment config and code-plus-data backup/update/rollback instructions.

Live SMS/SMTP receipt, physical devices, native translation approval, medical-lead
catalog/rubric approval, real credential verification, production clinical use,
real-money providers/settlement/ERPNext posting remain separately disclosed gates.
No merge, remote deployment or real external delivery occurred.
