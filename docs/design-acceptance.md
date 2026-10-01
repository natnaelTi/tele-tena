# TeleTena redesign acceptance

Authoritative checklist against `design-system.md`. An unchecked gate is not a
pass. Browser evidence must name actual run, viewport, fixture type and limitation.

- [x] Save the authoritative specification and require it in AGENTS.md.
- [ ] Fetch/inspect main and PRs #3–#5; consolidate in dependency order.
- [ ] Preserve call cleanup/revocation, OTP, permissions, data and credentials.
- [ ] Record authentication/contact/onboarding model and permissions before code.
- [ ] Phone-first entry and separate code step; no contact enumeration.
- [ ] Secure email OTP/delivery setup and explicit password alternative.
- [ ] Resumable patient/clinician onboarding; no public clinician privilege grant.
- [ ] Original logo/wordmark/mono/reversed/favicon; 16/24/32 px checks.
- [ ] Licensed local Manrope/Noto Sans Ethiopic; exact tokens and contrast evidence.
- [ ] Reusable component showcase, keyboard/focus/associated errors/dialog behavior.
- [ ] Routes/layouts/features/hooks; App.tsx only composes application infrastructure.
- [ ] Public homepage, clinician invitation and compact disclosures.
- [ ] Patient home/discovery/appointments/account/payment/booking workflow.
- [ ] Clinician Today/requests/availability/services/care/earnings/profile screens.
- [ ] Dedicated administration and consultation/preflight screens.
- [ ] Clearly mark missing backend capabilities; no fabricated claims/statistics.
- [ ] Supported Playwright dependency setup and actual Chromium launch.
- [ ] Render/inspect/capture all requested screens at 390/768/1440 px.
- [ ] Check 320 px, 200% zoom, reduced motion, keyboard and Ethiopian script.
- [ ] OTP/permissions/booking/balance/migration regression suites.
- [ ] Full hosted two-browser media + Leave/rejoin/End regression, root cause fixed.
- [ ] Hosted initial/refreshed cached-token rejection (departed participant included).
- [ ] Review screenshots contain synthetic data only, no credentials/tokens.
- [ ] Review PR, checks on final commit, source PR accounting, conditional merge.

## Merge gate
No merge while the complete hosted End regression is unexplained/failing or the
integrated authentication/security/transaction checks fail. No production deployment.
