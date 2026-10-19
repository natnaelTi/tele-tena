# Compact Account Settings and Photo Crop — 19 October 2026

Runtime/packaged source: `f45cf77e919da6b4f9759fe69787d99e1c4b704a` on `feat/guest-first-mvp`, draft PR #47 (PR #46 ancestry retained). Subsequent screenshot/documentation commits contain no runtime changes.

Preview: http://127.0.0.1:8017/teletena/ · `teletena-mvp-presentation.localhost` · `/home/frappe/frappe/frappe-bench` (Frappe15/Python3.12). Existing owned web257763, worker257690, scheduler257695 and queue13917 remain running; HTTP200 and all41 packaged asset hashes match. These Python processes started at the notification checkpoint; `tele_tena/` and hooks are byte-identical because this Account change is frontend-only. No Vite, migration, dependency change, reseed, shared-service restart, merge or remote deployment.

## Implemented Micro-flows

- A stable Account title, desktop settings index with role-specific icons, and a compact native section selector on mobile. All settings are discoverable immediately. Selecting a section edits within Account, retaining entered parent form values across section changes.
- Overview summarizes identity/preferences, with the existing patient wallet/shared-care entries or clinician practice links. Personal details no longer occupy a large form on the overview. Patient history/text/private files have their own coherent local section; privacy, language/timezone, notifications, contact/sign-in and help each have a focused editor. Clinician professional introduction, care languages and private resume remain available. Complex practice/application/affiliation/shared-care workflows retain their explicit authorized links rather than being duplicated into a massive account form. Unsupported contact changes remain truthfully unavailable.
- A compact photo row with avatar, drag/drop/picker, formats/limit and current visibility. Selection opens a modal with a circular avatar guide, zoom, horizontal/vertical position, direct pointer drag, keyboard range controls and Reset. Nothing uploads before Save photo. Escape/Cancel discards the candidate; old saved photo remains. Save uses a512px JPEG crop and existing authenticated normalization/private-download/public-eligibility APIs. The server still enforces ownership, type, dimensions, size and publication eligibility. Browser candidate image/object URL/canvas stay in memory; no browser persistence, analytics or external image service.
- A failed upload keeps the crop available for retry and leaves the saved image unchanged. Busy controls prevent normal repeated submission. New copy uses English/Amharic/Afaan Oromo; translations are provisional.

## Evidence and Results

Private logs: `/home/frappe/teletena-guest-first/account-*.log`.

| Check | Actual result |
|---|---|
| Locked production build/TypeScript | Pass; exact runtime source above; all41 packaged hashes verified |
| Frontend lint | Pass,69 warnings/0 errors; existing hooks/render-purity warning debt is not represented as clean-warning output |
| `scripts/browser-account-settings.cjs` on main built app | Pass patient/clinician entries and local editors, typed value retention, 390/768/1440, compact photo row, native mobile navigation, crop zoom/position/drag/keyboard/reset, Escape/Cancel with zero uploads. No retained-site profile/photo/preference writes |
| Same browser script on Frappe16 | Pass against `teletena-guest-first-test.localhost` on compatibility Bench (Frappe16.2.1/ERPNext16.1.0/Python3.14.2). Real saves/reloads for both roles, selected crop pixel verified in the actual returned512px image, injected failed network request then successful retry, saved image unchanged on failure, cross-role private-photo denial. Fixture profile values/photos restored through authorized APIs; no direct database repair |
| Existing photo backend regression | `Presentation.test_profile_photo_owner_visibility_validation_and_revocation` passes: owner/reviewer/other-user denial, invalid format/content/size preservation, replacement revocation, clinician visibility and private cache headers; repeat photo-table patch preserved records. One focused test, not a full financial or hosted-call rerun |
| Actual Chromium200% | Pass both roles, outer1440/inner720/DPR2/visualViewport.scale1; mobile selector, form controls and scrollable crop action buttons accessible, Escape, sign-out success followed by authenticated endpoint/private inbox denial |
| Locales | Amharic/Afaan Oromo font and layout checks at1440/390 pass with no horizontal overflow; no preferences saved. Not native-language approval |
| Preservation | Original24 private manifests/provider/key files byte-identical; original site configuration values identical. No changes to registration/provider switches, credentials, balances, financial postings, notes or call authorization |

The first narrow-screen run exposed a compact-upload flex-direction collision: the old column direction combined with a new full-basis helper line caused horizontal overflow. It was corrected in the shared optional compact variant, not hidden with overflow clipping. The final run passes without clipping content. The upload hint explicitly retains the drag/drop affordance.

## Visual Comparison and Owner Review

References were rendered from `/home/frappe/teletena-design-reference` at matching dimensions/100%zoom:

| Reference/state | Application images | Comparison inspected |
|---|---|---|
| H011440/390, Account | `reference-h01-*` vs `patient-*` / `clinician-*` | Inter typography, restrained borders/radii, original dark wallet and settings row icon language retained. Explicit owner-requested deviation: desktop settings index, mobile native selector, read-only overview and compact photo row replace bulky repeated forms |
| H03Privacy1440 | `reference-h03-1440.png` vs `patient-privacy-sharing.png` | Existing privacy preview and consent wording retained inside the Account editor; actual encounter access history is an operational addition, not fabricated prototype content |
| H04Preferences1440 | `reference-h04-1440.png` vs notification/contact editors | Existing component styling retained while groups become separate compact local micro-flows; no fake settings or provider availability added |
| New photo crop state | `portrait-crop-1440.png`, `portrait-crop-390.png`, `*-crop-200-percent.png` | No exact prototype state exists. Existing shared dialog/buttons/inputs extended minimally. Circle guide, sliders, readable error/actions and small-screen/zoom scrolling inspected |
| Translated/mobile settings | `patient-am-*`, `patient-om-*`, role390/768 screenshots | Glyph coverage and wrapping inspected. Native phrasing and owner acceptance remain pending |

All paths above are within `docs/screenshots/account-consolidation/`; `disposable/` holds real-backend save/crop evidence. Fictional portrait previews were cancelled without uploading. Functional screenshots using color blocks deliberately prove crop selection; they do not replace portrait visual inspection. Reference balances/contact fields are not copied into real records. Clinical text, existing consents and historical disclosure remain unchanged.

## Owner Walkthrough

1. Patient Account: use the settings index (or mobile Account section selector). Edit Personal profile, move to Language & timezone and back: entered text stays. Save only when desired.
2. Open Medical history for saved text/private documents; Privacy & sharing for defaults/access history; Notifications for existing email/SMS preferences. Wallet and shared-care links remain on Overview.
3. Clinician Account: inspect Professional profile & practice, care languages, private resume and existing service/application/availability/earnings/affiliation links.
4. Drop or select a JPEG/PNG/WebP up to3MB. Adjust zoom, drag, or use arrow keys on position sliders. Reset and Cancel upload nothing. Save photo persists the selected crop; its public visibility still requires the existing explicit clinician choice and approved public eligibility.

Owner visual acceptance and native-language review are pending. No live SMS/email, physical-device calling, new financial suite, fresh installation or remote deployment is claimed for this frontend-only follow-up; valid unchanged evidence remains in the existing acceptance matrix. Temporary disposable browser server8029 is stopped after verification; the main preview and its owned processing remain running.
