# Country selection and private history uploads

Phone entry has a native international country-code selector. The same-origin
country suggestion uses an offline DB-IP Country Lite MMDB; visitor IPs are not
sent to a lookup provider or stored by this feature. Country is only a suggestion,
never authorization, residency evidence, matching eligibility or an OTP rate-limit
identity. Explicit selection/typed input wins over late suggestions. Loopback,
private IPs or unavailable data fall back to Ethiopia and remain editable.

SMS Ethiopia remains Ethiopian-mobile-only. Other countries are selectable, but
the UI explains email access instead of pretending international delivery works.
Existing provider checks, phone normalization, abuse controls and site registration
switches are unchanged. No live SMS/email was sent as part of this change.

## Site-specific offline country setup

Download the monthly Country Lite MMDB from
[DB-IP](https://db-ip.com/db/download/ip-to-country-lite), verify the published
checksum, decompress and store outside Git under an owned private directory.
It is CC BY4.0; the phone form displays the required DB-IP link when it uses a
country suggestion. The local review uses October2026 data; country lookup is
approximate and VPN/proxy users can override it.

With the site Bench Python and existing optional MaxMind reader installed:

```bash
bench --site SITE execute tele_tena.country_setup.configure
```

Enter the absolute MMDB path and **only** the actual trusted proxy CIDRs. Empty
means direct HTTP. Never trust all sources (`0.0.0.0/0`/`::/0`). Behind the observed
Selfmade local nginx→Gunicorn arrangement, inspect its current peer address and
X-Forwarded-For append behavior before setting loopback CIDRs. The lookup walks
from the trusted peer right-to-left and ignores arbitrary forwarded headers from
untrusted peers. OTP rate limits deliberately retain their existing peer logic.
The helper does not install dependencies, change authentication switches or modify
framework/proxy configuration. If the optional reader is absent, manual selection
works and IP defaults await separately reviewed setup.

## Shared upload component

`FileUpload` retains the native picker, adds drop affordance, keyboard-operable
Choose file(s), busy/drag/disabled/focus states and useful size feedback. It is
used for profile pictures, resumes, scope evidence and history records. Existing
owner/reviewer/backend validation remains authoritative; a drop grants no access.
Single-document fields reject multi-file drops rather than silently losing files.

## Patient history

Both optional onboarding background and Account→Personal profile→Optional saved
history retain their textarea and add a multiple-file upload/list/download/remove
section. PDF/JPEG/PNG,5MB each; no fixed file-count cap,100MB owner storage budget
by default (`tele_tena_history_storage_mb` configurable). Files save immediately,
independently from the profile Save button; partial batches show saved files and
an explicit remaining-upload error. Same-byte/same-name retries are idempotent.

Additive v1.39 uses app-owned binary storage with owner-only command/download
APIs, matching the existing private photo/resume boundary. Generic Frappe File/
DocType URLs cannot retrieve these blobs. Content type/signatures/parsing are
validated server-side; encrypted/interactive/JavaScript PDFs are rejected. Downloads
are attachment-only, no-store, nosniff and sandboxed. No virus scanner is claimed.

**No automatic clinician sharing:** the existing history-sharing toggle applies
to textarea text only. Files stay private to the patient; clinicians, reviewers,
clinic members, other patients and guests cannot download them. Existing booking
snapshots are unchanged. File-specific encounter grants are outside this update,
not implied by uploading. A verified adult-consenting patient onboarding draft
can upload before completion only while that registration path remains enabled.

The owner can remove an uploaded private file; no clinical/financial historical
record or previously disclosed file is altered (these files have no encounter
sharing grants). No clinical bytes/text enter logs, browser storage or PWA caches.
New Amharic/Afaan Oromo strings require human review.
