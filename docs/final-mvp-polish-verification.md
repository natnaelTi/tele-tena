# Final bounded MVP polish and portable dataset —14October2026

## Candidate identity and review

Runtime release: **105cd15af1d1432e37b95de583f151d3056f6950**, branch
`feat/mvp-release-handover`, draft [PR44](https://github.com/natnaelTi/tele-tena/pull/44).
PR43 (`1e8d161468eb8d3563f1b5743982722c749bbcbf`) ancestry is preserved.
The subsequent evidence/document/test-only commit does not change backend,
frontend runtime, hooks, schema, dependency locks or packaged assets.
Both production builds identify this exact runtime commit in `release.json`.
The release pin is deliberately the tested runtime, not a moving branch.

Review: **http://127.0.0.1:8017/teletena/**, site
`teletena-mvp-presentation.localhost`, Bench `/home/frappe/frappe/frappe-bench`.
Owned web2011, queue Redis1999, worker2005 and scheduler2007 were running at
verification; HTTP200. `scripts/local_review.py status` gives current PIDs.
This is the Frappe production-built route, not Vite. Original development
site and Selfmade were not migrated, restarted, reseeded or deployed.

## Bounded changes

- One owner avatar/name Account trigger, initials fallback, Account and Sign out;
  keyboard navigation, Escape/focus return, outside dismissal and busy/error states.
  Removed the duplicate reviewer sidebar Sign out. At narrow widths the accessible
  avatar trigger retains the full name in its label; visible text collapses to fit.
- More drawer: role-aware sections, consistent outline icons, active/deep-link
  behavior, no duplicate destinations; pending applicants do not get unavailable
  service/earnings links or an empty More button. Existing Radix focus/dismissal
  and notifications/presence are preserved.
- Native details/summary affordances: whole trigger, aligned chevron, open/focus
  states; mounted fields preserve entered values. Native selects remain native.
- Portable explicit fictional dataset, versioned private record tracking, dry run,
  random private credentials, checkpointed idempotency and owner reconciliation.
  No install-hook seeding, public endpoint, outbound delivery, real transfers,
  public-registration enabling or existing credential/decision reset.
- Frappe16 binary storage fix: ASCII-base64 SQL parameters with FROM_BASE64 for
  photo/resume/evidence bytes. Frappe16's SQL query decoder rejected non-UTF8 binary
  parameters. Stored bytes and permissions are preserved; framework core untouched.

## Checks actually performed

| Check | Result/evidence |
|---|---|
| Locked frontend build, main Node22.23.3 and exact-target Node24.13.0 | PASS; both package105cd15. TypeScript build passed. |
| Frontend oxlint | PASS exit0; existing React purity/ref/effect warnings remain. Build retains its large-chunk warning. |
| Frappe15 financial reservation/release/dispute/concurrent payout tests |3/3 PASS; initial inherited closure fixture corrected to use actual End and assert closure, not bypass finalization. |
| Frappe15 binary PDF/photo preservation/permissions |2/2 PASS. |
| Frappe16 focused binary/profile/finance/concurrent/new-clinician-scope chain |6/6 PASS. |
| Frappe16 couples regressions |11/11 PASS. |
| Frappe16 contact authentication regressions |8/8 PASS; controlled transport, not live delivery. |
| Frappe16 dependency check | `pip check`: no broken requirements. No new dependency packages introduced. |
| Frappe16 retained-site migration/repeat preservation |PASS; target backed up first; original checkout03435bd retained separately. |
| Fresh Frappe16+ERPNext+TeleTena install and repeat migration |PASS on `teletena-final-mvp3-fresh.localhost`, schema v1.38; seed preflight/first/repeat/refresh, permissions, no outbound delivery, preserved unrelated-site fingerprint. Site/database/site user/temp admin/credential cleanup PASS. |
| Twice seed/preservation on existing Frappe15 and16 sites |PASS; all5 patient owners,4 clinician owners and every journal reconcile. Repeated run changes no balances/bookings/decisions. |
| Real browser menus/drawer/account/sign-out |PASS patient/counselor/reviewer/applicant on Frappe15 and16;320/390/768/1440. Persisted authentication and server data, no frontend API-success mocks. |
| Actual200% Chromium browser zoom |PASS patient/clinician/reviewer;720 CSS viewport from1440 window, DPR2, visualViewport.scale1; controls and scrolling remain accessible. |
| Seeded calendar → disclosure → confirmation → detail/reload |PASS on8017; created a real additional fictional reservation/appointment via UI. Owner reconciliation rechecked afterward. |
| Native background jobs |Observed automatic Complete logs after isolated scheduler start: release18 executions, request/couples/extensions expiry80 each in captured sample; queue empty and site-scoped. These are enqueue/worker logs, not manual function invocations. |
| Assets/privacy |PASS hash/scope/no-config/source-map/devURL checks;20 known local secrets/passwords absent from generated assets. |
| PWA |Unchanged public-static-only policy and supported waiting-worker update behavior retained; controlled waiting-worker browser check is separately labelled, not proof of remote installation. |

Safe current results are in `docs/evidence/final-mvp-polish/`. Private detailed
compatibility logs remain under `/home/frappe/teletena-compat/runtime/final-*`.

Diagnostics resolved rather than concealed: fresh1 exposed the absent site signing
key; only a genuinely new site without encrypted data now creates it. Missing keys
on populated sites stop for restoration. A second fresh run's retained fingerprint
was invalidated by concurrent test fixtures; a standalone third run passed.
The first Frappe16 browser process imported the wrong local site path; explicit
PYTHONPATH and a scoped restart restored the correct site. Menu assertions now wait
for actual asynchronous focus/dismissal transitions before checking their results.

## Visual comparison

Reference `/home/frappe/teletena-design-reference` was rendered locally. Exact
reference C01/#c01, C02/#care, F01/#f01, H01/#h01, H02/#h02 and I01/#i01 were
captured390/768/1440. Screenshots were visually inspected, not only generated.
Paired evidence: `docs/screenshots/final-mvp-polish/`.

| Reference / implemented state | Inspection result and necessary differences |
|---|---|
| C01 patient home390/1440, own Account open |Same ink hero, card/wallet hierarchy, Inter and border/radius family. Global demo ribbon, working search/private-request entry and actual persisted records add content. No fabricated prior clinicians or reference amounts. |
| F01 clinician home1440, Account and More |Same stats/next-appointment/readiness composition; new compact dropdown and grouped drawer extend reference components. Live presence ribbon, real counts and truthful scope setup remain. |
| H01 reviewer390, header/menu |Same typography/icon language; grouped mobile More and single own-account menu replace duplicate exit controls. Saved screenshots crop before applicant identities; this is shared-header evidence, not a new whole-reviewer acceptance claim. |
| Shared mobile drawers and actual200% |Readable labels, visible chevrons, touch targets and scroll recovery.320 header wraps instead of overlapping logo/controls. Open dialogs legitimately cover their background; content is not clipped to force no-scroll. |
| Booking review and persisted consultation detail |Actual generated date, fee, privacy snapshot and resulting appointment captured. No unrelated calendar/call redesign in this bounded pass. |

The current work verifies the changed shared patterns. It does **not** retroactively
mark all142 reference screens accepted. The existing `mvp-screen-acceptance.json`
retains per-screen differences/evidence and owner-review status. The accepted
media-left/information-right desktop consultation layout was not changed.

## Portable data and private accounts

See [demo-dataset.md](demo-dataset.md) for dry-run/create/refresh commands,10 account
roles,7 service definitions and all scenarios. The configured financial fee/window
is retained; amounts are illustrative, not market claims. Completed seed sessions
use explicit process-local synthetic timing and offline room adapters; they are
financial/status fixtures, not actual media evidence. Clinicians start paused;
a browser must explicitly enable and renew immediate availability.

Current private credentials:
`/home/frappe/frappe/frappe-bench/sites/teletena-mvp-presentation.localhost/private/tt-demo-mvp-v2-accounts.json`
(mode600). Adjacent `tt-demo-mvp-v2-records.json` maps roles and tagged records.
Existing older presentation accounts/photos/credentials are preserved. Never
paste passwords into reports. New seed accounts deliberately exercise initials;
existing uploaded fictional portraits exercise the unchanged photo path.

Original records/decisions never refresh automatically. Explicit `refresh` adds
new request/offer scenarios with a stable generation label, normal eligibility and
limits. Offers may expire normally. Existing schedules/clinical snapshots/funds
are never moved or replenished merely to make a presentation look current.

## Review, operation and external limitations

1. Mahi: own account menu → Find care → Sara → generated time → privacy → book;
   view reservation/activity and persisted appointment.
2. Mahi/Sara/Michael: use an explicitly refreshed scheduled request; compare two
   private offers, accept one, then clinician Your offers/notification appointment link.
3. Aster/Sara: completed record; patient shared summary vs clinician-only note.
4. Sara: pending/dispute/available earnings, requested and cancelled payout; no
   external transfer or fabricated Paid state.
5. Liya/Yonatan: separate shared appointment consent/access; configured real-call
   core is unchanged. Meron: Netsanet pending general application and individual
   Submitted/Clarification/Rejected scope evidence.

Restart after WSL reboot, as normal frappe:

```bash
cd /home/frappe/frappe/frappe-bench/apps/tele_tena
../../env/bin/python scripts/local_review.py start
../../env/bin/python scripts/local_review.py status
# Explicitly stop only this owned preview when desired:
../../env/bin/python scripts/local_review.py stop
```

Database/shared cache services must already be running; start fails clearly if
missing and never edits privileged system startup or kills unrelated services.

[Exact Selfmade update/seed/smoke/backup/rollback instructions](selfmade-final-mvp-update.md)
are pinned to the runtime SHA above. The current remote SHA/services must first be
inspected. Shared web/worker/scheduler restart impacts every Bench site; no remote
changes were made here. Database rollback after migration/seed requires the matched
backup, not only an older code checkout.

PR44 stays draft for owner acceptance. No known failure remains in these bounded
checks. Live SMS/SMTP delivery was not tested; previously verified hosted LiveKit
End/rejoin/token evidence is reused because call code is unchanged, not claimed
as rerun. Physical-device calling/installation, native-language approval and remote
HTTPS/network checks remain external/manual. Fictional approvals are not regulatory
credential verification; demo accounting is not ERPNext custody/provider settlement.
Deferred laboratories, subscriptions, tourism and full clinic operations remain
post-MVP; no legal-policy phase was begun.
