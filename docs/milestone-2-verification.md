# Milestone 2 verification

Run on 2026-10-01 against the installed Frappe 15.121.2 / ERPNext 15.121.6
development bench. All application records and accounts in the new checks were
synthetic. No real LiveKit project credential file existed before testing; the
automated media check created random local-only credentials and removed them.

## Results

- `bench --site erp.localhost migrate --skip-search-index`: passed for the
  consultation table and close-confirmation marker patches.
- `../../env/bin/python tests/integration.py`: all 15 tests passed, including the
  existing authorization, CSRF, atomic booking, balance, replay, privacy,
  service-scope and rollback checks plus guessed appointment IDs, guest denial,
  join-window denial, audio/video token grants, opaque aliases, participant
  rejoin, clinician-only end, ended-room denial and provider-close retry.
- `../../env/bin/python scripts/check_migration.py`: passed twice through normal
  Bench migrations; legacy app-table fingerprints and catalog rows remained
  unchanged; five patch-log entries and the consultation close marker were found.
- `npm run build`: passed. The LiveKit client is split into a lazy-loaded chunk;
  Vite reports that chunk is 517.62 kB minified (134.45 kB gzip), just above its
  500 kB advisory threshold.
- `npm run lint`, Python `compileall`, and `git diff --check`: passed.
- `scripts/check_review_browser.py`: passed the existing milestone 1 Chromium
  browser regression.
- `scripts/check_consultation_browser.py`: passed with two independent headless
  Chromium contexts and fake camera/microphone devices against a temporary,
  checksum-verified LiveKit 1.13.7 server. Remote audio and video elements arrived
  in both sessions; patient leave/rejoin and clinician ending both sessions
  passed. This is automated fake-media evidence, not human/device testing.
- The temporary LiveKit server process, generated credential file, config and
  temporary browser fixtures were removed. No local LiveKit credentials remain.

At the original milestone baseline, this branch did not repeat the disposable new-site installation test that was
run for PR #2. The new consultation tables are included in both normal versioned
migration and fresh-install bootstrap, but a new disposable site was not created
for milestone 2. No physical phones, actual cameras/microphones, mobile network,
reconnection under packet loss or human two-device test was available. SMS/phone
OTP remains incomplete. Hosted-project review results are recorded below.

## PR #3 review follow-up (2026-10-01)

- `../../env/bin/python tests/integration.py`: all 18 tests passed, including
  per-clinician service scopes, request-level sharing isolation, replay before
  mutable-profile validation, exact Cloud revocation parameters for both
  opaque identities, and serialized Join/End requests.
- `npm run build` and `npm run lint`: passed. The LiveKit client chunk remains
  517.62 kB minified, above Vite's advisory threshold.
- Python compilation, JavaScript syntax checks, and `git diff --check`: passed.
- Hosted LiveKit Cloud cached-token browser regression: passed. Two independent
  synthetic browser sessions each obtained an initial and a refreshed
  participant token; after clinician End, direct SDK reconnect attempts with
  all four cached tokens were rejected. The patient had left before End, so
  this also verifies revocation for a departed participant. The check used
  the configured hosted `*.livekit.cloud` project, not a self-hosted server.
- Hosted fake-media browser checks exercised device-mode preview cleanup,
  connection/publication failure cleanup, duplicate Join/unmount handling,
  two-way audio/video elements, polling while connected, and patient
  Leave/rejoin. The integrated browser script did not finish cleanly at its
  final End-control assertion. After correcting its appointment-scoped media
  selector, a focused hosted browser regression covering Join, patient
  Leave/rejoin, and clinician End passed and confirmed both session views
  ended. Treat this as focused automated fake-device evidence; it is not a
  clean pass of the complete browser script and is not human/device testing.
- Existing appointments and simulated balances were preserved. Browser runs
  used only synthetic test accounts/appointments and removed their temporary
  fixture records on completion.
- Self-hosted tests do not prove Cloud cached-token revocation: LiveKit
  documents revocation through `RemoveParticipant` as a Cloud behavior. On
  self-hosted deployments, deleting the room does not invalidate a cached
  signed token; an existing token may reconnect until expiration. Cloud End
  uses a 30-second future revocation cutoff (within Cloud's documented ±60-second
  bound), attempts revocation for both appointment identities, and remains
  retryable if closure fails.

## Local LiveKit setup

From a normal-user Bench terminal, follow [development setup](development.md) to
run `bench --site erp.localhost execute tele_tena.development.configure_livekit`.
It securely prompts for the public LiveKit URL, API key and hidden API secret.
Never paste credentials into tickets, source, chat or Vite variables.

## Two-device review checklist

1. Configure a hosted development LiveKit project, keep Frappe and Vite running,
   and sign in to `http://erp.localhost:5173` with the existing synthetic patient
   and clinician accounts in two separate browser profiles/devices.
2. On the patient device, add only simulated ETB, choose the approved offering,
   choose a clinician availability time, review the sharing preview and book.
   Open the appointment when it is inside the configured join window.
3. On each device, press **Check microphone and camera**, grant permission, then
   press **Join consultation**. Confirm both can hear and see the other participant.
4. Test mute/unmute, camera on/off and audio-only mode. Patient **Leave** should
   keep the clinician in the room and permit patient rejoin within the window.
5. Clinician **End consultation for both participants** should disconnect both;
   refresh the patient status and verify that new joins are denied. Confirm no
   balance changes or additional charges.

Remote phones require HTTPS for camera/microphone access. For development, use a
temporary authenticated HTTPS tunnel for the Vite application port only, while
keeping Bench/Frappe port 8000 bound to loopback and untunneled. Keep synthetic
accounts only, and make sure the browser can reach the configured secure LiveKit
WebSocket URL.
