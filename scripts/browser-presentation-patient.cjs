// Read-only paired MVP evidence using private fictional presentation accounts.
// Authentication and queries use the built Frappe backend, without frontend mocks.
const fs = require("node:fs"),
  assert = require("node:assert/strict"),
  { chromium } = require("playwright");
const privateRoot =
  "/home/frappe/frappe/frappe-bench/sites/teletena-mvp-presentation.localhost/private";
const seed = JSON.parse(
  fs.readFileSync(privateRoot + "/tele_tena_presentation_seed.json"),
);
const credentials = JSON.parse(
  fs.readFileSync(privateRoot + "/tele_tena_presentation_accounts.json"),
);
const base =
  process.env.TELE_TENA_BROWSER_BASE || "http://127.0.0.1:8017/teletena";
const output =
  process.env.TELE_TENA_EVIDENCE_DIR || "/tmp/teletena-presentation-patient";
fs.mkdirSync(output, { recursive: true });
let stage = "launch";
async function ready(p) {
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(200);
}
async function pair(ctx, p, id, hash, width) {
  await ready(p);
  await p.screenshot({
    path: `${output}/${id}-application-${width}.png`,
    fullPage: true,
  });
  const ref = await ctx.newPage();
  await ref.goto("http://127.0.0.1:8044/?embed=1#" + hash);
  await ready(ref);
  await ref.screenshot({
    path: `${output}/${id}-reference-${width}.png`,
    fullPage: true,
  });
  await ref.close();
}
(async () => {
  const browser = await chromium.launch();
  try {
    for (const width of [390, 768, 1440]) {
      stage = "patient " + width;
      const ctx = await browser.newContext({
          viewport: { width, height: 1000 },
          timezoneId: "Africa/Addis_Ababa",
        }),
        p = await ctx.newPage();
      p.setDefaultTimeout(15000);
      await p.goto(base + "/sign-in");
      await p.getByLabel("Phone number", { exact: true }).waitFor();
      assert.ok(
        await p
          .getByRole("button", { name: "Continue", exact: true })
          .isDisabled(),
      );
      await pair(ctx, p, "A04", "a04", width);
      await p
        .getByRole("button", { name: "Use email instead", exact: true })
        .click();
      await pair(ctx, p, "A06", "a06", width);
      await p
        .getByRole("button", { name: "Use password instead", exact: true })
        .click();
      await p.getByLabel("Email", { exact: true }).fill(seed.users.patient);
      await p
        .getByLabel("Password", { exact: true })
        .fill(credentials[seed.users.patient]);
      await p.getByRole("button", { name: "Sign in", exact: true }).click();
      await p.getByRole("button", { name: "Sign out", exact: true }).waitFor();
      await p
        .getByRole("button", { name: "Dismiss tour invitation", exact: true })
        .click()
        .catch(() => {});
      const search = p.getByRole("button", { name: "Find care", exact: true });
      await search.hover();
      assert.notEqual(
        await search.evaluate((el) => getComputedStyle(el).backgroundColor),
        "rgb(29, 61, 73)",
      );
      const inputBounds = await p
          .getByLabel("Search available support", { exact: true })
          .boundingBox(),
        buttonBounds = await search.boundingBox();
      assert.ok(Math.abs(inputBounds.y - buttonBounds.y) < 5);
      await pair(ctx, p, "C01", "c01", width);
      await p.goto(base + "/patient/discovery");
      await p
        .getByRole("button", { name: "View profile", exact: true })
        .first()
        .waitFor();
      await pair(ctx, p, "C02", "care", width);
      stage = "discovery overflow " + width;
      assert.ok(
        await p.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      );
      stage = "hidden discovery label " + width;
      const labelBox = await p
        .locator("label[for=discovery-care-query]")
        .boundingBox();
      assert.ok(labelBox.width <= 1 && labelBox.height <= 1);
      const trigger = p
        .getByRole("button", { name: "View profile", exact: true })
        .first();
      await trigger.click();
      await p
        .getByRole("dialog")
        .getByRole("link", { name: "View full profile", exact: true })
        .waitFor();
      await ready(p);
      await p.screenshot({
        path: `${output}/C02-preview-application-${width}.png`,
      });
      const ref = await ctx.newPage();
      await ref.goto("http://127.0.0.1:8044/?embed=1#care");
      await ref.locator('button[data-action^="clinician-"]').first().click();
      await ready(ref);
      await ref.screenshot({
        path: `${output}/C02-preview-reference-${width}.png`,
      });
      await ref.close();
      await p.keyboard.press("Escape");
      await p.getByRole("dialog").waitFor({ state: "hidden" });
      stage = "preview focus return " + width;
      await p.waitForFunction(
        (el) => el === document.activeElement,
        await trigger.elementHandle(),
        { timeout: 2000 },
      );
      await trigger.click();
      await p
        .getByRole("dialog")
        .getByRole("link", { name: "View full profile", exact: true })
        .click();
      await p
        .getByRole("heading", { name: "Hana Tesfaye", exact: true })
        .first()
        .waitFor();
      await pair(ctx, p, "C04", "c04", width);
      await p.goto(base + "/patient/discovery");
      await p
        .getByRole("link", { name: "Choose a time", exact: true })
        .first()
        .click();
      await p.locator(".booking-month-grid button:enabled").first().click();
      const selected = p.locator(
        ".booking-month-grid button[aria-pressed=true]",
      );
      await selected.hover();
      stage = "selected date hover " + width;
      assert.notEqual(
        await selected.evaluate((el) => getComputedStyle(el).backgroundColor),
        "rgb(234, 245, 245)",
      );
      await p.locator(".booking-slot-grid button").first().click();
      await pair(ctx, p, "C06", "c06", width);
      await p.getByRole("button", { name: "Continue", exact: true }).click();
      await p
        .locator("textarea")
        .fill(
          "I would like to reflect on everyday stress and identify practical next steps.",
        );
      await p
        .getByRole("button", { name: "Preview and continue", exact: true })
        .click();
      await p.locator(".booking-review-panels").waitFor();
      await pair(ctx, p, "C08", "c08", width);
      await p.getByRole("button", { name: "Back", exact: true }).click();
      stage = "disclosure back " + width;
      assert.equal(
        await p.locator("textarea").inputValue(),
        "I would like to reflect on everyday stress and identify practical next steps.",
      );
      await ctx.close();
    }
    console.log(
      "PASS: invited-review real password login; patient home/discovery/public profile; preview focus; authoritative calendar and hover contrast; disclosure review/back preserves input; paired 390/768/1440 evidence. No bookings or financial mutations. Visual comparison required separately.",
    );
  } catch (e) {
    console.error(
      "FAIL: " + stage + " (" + e.name + "); private details withheld",
    );
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
