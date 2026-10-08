// Built-app relationship-link smoke test on the isolated invited-review site.
// Reads the site's private synthetic-account file but never prints credentials.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const site = process.env.TELE_TENA_REVIEW_SITE_PATH;
assert.ok(site && /^tele-tena-[a-z0-9-]+\.localhost$/.test(path.basename(site)));
const seed = JSON.parse(fs.readFileSync(path.join(site, 'private/tele_tena_review_seed.json'), 'utf8'));
const accounts = JSON.parse(fs.readFileSync(path.join(site, 'private/tele_tena_review_accounts.json'), 'utf8'));
const patient = seed.users.patient;
assert.ok(patient && accounts[patient]);
const app = (process.env.TELE_TENA_BROWSER_ORIGIN || 'http://127.0.0.1:8017') + '/teletena';
const output = process.env.TELE_TENA_SCREENSHOT_DIR || 'docs/screenshots/adult-relationship-links';

async function signIn(page) {
  await page.goto(app + '/patient/relationships');
  await page.getByRole('button', { name: 'Use email instead', exact: true }).click();
  if (await page.getByRole('button', { name: 'Use password instead', exact: true }).count()) {
    await page.getByRole('button', { name: 'Use password instead', exact: true }).click();
  }
  await page.getByLabel('Email', { exact: true }).fill(patient);
  await page.getByLabel('Password', { exact: true }).fill(accounts[patient]);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.waitForURL(/\/teletena\/patient(?:\/|$)/, { timeout: 15000 });
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.name));
    await page.goto(app + '/relationship-invitation#invite=' + 'A'.repeat(43), { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'A private adult relationship link' }).waitFor();
    const options = await page.evaluate(async () => {
      const response = await fetch('/api/method/tele_tena.api.contact_auth.sign_in_options', { cache: 'no-store' });
      return (await response.json()).message;
    });
    if (options.patient_registration && (options.phone_otp || options.email_otp)) {
      await page.getByRole('button', { name: 'Sign in or create a patient account', exact: true }).waitFor();
    } else {
      await page.getByRole('button', { name: 'Sign in to review invitation', exact: true }).waitFor();
      assert.equal(await page.getByRole('button', { name: 'Sign in or create a patient account', exact: true }).count(), 0);
    }
    fs.mkdirSync(output, { recursive: true });
    await page.screenshot({ path: path.join(output, 'invitation-guest-390.png'), fullPage: true });

    await signIn(page);
    await page.goto(app + '/patient/relationships', { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Shared care' }).waitFor();
    await page.getByText('Invite an adult you trust', { exact: true }).waitFor();
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
    await page.screenshot({ path: path.join(output, 'patient-links-390.png'), fullPage: true });
    await page.setViewportSize({ width: 1440, height: 960 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
    await page.screenshot({ path: path.join(output, 'patient-links-1440.png'), fullPage: true });

    await page.waitForFunction(() => navigator.serviceWorker?.getRegistration('/teletena/').then(Boolean));
    const sw = await page.evaluate(async () => {
      const registration = await navigator.serviceWorker.getRegistration('/teletena/');
      return { scope: registration?.scope, script: registration?.active?.scriptURL };
    });
    assert.equal(sw.scope, new URL('/teletena/', app).href);
    assert.match(sw.script, /\/teletena\/sw\.js$/);
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({
      guestInvitation: 'pass',
      registrationPolicyCopy: options.patient_registration ? 'enabled copy' : 'disabled copy',
      authenticatedPatientPage: 'pass',
      responsiveWidths: [390, 1440],
      serviceWorker: sw,
      pageErrors: errors.length,
      screenshots: output,
    }));
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(`FAIL: relationship-link browser check; credentials and response data withheld; ${error.name}`);
  process.exitCode = 1;
});
