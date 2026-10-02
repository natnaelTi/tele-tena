# Incremental hosted phone access: Selfmade review site

This updates the **already installed** TeleTena review site
`teletena.selfmadecs.com` in `/home/smcs/frappe-bench` from release
`bba5ed9f15bd0b140967618ed2bd982c31a76c1b`. It does not call the seed,
create a new site, change Frappe/ERPNext, or enable generic Frappe signup.
The final verified update SHA is recorded in the verification report. PR dependencies:
this phone-access branch includes open PR #9, #8 and #7; merge is separate.

## Gate: review the target before modifying it

Use the shared Bench maintenance window. Confirm the TeleTena checkout is clean,
site really has the expected release, and framework commits still match the
[compatibility report](frappe16-compatibility-verification.md). Confirm that the
site backup and private files can be restored. Any framework/dependency mismatch
is a stop; no `bench update`, global pip change or all-site migration.

The SMS Ethiopia public page still conflicts: prose calls for `Authorization`,
while its [send example and FAQ](https://smsethiopia.com/#/api-reference) use
`KEY`. The helper requires an explicit header selection from the operator's
account-specific documentation; it never falls back and never tries two sends.
If account documentation does not resolve this, use one consented whitelisted
recipient in the controlled test below. Provider API acceptance is not delivery.
Trial accounts may send only to whitelisted numbers. Sender/template requirements
and delivery receipt API are not established by the public page; do not claim
more than the returned acceptance state and the recipient's observation.

## Pinned code and backup

All commands run as `smcs` in `/home/smcs/frappe-bench` unless they begin with
`sudo`. The SHA in the report must replace `UPDATE_SHA` below before running.
The staged update includes no new Python package or schema requirement. It still
runs a site-only migration as a safe hook/patch check and rechecks `pip check`.

```bash
set -euo pipefail
umask 077
cd /home/smcs/frappe-bench
UPDATE_SHA='REPLACE_WITH_FULL_VERIFIED_UPDATE_SHA'
test "$UPDATE_SHA" != REPLACE_WITH_FULL_VERIFIED_UPDATE_SHA
[[ "$UPDATE_SHA" =~ ^[0-9a-f]{40}$ ]]
test "$(git -C apps/tele_tena rev-parse HEAD)" = bba5ed9f15bd0b140967618ed2bd982c31a76c1b
test -z "$(git -C apps/tele_tena status --porcelain)"
test "$(git -C apps/frappe rev-parse HEAD)" = 8f6e24728b86b7c6427908ed6536289a41ea9cf4
test "$(git -C apps/erpnext rev-parse HEAD)" = bb2bada1fde0ae7a3c3cad32bed781ebd470e27d
bench --site teletena.selfmadecs.com list-apps
env/bin/python -m pip check
bench --site teletena.selfmadecs.com backup --with-files
# Verify today's DB/public/private archives before going further. Copy the site's
# site_config.json and encryption key to approved private backup storage as well.
git -C apps/tele_tena fetch origin "$UPDATE_SHA"
git -C apps/tele_tena checkout --detach "$UPDATE_SHA"
test "$(git -C apps/tele_tena rev-parse HEAD)" = "$UPDATE_SHA"
env/bin/python apps/tele_tena/scripts/build_review.py
bench build --app tele_tena --production
bench --site teletena.selfmadecs.com migrate
bench --site teletena.selfmadecs.com clear-cache
env/bin/python -m pip check
```

`build_review.py` uses the locked npm dependencies, embeds the exact source SHA,
and has no Vite or secret variable requirement. The asset link/build has shared
Bench scope. Do not regenerate global nginx/Supervisor configs.

## Private key entry and explicit access switch

First use the account dashboard documentation to select the expected key header.
Enter the key **only at the hidden prompt**. No key in shell arguments, `.env`,
frontend variables, a ticket, chat or logs.

```bash
cd /home/smcs/frappe-bench
bench --site teletena.selfmadecs.com execute tele_tena.development.configure_sms
```

At the prompt, choose `KEY` or `Authorization` from the provider account docs;
if `Authorization`, choose `raw` or `bearer` based on those docs. Re-running the
helper atomically replaces the private mode-600 configuration. It sends no SMS.
The prior private key file is left in place until a successful replacement.

Then enable the three independent access choices. For the requested hosted
patient and clinician test, answer exact site name, `yes`, `yes`, `yes`, then a
small SMS attempt cap such as `10` for the first review day. The cap can later
be adjusted from 1–100. The helper refuses to enable phone access without a
valid private SMS configuration.

```bash
bench --site teletena.selfmadecs.com execute tele_tena.review.configure_contact_access
bench --site teletena.selfmadecs.com clear-cache
```

This keeps `Website Settings.disable_signup=1`, developer mode off, CSRF active,
review demo funding bound to this site, and password reviewer access available.
To pause SMS cost without altering other review settings, rerun the access helper
with `no` for phone OTP. You may separately pause either registration type.

## Shared service reload and smoke test

The observed Supervisor web process is
`frappe-bench-web:frappe-bench-frappe-web`. Coordinate this in a shared Bench
maintenance window: restarting it interrupts **all sites** briefly. Workers,
scheduler, Redis, MariaDB, socket.io and nginx have no code/config changes that
require a restart for this update. Do not use `supervisorctl restart all`.

```bash
sudo supervisorctl restart frappe-bench-web:frappe-bench-frappe-web
sudo supervisorctl status frappe-bench-web:frappe-bench-frappe-web
env/bin/python apps/tele_tena/scripts/check_review_url.py https://teletena.selfmadecs.com
env/bin/python apps/tele_tena/scripts/check_review_assets.py \
  --site-private sites/teletena.selfmadecs.com/private
```

Inspect `https://teletena.selfmadecs.com/teletena/sign-in` in a private browser:
phone entry is one field; email password remains selectable. Test reviewer
password sign-in and logout first. Confirm `/api/method/tele_tena.api.contact_auth.sign_in_options`
reports phone enabled and only the intended registration paths. It reports
site policy/provider configuration, never whether a number exists.

Before a live SMS, verify the sender account's test whitelist contains **your
own consenting phone** and credits are sufficient. Do not use a doctor's or
patient's number without their specific consent. From your own browser, request
**one** code. Record only time, provider state (`accepted`, `rejected` or
`uncertain`) and whether your phone actually received a message; do not copy the
code. After receipt, enter it once in the browser and confirm the server signs
you in or starts guided onboarding. An accepted API response is only provider
acceptance; receipt and successful verification are separate observations.

If the provider rejects or the outcome is uncertain, do not automatically retry
or swap headers inside a request. Inspect account documentation, key permissions,
trial whitelist and the selected header locally, then deliberately repeat the
single-number test after the 60-second cooldown. The site cap bounds cost. Do
not log provider request bodies, OTPs or full response headers. Check the web
process receives the true WSGI peer under the actual trusted nginx proxy rules;
TeleTena ignores arbitrary client `X-Forwarded-For`. If all users appear as one
proxy address, the per-peer rate limit will be shared conservatively; do not
trust a spoofable forwarded header to relax it.

Test a **new** consenting patient number and clinician number only after the
first login succeeds, with no clinical information and a synthetic resume. The
clinician must stay Pending until manual application and service-scope approval.
Confirm disabled public Frappe signup, private records, and no real-money route.
No live SMS is sent by the automated verification suite.

## Rollback

First disable phone and both registration paths with the local access helper
(`no/no/no`; keep the existing cap) and clear this site's cache. For a full code
rollback, coordinate the shared web restart, restore the matching previous
source `bba5ed9f15bd0b140967618ed2bd982c31a76c1b`, rebuild its assets,
run site-only migration and smoke checks. Preserve new review account records
unless restoring the **matching** pre-update database/private/public/config
backup as a deliberate whole-site rollback; never delete registrations silently.
Checking out old code alone is not a schema-changing rollback method. This
update adds no schema, but backups remain necessary because live registration
may create real site data.
