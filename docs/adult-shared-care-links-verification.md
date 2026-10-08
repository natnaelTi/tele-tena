# Adult relationship links: local verification

The focused implementation is in commit
`d46edbb9f899146dc2390143f53f73f70ef81b07` on
`feat/adult-relationship-links`, based on the local clinic-calendar checkpoint
`5c62499dd89af5b5918aa5a699cf37b1465b1325`. The dependent branch remains
unmerged in draft PR [#43](https://github.com/natnaelTi/tele-tena/pull/43),
stacked on PR #42. The release manifest at `tele_tena/public/review/release.json` is the
authoritative source SHA for the currently packaged frontend; it is rebuilt
from the clean branch checkout after verification documentation is committed.

## Preview

- URL: `http://127.0.0.1:8017/teletena/`
- Site: `tele-tena-pr12-fresh.localhost`
- App: production-built React served by Frappe's `/teletena/` route; no Vite
  server is involved.
- Gunicorn is bound to loopback on port 8017 and loads the isolated review WSGI
  app from the local Bench. The served HTML references packaged Frappe assets.
- Playwright confirmed service-worker scope `/teletena/` and script
  `/teletena/sw.js`. The worker changes its cache name per source commit and
  offers the existing safe update notice rather than forcing a reload.
- Scheduler is enabled for this site and `bench doctor` reported one worker
  online. The new hourly invitation-expiry cleanup has not been observed
  executing; API preview/acceptance independently enforce expiry using the
  database UTC clock. Shared Bench services were not restarted.

## Checks run

- `bench --site tele-tena-pr12-fresh.localhost backup --with-files` completed
  before migration. The backup is under the site's private `backups` directory.
- Frappe v1.30 additive schema migration completed. Calling its idempotent
  `execute` routine twice afterward succeeded.
- Frappe presentation suite: 47/47 passed. The additional reviewer-role denial
  assertion passed in a focused rerun after that full run.
- Frappe integration suite: 24/24 passed.
- Focused adult-link acceptance/revoke/consent and decline/expiry/rate-limit
  tests passed.
- Frontend `npm run build` passed. `npm run lint` completed with existing
  repository warnings and no blocking errors.
- `scripts/build_review.py` completed after the verification checkpoint was
  committed; the release manifest identifies the exact source SHA.
- `scripts/check_review_assets.py --site-private …/private` passed artifact
  hashes, app scope and exact private credential scan (zero configured
  credentials found in assets).
- Headless browser against the built Frappe app passed the public invitation
  route, invited-review registration-disabled copy, patient sign-in, patient
  links workspace, service-worker scope, and overflow checks at 390 and 1440px.
  It used the existing synthetic Review Patient account without changing
  relationships or creating invitations. No browser page errors were observed.
- JSON validation for `docs/operational-screen-map.json`, Python compilation,
  and `git diff --check` passed.

Screenshots:

- `docs/screenshots/adult-relationship-links/invitation-guest-390.png`
- `docs/screenshots/adult-relationship-links/patient-links-390.png`
- `docs/screenshots/adult-relationship-links/patient-links-1440.png`

## Scope and remaining verification

Backend tests exercise invitation creation/retry, digest-only token storage,
separate adult attestations, patient/clinician/reviewer authorization, minimal
preview/list responses, acceptance, decline, expiry, reciprocal deduplication,
revocation, relinking, request limits, and the fact that a relationship link
does not grant appointment access. The UI browser check does not yet create and
accept an invitation through two independent browser sessions. A registration-
enabled browser configuration, fresh-site install, tablet/narrow/200%-zoom
checks, and native-language review remain pending.

Adult confirmation is a self-attestation, not age or identity verification.
Couples/family offerings remain unavailable. This work adds no appointment
participants, clinical-history sharing, private intake, multi-party LiveKit,
or recipient-specific notes. Medical/legal consent review is required before
real-care use. Amharic and Afaan Oromo text is provisional. No remote site was
modified, no merge occurred, and no credentials or provider deliveries were
used.
