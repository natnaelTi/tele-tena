# Guest-First MVP Release Readiness —20 October 2026

**Incremental package prepared for operator deployment, subject to the target
preflight/maintenance checkpoints below.** This is not owner visual acceptance,
remote deployment, real clinical readiness or real-money activation. PR47 and its
PR46 dependency remain draft/open; neither was merged.

## Immutable Candidate and Environments

- Install/build **`d8f11c8c8b16148c8b68e42320e847a13106c299`**, branch
  `feat/guest-first-mvp`, [PR47](https://github.com/natnaelTi/tele-tena/pull/47).
  PR46 base/head `6c7e30ad911d6c4f143e7debed68c200cbbb1227` is an ancestor,
  as are800a591,deeb583 and earlier PR43–45 work. Later guide/matrix/evidence
  commits change documentation only. No automatic merge/deployment.
- Current packaged app contains41 SHA256-verified files. Manifest:
  [releases/guest-first-mvp-2026-10-20.json](releases/guest-first-mvp-2026-10-20.json).
  `release.json` SHA256: `d9f7e8d4d4e36b406d6f5330a52a5ac28793d12b6275c4640cbd6a0ed0e5cdfb`.
  Frontend lock: `a5f7a16b739627b44fcb73fb348f6c71a7974a55fec90a0d3c3caa4d6345e696`.
  No wheels/database/private manifests need transfer: fetch source, build locked
  assets on target. Private dependency reports remain local/operator backup data.
- Retained preview **http://127.0.0.1:8017/teletena/**,
  `teletena-mvp-presentation.localhost`, Bench `/home/frappe/frappe/frappe-bench`:
  Frappe15.121.2/ERPNext15.121.6/Python3.12.3. Web277161, worker277150,
  scheduler277157 and loopback Redis13917 remain running. These Python services
  were started at ebb76ad; their application/backend code is byte-identical to
  this candidate. Current packaged source is the candidate above, not Vite.
- Separate compatibility Bench `/home/frappe/teletena-compat/bench`:
  Frappe16.2.1 `8f6e24728b86b7c6427908ed6536289a41ea9cf4`, ERPNext16.1.0
  `bb2bada1fde0ae7a3c3cad32bed781ebd470e27d`, Python3.14.2, Node24.13.0,
  MariaDB10.6.22 and Redis6.0.16. Guarded clean trial environment:
  `/home/frappe/teletena-shared-repair/trial-env`. Distinct from the retained preview.
- Native app version remains **0.1.0**, schema through
  **`v1_42_patient_notifications`**. A package version is not the schema/build ID.

## Delta From Previously Prepared deeb583

No `pyproject.toml`, `frontend/package.json` or frontend-lock change. All existing
repaired Python package versions/direct/editable identities are protected.

| Area | Additive change / preserved rule |
|---|---|
| v1.40 | Nullable `tt_profile.care_alias`; empty policy acceptance, encounter file grant/event, notification preference and booking-outbox tables. No historic preference/file/financial backfill. |
| v1.41 | `tt_schedule.auto_requests` default0; presence `control_mode` defaultmanual. Fresh connected workspace lease remains required; manual pause wins. |
| v1.42 | Empty owner notification inbox and booking-confirmation observation tables. No historical scoring inference. |
| APIs/UI | Allowlisted public service groups/filters/profiles; role/intent-led auth returns; calendar/readiness; consolidated Requests; compact Account/photo crop; neutral notifications and request/offer handoff. |
| New patient defaults | Name/text-history enabled only for new patients unless explicitly disabled. Existing stored choices remain. Individual history files require selection; immutable encounter consent and server validation remain. |
| Notices | Durable idempotent queue. One email reminder after180seconds for newly snapshotted manual-confirmation policy; cancellation follows accepted expiry, not an invented three-minute cancellation. ProviderAccepted is not delivery. Confirmation response is separate from competence/ranking. |
| Configuration | No migration enables signup, provider, automation, funding or real-money settings. Existing service/booking/dispute policy snapshots remain authoritative. No Amazon/shared-framework/Nginx changes. |

Local preparation added **tests and a read-only CLI preservation helper only**;
application code/assets are unchanged from the completed1451902 checkpoint.
The helper hashes original row columns and private/config files while writers
are stopped; it never prints/exports row contents. Missing/mismatched snapshots
fail closed. It does not repair finances or change permissions.

## Candidate Checks and Evidence

Private local execution logs: `/home/frappe/teletena-release-20261020/` (mode700).
No credentials/dumps/provider settings are committed.

| Gate | Actual result | Evidence |
|---|---|---|
| Latest combined fresh schema | Passed native Frappe+ERPNext+TeleTena fresh install, all v1.39–v1.42 logs/structures, empty wallets/journals/grants/notices, disabled default access/funding. Two native repeat migrations preserve69tables/686rows/two config/private files. No seed. | `fresh2.log`, `fresh-repeat.log`; fresh site `teletena-guest-release142b.localhost` retained for isolated checks |
| Existing installation / repeat upgrade | Full existing-install upgrade and repeat migration passed. A newly restored original800a591 backup ran v1.39,v1.40,v1.41,v1.42 and a second migration:61original operational/auth/native tables,1,225original rows and six protected private/config files unchanged on original columns; historical LegacyHold remains1. The previously upgraded v1.40 clone separately preserved67tables/1,225rows. | `original-upgrade.log`, `restore-original.log`; `teletena-guest-release-upgrade.localhost` is restored from the verified original800a591 backup, without seeding. Auxiliary `upgrade.log` covers the previously upgraded clone. |
| Owner financial reconciliation | Upgrade clone:6patient/5clinician owners pass; presentation:11patient/8clinician owners pass; journals balanced, no repairs. Historical holds untouched. | `preview-reconciliation.log`, populated clone check; warning about aborted temporary fixture below |
| Dependency guard | Actual app-only editable dry-run/install/verify passed in isolated repaired environment; every other package version/direct/editable identity preserved; pip check clean. Eight install/update/replacement/source-identity unit tests pass. | `dependency-check.log`, `dependency-plan.json`, `dependency-install.log`, `pip-check.log`; `tests/dependency_checkpoint.py` |
| Backups / checkpoint | Native DB/public/private/config backup and named-archive checks pass. Missing/empty/corrupt required archive tests pass. Preservation helper snapshot/verify passes; deliberately tampered digest fails without data edits. | `backup.log`, `backup-tests.log`, protected checkpoint files; helpers documented in update guide |
| Discovery, files, presence, notifications |17persisted guest-first checks plus10notification checks pass: public projection/eligibility, calendar/capacity/lease distinction/manual pause, file owner/grant/revocation/snapshot isolation, new defaults/existing opt-outs, pending-vs-confirmed, reminder deduplication, expiry/release once, read authorization, provider failure/unknown outcome/caps. | `guest-notifications-final.log`:27passed |
| Auth / abuse controls | Eight persisted contact-auth tests pass: private onboarding/resume, explicit opt-out recovery, non-enumeration, single use, attempts/expiry, racing verification, uncertain delivery, role injection and existing account. | `contact-auth-final.log`:8passed |
| Booking, request acceptance, call documentation, finance/couples | Nine selected individual/request/finance regressions plus12couples tests pass: private competing offers, shortfall/idempotent acceptance, continuous immediate start, concurrent slot claim, End/closure-before-finalize, note isolation/revisions, dispute/release and payout races; couples consent/invite/withdrawal, recipient isolation, joint reschedule/extension and one earning. Provider call operations mocked here. | `consultations-finance-final.log`:21passed |
| Actual background processing | Isolated native scheduler/worker on Redis16480/default,short,long automatically executed reminder+dispatch and request expiry; earnings-release job has current execution metadata. A real pending booking produced exactly one ProviderAccepted reminder/attempt after controlled181-second observation aging. Decline retry produced one booking and one release journal. No direct reminder/dispatch invocation in this check. | `scheduled-result.log`, private worker/scheduler logs; completed20October; original test scheduler config restored and task processes stopped |
| Real backend registration | New patient via random SMS test code → wrong-code/cooldown → persisted interrupted onboarding/defaults/policies → exact offering → explicit file selection → supported demo funding → one reserved booking. Guest draft memory safety and clinician intent/application-draft recovery pass. Separate freshly installed invited-review configuration blocks signup/delivery but keeps password choice. | `registration-browser-final.log`, `disabled-browser-final.log`; test transport only, no live providers |
| Built browser / PWA | Frappe16 and retained preview guest → filters/profile → existing password sign-in → exact calendar + reload;390/768/1440. Actual current SW control/static-only caches/offline fallback/online recovery pass. | `guest-browser.log`, `preview-browser.log`, `pwa-current.log` |
| Production artifact | Locked production build/TypeScript, lint (existing warnings), all41hashes, namespace/deep links and credential scan pass. No new framework/source/dependency changes. | `pinned-build.log`, `lint.log`, `assets.log`; manifest linked above |
| Presentation preservation | Original24private manifests/provider/key files byte-identical; config values unchanged. No presentation-site seed, password reset, funds/preferences change or migration for this packaging task. | `preview-preservation.log` |

Fresh installation initially stopped because an empty root password caused Frappe
to prompt in a noninteractive process. Retried with the **existing private isolated
DB administrator**, not new production/root authentication. Successful native
installation is the `142b` site. Both browser configurations were deliberately
set only on the named disposable sites and restored byte-for-byte afterward.

### QA Fixture Warning — Not a Production Reconciliation Repair

The first combined run overlapped two suites against the **same disposable
fixture database**, producing a teardown deadlock and a subsequent duplicate
fixture-user setup error. The sequential rerun passes all21checks. That aborted
teardown left one `tt-test-*` clinician with a requested payout/postings but no
earning row (owner hash `72d8ac00db`). Full disposable-site owner reconciliation
therefore correctly fails for that temporary fixture. Its records/logs are
preserved; no balances, entries or discrepancies were erased/repaired to pass.
The retained presentation site and independent populated migration clone both
reconcile. This QA artifact is not present in either release-preservation source,
is not seeded/transferred by the update, and is not evidence of a production
migration defect. Do not cite full disposable-site owner reconciliation as passed.
Future fixture suites sharing that DB must run sequentially.

Two older expectations were corrected, with assertions retained:20-row dispatch
batches must account for older queued notices, and private-history opt-out tests
must explicitly opt out now that new-patient sharing defaults are on. New default-on
tests independently cover the changed behavior. No production guard was weakened.

## Reused Unchanged Evidence — Not Reclaimed as New Testing

- The full two-role publication → offer → shortfall/top-up → acceptance/reload,
  one reservation, cross-owner denial and current appointment outcomes:
  [request-workspace verification](request-workspace-verification-2026-10-19.md).
  New shorter sharing path and Requests availability card:
  [sharing/presence verification](request-sharing-presence-verification-2026-10-19.md).
- Hosted LiveKit original/refreshed-token rejection, participant/rejoin/End and
  three-participant consented media are historical fake-device/real-hosted-media
  evidence cited in [MVP journey report](mvp-journey-verification-2026-10-09.md),
  including9d148b5/22373e4. No call security/media changes in this release-prep pass;
  targeted21backend regressions above cover changed integration boundaries.
  **The full hosted suite was not rerun in this pass.**
- Policy-timed pending→released earnings, dispute hold and worker-restart recovery
  from the earlier continuous-processing MVP evidence remain applicable to the
  unchanged accounting engine. Current scheduled execution and direct race tests
  are separate evidence, not a new claim of a full fresh timed release scenario.
- The real18October existing-controlled-browser update prompt/explicit activation
  evidence remains valid for unchanged SW logic. Current offline/recovery was
  retested; an artificial older-version asset swap was not made on the owner's
  active preview merely to repeat it.
- Rendered reference/application and actual200%zoom comparisons for accepted
  Account, directory, Requests, calendar, notification and consultation refinements
  remain in their19October reports/screenshots. No accepted screen was redesigned.
  Current source-only release does not claim new owner visual acceptance.

## Acceptance Matrix Reconciliation

The only matrix is [mvp-screen-acceptance.json](mvp-screen-acceptance.json), now
with a dated release gate overlay. Historic pending flags retain their historical
meaning; latest evidence below supersedes them for the identified gates:

- Fresh latest-combined schema: **closed locally** by native v1.42 fresh+repeat checks.
- Existing-record/credential/file/financial preservation: **closed on the named
  representative upgrade and presentation sites**, with the QA warning above.
- New-patient browser registration and clinician intent/recovery: **closed for
  private test transport**; full human vetting chain remains prior persisted evidence.
- Couples permission/notes/extensions/rescheduling: **functionally verified** by
  current12tests; hosted media evidence inherited, physical devices pending.
- Background notification/reminder jobs: **current scheduler/worker execution
  verified**. Current pending-earning release mechanics reuse earlier timed/worker
  recovery evidence plus current execution/race checks.
- Visual: unchanged accepted behavior preserved; owner acceptance remains separate.
  No historical screenshot is presented as newly accepted by the owner.

## Operator Dependencies and External Limits

No known application-code defect blocking this **incremental package** was found.
Deployment is conditional on [the exact update guide](selfmade-guest-first-mvp-update.md):
actual remote SHA/worktree/versions, clean repaired package guard, loaded service
names/launchers, full verified backup, shared maintenance approval, successful
site-only migration/preservation, original Amazon/lockfile/Nginx state and HTTPS.
The server was not accessed; its current installed SHA is intentionally **unknown**.

External/manual: owner visual acceptance; live SMS/email receipt with consenting
recipients; physical-device/network/camera/microphone behavior; native Amharic/
Afaan Oromo approval; approved production Terms/Privacy/clinical/legal policies;
real payment/provider activation. None is claimed passed or enabled. SMS Ethiopia
stays Ethiopian-only. No new real-money or future-platform scope is included.
Existing demo data/passwords must remain; **do not seed or refresh** during update.
