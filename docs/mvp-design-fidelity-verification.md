# MVP design fidelity — active correction, not release acceptance

The user rejected the current visual implementation. This report records the
first correction checkpoint, not completion of the landing-to-booking slice or
MVP. Older reports do not supersede this gate.

## Source and runtime

- Branch `feat/mvp-release-handover`; draft PR #44 depends on draft PR #43.
- Built functional source: `9265aae327afa0eb7d615835b115d285324c38f8`.
  Later evidence-only commits do not change the application code in this build.
- URL: **http://127.0.0.1:8017/teletena/**.
- Bench `/home/frappe/frappe/frappe-bench`; site
  `tele-tena-pr12-fresh.localhost`. Gunicorn PID 392014, two workers, explicitly
  site-bound loopback WSGI; production packaged assets, no Vite server.
- Local reference: `/home/frappe/teletena-design-reference`, served read-only at
  `http://127.0.0.1:8044/?embed=1#<reference hash>`.
  All nine requested source files were inspected; actual inventory has 142
  entries. File hashes and reference hashes are in `mvp-screen-acceptance.json`.
- Original development site, existing records/credentials, Selfmade and shared
  background services were not modified. No schema migration or reseeding.

## Corrections

- Shared raw-button white foreground caused unreadable inactive hero chips.
  Bare buttons now inherit text color; explicit Button variants own action styles.
  Existing preflight actions were given explicit variants to preserve their
  presentation. Authentication/media authorization and cleanup logic unchanged.
- Supplied JPEG logo, existing matching bundled Inter weights, scoped landing
  layout, two role panels, clinician tools, public feature strip and navigation.
- Visible patient registration and clinician application links retain intent.
  Existing capability policies remain enforced. The invited site accurately
  explains that registration and SMS delivery are unavailable.
- Email selection no longer implicitly selects password when email delivery is
  absent. The user explicitly chooses password. Email-code unavailability is
  visible; the email code action stays disabled until configured.
- Booking uses a monthly date grid with only backend-generated available dates,
  a bounded time-choice area, timezone selection and preserved Back navigation.
  The server still authorizes/validates every reservation; this UI creates no
  new arbitrary-date acceptance path.
- New copy uses English/Amharic/Afaan Oromo dictionaries; translations are
  provisional. No native-language approval or full localized-layout acceptance.

## Checks actually run

- `python3 scripts/check_review_assets.py`: passed artifact hashes, app/PWA scope and exact configured-private-credential scan (zero matches).
- Locked production packaging with `python3 scripts/build_review.py`: passed.
  Build warning: existing LiveKit/main chunks exceed 500 kB.
- `npm run lint --prefix frontend`: passed with existing hook/purity warnings.
- Real MariaDB `tests/contact_auth.py` on the isolated site: **7/7 passed**;
  external email/SMS transport mocked in backend tests. This is not delivery.
- `browser-mvp-care-query.cjs`: actual built landing → existing patient password
  sign-in → discovery; care query preserved only in application memory and
  cleared on sign-out; URL/history/browser storage exclusion passed.
- `browser-authentication-flow.cjs`: real invited-site patient/clinician password
  sign-in passed. Explicit password choice and accurate password error passed.
  Its enabled OTP UI/error cases use frontend interception and **are not backend
  new-registration acceptance**.
- Actual authenticated calendar check: discovery → real offering → available
  date/slot → disclosure step → Back retains slot; 390/768/1440 no page overflow.
  **No appointment or reservation was submitted in this check.**
- Paired full-page captures: A01, A04, A06, C06 at 390/768/1440. No credentials
  or codes captured. C06 contains preserved synthetic test fixtures and is
  diagnosis evidence, not approved presentation content.

## Rendered comparison notes

Pairs: `docs/screenshots/mvp-design-fidelity/<ID>-reference-<width>.png` and
`<ID>-application-<width>.png`. Desktop A01/C06 and mobile A01 were visually
inspected, beyond overflow/assertion checks.

| Screen | Observed correction | Remaining differences / acceptance |
|---|---|---|
| A01 | Reference logo, matching hero width/headline breaks, two role panels, readable chips, tools and horizontal feature strip | Required demo ribbon/language selector/registration entry extend reference. Footer, touch spacing, exact feature copy/icons and all languages/zoom still need final comparison. Not visually accepted. |
| A04 | Phone-first entry retained; explicit registration links and truthful disabled-site state | Needs enabled-registration transport/browser journey and reference auth spacing. Current invited policy is intentionally not a working public registration fixture. |
| A06 | Email-only first step, explicit password selection, accurate delivery-unavailable message | Reference auth composition and enabled email OTP journey pending. No live email proof. |
| C06 | Monthly calendar replaces date strip; generated slot selection and Back work | Current sidebar shell, external session card and fixture names differ from reference. Compact slot scrolling is implemented after inspecting the first unbounded render. Calendar selection is functional; complete reference composition is pending. |

The screen matrix now keeps functional and visual evidence separate for every
MVP route/state. An inherited “implemented” flag is not visual acceptance.

## Remaining release gates

1. Finish patient home/discovery and booking shell/composition, then all remaining
   MVP patient/clinician/reviewer screens and state-specific paired comparisons.
2. Real persisted patient and clinician signup with controlled local-only
   transport, wrong/expired code and interrupted onboarding; retain invited
   policy tests. Do not expose codes publicly or use a fixed OTP.
3. Dedicated presentation setup/data and centrally defined illustrative prices;
   preserve historical test/financial/clinical records. Do not rename fixtures.
4. Working two-adult couples appointment/call/note recipients, as required by the
   MVP scope; optional relationship links alone do not fulfill that gate.
5. Current dedicated scheduler/worker routing and earnings checks, fresh install,
   owner-level migration/reconciliation, and required financial/privacy/media
   regressions. Shared older worker/scheduler processes remain untouched; current
   job execution is not established by this visual checkpoint.
6. Actual 200% browser zoom, all MVP responsive/language states and tours.

No merge, remote deployment, live SMS/email delivery, real-money operation,
physical-device media test or native translation approval occurred.
