// Verifies the built share-link booking journey sends its opaque source token
// to the booking command, then aborts before the server can write an appointment.
// Credentials come from private mode-600 synthetic fixtures and are never logged.
const { chromium } = require('playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const path = require('node:path');

const sitePath = process.env.TELE_TENA_REVIEW_SITE_PATH;
assert.ok(sitePath && /^tele-tena-[a-z0-9-]+\.localhost$/.test(path.basename(sitePath)));
const fixture = JSON.parse(fs.readFileSync(path.join(sitePath, 'private/tele_tena_review_seed.json'), 'utf8'));
const passwords = JSON.parse(fs.readFileSync(path.join(sitePath, 'private/tele_tena_review_accounts.json'), 'utf8'));
const base = process.env.TELE_TENA_BROWSER_ORIGIN || 'http://127.0.0.1:8017';

async function signIn(page, user) {
  await page.goto(base + '/teletena/sign-in');
  await page.getByLabel('Phone number', { exact: true }).or(page.getByLabel('Email', { exact: true })).waitFor();
  const emailAlternative = page.getByRole('button', { name: 'Use email instead', exact: true });
  if (await emailAlternative.count()) await emailAlternative.click();
  await page.getByLabel('Email', { exact: true }).fill(user);
  const passwordAlternative = page.getByRole('button', { name: 'Use password instead', exact: true });
  if (await passwordAlternative.count()) await passwordAlternative.click();
  await page.getByLabel('Password', { exact: true }).fill(passwords[user]);
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
    await page.getByRole('button', { name: 'Copy patient booking link', exact: true }).click();
    const sharedUrl = await page.getByLabel('Patient booking link', { exact: true }).inputValue();
    const token = new URL(sharedUrl).pathname.split('/').at(-1);
    assert.match(token, /^[a-f0-9]{64}$/);

    await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await page.goto(sharedUrl);
    await page.getByLabel('Phone number', { exact: true }).or(page.getByLabel('Email', { exact: true })).waitFor();
    const emailAlternative = page.getByRole('button', { name: 'Use email instead', exact: true });
    if (await emailAlternative.count()) await emailAlternative.click();
    await page.getByLabel('Email', { exact: true }).fill(fixture.users.patient);
    const passwordAlternative = page.getByRole('button', { name: 'Use password instead', exact: true });
    if (await passwordAlternative.count()) await passwordAlternative.click();
    await page.getByLabel('Password', { exact: true }).fill(passwords[fixture.users.patient]);
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await page.waitForURL('**/teletena/patient/book-link/**');
    await page.getByRole('heading', { name: 'Choose a time' }).waitFor();
    await page.locator('.booking-dates button').first().click();
    await page.locator('[aria-label="Available times"] button').first().click();
    await page.getByRole('button', { name: 'Continue', exact: true }).click();
    await page.getByLabel('What would you like to talk about?').fill('Synthetic referral-attribution preview.');
    await page.getByRole('button', { name: 'Preview and continue' }).click();

    let bookingPayload;
    let resolveBookingAttempt;
    const bookingAttempt = new Promise(resolve => { resolveBookingAttempt = resolve; });
    await page.route('**/api/method/tele_tena.api.journey.book', async route => {
      bookingPayload = route.request().postDataJSON();
      resolveBookingAttempt();
      await route.abort('failed');
    });
    await page.getByRole('button', { name: /^Confirm session/ }).click();
    await bookingAttempt;
    assert.equal(bookingPayload?.booking_link_token, token,
      'the built patient route must forward its opaque clinician-share token to the booking command');
    console.log('PASS: packaged booking-link flow forwards its verified opaque attribution token; request aborted before persistence');
    await context.close();
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error('FAIL: booking attribution browser assertion:', error?.name || 'Error', error?.message || '(details withheld)');
  process.exitCode = 1;
});
