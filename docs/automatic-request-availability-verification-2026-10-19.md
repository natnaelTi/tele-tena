# Connected schedule availability follow-up — 19 October 2026

Current runtime/package: `624b013b3aa41017107e0fd6cd551805834deea3` on
`feat/guest-first-mvp`, draft PR #47, dependent on PR #46. Subsequent evidence/test-only
commits do not require a runtime rebuild. No dependency changes, reseed, merge or remote deployment.

Preview: http://127.0.0.1:8017/teletena/ · `teletena-mvp-presentation.localhost` ·
`/home/frappe/frappe/frappe-bench`. This preview is Frappe 15/Python 3.12; separate
backend compatibility checks use Frappe 16.2.1/ERPNext 16.1.0/Python 3.14.2 in
`/home/frappe/teletena-compat/bench`, never upgrade the original Bench. Node 24.13.0 builds
production assets, with no Vite server. Existing preview-owned web/worker/scheduler and
Redis13917 remain running; unrelated Bench services remain untouched.

The owned Python processes were restarted at `bfca605bbb381ef8ae35479a7232a514d162ae6b`.
Their backend code is byte-identical to the packaged candidate: the subsequent runtime
changes are CSS only, plus a browser test. The manifest hashes were checked against all
packaged files.

## Implemented behavior

- Availability: save **Automatic immediate requests** on each selected schedule.
  Off by default, with additive v1.41 columns and no historical backfill. Published
  local rules, date replacements, breaks and unavailable days determine working hours.
- Authenticated reachable clinician workspaces renew a bounded lease every30 seconds.
  Automatic hours do **not** advertise unattended/offline clinicians. Approval, exact
  scope, language, immediate-care policy, full duration, buffers and conflicts still apply.
- Today: green Available card; neutral Paused, amber Setup, blue Occupied/In consultation.
  Setup steps link to the relevant pages. Manual pause survives navigation/reload;
  Resume automatic and Go available now retain explicit manual control. Manual start
  preserves existing immediate policy validation even outside automatic hours.
- No visible presence bar on other workspace pages. Its headless provider keeps the
  heartbeat active while navigating. Booking acceptance notifications remain intact.
- Calendar blocks have text plus distinct colors for confirmed, pending, active,
  completed, cancelled and incomplete/expired history. Cancelled/expired history does
  not become a booking conflict. Existing appointments/reservations are not modified.
- Native selects use TeleTena closed-control/focus styling and a progressive native
  picker theme in supporting browsers. Other browsers retain their accessible native
  menu. Accordions retain values, native keyboard operation and clear chevrons.

## Reported stale In progress — observed cause

The presentation appointment on 14 October at15:30 Africa/Addis_Ababa has a persisted
`Booked` appointment and `Open` consultation created at12:24:51 UTC, with no recorded End.
The list previously classified every Open row as In progress indefinitely. There is no
reliable continuous connected-time record that could establish an ongoing call days later.

Now an opened call after its booked/extended end is in Past, **Outcome not recorded**,
with an explanation that a call was opened. Call activity says **Call opened**. Within
its booked interval an opened call can still display In progress. Terminal states take
precedence. This display correction does not End a room, infer completion/no-show, mutate
history, revoke tokens, or settle funds. The original appointment/call remain unchanged.

## Actual checks and limits

| Check | Result |
|---|---|
| Complete native DB/public/private/config backup before migration | Verified at private `/home/frappe/teletena-guest-first/before-auto-presence` |
| Frappe15 presentation migration | Pass; v1.41 only adds off-by-default preference/control columns |
| Frappe16 existing-site migration + repeat migration | Pass on `teletena-guest-first-test.localhost` |
| Previously verified clean-install site's new schema migration | Pass on `teletena-guest-first-fresh.localhost`; not a newly created v1.41 fresh installation |
| `tests/schedule_presence.py` | 8 passed: persistence, pause/resume/expiry, exceptions/breaks, capacity loss/recovery, real capacity, occupancy/opened-call state, manual override, authorization/invalid-save rollback |
| `tests/guest_first.py` | 15 passed; real backend/public projection, availability/conflicts and private disclosure/files/notices regressions |
| Appointment status/group Node tests | Pass; past Open regression, current Open, terminal precedence, truthful elapsed outcome, patient task isolation |
| Production build/TypeScript | Pass; packaged source above |
| Frontend lint | Pass with68 existing warning lines; no lint errors |
| `scripts/browser-schedule-presence.cjs` | Pass; real-backend setting save/reload/restore, dashboard/no topbar, navigation,1440/768/390, historical list |
| `scripts/browser-schedule-presence-state.cjs` | Pass; real generated capacity/automatic activation, green card, Pause/reload/Resume,32-second heartbeat while on Requests |
| `scripts/browser-schedule-presence-zoom.cjs` | Pass; actual Chromium200% zoom (outer1440/inner720/DPR2), native dropdown keyboard selection; both open options inside the zoomed viewport; no horizontal clipping |
| Owner-by-owner reconciliation | 11 patient owners/8 clinician owners pass; every journal balanced; no repairs |

Backend occupancy tests use a controlled future join window and token transport with real
appointment creation/authorization/storage; they are not hosted-media evidence. Date/rule
and pause tests isolate capacity where needed; the separate real-capacity test and actual
browser activation use existing booking rules. Site-clock changes and external delivery are
not used. Browser schedule values are restored; the test clinician is deliberately left
paused after testing. No balance, provider setting, password or historical outcome is reset.

Unchanged hosted LiveKit End/revocation, individual/couples clinical recipient isolation and
financial acceptance evidence remain in prior reports. No new physical-device, live SMS/email,
or native-language approval is claimed. New Amharic/Afaan Oromo copy remains provisional.
Owner visual acceptance remains pending.

## Paired visual review

Files: `docs/screenshots/schedule-presence/`.

| Reference/state | Application evidence | Comparison |
|---|---|---|
| F01 `#f01`,1440×900 | `reference-today-1440.png` / `dashboard-1440.png`, `available-1440.png`, `manually-paused-1440.png` | Preserved title, three metrics, schedule/readiness columns, typography and gutters. New wallet-like readiness card is the explicitly requested extension, not a prototype panel. Real amounts/names/counts differ. |
| F05 `#availability`,1440×900 | `reference-availability-1440.png` / `scheduler-1440.png` | Preserved configuration/calendar composition; new opt-in is an operational extension. Multiple intervals, full weekly grid and exceptions remain; prototype fixed data is not copied. |
| Responsive F01/F05 | `dashboard-768.png`, `dashboard-390.png`, `scheduler-768.png`, `scheduler-390.png` | Readable single-column card/agenda and scrollable settings; desktop grid is not compressed onto mobile. |
| Native picker/zoom | `scheduler-200-percent.png` | Actual browser zoom and native keyboard selection; controls remain reachable by page scrolling. Browser picker fallback intentionally varies by platform. |
| Historical appointments | `historical-appointments.png` | Past outcome remains truthful; no automatically fabricated Completed state. |

Rendered images were opened and visually inspected, separately from overflow/click checks.
This follow-up extends the existing matrix; it does not assert unrelated whole-MVP acceptance.

## Review

Sign in as an approved clinician. Today now contains request readiness. Open Availability,
select a service, opt into Automatic immediate requests and save Published. During eligible
working hours return to Today: green availability requires a full feasible session. Pause,
reload, resume; navigating elsewhere keeps the authenticated heartbeat working. Closing the
workspace expires presence rather than promising unattended care. Existing occupied time is
protected. In Appointments, inspect14 October history: it remains incomplete, not In progress.

Use existing private account manifests described in `docs/local-preview.md`. Restart only
this preview with the documented `scripts/local_review.py` commands. No Selfmade commands
were executed; the previous remote release remains unchanged.
