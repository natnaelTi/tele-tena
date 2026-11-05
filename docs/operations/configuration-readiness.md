# Actual Working Configuration Follow-Up

Source continuation: draft PR52 → PR51; baseline7e933f8, built15a051c. The populated
working file `/home/frappe/teletena-operations-config/providers.json` was read, not
replaced by the template. No credential value/full DSN/provider body is in this report.

Local validation: directory700, file600, owned/non-symlink file, correct schema,
PostHog EU ingestion/admin host consistency and project335848, Bugsink DSN/API/project
consistency, owner email syntax, owner_account intentionally empty and
live_test_authorized false. **Missing/invalid fields: none. Optional missing fields:
none. Telegram setup missing field: telegram_chat.** Token presence does not prove
scopes or project access. Existing private SMTP file is structurally complete/600;
SMTP connectivity/receipt was not tested.

Exactly one bounded Telegram getUpdates request (limit100, timeout0, no offset or
allowed_updates changes) found zero exact-message private chats. No messages/body
were printed; no webhook/consumer/bot setting changed, no recipient guessed, file
unchanged and no message sent. Owner must open the dedicated bot, press Start and
send exactly **TeleTena owner alert setup**. A subsequent bounded discovery can
then resolve it; multiple matches require owner selection.

The working file is **not bound to the presentation site**. Existing UI runtime
Unconfigured labels describe that site's binding, not absence of the owner's
projects/credentials. No site configuration/collection/provider/alert switch was
changed. All reviewer access stays as implemented; no alert-account linkage or
role changes. No new build is required for this configuration/tooling/documentation
checkpoint; actual served runtime remains15a051c.

| Capability | Implementation | Actual Provider State |
| --- | --- | --- |
| Backend/job Bugsink errors | Isolated SDK and sanitized-envelope/memory transport tested | Credentials present; authorized ingestion/readback pending |
| Frontend errors | Kind/route reporting and pre-egress canary tests implemented | Live ingestion pending; useful JS frames/debug-ID map wiring not implemented |
| PostHog events | Allowlisted server adapter, timeout/redaction tests | EU335848 credentials present; authorized ingestion/query scope/readback pending |
| Masked replay | SDK pinned, policy quarantined, recorder never started | Useful capture adapter not implemented; isolated pre-egress/proof work pending authorization |
| Full raw export | Current adapter raises ArchiveUnverified | Not implemented; schema/source/segment inspection pending authorized project access |
| Independent playback | API explicitly returns unavailable | Not implemented; project-format normalization/player proof required |
| Archive retention/storage | Private bounded local storage, capture-time expiry, restore tombstones, isolated-clock tests | Real raw recording ingestion/integrity/late-arrival/90day availability not verified |
| Provider replay deletion | Native tombstone exists, provider state Pending | Adapter not implemented; scoped delete credential present, permissions unverified |
| Source maps | Not uploaded; no upload/debug-ID integration yet | Optional credential present; selected server/tool compatibility unverified; basic error ingestion remains separately configured |
| Telegram | Adapter and dedupe/recovery mocked tests implemented | Token present; private chat missing, sending/receipt unverified |
| Email | Existing SMTP adapter, mocked alert/digest tests, structurally complete private config | Live transport/receipt awaiting opt-in |
| UptimeRobot | Operator instructions prepared | Separate account/monitor setup unknown, no monitor or call made |

No selected-provider limitation has yet been observed. Public snapshot-API warnings
are compatibility risks, not proof that this EU project cannot export. A metadata
row/URL is not an archive. None of capture/export/player can be called complete
from the synthetic lifecycle tests. Native Sprint1 work remains preserved; these
specific missing implementations must continue after authorization/project-format
inspection, within [PlanV1](live-verification-plan-v1.md).

## Prepared Next Action

[One consolidated bounded plan](live-verification-plan-v1.md) covers synthetic
analytics/errors, three short replay fixtures, capped project-only reads, independent
playback, optional private source maps, only new-test-recording deletion and exactly
two owner Telegram/two owner emails. It includes a25hour settled-recording recheck;
no production timestamp changes or synchronous day-long wait. No plan phase has run.

Private concrete destination/cap/message manifest:
`/home/frappe/teletena-operations-config/live-verification-plan-v1.json` (600).
Working/template files are separate. Keep owner_account blank. Keep live flag false
until owner approval; no provider calls beyond the already-authorized discovery.

## Repeatable Local Check

```bash
python3 scripts/operations_provider_preflight.py \
  --config /home/frappe/teletena-operations-config/providers.json \
  --expected-project 335848
python3 -m unittest discover -s tests -p operations_provider_preflight.py
```

Seven network-free tests pass: private permissions/symlinks, region/project/owner/live
flag validation, optional source-map independence, no/multiple exact matches,
single private-chat-only save, existing-chat preservation, neutral transport/webhook
failure and concurrent-change refusal. The explicit discovery flag is for an
owner-authorized retry after the setup message; validation alone makes no request.
