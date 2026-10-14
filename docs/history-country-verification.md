# Country selector and private history upload verification — October14,2026

Implementation runtime checkpoint:62706f9, plus subsequent focused test/evidence
commit on feat/mvp-release-handover / draft PR44. No merge or remote changes.
The current packaged source is recorded by /assets/tele_tena/review/release.json;
the final handoff reports that full SHA. Backend and package use the same worktree.

## Implemented behavior

| Requirement | Result | Evidence / limits |
|---|---|---|
| Country selector in phone sign-in/signup | Implemented, locally verified | Native select, localized country names/calling codes, editable national number. Manual choice/input wins over delayed lookup. Main localhost falls back to Ethiopia. Actual configured offline MMDB returns US for controlled8.8.8.8 input. Proxy-chain unit checks ignore untrusted forwarded headers. No visitor IP sent to external service. |
| Drop/picker for attachment widgets | Implemented | Shared component replaces photo, onboarding/account resume and vetting evidence inputs; keyboard/picker/drop/busy/size states. Existing validators and evidence permissions preserved. Browser exercised shared picker through keyboard and real multi-file drop; individual resume/evidence upload endpoints were unchanged and their earlier evidence is retained. |
| Multiple medical-history files | Implemented, locally verified | Onboarding optional-background and Account→Personal profile→Optional saved history; textarea retained. PDF/JPEG/PNG5MB each; configurable100MB default owner budget, no fixed count. Same-file retries idempotent. Files immediately saved privately, not implicitly shared. |
| Onboarding access | Backend verified; owner visual review pending | Persisted post-verification identity/draft can upload only after adult/consent and while patient registration remains enabled. New onboarding field rendering follows existing component; full live-registration/provider journey not repeated. |

## Exact focused checks

- Python3.14.2 / Frappe16.2.1 / ERPNext16.1.0 isolated
  teletena-existing-upgrade.localhost:tests/history_uploads.py **4/4 PASS**.
  Owner retry/download and history/default preservation; other patient,
  clinician, reviewer and guest denial; malformed PDF/executable rejection,
  quota atomicity; trusted/untrusted proxy chain; verified draft/disabled
  registration gate. Savepoint rollback removes temporary onboarding fixture.
- Native v1.39 migration on main presentation and compatible existing site:
  **PASS**, additive table. Existing records/history unchanged.
- Compatible fresh Frappe+ERPNext+TeleTena install at62706f9, schema bootstrap,
  repeat migration, guest denial and retained-site fingerprint:**PASS**.
  Disposable teletena-history-v139-fresh.localhost/database/user, scoped database
  administrator and mode600 credentials:**cleanup PASS**. Evidence privately in
  /home/frappe/teletena-compat/runtime/history-v139-fresh-result.log.
- Production-built real Frappe browser: scripts/browser-history-uploads.cjs
  **PASS**. Existing password login, manual country selection, keyboard Enter
  opens native chooser; two-file upload, third-file real drop, reload,
  unchanged textarea, authorized no-store download, remove only newly uploaded
  test files.390/768/1440 captures. No mocked success/API responses.
- npm run lint:**PASS**, existing repository warnings remain.
- Locked production build:**PASS**; existing large-chunk warning remains.
- scripts/check_review_assets.py:**PASS**, hashes/scope/no sourcemaps or configs,
  exact private credential scan0. Sensitive APIs/files are not PWA cached.
- Actual configured DB-IP October2026 MMDB:published decompressed SHA1/MD5
  verified, outside Git. Controlled public-IP country lookup:**PASS**.

## Rendered inspection

[Country field](screenshots/history-country-v139/country-selector.png),
[390px](screenshots/history-country-v139/history-390.png),
[768px](screenshots/history-country-v139/history-768.png),
[1440px](screenshots/history-country-v139/history-1440.png).

Inspected desktop country field and390px populated profile screenshots:
select/input readable, existing form width maintained, drop areas distinguishable,
long filenames wrap, download/remove accessible; mobile page scroll remains
necessary and supported. This is a minimal extension of existing sign-in/profile
components, not a replacement design. Owner acceptance remains separate.

Main local preview:http://127.0.0.1:8017/teletena/
Site:teletena-mvp-presentation.localhost, original Frappe15 bench.
Frappe16 compatibility tests use the separate compatibility bench. No financial,
appointment, LiveKit or OTP authorization code changed; unchanged expensive
hosted media/financial suites were not repeated. No physical-device, live SMS,
SMTP delivery or native-language approval claimed. Ethiopian SMS provider remains
Ethiopian-only even though country selection supports international numbers.

## Setup and privacy

See history-uploads-and-country.md for secure site-local MMDB/proxy setup and
owner-only files. Loopback cannot infer a public visitor country. Optional reader
missing/unconfigured falls back to editable manual selection. Files are not made
available to clinicians by the text-history sharing toggle. No virus scanning is
claimed. Remote operator should verify request-body limits allow the5MB file's
base64 JSON payload (approximately7MB); no nginx/shared configuration is changed
by the helper. All new translations remain provisional.
