# Masked Archive Review — 6 November 2026

Synthetic persisted clone, production-built app. No patient documents or real
clinical data. Project status is substituted **only in the isolated test WSGI**;
these images do not establish provider cleanup or production activation.

- [Desktop1440](archive-playback-1440.png)
- [Tablet768](archive-playback-768.png)
- [Mobile390](archive-playback-390.png)
- [Actual200% Chromium zoom](archive-200-percent-screen.png)

All four were visually inspected. Dialog typography/spacing and close control follow
the shared system; the inert playback is intentionally masked, with scrollable
content. Keyboard Play/Pause/Escape and focus restoration pass. The200% image is an
actual X11 screen capture with Chromium's200% indicator; Playwright's zoomed raster
capture was blank despite a painted window, so it is not used as visual evidence.
Owner visual approval remains separate. Earlier Overview/Support/Reports screenshots
remain in `../operations-sprint-1/` and provider fixture in `../operations-provider-proof/`.

[Actual V2 provisional independent playback](native-v2-provisional-playback.png)
uses exported masked data and the corrected owned-CSS player. It is not the settled
archive certificate. All screenshot variants were refreshed after the CSS/control
fix and visually reinspected; current screenshots replace earlier unstyled-player
images. Safe controls and scrolling remain usable at390px and actual200% zoom.
