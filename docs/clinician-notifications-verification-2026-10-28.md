# Clinician Live Notifications — 28 October 2026

Runtime/build: `3e6aa71765b90d68174e6a0783ec46633013461b`.
Branch `feat/offline-telebirr-mvp`, draft PR50 dependent on PR49.
Preview: http://127.0.0.1:8017/teletena/ on
`teletena-mvp-presentation.localhost`. No schema/dependency/provider/mode change.

## Reproduction and Fix

The previous payment popup discarded events older than its client-side mount
clock. On the previous packaged `cd89a9f` runtime, an injected ten-minute browser
clock skew reproduced the missing clinician Account-page alert while the actual
backend submission persisted. This proves a failing condition, not that the
owner's machine clock was necessarily wrong. No diagnostic health text was logged.

Payment alerts now discover unseen server notification IDs, independent of client
clock and navigator.onLine. The first successful snapshot supplies the historic
bell list without flooding old popups; new arrivals are foregrounded. The bell,
popups and payment-queue refresh events share an actor-scoped feed. Polling is
bounded to five seconds, recovers on focus/visibility/reconnection, and aborts
stalled requests after eight seconds. Actual network/browser suspension can delay
updates; returning to the reachable page refreshes without navigation. No guarantee
of delivery while a browser is closed.

The old clinician pane combined three independently polled projections; accepted-
offer query failure could block its entire refresh. One shared feed now isolates
general/offer failures, retains prior successful portions, and exposes recovery
feedback. Pending receipt sections also refresh on feed events and a five-second
fallback instead of waiting for page navigation. All APIs still enforce owner access.

Clinicians now use the exact patient bell/pane component: All/Unread controls,
unread cards, timestamps, meaningful payment/consultation links, read persistence,
keyboard dismissal and focus return. Clinician-specific explanatory copy covers
payments, accepted offers and practice updates. Accepted-offer popup composition,
booking-state wording and authorized consultation handoff remain. No call layout,
financial state machine or external notice behavior was modified.

## Verification

All critical browser actions used persisted backend records, separate browser
contexts and the packaged frontend on the Frappe16.2.1/ERPNext16.1.0 compatibility
site `teletena-payments-v147-fresh.localhost`, port8021. Only explicit network faults
were injected; notification/payment success responses were not mocked.

- `scripts/browser-payment-clock-timeout.cjs` passed on this runtime: ten-minute
  clock skew, false browser online flag and one stalled feed request; clinician
  receives exact payment alert on Account; confirmation updates the patient's
  same document and alert; form remains read-only; no repeated alert after durable
  dismissal; one verification event; zero browser errors. The original clock test
  failed before the fix and passed afterward.
- `scripts/browser-notification-pane.cjs` passed: newly submitted payment appears
  in the already-open clinician pane AND Requests queue, without refresh; a failed
  accepted-offer endpoint does not block payment updates. All/Unread, persistent
  mark-read, exact receipt route, Escape/focus return and whole-network
  disconnect/reconnect recovery passed. Patient updates after confirmation.
- Existing accepted-offer pane/query/authorized link/read handling checked through
  `scripts/browser-accepted-offer-pane.cjs`; no new acceptance or hosted call invoked.
- 390/768/1440 screenshots inspected against the existing patient pane composition.
  Recovery notice appears above the scrollable list. Actual Chromium200% zoom
  passed for both roles with `scripts/browser-notification-zoom.cjs` (720CSS pixels,
  devicePixelRatio2, visualViewport.scale1 at1440physical width). Normal scrolling
  keeps controls reachable. This does not constitute owner visual acceptance.
- Production build, lint and artifact/privacy/hash checks passed. Existing lint and
  chunk-size warnings remain. Localization CSV exchange4/4 passed. Retained8017
  shell/deep links/build checked directly over HTTP; hosted HTTPS remains operator
  verification. No live SMS/email send was invoked.

Inherit the unchanged21 backend payment/permission/notification preference tests
from `payment-live-updates-2026-10-28.md`, and v148 migration/scheduler/hosted-call
history from earlier reports. No new migration or expensive hosted-call rerun was
needed for this client update.

## Review

Refresh once to load this new build (or use the PWA update prompt). Then leave
clinician Account or Requests open, submit a patient receipt in a separate session,
and watch the popup, bell and receipt queue update automatically. Open Notifications,
filter Unread, and follow Review Payment. Confirming receipt updates the patient's
open payment page. Subsequent activity requires no refresh.

Screenshots: `docs/screenshots/clinician-notifications/`. They contain only isolated
fictional test accounts. The visible partial-error banner is deliberately induced
by the failed-offer-endpoint test, not the normal production state.

No records/balances/credentials/provider switches were reset, no reseeding or
remote deployment/merge. Live delivery, physical devices, translations and owner
acceptance retain their prior external/manual status.
