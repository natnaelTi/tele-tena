# Demonstration consultation extensions

## Data model and decisions

`tt_consultation_extension` is an app-private, append-only-per-state-change
record linked to one booked appointment and its authenticated patient and
clinician. It snapshots block duration, integer ETB minor-unit price, the
published offering rate, appointment end before the block, expiry and the
versioned extension policy. A unique appointment/retry key makes proposal
retries idempotent. Transaction history is recorded in the existing balanced
demonstration subledger and simulation activity log; no parallel wallet system
is introduced.

For this demonstration, a block is 15 minutes by default and its price is the
published offering price prorated by integer ceiling against the booked session
duration. Both settings are site configurable. The offer expires after 10
minutes by default. These are configurable demonstration defaults, not an
approved commercial policy. The clinician proposes one block at a time, up to
60 added minutes by default. The patient sees the exact duration and total price
before acceptance. There is no undisclosed fee or automatic extension charge.

Acceptance reserves the full block amount from the patient's available balance
and extends the appointment's effective end time under the clinician conflict
lock. The originally booked duration remains separately recorded. The clinician
must explicitly start an accepted block after its `start_after` time. If the
call ends first, any accepted but unstarted block is released exactly once.
Only explicitly started blocks are included in the clinician's earnings when
the consultation is later finalized. Finalization continues to apply the
booking's snapshotted fee and withholding policy. Call duration alone never
starts or charges an extension.

## States and permissions

`Proposed → Accepted | Declined | Withdrawn | Expired`;
`Accepted → Started | Released`; `Started → Settled` on explicit consultation
finalization. Patient-only acceptance/decline; clinician-only proposal,
withdrawal-before-start, and start; the existing appointment participant and
active call checks apply to every command. Financial and consultation admin
roles do not inherit clinical note access.

Only one unresolved extension offer can exist per appointment at a time. An
accepted block reserves clinician time even before it starts. The server
revalidates call state, offer expiry, available funds, subledger projection and
conflicting clinician appointments at acceptance. Existing appointment and
balance checks use the same global transaction gate and wallet lock order.
Unanswered offer expiry is processed by a once-per-minute Frappe scheduler job;
the authenticated status query also reports an elapsed offer as expired without
mutating state, and a retry/accept command enforces expiry transactionally.

## Acceptance criteria

- An authorized clinician can propose a configured block during an open,
  booked consultation; the patient sees its exact terms and expiry.
- The patient can accept once. Insufficient funds leave the offer retryable
  while valid and create no partial posting; decline and changed retries cannot
  reserve funds.
- Concurrent acceptance/retries produce one reservation and one effective-end
  extension. A conflicting appointment rejects acceptance atomically.
- Only the clinician can explicitly start an accepted block and only after its
  permitted start time. Ending first releases the unstarted reservation once.
- Consultation finalization consumes base plus explicitly started blocks once,
  using the accepted financial-policy snapshot. An accepted but unstarted
  block is never earned.
- Patient and clinician APIs expose only the participant-authorized extension
  terms and state. Generic DocType access is denied.
- Existing balances, appointments and earnings remain unchanged by migration;
  repeat migration is safe.

Real money, provider settlement, external payout, production extension pricing,
and automatic duration-based charges are out of scope.
