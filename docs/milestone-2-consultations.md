# Milestone 2: authorized consultations

Recorded before implementation on 2026-10-01. Depends on merged foundation and
milestone 1 (`main` at the PR #2 merge commit). Demonstrations use synthetic
accounts/bookings and LiveKit only; no SMS activation or real funds are needed.

## Agreed rules and configurable demonstration defaults

Only the authenticated patient and clinician attached to a booked appointment
may enter its room. A guessed appointment or room identifier confers no access.
Tokens are short-lived and scoped to one opaque room and one opaque participant
identity. Name and metadata claims are omitted. Audio/video is human-to-human;
no recording, transcription, agent, notes, extension charge or clinician earnings
release is included. A participant leaving only disconnects that participant.
Only the appointment's clinician may end the consultation; ending closes the room
and prevents future token issuance. Either participant may leave and later rejoin
while the session remains open and the appointment window permits it.

The demo defaults allow joining from 15 minutes before appointment start until
30 minutes after its scheduled end. These values are configurable in site config
(`tele_tena_consultation_early_minutes` and
`tele_tena_consultation_late_minutes`); they are not agreed product policy.
The participant token expires after 5 minutes (configurable as
`tele_tena_livekit_token_seconds`, bounded server-side to 60–600 seconds).
These are connection/security defaults, not appointment extensions or billing
rules. No automatic extension or automatic reservation release occurs.

## Data model

- Consultation: one record per appointment, opaque random primary key,
  opaque LiveKit room name, state Open/Ended, creation/end timestamps and the
  clinician who ended it plus a private provider-close confirmation flag. Created
  lazily on the first authorized room request.
- Consultation participant mapping: opaque patient and clinician identities
  generated independently of Frappe users. No account identifiers or names are
  sent as LiveKit identity, name, metadata or attributes. Appointment linkage
  remains private in the application database.
- Existing appointment remains Booked; consultation state is separate. No
  financial or clinical content is added to the LiveKit room.
- LiveKit URL/key/secret are held in a mode-600, untracked file in the site's
  private directory. The public connection URL and participant token are returned
  only to the authorized browser over the authenticated, no-store API.

## Permission matrix

| Actor | Allowed |
|---|---|
| Guest | No consultation discovery, state, token, leave or end access |
| Booked patient | Read own consultation state; request own join token; leave own connection |
| Booked clinician | Read own consultation state; request own join token; leave; explicitly end consultation |
| Other authenticated account | No state or token access, even with guessed appointment/room ID |
| Approver / administrator role | No participant token by virtue of role; must be the appointment participant |
| LiveKit participant token | Join exactly one room; publish microphone and camera (or microphone only for audio-only); subscribe; no room administration, room creation/listing/recording, data publishing or other service grants |

Server authorization checks session identity, participant side, Booked appointment,
and current join window on every state/token request. Database uniqueness and a
transactional create-if-absent mapping ensure one room per appointment. End is
idempotent; room deletion is retried on repeated clinician end requests if needed.

## Workflow states

- `Not started`: no consultation row exists; appointment is Booked.
- `Open`: first authorized room request inside the join window creates one opaque
  room. Either participant can join/rejoin while still inside the window.
- `Ended`: clinician explicitly ended it; LiveKit DeleteRoom disconnects all
  participants. New joins are denied permanently. Participant leave never sets
  this state.
- Transport UI states: `Checking devices`, `Ready`, `Connecting`, `Connected`,
  `Reconnecting`, `Disconnected`, `Ended`, or a recoverable failure. These UI
  states do not change appointment or financial state.

## Acceptance criteria

1. Authorized patient and clinician can create/join a room only during the
   configured window; unrelated accounts and guests cannot read or join it.
2. Ended consultations deny new join tokens; clinician end closes an active room;
   failed close remains visibly retryable by the clinician; participant leave
   leaves the consultation open for rejoin.
3. Decoded tokens prove one room, opaque identity, short expiry, no PII/metadata,
   no admin/record/data grants, and microphone-only publishing in audio-only mode.
4. Preflight obtains browser device permission before explicit Join; the connected
   UI supports real audio/video, mute, camera toggle, audio-only, connection and
   reconnection feedback, Leave, and clinician-only End.
5. Persisted API state remains unchanged for funds, appointment price, duration,
   disclosure and clinician earnings. No recording/transcription/AI/extension billing.
6. English, Amharic and Afaan Oromo keys exist; non-English text is visibly
   provisional and requires human review.
7. Automated checks cover authorization/window/ended/rejoin/token restrictions
   and disclosure-safe aliases. Two independent browser clients exchange actual
   media against a real LiveKit server; automated fake-media evidence is labelled
   separately from human/device testing. Existing regressions, build, lint and
   migration checks are reported accurately.

## Unresolved policy

The early/late join limits, token TTL, room retention after disconnect, and any
future session rescheduling/cancellation effects require product approval before
pilot. This milestone uses only the configurable demonstration defaults above.
LiveKit credentials and production hosting are not yet configured. HTTPS is
required for remote mobile browser device access; development exposure must be
limited to the application route and must not publish the Bench administrator UI.
