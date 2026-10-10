// Read-only F01/E02 evidence on the named local presentation site. No frontend mocks.
const fs = require("node:fs");
const assert = require("node:assert/strict");
const { chromium } = require("playwright");
const privateRoot =
  "/home/frappe/frappe/frappe-bench/sites/teletena-mvp-presentation.localhost/private";
const seed = JSON.parse(
  fs.readFileSync(privateRoot + "/tele_tena_presentation_seed.json"),
);
const credentials = JSON.parse(
  fs.readFileSync(privateRoot + "/tele_tena_presentation_accounts.json"),
);
const base = "http://127.0.0.1:8017/teletena";
const output =
  process.env.TELE_TENA_EVIDENCE_DIR || "/tmp/teletena-presentation-overview";
fs.mkdirSync(output, { recursive: true });
let stage = "launch";
async function signIn(page, role) {
  await page.goto(base + "/sign-in");
  await page
    .getByRole("button", { name: "Use email instead", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Use password instead", exact: true })
    .click();
  await page.getByLabel("Email", { exact: true }).fill(seed.users[role]);
  await page
    .getByLabel("Password", { exact: true })
    .fill(credentials[seed.users[role]]);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.getByRole("button", { name: "Sign out", exact: true }).waitFor();
}
async function query(page, method) {
  return page.evaluate(async (method) => {
    const response = await fetch("/api/method/" + method);
    if (!response.ok) throw Error("Authorized query failed");
    return (await response.json()).message;
  }, method);
}
async function pair(context, page, id, width) {
  await page.evaluate(() => document.fonts.ready);
  assert.ok(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  );
  await page.screenshot({
    path: `${output}/${id}-application-${width}.png`,
    fullPage: true,
  });
  const reference = await context.newPage();
  await reference.goto(
    "http://127.0.0.1:8044/?embed=1#" + id.split("-")[0].toLowerCase(),
  );
  await reference.evaluate(() => document.fonts.ready);
  await reference.screenshot({
    path: `${output}/${id}-reference-${width}.png`,
    fullPage: true,
  });
  await reference.close();
}
(async () => {
  const browser = await chromium.launch();
  try {
    for (const role of ["clinician", "patient"]) {
      const context = await browser.newContext({
        viewport: { width: 1440, height: 1000 },
        timezoneId: "Africa/Addis_Ababa",
      });
      const page = await context.newPage();
      page.setDefaultTimeout(15000);
      stage = role + " sign-in";
      await signIn(page, role);
      const walletMethod =
        role === "patient"
          ? "tele_tena.api.journey.wallet"
          : "tele_tena.accounting.clinician_earnings";
      const before = await query(page, walletMethod);
      const appointments = await query(
        page,
        "tele_tena.api.journey.appointments",
      );
      assert.ok(appointments.length > 0);
      const appointment =
        appointments.find(
          (item) =>
            item.state === "Booked" && Date.parse(item.end) > Date.now(),
        ) || appointments[0];
      for (const width of [390, 768, 1440]) {
        await page.setViewportSize({ width, height: 1000 });
        if (role === "clinician") {
          stage = "F01 compact overview " + width;
          await page.goto(base + "/clinician");
          await page
            .getByRole("heading", { name: "Your day at a glance", exact: true })
            .waitFor();
          await page.locator(".schedule-appointment-row").first().waitFor();
          assert.equal(
            await page
              .locator(".clinician-today-layout .appointment-card")
              .count(),
            0,
          );
          const row = page.locator(".schedule-appointment-row").first();
          const link = row.getByRole("link");
          await link.focus();
          assert.ok(
            await link.evaluate(
              (element) => document.activeElement === element,
            ),
          );
          await pair(context, page, "F01", width);
          await link.press("Enter");
          await page.waitForURL(/consultations\//);
          await page.getByRole("heading", { level: 1 }).waitFor();
          assert.equal(await page.locator(".consultation-summary").count(), 1);
        }
        stage = role + " persisted appointment detail " + width;
        await page.goto(base + "/" + role + "/consultations/" + appointment.id);
        await page.locator(".consultation-summary").waitFor();
        await page
          .getByRole("heading", { name: "Your conversation", exact: true })
          .waitFor();
        await pair(
          context,
          page,
          role === "patient" ? "E02" : "E02-clinician",
          width,
        );
        await page.reload();
        await page.locator(".consultation-summary").waitFor();
        const timeAction = page.getByRole("button", {
          name: "Request a new time",
          exact: true,
        });
        if (await timeAction.count()) {
          assert.equal(await page.locator(".reschedule-panel").count(), 0);
          await timeAction.click();
          const choices = page.getByLabel("Choose an available time", {
            exact: true,
          });
          await choices.waitFor();
          await choices.selectOption({ index: 1 });
          assert.ok(
            await page
              .getByRole("button", { name: "Send time request", exact: true })
              .isEnabled(),
          );
          await page
            .locator(".reschedule-panel")
            .getByRole("button", { name: "Cancel", exact: true })
            .click();
          assert.equal(await page.locator(".reschedule-panel").count(), 0);
        }
      }
      assert.deepEqual(await query(page, walletMethod), before);
      await context.close();
    }
    console.log(
      "PASS: compact clinician overview, keyboard detail navigation, loaded participant details/reload at 390/768/1440; financial queries unchanged. Paired evidence is not universal visual acceptance.",
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
