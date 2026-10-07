# Immediate-care service policy

Status: demonstration workflow specification. Immediate-care activation is a
manual service-level safety decision; it does not follow automatically from a
clinician's general or per-scope approval.

## Data model

- `Tele Tena Service.immediate_care_enabled` remains the effective switch for
  a service definition. It is false by default for new services.
- A private app-owned `tt_immediate_service_policy_event` append-only log
  records service, previous and resulting state, reviewer account, reason,
  service definition version and server timestamp.
- The service record and its policy event are written in one transaction under
  the global TeleTena mutation gate and a row lock on the service definition.
- Generic DocType edits may not change the effective switch. The guarded
  application command is the only write path.

## Permission matrix

| Actor | View policy queue | Change policy | View patient request/clinical data |
|---|---:|---:|---:|
| Tele Tena Approver | Yes | Yes, with recorded reason | No, unless separately authorized for a specific clinical workflow |
| Administrator without approver role | No | No | No implicit access |
| Clinician | No | No | Only requests delivered to that clinician, disclosure-limited |
| Patient | No | No | Own request and offers |
| Guest | No | No | No |

Approvers see service configuration and audit history only. This permission
does not make them eligible to read patient records, request narratives, or
consultation notes.

## Workflow states

The effective service state is `Disabled` or `Enabled`. Each authorized change
appends a policy event. `Enabled` requires an active reviewed service definition
(`Active` with clinical review approved), or a `Legacy test` definition on the
explicitly bound review site. It never enables a Draft, Retired, or
clinically unreviewed service. New and migrated services remain disabled unless
already explicitly configured.

Disabling is refused while unexpired immediate requests for the service remain
open. This avoids showing offers that cannot pass the same policy check at
acceptance. Existing appointments and financial records are never changed.

## Acceptance criteria

- Approver-only query and command; unauthorized roles and generic DocType writes
  cannot read or change the policy.
- A valid change requires a reason, is audited with before/after state, and is
  atomic; duplicate retries do not add a second event.
- Reusing a key with changed state or rationale is rejected, and generic
  service DocType writes cannot change the setting.
- Enabling a Draft, Retired, or unreviewed active catalog service is rejected.
- A disabled service produces `immediate_policy_required` in clinician
  readiness; after explicit approval, it no longer does, while language,
  presence, capacity, scope, and schedule checks remain independent.
- Disabling cannot invalidate active immediate requests; direct and open-request
  booking checks continue to enforce the effective state.
- No service is enabled by migration, installation, demo funding, or signup.

## Observed local synthetic failure

On 2026-10-08, read-only inspection of the retained `Review Clinician` returned
`language_required` and `immediate_policy_required`. The saved care-language
list was empty. The published offering had an approved scope and schedule, but
its service was a `Legacy test` definition with `immediate_care_enabled=false`.
This reconciles the user-visible “available” toggle with the empty inbox: the
toggle is a short-lived presence lease, not an override for language or service
policy. No existing profile, service, schedule, request, appointment, or balance
was modified by this inspection.

The `tele_tena_demo_immediate_care_enabled` fallback is an explicit
site-scoped demonstration switch for legacy test data, not a default. New
catalog services use the audited service-level review command described here.
