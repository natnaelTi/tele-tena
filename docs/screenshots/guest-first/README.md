# Guest-first paired captures

Capture source: `cd995539be4d4fd583358082f3bb324a8e4b6d94`, production-built
8017 presentation application. Reference: local extracted source on8044.
`capture-manifest.json` records the identical viewport widths and exact reference IDs.
The compatibility registration/file/browser uses the same UI build and the binary
snapshot fix in c637893. No screenshots contain actual verification codes/passwords.

`*-app-*` and `*-ref-*` are matching viewport pairs. Full-page captures retain scroll
regions. `*200-percent*` are **actual browser zoom** viewport captures via CDP at
outer1440/inner720, DPR2; `-scrolled` shows the lower scroll region. They are not
CSS zoom or a small emulated screen. Amharic/Oromo captures require translated
headings and rendered fonts; they do not establish native-language approval.

| Prefix | Reference / operational state | Codex inspection / specific difference |
|---|---|---|
| landing | A01 welcome | Same two-audience hero/practice preview;AI query/chips removed by new direction;ribbon and real auth methods retained |
| phone / code-error | A04 / A05 | Phone-first plus real country selector, explicit alternatives, empty-code error/cooldown;no prototype credential bypass |
| directory | C02 care | List/card/price-action hierarchy retained;guest nav/reactive sidebar replaces interpreted-query surface |
| directory-empty / network-error / mobile-filters | C02 extensions | Genuine empty backend result;simulated network failure truthfully labelled;native keyboard filter accordion,values preserved |
| preview | C02 care → Profile modal | Modal/service facts/action hierarchy retained;no copied fake feedback or regulatory verification |
| profile | C04 | Public gutters corrected;approved offerings selectable,truthful trust dimensions;no fabricated biography/qualifications |
| calendar | C06 | Calendar/time pairing retained;language/timezone explicit and compact;actual slot count/current date differs |
| guest-request | D01+D02 combined | Approved reduced-step draft,real memory-loss/emergency notices;no fake pre-auth dispatch rail |
| patient-home | C01 | Same hero/wallet/appointment hierarchy;new private-request entry;actual balances/statuses retained |
| account / privacy | H01 / H03 | Focused settings/preview retained;alias editable;audited file-history disclosure is expandable |
| notifications | H06 comparison | Reference is a feed;app preferences belong under Contact & sign-in;actual messages in persistent updates menu;intentional operational extension |
| onboarding-policies | B05 extension | Separate review-only policy/care choices;production legal content not fabricated |
| new-patient-schedule / booked | C06 / C09 | Persisted new-patient return/funding/booking,not a mocked successful screen |
| new-clinician-resume | B06/B07 | Separate clinician intent and resumed private application;no scope automatically approved |
| offer-shortfall | D05 / C08 extension | Real private quote,exact wallet shortfall and explicit top-up;acceptance disabled until funded |
| accepted-preflight / clinician-accepted-popup | E05 / F15 | Authorized appointment handoff and cross-page read-persisted notification;no new connected-media claim |

All images inspected as named in the verification report. Remaining intentional
differences are documented there. Owner visual acceptance remains pending.
