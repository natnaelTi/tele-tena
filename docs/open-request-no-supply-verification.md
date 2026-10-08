# Patient no-supply open-request browser verification

The production-built `/teletena/` app was exercised against
`tele-tena-pr12-fresh.localhost` with a seeded synthetic patient and the real
Frappe request APIs. The patient published an immediate audio request while
current published availability could not fit a complete session in the
configured 30-minute immediate window. The persisted request reported zero
eligible clinicians; the browser rendered the publication-time explanation,
kept the request open, and offered schedule-later and discovery paths. Choosing
schedule later preserved the description, service, language, audio format,
disclosure choices and price limit in the composer. The synthetic request was
then cancelled through the application and cancellation was re-read from the
backend.

The browser check is `scripts/browser-open-request-zero-supply.cjs`. It reads
the isolated site's synthetic review-account file locally, prints no account
or request identifiers, refuses to run when the selected patient already has
an open request, and cancels the request it creates. The verification screenshot
is [`screenshots/open-request/zero-supply-390.png`](screenshots/open-request/zero-supply-390.png).

This verifies the patient zero-supply and recovery route, not delivery to the
retained Review Clinician. Their persisted schedule begins at 08:00
Africa/Addis_Ababa, so at the observed 07:xx local time a 30-minute immediate
request correctly had no feasible clinician start. A later-window two-sided
offer/accept browser journey remains pending. Translation strings are
provisional pending native-speaker review.

The browser check passed on frontend source commit
`398f74318ae23c7fe35e22c66b33d71660fb07e1`; the final packaged review manifest
must be read from the current `/assets/tele_tena/review/release.json` after
the subsequent documentation/test commit.
