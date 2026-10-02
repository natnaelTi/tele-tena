// Production-built Frappe route only. Uses private synthetic credentials from
// the disposable review site's mode-600 fixture files; never prints them.
const { chromium } = require('playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const root = process.env.TELE_TENA_REVIEW_SITE_PATH;
assert.ok(root?.endsWith('/tele-tena-pr2-test.localhost'));
const fixture = JSON.parse(fs.readFileSync(root + '/private/tele_tena_review_seed.json', 'utf8'));
const credentials = JSON.parse(fs.readFileSync(root + '/private/tele_tena_review_accounts.json', 'utf8'));
const base = 'http://127.0.0.1:8017';

async function signIn(page, user) {
  await page.goto(base + '/teletena/sign-in');
  const emailAlternative = page.getByRole('button', { name: 'Use email instead', exact: true });
  if (await emailAlternative.count()) await emailAlternative.click();
  const passwordAlternative = page.getByRole('button', { name: 'Use password instead', exact: true });
  if (await passwordAlternative.count()) await passwordAlternative.click();
  await page.getByLabel('Email', { exact: true }).fill(user);
  await page.getByLabel('Password', { exact: true }).fill(credentials[user]);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('button', { name: 'Sign out', exact: true }).waitFor();
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    await signIn(page, fixture.users.clinician);
    await page.goto(base + '/teletena/clinician/availability');
    await page.getByRole('heading', { name: 'Weekly availability' }).waitFor();
    const mondayStart = page.getByLabel('Monday starts', { exact: true });
    assert.match(await mondayStart.inputValue(), /^\d{2}:\d{2}$/);

    for (let n = await page.getByRole('button', { name: 'Remove', exact: true }).count(); n > 0; n--) {
      await page.getByRole('button', { name: 'Remove', exact: true }).first().click();
    }
    const monday = page.locator('.schedule-day').filter({ has: page.getByRole('heading', { name: 'Monday', exact: true }) });
    await monday.getByRole('button', { name: 'Add time' }).click();
    await page.getByLabel('Monday starts', { exact: true }).fill('09:00');
    await page.getByLabel('Monday ends', { exact: true }).fill('17:00');
    const tuesday = page.locator('.schedule-day').filter({ has: page.getByRole('heading', { name: 'Tuesday', exact: true }) });
    await tuesday.getByRole('button', { name: 'Add time' }).click();
    await page.getByLabel('Tuesday starts', { exact: true }).fill('09:00');
    await page.getByLabel('Tuesday ends', { exact: true }).fill('17:00');

    const responseWait = page.waitForResponse(response =>
      response.url().includes('/api/method/tele_tena.api.scheduling.save_schedule'));
    await page.getByRole('button', { name: 'Save schedule' }).click();
    const response = await responseWait;
    assert.equal(response.status(), 200, 'built availability editor save must succeed');
    const body = response.request().postDataJSON();
    assert.equal(body.intervals[0].start_local, '09:00');
    assert.equal(body.intervals[0].end_local, '17:00');
    await page.locator('p[role="status"]').getByText('Schedule saved.', { exact: true }).waitFor();
    await page.reload();
    await page.getByRole('heading', { name: 'Weekly availability' }).waitFor();
    assert.equal(await page.getByLabel('Monday starts', { exact: true }).inputValue(), '09:00');
    assert.equal(await page.getByLabel('Monday ends', { exact: true }).inputValue(), '17:00');

    await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await signIn(page, fixture.users.patient);
    await page.goto(base + '/teletena/patient/book/' + fixture.offering);
    await page.getByRole('heading', { name: 'Choose a time' }).waitFor();
    const dates = page.locator('.booking-dates button');
    await dates.first().waitFor();
    await dates.first().click();
    const available = page.locator('[aria-label="Available times"] button');
    await available.first().waitFor();
    await available.first().click();
    await page.getByRole('button', { name: 'Continue', exact: true }).click();
    await page.getByLabel('What would you like to talk about?').fill('Synthetic availability regression request');
    await page.getByRole('button', { name: 'Preview and continue' }).click();
    await page.getByRole('button', { name: /^Confirm session/ }).click();
    await page.getByRole('heading', { name: 'Appointments' }).waitFor();
    console.log('PASS: production-built availability save, request payload, reload persistence and patient booking on disposable Frappe site');
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error('FAIL: production-built availability journey assertion:', error?.name || 'Error', error?.message || '(details withheld)');
  process.exitCode = 1;
});
