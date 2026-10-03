# PR #7–#10 consolidation — 2026-10-02

All four PRs had clean worktrees and a linear dependency chain before merge.
Their heads and bases were checked against GitHub; no review comments or
outstanding review decisions were present. Latest reported CI checks passed.
Each PR was retargeted to `main` after its predecessor merged, its diff was
inspected, and GitHub created a merge commit. No source branch was deleted.

| PR | Head before merge | Main merge commit | Included scope |
| --- | --- | --- | --- |
| [#7](https://github.com/natnaelTi/tele-tena/pull/7) | `84bd97296e2030e679f621f7d8776921b65f0ec6` | `d329576b0d0a95ff812ece0775e976fb7db5701e` | Presentation workflows, recurring schedules, booking states, notes, care, private resume, tours and PWA |
| [#8](https://github.com/natnaelTi/tele-tena/pull/8) | `ba674b79bfa493a05689b1cee96d7a0d663766ec` | `151d3bef620b7df2c5bacbae24ba080d92ce1d14` | Production React/Frappe packaging and review-site safeguards |
| [#9](https://github.com/natnaelTi/tele-tena/pull/9) | `ada9efc1b5412b5130eae4f3416e5e46068eeaa0` | `6ffae7e834a0f82ff71c32921ecfda85855df002` | Exact Frappe 16 target-stack compatibility checkpoint |
| [#10](https://github.com/natnaelTi/tele-tena/pull/10) | `c569eb1d63ace2f162be586c40ff841e6e49ef60` | `4cc0be9a0a96c3b209d07b47fd5e7c46ab4c31a2` | Site-bound hosted phone OTP and patient/clinician registration switches |

The resulting `main` tree equals the combined #10 head, and the #10 head is an
ancestor of the new `main`. Thus each dependent change is present once with its
original commit ancestry. Main contains the consultation authorization and
LiveKit Cloud End/revocation code, request-specific disclosure/privacy controls,
booking/balance transaction safeguards, and the existing email/password path.

## Validation basis

Against the combined #10 tree before merge, the isolated Python 3.14.2 / Frappe
16 environment passed `tests/review_package.py` (9), `tests/hosted_phone_unit.py`
(4), `tests/dependency_checkpoint.py` (3), `pip check`, Python compileall,
`tests/service_worker.mjs`, production `scripts/build_review.py`, asset-scope
checks and frontend lint (exit 0 with existing warnings). The production build
embedded the exact #10 SHA `c569eb1d63ace2f162be586c40ff841e6e49ef60`.
After merging, `git diff --quiet` confirmed the same source tree on `main`.

The prior disposable-site run on installation commit
`8f7ab9cd8d5e779d17b632dc9afdae3e700ab3c6` passed Frappe 16 booking,
privacy and consultation integration (24), contact auth (7), hosted
registration (7), repeat migration, site-bound RQ expiry, browser review
routes, and hosted Cloud cached-token revocation. The separate #9 compatibility
run passed the presentation tests (5) before the #10 runtime changes, which did
not alter the presentation workflow. The only subsequent commit before #10 merge
pinned documentation and changed no runtime files. See
[hosted phone verification](hosted-phone-verification.md) and
[Frappe 16 verification](frappe16-compatibility-verification.md) for exact
scope, including the first combined media run's timeout and successful separate
fake-device rerun. The full seeded-site script was not rerun after its test
expectation fix, as documented there; it must not be counted as a later pass.

No fresh database install, remote HTTPS check, live SMS delivery or physical
device test was performed during this merge turn. Native review of Amharic and
Afaan Oromo remains outstanding. Selfmade stays installed at
`bba5ed9f15bd0b140967618ed2bd982c31a76c1b`; these GitHub merges did not
enable hosted phone access or update the remote site.

The [next-design inventory](design-update-inventory.md) records all current
routes and shared components and names absent capabilities separately, notably
clinician earnings and the planned double-entry/ERPNext boundary.
