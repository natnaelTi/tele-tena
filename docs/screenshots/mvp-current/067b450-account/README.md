# H01–H05 named account comparison

Built source067b450052d11c4ad3fcf83902ab8c5b8de389d4; presentation site at8017.
Real password sessions/backend queries; no API mocks or persisted mutations.
Patient and clinician sections, stable populated private-field label, draft preserved
across section navigation, capabilities match server, unchanged profiles/funds.
Paired English390/768/1440 images captured at100% zoom. Inspected H01desktop/mobile,
H03desktop/mobile and H04/H05desktop against extracted reference. Screenshot capture
alone does not establish every state’s fidelity.

Corrections: card checkboxes/primary privacy action, reference settings order,
shared-care link/notice, compact horizontal navigation that does not scroll the page,
readable site-specific sign-in rows, compact wallet typography. Financial values
remain actual; no test balances were reset to match the reference.

Remaining/intentional differences: demo ribbon/authenticated shell/tour button;
prototype gallery navigation omitted. Patient city/contact editing and age-range
sharing are not implemented by the existing profile contract; no fake controls.
H04 has real language/timezone controls but no fabricated notification settings.
H05 does not claim contact change/session management or OTP activation. Full pending,
error/saving/rejected and language/zoom state comparisons remain in the matrix;
owner acceptance is outstanding. The readonly test does not establish saving behavior.
