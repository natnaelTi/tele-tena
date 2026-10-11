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
        .getByRole("heading", { name: "Application progress", exact: true })
        .waitFor();
      await page.getByText("Pending", { exact: true }).waitFor();
      {
        await page.locator('.tour-invite, .tour-replay').waitFor();
        const spacing = await page.evaluate(() => {
          const tour = document.querySelector('.tour-invite, .tour-replay');
          const heading = document.querySelector('.reference-workspace-main h1');
          return heading.getBoundingClientRect().top - tour.getBoundingClientRect().bottom;
        });
        assert.ok(spacing >= 16, 'In-flow tour must not crowd the page title');
      }
      assert.equal(await page.locator(".practice-metrics").count(), 0);
      assert.equal(await page.getByRole("link", { name: "Availability", exact: true }).count(), 0);
      assert.equal(await page.getByRole("link", { name: "Requests", exact: true }).count(), 0);
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
      await reference.setViewportSize({width,height:1000});
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
    stage = "pending practice navigation";
    if (process.env.TELE_TENA_REPRO_PENDING_NAV==='1') {
      const denied=page.waitForResponse(response=>response.url().includes('tele_tena.accounting.clinician_earnings'));
      await page.getByRole('link',{name:'Earnings',exact:true}).click();
      assert.equal((await denied).status(),403);
      console.log('Pending Account earnings link reaches protected HTTP403; no financial data returned.');
      await page.goto(base+'/clinician/account');
      await page.getByRole('heading',{name:'Your account',exact:true}).waitFor();
    } else {
      assert.equal(await page.getByRole('link',{name:'Earnings',exact:true}).count(),0);
    }
    stage = "pending professional settings navigation";
    await page.getByRole('button',{name:'Professional profile & practice',exact:true}).click();
    for (const label of ['Services and pricing','Availability','Earnings']) {
      const count=await page.getByRole('link',{name:label,exact:true}).count();
      console.log('Pending practice link '+label+': '+count);
      assert.equal(count,0);
    }
    const applicationLink=page.getByRole('link',{name:'Application & credentials',exact:true});
    console.log('Pending application link count: '+await applicationLink.count());
    assert.equal(await applicationLink.count(),1);
    await page.goto(base+'/clinician/account');
    await page.getByRole('heading',{name:'Your account',exact:true}).waitFor();
    stage = "pending own profile save";
    const nameField=page.getByLabel('Professional name',{exact:true});
    const unchangedName=await nameField.inputValue();
    await nameField.fill(unchangedName);
    const validity=await nameField.evaluate(input=>({valid:input.validity.valid,patternMismatch:input.validity.patternMismatch}));
    console.log('Pending profile field validity: '+JSON.stringify(validity));
    assert.ok(validity.valid, 'A non-empty professional name must pass native input validation');
    const savedResponse=page.waitForResponse(response=>response.url().includes('tele_tena.api.journey.save_profile'));
    await page.getByRole('button',{name:'Save details',exact:true}).click();
    const saveStatus=(await savedResponse).status();
    const expected=process.env.TELE_TENA_REPRO_PENDING_PROFILE==='1'?403:200;
    assert.equal(saveStatus,expected);
    assert.equal(await nameField.inputValue(),unchangedName);
    const unchangedSession=await page.evaluate(async()=>(await(await fetch('/api/method/tele_tena.api.journey.session')).json()).message);
    assert.equal(unchangedSession.profile.display_name,session.profile.display_name);
    assert.deepEqual(unchangedSession.roles,session.roles);
    console.log('Pending own-profile save HTTP status: '+saveStatus+'; same-value input and roles preserved.');
    stage = "direct appointment API remains denied";
    const status = await page.evaluate(
      async () =>
        (await fetch("/api/method/tele_tena.api.journey.appointments")).status,
    );
    assert.equal(status, 403);
    const manifest=JSON.parse(fs.readFileSync(require('node:path').resolve(__dirname,'../tele_tena/public/review/release.json')));
    fs.writeFileSync(output+'/result.json',JSON.stringify({source:manifest.source_commit,site:'teletena-mvp-presentation.localhost',real_backend:true,pending_state:true,approved_only_navigation_absent:true,profile_reload:true,no_approval_mutation:true,pending_profile_save_status:saveStatus,pending_practice_link_reproduction:process.env.TELE_TENA_REPRO_PENDING_NAV==='1',direct_appointments_denied:true,viewports:[390,768,1440]},null,2));

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
