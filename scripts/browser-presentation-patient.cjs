// Read-only paired MVP evidence using private fictional presentation accounts.
// Authentication and queries use the built Frappe backend, without frontend mocks.
const fs = require("node:fs"),
  assert = require("node:assert/strict"),
  { chromium } = require("playwright");
const initialBuild=JSON.parse(fs.readFileSync("tele_tena/public/review/release.json"));
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
      stage = "authorized Home care links " + width;
      await p.locator('.patient-care-links').waitFor();
      const owned = await p.request.get(new URL('/api/method/tele_tena.api.journey.appointments',base).href);
      assert.equal(owned.status(),200);
      const completed = (await owned.json()).message.filter(item=>item.state==='Completed');
      const expected=[];
      for(const item of completed.sort((a,b)=>b.end.localeCompare(a.end)).slice(0,5)) {
        const response=await p.request.get(new URL('/api/method/tele_tena.api.presentation.appointment_detail?appointment='+encodeURIComponent(item.id),base).href);
        assert.equal(response.status(),200);
        const detail=(await response.json()).message;
        if(detail.patient_summary_revisions.length || detail.individual_followup_revisions.length) expected.push(item.id);
      }
      if(expected.length) {
        await p.locator('.patient-care-links .patient-care-link').first().waitFor();
        for(const link of await p.locator('.patient-care-link').all()) {
          const href=await link.getAttribute('href');
          const id=decodeURIComponent(href.split('/').at(-1));
          assert.ok(completed.some(item=>item.id===id), 'Care links belong to this patient’s completed encounters');
          const response=await p.request.get(new URL('/api/method/tele_tena.api.presentation.appointment_detail?appointment='+encodeURIComponent(id),base).href);
          assert.equal(response.status(),200);
          const detail=(await response.json()).message;
          assert.ok(detail.patient_summary_revisions.length || detail.individual_followup_revisions.length);
          assert.equal(Object.hasOwn(detail,'private_note'),false);
        }
      }
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
      const profileButtons=p.getByRole("button",{name:"View profile",exact:true});
      assert.ok(await profileButtons.count()>=2,'Presentation requires distinct selectable offerings');
      const trigger = profileButtons.nth(1);
      const selectedClinician = await trigger.locator("xpath=ancestor::section[contains(@class, 'clinician-card')]").locator("h3").innerText();
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
      // Evaluate in the locator's own context: reference capture opens another tab.
      // Retain the same focus assertion and bounded retry, without passing a DOM
      // handle into waitForFunction's isolated execution world.
      let focusReturned = false;
      for (let attempt = 0; attempt < 20; attempt++) {
        focusReturned = await trigger.evaluate(el => el === document.activeElement);
        if (focusReturned) break;
        await p.waitForTimeout(100);
      }
      assert.ok(focusReturned, "Closing clinician preview must restore focus to its opener");
      stage = "reopen clinician preview " + width;
      await trigger.click();
      const selectedBooking=await p.getByRole('dialog').getByRole('link',{name:'Choose a time',exact:true}).getAttribute('href');
      await p
        .getByRole("dialog")
        .getByRole("link", { name: "View full profile", exact: true })
        .click();
      stage = "selected clinician profile " + width;
      await p
        .getByRole("heading", { name: selectedClinician, exact: true })
        .first()
        .waitFor();
      stage='selected profile offering '+width;
      assert.equal(await p.locator('.public-profile-booking').getByRole('link',{name:'Choose a time',exact:true}).getAttribute('href'),selectedBooking,'Full profile must retain the service selected in discovery');
      await p.reload();
      await p.locator('.public-profile-booking').getByRole('link',{name:'Choose a time',exact:true}).waitFor();
      assert.equal(await p.locator('.public-profile-booking').getByRole('link',{name:'Choose a time',exact:true}).getAttribute('href'),selectedBooking);
      await pair(ctx, p, "C04", "c04", width);
      if(process.env.TELE_TENA_PROFILE_CONTEXT_ONLY==='1'){await ctx.close();continue;}
      await p.goto(base + "/patient/discovery");
      await p.locator('a[href="'+selectedBooking+'"]').first().click();
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
    const manifest=JSON.parse(fs.readFileSync('tele_tena/public/review/release.json'));
    assert.equal(manifest.source_commit,initialBuild.source_commit,'Package changed during browser verification');
    fs.writeFileSync(output+'/result.json',JSON.stringify({source:manifest.source_commit,site:'teletena-mvp-presentation.localhost',real_backend:true,selected_offering_profile_reload:true,preview_focus_return:true,calendar_disclosure_back:process.env.TELE_TENA_PROFILE_CONTEXT_ONLY!=='1',viewports:[390,768,1440]},null,2));
    console.log(process.env.TELE_TENA_PROFILE_CONTEXT_ONLY==='1' ? 'PASS: real password session, Home/discovery, preview focus, selected offering preserved through public profile and reload at390/768/1440; calendar/disclosure not repeated.' :
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
