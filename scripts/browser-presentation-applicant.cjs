// Applicant state and direct permission checks, using private fictional accounts.
const fs = require("node:fs"),
  assert = require("node:assert/strict"),
  { chromium } = require("playwright");
const root =
  "/home/frappe/frappe/frappe-bench/sites/teletena-mvp-presentation.localhost/private";
const seed = JSON.parse(
  fs.readFileSync(root + "/tele_tena_presentation_seed.json"),
);
const credentials = JSON.parse(
  fs.readFileSync(root + "/tele_tena_presentation_accounts.json"),
);
const base = "http://127.0.0.1:8017/teletena",
  output = "/tmp/teletena-presentation-applicant";
fs.mkdirSync(output, { recursive: true });
let stage = "launch";
(async () => {
  const browser = await chromium.launch();
  try {
    const context = await browser.newContext({
        viewport: { width: 1440, height: 1000 },
      }),
      page = await context.newPage();
    page.setDefaultTimeout(15000);
    stage = "applicant sign-in";
    await page.goto(base + "/sign-in");
    await page
      .getByRole("button", { name: "Use email instead", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Use password instead", exact: true })
      .click();
    await page
      .getByLabel("Email", { exact: true })
      .fill(seed.users.second_clinician);
    await page
      .getByLabel("Password", { exact: true })
      .fill(credentials[seed.users.second_clinician]);
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await page.getByRole("button", { name: "Sign out", exact: true }).waitFor();
    const session = await page.evaluate(
      async () =>
        (
          await (
            await fetch("/api/method/tele_tena.api.journey.session")
          ).json()
        ).message,
    );
    assert.ok(!session.roles.includes("Tele Tena Clinician"));
    for (const width of [390, 768, 1440]) {
      stage = "pending application " + width;
      await page.setViewportSize({ width, height: 1000 });
      await page.goto(base + "/clinician");
      await page
        .getByRole("heading", { name: "Your application", exact: true })
        .waitFor();
      await page.getByText("Pending", { exact: true }).waitFor();
      assert.equal(await page.locator(".practice-metrics").count(), 0);
      assert.equal(
        await page
          .getByText("Appointments couldn’t be loaded.", { exact: true })
          .count(),
        0,
      );
      assert.ok(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      );
      await page.evaluate(() => document.fonts.ready);
      await page.screenshot({
        path: `${output}/B11-pending-application-${width}.png`,
        fullPage: true,
      });
      const reference = await context.newPage();
      await reference.goto("http://127.0.0.1:8044/?embed=1#b11");
      await reference.evaluate(() => document.fonts.ready);
      await reference.screenshot({
        path: `${output}/B11-reference-${width}.png`,
        fullPage: true,
      });
      await reference.close();
      await page
        .getByRole("link", { name: "Your account", exact: true })
        .click();
      await page
        .getByRole("heading", { name: "Your account", exact: true })
        .waitFor();
      await page.reload();
      await page
        .getByRole("heading", { name: "Your account", exact: true })
        .waitFor();
    }
    stage = "direct appointment API remains denied";
    const status = await page.evaluate(
      async () =>
        (await fetch("/api/method/tele_tena.api.journey.appointments")).status,
    );
    assert.equal(status, 403);
    console.log(
      "PASS: pending applicant lands on actual application state, profile/reload works at 390/768/1440, no approved-only dashboard queries; direct appointment API denied 403. No approval or financial mutation.",
    );
  } catch (error) {
    console.error(
      "FAIL: " + stage + " (" + error.name + "); private details withheld",
    );
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
