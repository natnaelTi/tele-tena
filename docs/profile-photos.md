# Profile photos — local MVP addition

Owners can upload, replace and remove JPEG, PNG or WebP photos in Account.
Reviewers have a separate `/admin/account` route. No role, credential or scope
approval follows from a photo. Patient and reviewer photos are owner-only.
Clinicians explicitly choose publication; patient discovery can display a photo
only for a currently eligible clinician. Suspension/scope revocation immediately
removes download authorization. No patient photo is added to an encounter,
request, shared-care disclosure, care record or LiveKit metadata.

The v1.38 patch creates one isolated `tt_profile_photo` table with an opaque ID,
owner, normalized image bytes, publication choice and modification timestamp.
This uses the existing command-storage architecture for a small private raster
asset, not a competing clinical record model. There are no Frappe File records
or public/private-file paths to bypass custom authorization, and no generic
DocType API for the table. Site database backups include photo bytes. Migration
is idempotent and leaves all existing records unchanged. Seed setup is explicit,
never automatic during installation or migration.

Server limits: 3 MiB input, 32–4096 pixels per dimension, at most16 million pixels,
one frame. The server decodes and resizes to a512px square JPEG, dropping EXIF
and other source metadata. SVG/executable/invalid/animated images are rejected.
Images are served with authenticated access, `private, no-store`, `nosniff` and
opaque IDs. Service-worker rules continue to exclude all API responses. Removal
or replacement invalidates the previous ID. A recipient who previously saw or
saved a published image may retain it; removal cannot retract that copy.

## Fictional demonstration portraits

The four original, AI-generated fictional portraits are under
`assets/demo-portraits/{patient,clinician,second_clinician,reviewer}.png`.
They are outside public assets. They do not represent real patients or experts.
The built-in imagegen tool generated each separately, using centered head-and-
shoulders realistic portraits, Ethiopian adult fictional identities, neutral
backgrounds, everyday/professional plain clothing, soft natural light and no
text, logos, credentials or medical props. Patient woman30s; clinician woman40s;
second clinician man40s; reviewer woman50s. No real-person references were used.

Explicit local-only setup:

```bash
cd /home/frappe/frappe/frappe-bench
bench --site teletena-mvp-presentation.localhost execute tele_tena.demo_photos.install
```

The command requires that exact site and its existing fictional seed metadata,
uses owner upload commands, adds only missing photos, preserves any current
photo and changes no balances, appointments, profiles or approval decisions.
Demo clinician portraits are published; other portraits are owner-only.
Newly registered user accounts are not assigned fictional portraits.

Photo copy translations are provisional Amharic/Afaan Oromo and need native
review. Owner review of the rendered account controls remains required.
