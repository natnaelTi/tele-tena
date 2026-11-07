# Sprint 1 Runtime Reconciliation — 7 November 2026

Read-only observation of the actual 8017 web and dedicated Operations worker, before
restart/build changes. The process uses retained Frappe15.121.2/ERPNext15.121.6,
Python3.12.3/Node22.23.3; compatibility tests use Frappe16.2.1/Python3.14.2.
The source starts at cf53c4f and served production build at 4e5b126.

## What the Actual Site Loads

Web gunicorn uses `scripts.review_test_wsgi`, main Bench sites; the dedicated RQ
worker and scheduler use `/home/frappe/teletena-mvp-runtime/sites`. Both site/common
configuration sets have **no Operations file binding or inline provider settings**.
The main site's actual API confirmed no ingestion/proof capability. An explicitly
enqueued read-only probe completed on the dedicated worker and independently
confirmed no binding/private configuration, with the same stored flags and build.
This proves that job executed; it is not continuous health or provider connectivity.
Private process/observation evidence is under
`/home/frappe/teletena-operations-proof/sprint2/`, never credential-bearing responses.

The populated `/home/frappe/teletena-operations-config/providers.json` is valid,
private and remains outside Git. It is a separate authorized-test input, **not**
implicitly loaded by a site just because it exists on disk. Preflight reported no
missing/invalid fields. No credential or binding was changed.

Stored revision2: native events enabled; analytics, errors and owner alerts saved
**enabled**, environment **review**; replay/archive saved **disabled**. These are
observations, not toggles performed in this sprint. External providers remain
ineffective because site credentials are absent. Preserve this distinction instead
of claiming every stored switch is off.

| Integration | Site Configuration / Enablement | Last Verified Scope | Running-Site Health |
| --- | --- | --- | --- |
| PostHog | Unconfigured; analytics switch saved on, ineffective | Two bounded synthetic events; native synthetic replay acceptance/provisional export in EU335848 | No current ingestion/readback probe; native delivery outcomes displayed separately |
| Bugsink | Unconfigured; errors switch saved on, ineffective | Five approved synthetic errors, grouping and original source-line resolution | No current ingestion measurement |
| Mobile Alerts | Unconfigured; alerts switch saved on, ineffective | Owner confirmed two Telegram and two amended email receipts | No current live delivery measurement; no more tests sent |
| Replay Archive | No bound project proof/storage activation; capture/export off | V1 settled proof complete; V2 native provisional independent playback passed, settled checkpoint separately pending | Operational90days not established |
| Private Source Maps | Current production-bundle upload unverified | One private synthetic pair resolved original TypeScript line | Historical capability is not current-build mapping proof |

## Corrections

Legacy credential checks were correct for this site but conflated configuration,
activation and verification. Archive/source-map labels were hard-coded regardless
of proof state. Archive status now derives its proof label from the real capability
check. The portal's separate integration projection shows site binding, saved flag,
effective state, observed outcomes and dated historical scope. Source maps truthfully
say **Not Verified for This Build**, with successful isolated capability separately.
No page load performs a provider test. No secret path/DSN/token reaches the API.

## Next Operator Action — Not Performed Here

**First review and disable saved external analytics/errors/alerts/replay/export
switches before binding credentials.** A valid private file alone is not activation
approval; binding it while saved switches are on could activate delivery. Then bind
reviewed configuration through the existing operator workflow, keep production
collection off, satisfy policy/storage/project gates, and obtain separate activation
approval. Provider acceptance remains distinct from receipt. Do not restore provider
automatic alert destinations or run another live test incidentally.

V1 remains closed. V2 retains its one recording and original budgets; do not alter
its timestamps or replay the experiment. See the saved V2 report and exact due-time
resume procedure. UptimeRobot, approved production private storage/backup expiry,
independent alert launcher, recurring backup source and policy/language acceptance
remain separate launch prerequisites.
