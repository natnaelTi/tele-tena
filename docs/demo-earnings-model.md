# Demonstration earnings policy and ledger model

This is an explicitly simulated operational subledger, not custody, payment
processing, ERPNext accounting or external settlement. Existing `tt_ledger`
remains an append-only simulation activity log; it is not relabeled as a
double-entry journal.

## Demonstration policy decisions

| Policy | Demonstration rule | Production status |
|---|---|---|
| Platform fee | 0 basis points; no commission is inferred | Unresolved; must be disclosed/agreed before real transactions |
| Withholding | Site setting `tele_tena_demo_dispute_window_minutes`, default 60 minutes after explicit consultation finalization | Demonstration default only |
| Existing completed appointment with reserved funds | Preserve wallet and reservation; create a `LegacyHold` case for authorized review. Never infer settlement from `Completed` or End | Must be resolved before launch |
| Pre-finalization cancellation | Existing accepted policy snapshot returns the full patient reservation exactly once | Demonstration only |
| Post-finalization refund/cancellation | Do not edit or reverse history automatically. Freeze affected earning and send for authorized dispute resolution; unsupported already-requested payout blocks automated refund | Production policy unresolved |
| Dispute/release race | Serialize on the earning row. A dispute committed before release blocks it; release committed first requires a compensating, audited resolution | Operational demonstration only |
| Payout | Request reserves clinician available earnings. Cancellation releases reservation exactly once. No provider invocation and no `Paid` state without an explicit simulated settlement event | Real transfer disabled |

## Balanced posting accounts

Use exact integer ETB minor units. Every journal has a stable event reference and
idempotency key, and at least two lines whose debit and credit totals balance.
Correction is by a compensating journal, never an edited/deleted posting.

| Event | Debit | Credit |
|---|---|---|
| Initial migration opening | Demonstration opening-control | Patient available / patient reserved |
| Simulated deposit | Demonstration cash-clearing | Patient available |
| Booking reservation | Patient available | Patient reserved |
| Supported pre-start cancellation/decline/expiry | Patient reserved | Patient available |
| Explicit finalization | Patient reserved | Clinician pending earnings |
| Eligible release | Clinician pending earnings | Clinician available earnings |
| Payout request | Clinician available earnings | Clinician payout-reserved |
| Payout cancellation | Clinician payout-reserved | Clinician available earnings |

Opening journals are an additive cutover snapshot of existing wallet balances.
They do not replay old deposits or reservations. Historical `Completed`
appointments with no matching release remain reserved and receive review-only
legacy holds; migrations never create pending or available clinician earnings
for them. A reconciliation report must surface any wallet balance that cannot be
represented without guessing and stop the cutover rather than altering it.

## Lifecycle and authorization

Appointment, call, documentation, dispute and earning states remain separate.
Only the treating clinician explicitly finalizes a note after call End; that
transaction atomically consumes the appointment reservation and creates one
pending earning under the accepted zero-fee/withholding snapshot. A retry returns
the same earning/posting. Scheduled release uses server time and unique posting
references, and a hold/dispute locks out release until a reviewer records an
audited resolution. A financial reviewer can access this workflow without
receiving clinical notes.

Only the owner clinician reads their earning and payout rows. Patient and
clinician activity views derive from the same journal references and must
reconcile. A payout is `Requested`, `Processing`, `Cancelled` or `SettledDemo`;
the confirmation states that no external transfer occurs. There is no real
settlement route.

## Acceptance arithmetic

With a patient opening balance of ETB 1,000 and a zero-fee ETB 300 booking:

1. Booking: patient available ETB 700, reserved ETB 300.
2. Explicit clinician finalization: reserved ETB 0, clinician pending ETB 300.
3. After the configured dispute window: pending ETB 0, available earnings ETB 300.
4. Payout request of ETB 200: available earnings ETB 100, payout-reserved ETB 200.

Each row must reconcile to balanced, immutable journals. This arithmetic does
not imply an external payment or bank transfer.
