# Navigation, Private Previews and Encounter Photos — 29 October 2026

**End-to-end demo candidate: ready for owner review and guarded operator deployment.**
**Final localized release: blocked pending genuine independent language approval.**
No workbook draft was imported. Demo readiness uses existing permitted translations
and documented English fallbacks; it is not production clinical/legal/payment or
native-language acceptance. No merge or remote deployment occurred.

## Candidate and Preview

- Immutable installation/build pin: `553a6190b4c4a0431dc5126fc6d2d095e50f5faa`.
- Branch `feat/offline-telebirr-mvp`, draft [PR50](https://github.com/natnaelTi/tele-tena/pull/50), dependent on draft PR49. Earlier PR ancestry is preserved.
- Owner preview http://127.0.0.1:8017/teletena/ ; site
  `teletena-mvp-presentation.localhost` in `/home/frappe/frappe/frappe-bench`.
  Retained Frappe15.121.2 / ERPNext15.121.6 / Python3.12.3, app0.1.0 / schema v1.49.
- Isolated compatibility Bench `/home/frappe/teletena-compat/bench`:
  Frappe16.2.1 / ERPNext16.1.0 / Python3.14.2 / Node24.13.0.
  Browser fixtures use `teletena-payments-v147-fresh.localhost`:8021 with private
  random OTP capture and mocked outbound adapters. Existing fixture names are
  historical; native migration loads the current application explicitly.
- Current owner-site payment mode **Offline**, preserved. No provider/access,
  signup, policy-publication, password, balance or Amazon/shared-dependency change.
- Subsequent source commits add only this evidence, guides, screenshots and test
  harnesses/review artifacts. The packaged runtime pin above remains exact; inspect
  `git diff <pin> HEAD -- frontend/src tele_tena` before claiming equivalence.

## Completed Changes

The authoritative matrix remains `mvp-screen-acceptance.json`, revision
`attachment_photo_revision_2026_10_29`. Historical screen/reference evidence stays
intact. These changes reuse its B06, D08, E02/E13, F10/F11, H01/H03 and N07/N08
compositions and the existing shared Dialog/Avatar primitives. Private preview is
an owner-requested operational state without a separate static reference screen.

- Patient My Requests and Shared Care are primary links, absent from More. The
  patient-only mobile/compact-width rail has deliberate horizontal scrolling,
  keyboard access and minimum-width targets. Other roles retain their navigation.
- Receipts open an authorized in-app dialog with original filename, purpose,
  loading/error/retry, image fit/zoom, Close and explicit Download. Opening is not
  downloading. Native supported PDF rendering has an explicit download fallback.
- Final clinician review groups Identification, CV, Professional License, each
  credential's own title/description/files and retained earlier evidence. No upload
  controls are duplicated there. Missing selections are labeled honestly; viewing
  is type=button and does not submit/reset the application or change ownership.
- Clinician photos are projected into previous clinicians, appointment/detail/care
  records and private offer cards. Temporary SQL account fields are removed before
  serialization; raw private File paths are never exposed.
- **Latest owner correction:** encounter avatars sit immediately to the **left of
  the person's name**, in the identity element. Generic page headings have no photo.
  This covers appointment rows/cards, consultation/finished records, care records,
  participant disclosures and preflight/call information. Media-left/details-right
  consultation composition remains intact; new identity rows are compact.
- Patient Account → Privacy & Sharing includes **Share My Profile Photo With My
  Clinicians**, with recognition/masking and withdrawal explanations. It saves
  independently of name/history/file choices. Public clinic membership, competing
  offers, unrelated clinicians, partners and general reviewer status grant no access.

## Permission and Retention Decisions

`tt_patient_photo_preference` is additive. INSERT IGNORE enables only missing
preferences, including new patient profile creation, and preserves explicit opt-outs.
There was no earlier treating-clinician photo preference. The existing `published`
photo flag controls clinician public photos; patient `published=0` was not a patient
sharing choice. Name/history opt-outs remain independent and unchanged. Migration
creates no historical consent event and rewrites no encounter snapshot.

Encounter image URLs contain opaque appointment/participant references. Every
request rechecks the current viewer's appointment authorization, individual couples
consent and current photo preference. The URL resolves current bytes, so replacement
works without retaining an old image grant. Responses are private/no-store and use
fixed `profile.jpg`, revealing no original filename/contact/legal name. A patient
cannot use a partner's setting to retrieve that partner's photo. Reviewers gain no
new patient access. Clinician public-photo restrictions remain in force.

Visible avatars revalidate while active every30 seconds and on returning to a tab;
withdrawal rejects the **next image request immediately** and removes the visible
image on that bounded refresh/navigation. Object URLs are revoked and pending fetches
aborted on replacement/unmount. Previously viewed images cannot be recalled. Historic
clinical disclosures/audit records are preserved rather than reused as a permission
bypass. Photos are a current identity preference, not a new clinical-record snapshot.

Attachment previews fetch the existing permission-checked endpoints with no-store,
allow only JPEG/PNG/PDF and retain backend size/type/PDF restrictions. Responses and
site-wide headers/download behavior are unchanged. A new owner-only legacy-CV adapter
revalidates older header-only-checked PDFs using the existing safe PDF validator
before preview, and returns no-store. Original retained files are not rewritten.
No HTML injection, persistent document storage, public-file conversion or tokenized
public URL is introduced. The dialog cancels/revokes temporary resources on closure.
Native PDF plugins vary by browser; full Chromium PDF rendering was inspected;
headless-shell's unsupported plugin is not counted as visual proof.

## Verification Actually Performed

Private logs/artifacts: `/home/frappe/teletena-attachment-release/` (outside Git).
All test users/evidence are synthetic. Existing presentation data was not reseeded,
refreshed or reset. No live SMS/email, transfer, refund or payout was triggered.

| Check | Result |
| --- | --- |
| Focused real Frappe16 backend |31 pass:10 photo/attachment/default/recipient/projection tests plus21 retained Offline/Wallet payment regressions; includes duplicate actions, direct-payment finalization, private note isolation and couples payer/consent behavior |
| Additional couples withdrawal |1 focused pass: consent withdrawal denies the treating-clinician photo request even while that participant’s photo-sharing preference remains enabled |
| Professional onboarding |9 pass,100 protected existing tables preserved |
| Notifications |10 pass, including preferences, reminders, privacy and idempotency; adapters mocked |
| Care-language catalog |3 pass; normalized care languages remain separate from interface locales |
| Localization/backup/preservation tools |21 pass, including independent approved-only imports and stable keys across source-line ordering |
| Fresh target-compatible schema |Native v1.49 install plus two migrations pass; empty professional/payment evidence, bundled reference catalogs, signup/provider switches off and Wallet default unchanged |
| Restored populated upgrade |Full verified pre-upgrade backup restored to a disposable clone;101 protected tables /17,937 original rows unchanged,2 new defaults only,0 reviewer grants; strict repeat migration and private/config preservation pass; clone removed |
| Retained preview migration |Complete database/public/private/config backup; native v1.49 migration preserves101 original tables /18,757 rows and25 private/config files before browser test activity |
| Built guest/direct booking |Directory → profile → exact offering auth return → valid language → direct payment → private receipt → separate clinician verification → confirmed appointment/ledgers passes |
| Built Requests |Guest draft → auth/restoration → publication → two eligible clinician inboxes/private offers → patient selection → direct payment/verification → confirmed appointment/reload passes |
| Built navigation/receipts |Primary links/no sidebar duplicates, Back/Forward, mobile rail; both authorized roles' receipt previews, zoom, close/reopen, focus return, Escape and zero automatic downloads pass |
| Failure/stale fetch UI |One injected transport failure shows error, real-backend Retry succeeds; closing a delayed request and reopening remains correct. No mocked success responses used |
| Built new clinician |Private random OTP → grouped professional profile/evidence → final review filenames by section → image/PDF preview/close → reload → submitted pending application passes |
| Reviewer |New submitted application and authorized professional evidence dialog; existing Financial Configuration access verified without changing decisions/mode |
| Privacy UI |Save/reload, authorized clinician image, immediate denied GET after opt-out, active-avatar fallback and restored fixture preference pass; original photo is never replaced during fixture setup |
| Placement/preflight |Name/avatar geometry asserted with avatar on left and no avatar in page-title header; separate-role preflight at1440x900 passes with fake local devices, no Join/provider claim |
| Responsive/keyboard |Affected views390/768/1440; actual Chromium200% (720CSS/DPR2/visualViewport1), en/am/om, focus trap/Escape and scrollable primary rail pass |
| Build/lint/assets/PWA |Locked production build and lint pass with nonblocking warnings; exact manifest/dictionary hashes, secret scan, private-cache exclusions and real offline/online recovery pass |

Existing Account preferences/photos were restored after isolated browser toggles;
only a newly created synthetic test photo was removed. Historical clinical/financial
rows were never rewritten to improve screenshots. Successful browser reads/registrations
naturally add session/login/audit/test records; migration preservation is verified
on a restored quiescent clone, not concealed by resetting those legitimate records.

The new UI/placement is tested on the current build; earlier backend/schema results
are reused where code/schema is identical. Fresh v1.49 schema was tested before later
read-only preview/projection/placement changes; there is no subsequent schema delta.
The compatibility Bench retains an older separate app checkout, so current-source
native migrations/tests explicitly prepend this repository rather than assuming it
is the active editable package.

Unchanged evidence reused: hosted LiveKit participant/Leave/rejoin/End/revocation,
continuous scheduler/release/restart, concurrency and private-file/generic-API gates,
individual/couples notes/recipient flows, and saved-sign-out/same-user onboarding
recovery from `offline-telebirr-verification-2026-10-28.md` and the existing matrix.
Current31-test suite additionally uses fake provider join/End for real-database
finalization; that is **not** hosted or physical-device calling. A further repeated
OTP recovery attempt reached the isolated test contact's unchanged resend/rate
limit; it is **not claimed as a new passing replay**. No counters were erased,
expiry weakened, contact/IP spoofed or owner-site access switch changed. The new
attachment review's close/reload is verified; its form/save/sign-out code is unchanged.

Owner-site owner reconciliation:11 patients /2 clinicians /22 accounts, zero
projection/obligation/journal mismatches or unbalanced journals. Browser fixture
site:2 patient owners /4 accounts, all mismatch counts zero. The separate retained
guest-first fixture's previously documented clinician obligation discrepancy remains
preserved; no financial repair was attempted. Hosted deployment stops on any actual
baseline discrepancy rather than manufacturing a balancing entry.

## Localization: Two Independent Outcomes

The reviewed dictionary is unchanged, SHA256
`ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356`, zero independently
approved workbook rows in either locale. Existing English/Amharic/Afaan Oromo
provisional behavior and truthful fallbacks remain available for this **demo**.
`localization/attachment-photo-delta.csv` contains all new/changed app-owned copy.
The catalog contains8,415 rows; the new/changed-copy delta contains38 rows. Current workbook reconciliation records355 technical exclusions,3 removed-source review entries and83 new keys against its older baseline, with no fatal key/hash mismatches and no human approval. The original workbook and earlier approval package are preserved outside Git.
Current reconciliation is in the new private `localization-review/` folder; no
human attribution or status was invented and no draft-preview bypass was added.

Two unchanged Reason/Reason: entries had exchanged keys because source-location
strings crossed a line-number sorting boundary. Established key/context/English
identities were restored from the pre-sprint catalog, and extraction now reuses
those keys even if discovery order changes. A dedicated regression prevents this
false source-hash conflict. Evidence-purpose wire comparisons are excluded without
removing explicit display copy. No workbook keys/English/hashes were changed.

**Final localization** still requires independent native human review, genuine
approvals, validated per-locale import, a new verified immutable pin and rendered
review. Policies retain actual draft/publication status. Native-language acceptance,
owner visual approval, physical-device calls and consenting live message receipt
remain separate from automated/technical demo acceptance.

## Owner Walkthrough and Selfmade Handoff

Use the existing private accounts at:
`/home/frappe/frappe/frappe-bench/sites/teletena-mvp-presentation.localhost/private/tele_tena_presentation_accounts.json`.
Choose Use Email Instead → Use Password Instead. No passwords were reset.

1. Patient: Home → My Requests / Shared Care directly from the primary navbar;
   mobile users scroll the rail. More contains neither destination. Inspect an
   appointment and record: avatar is left of the clinician's name, not the page title.
2. Patient payment → Open Private Receipt: inspect filename, zoom/fit and Close;
   opening must not download. Download is explicit. Account → Privacy & Sharing
   controls the current photo separately from name/history/individual history files.
3. Clinician: inspect the same payment, appointment and care record; patient avatar
   is left of the authorized encounter name/alias. Withdrawal gives a normal fallback.
   Final application review shows filenames under their own document sections.
4. Reviewer: Applications → Private Documents → Open Attachment; ID still requires
   its specific assignment. Individual service/language decisions remain separate.
   Financial Configuration is available under the existing authorized role only.
5. Existing individual/couples records and summary recipients remain intact. Do not
   create real transfers or send live provider messages for a deployment smoke test.

[Selfmade update/backup/recovery guide](selfmade-translation-update.md) now provides
explicit `demo` versus `localized` purposes, exact immutable checkout, read-only
baseline/loaded launcher checks, init-versus-resume backups, dependency preservation,
public-only permissions, target migration, scoped restart, HTTPS/PWA verification
and pre-/post-migration recovery. Demo no longer fails solely for incomplete final
localization; the approved-only importer remains unchanged. Remote installed SHA
and current services must be observed by the operator; older/unrelated ancestry
requires a specific upgrade plan. No Nginx/Supervisor regeneration, shared repair,
Amazon patch change, reseed, mode cutover or provider/credential change is prescribed.

Restart locally using [local-preview.md](local-preview.md); the normal Bench alone
does not start8017. Review [before/after screenshots](screenshots/attachment-photos/README.md).
Private transferable approval package: `/home/frappe/teletena-attachment-release/TeleTena-Attachment-Photo-Language-Review.zip`, SHA256 `df963ab94a2f5f110ccd289466eaf9424a68facbab42df48020ec5ebc7b3a7d8`. It contains the separate annotated working copy, issue/correction/source-delta reports and per-locale review exchange, with no invented approvals.

The owner retains final acceptance. This task changed no public roadmap website.
