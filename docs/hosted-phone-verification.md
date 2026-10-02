# Hosted phone access verification — 2026-10-02

## Scope and dependency

This change enables independently controlled SMS sign-in and patient/clinician
registration on the designated review site. It is based on open compatibility
PR #9, which includes packaging PR #8 and presentation PR #7. It does not
change real-payment controls, generic Frappe signup, existing records, or the
deployed Selfmade site. No live SMS was sent.

The exact installation SHA is pinned in
[the incremental update guide](selfmade-phone-access-update.md). Local testing
used the isolated Frappe 16 Bench; remote HTTPS, proxy identity, provider
credentials, account-specific SMS header requirements, delivery, and physical
devices still require the controlled operator checks in that guide.

## Checks run

| Check | Result |
| --- | --- |
| Frappe 16.2.1, ERPNext 16.1.0, Python 3.14.2, Node 24.13.0 isolated Bench | Exact tested application/framework versions, separate from original WSL Bench |
| `tests/contact_auth.py` | 7 passed |
| `tests/integration.py` | 24 passed; booking, permissions, OTP, consultation regressions |
| `tests/review_package.py` | 9 passed; invited-review access and site gates |
| `tests/hosted_phone_unit.py` | 4 passed; provider header selection and budget logic |
| `tests/hosted_phone_access.py` on disposable MariaDB site | 7 passed; existing/new users, adult consent, pending clinician with resume, duplicate/racing verification, provider failure and site cap; SMS mocked |
| `scripts/check_migration.py` | Additive repeat migrations passed; retained appointment, balance, OTP, consultation and onboarding fingerprints preserved |
| `scripts/check_review_site.py --job-only` | Actual RQ expiry job released its reservation once on disposable site |
| `npm --prefix frontend run build` and `npm --prefix frontend run lint` | Passed; lint exit 0 with pre-existing React warnings |
| `scripts/build_review.py` and `scripts/check_review_assets.py` | Passed; packaged frontend, public-only assets, no private test SMS key in artifacts |
| `scripts/browser-hosted-phone.cjs` | Passed at 390, 768 and 1440 px on built frontend; provider send mocked |
| `scripts/browser-review-package.cjs` | Passed real password session, guest rejection, deep-link refresh, sign-out, private-note exclusion and PWA route checks |
| `scripts/check_hosted_livekit_revocation.py` against hosted Cloud project | Cached original and refreshed tokens for both identities rejected after End; the departed patient could not reconnect directly through SDK. Separate fake-device media phase passed Leave/rejoin/End and two-person media exchange on retry |
| `node tests/service_worker.mjs` | Passed API/private route and authenticated-data cache exclusion |
| `env/bin/python -m pip check`, compileall, `git diff --check` | Passed |

The first full `scripts/check_review_site.py` rerun on the freshly seeded
disposable site passed its setup, idempotent seed, repeat migrations, HTTP
password access and private-file assertions, then stopped at a stale test
expectation: it expected `review_password_required` from an unconfigured email
OTP route, while the new correct response is `email_otp_unavailable`. The
expectation was fixed. It was not rerun in full because its fixture is not
designed to recreate the same synthetic records on an already seeded site.
The separate browser, migration, unit/integration and RQ checks above were run
after the fix. This is a test-harness limitation, not evidence that the full
script passed.

The first combined hosted LiveKit run passed cached-token revocation but its
fake-media phase timed out awaiting the clinician's remote video element. The
separate media-only rerun completed with both participants, Leave/rejoin and
clinician End. The first failure remains recorded rather than relabeled as a
pass. These browser checks use automated fake devices and do not prove remote
HTTPS, a human device test, or uninterrupted mobile background calling.

## Rendered evidence

The built site was rendered and visually inspected at
[390 px](screenshots/hosted-phone/phone-entry-390.png),
[768 px](screenshots/hosted-phone/phone-entry-768.png), and
[1440 px](screenshots/hosted-phone/phone-entry-1440.png). The
[mobile code step](screenshots/hosted-phone/code-entry-390.png) and
[password alternative](screenshots/hosted-phone/email-password-390.png) were
also inspected. The screenshots contain only synthetic input and no OTP,
password, provider key or patient data. No horizontal overflow was observed.

## Security and provider limits

Site settings start disabled everywhere except the existing local development
mode. Enabling phone access requires a private provider configuration. A durable
rolling site-wide send cap complements per-phone and WSGI-peer limits; the
provider is called at most once per challenge. A timeout is uncertain, not a
reason to silently retry. Provider acceptance is not SMS delivery. New users
get an unprivileged contact identity first; professional service approval
remains manual. Reviewer email/password login remains available when SMTP is
not configured.

SMS Ethiopia's public reference gives conflicting `Authorization` and `KEY`
examples. Account-specific documentation or a single consented whitelist test
must resolve the selection. The helper prompts invisibly for the key and stores
it privately; neither a live provider request nor remote receipt was verified.
The shared Bench's actual nginx trust boundary has not been observed from this
local test. The remote operator must confirm true peer-IP behavior before
opening public registration at scale.

No remote installation or live signup has been performed by this branch.
