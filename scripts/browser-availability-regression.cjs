// Production-built Frappe route only. Uses private synthetic credentials from
// the disposable review site's mode-600 fixture files; never prints them.
const { chromium } = require('playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const root = process.env.TELE_TENA_REVIEW_SITE_PATH;
assert.ok(root && /^tele-tena-[a-z0-9-]+\.localhost$/.test(require('node:path').basename(root)));
const fixture = JSON.parse(fs.readFileSync(root + '/private/tele_tena_review_seed.json', 'utf8'));
const credentials = JSON.parse(fs.readFileSync(root + '/private/tele_tena_review_accounts.json', 'utf8'));
const browserFixture = JSON.parse(fs.readFileSync(process.env.TELE_TENA_AVAILABILITY_FIXTURE, 'utf8'));
const base = process.env.TELE_TENA_BROWSER_ORIGIN || 'http://127.0.0.1:8017';

async function signIn(page, user, password) {
  await page.goto(base + '/teletena/sign-in');
  // Wait for the capability request to select the site's actual login route.
  // A count() taken while React is still resolving capabilities can be zero
  // even though invited-review mode will render the phone-first entry next.
  await page.getByLabel('Phone number', { exact: true }).or(
    page.getByLabel('Email', { exact: true })
  ).waitFor();
  await chooseEmailPassword(page);
  await page.getByLabel('Email', { exact: true }).fill(user);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('button', { name: 'Sign out', exact: true }).waitFor();
}

async function chooseEmailPassword(page) {
  const emailAlternative = page.getByRole('button', { name: 'Use email instead', exact: true });
  if (await emailAlternative.count()) await emailAlternative.click();
  await page.getByLabel('Email', { exact: true }).waitFor();
  const passwordAlternative = page.getByRole('button', { name: 'Use password instead', exact: true });
  if (await passwordAlternative.count()) await passwordAlternative.click();
  await page.getByLabel('Password', { exact: true }).waitFor();
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.setViewportSize({ width: 1440, height: 1000 });
    await signIn(page, fixture.users.clinician, credentials[fixture.users.clinician]);
    await page.goto(base + '/teletena/clinician/availability');
    await page.getByRole('heading', { name: 'Weekly availability' }).waitFor();
    const calendar = page.locator('.availability-calendar-scroll');
    await page.waitForFunction(() => {
      const grid = document.querySelector('.availability-calendar-scroll');
      return grid instanceof HTMLElement && grid.scrollTop > 0;
    });
    assert.ok(await calendar.locator('.availability-block').first().evaluate(element =>
      element.getBoundingClientRect().top < innerHeight
    ), 'the first configured work interval should appear in the initial viewport');
    const compactBooking = page.locator('.calendar-booking').first();
    if (await compactBooking.count()) {
      assert.equal(await compactBooking.locator('span').count(), 0,
        'short appointment blocks must keep the permitted alias readable without clipping secondary details');
    }
    const mondayStart = page.getByLabel('Monday starts', { exact: true });
    assert.match(await mondayStart.inputValue(), /^\d{2}:\d{2}$/);
    const timeFields = page.locator('details.schedule-accessible-times');
    if (!(await timeFields.evaluate(element => element.open))) await timeFields.locator(':scope > summary').click();

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

    // Invalid intervals must be explained beside the field and remain editable.
    await page.getByLabel('Monday ends', { exact: true }).fill('08:00');
    await page.getByRole('button', { name: 'Save schedule' }).click();
    await page.getByText('End time must be after start time.', { exact: true }).waitFor();
    assert.equal(await page.getByLabel('Monday ends', { exact: true }).inputValue(), '08:00');
    await page.getByLabel('Monday ends', { exact: true }).fill('17:00');

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

    await page.getByRole('button', { name: 'Copy patient booking link', exact: true }).click();
    const sharedUrl = await page.getByLabel('Patient booking link', { exact: true }).inputValue();
    const sharedPath = new URL(sharedUrl).pathname;
    assert.match(sharedPath, /^\/teletena\/patient\/book-link\/[a-f0-9]{64}$/);
    assert.equal(sharedPath.includes(browserFixture.offering), false,
      'shareable URLs must not expose the internal offering identifier');

    const logoutResponse = page.waitForResponse(response =>
      response.url().includes('/api/method/frappe.handler.logout'));
    await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await logoutResponse;
    await page.goto(base + sharedPath);
    await page.getByLabel('Phone number', { exact: true }).or(
      page.getByLabel('Email', { exact: true })
    ).waitFor();
    await chooseEmailPassword(page);
    await page.getByLabel('Email', { exact: true }).fill(browserFixture.patient);
    await page.getByLabel('Password', { exact: true }).fill(browserFixture.password);
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await page.waitForURL('**/teletena/patient/book-link/**');
    await page.getByRole('heading', { name: 'Choose a time' }).waitFor();
    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false,
        `patient booking must not overflow at ${width}px`);
    }
    await page.setViewportSize({ width: 1280, height: 900 });
    const dates = page.locator('.booking-dates button');
    await dates.first().waitFor();
    await dates.first().click();
    const available = page.locator('[aria-label="Available times"] button');
    await available.first().waitFor();
    await available.first().click();
    await page.getByRole('button', { name: 'Continue', exact: true }).click();
    await page.getByLabel('What would you like to talk about?').fill('Synthetic availability regression request');
    await page.getByRole('button', { name: 'Preview and continue' }).click();
    const bookingResponseWait = page.waitForResponse(response =>
      response.url().includes('/api/method/tele_tena.api.journey.book'));
    await page.getByRole('button', { name: /^Confirm session/ }).click();
    const bookingResponse = await bookingResponseWait;
    const bookingPayload = await bookingResponse.json().catch(() => ({}));
    if (bookingResponse.status() !== 200) {
      const messages = JSON.parse(bookingPayload._server_messages || '[]');
      const safeMessage = messages.map(value => {
        try { return JSON.parse(value).message; } catch { return ''; }
      }).filter(Boolean).join(' | ');
      console.error(`Booking API rejected the synthetic request: ${safeMessage || 'no user-facing validation message'}`);
    }
    assert.equal(bookingResponse.status(), 200,
      `built patient booking request must succeed (status ${bookingResponse.status()}, exception ${bookingPayload.exc_type || bookingPayload.exception || 'none'})`);
    await page.waitForURL('**/teletena/patient/booked/*');
    await page.getByRole('link', { name: 'View appointment', exact: true }).click();
    await page.waitForURL('**/teletena/patient/consultations/*');
    await page.getByRole('link', { name: 'Back to appointments', exact: true }).click();
    await page.getByRole('heading', { name: 'Appointments' }).waitFor();
    console.log('PASS: production-built availability save, request payload, reload persistence and patient booking with an isolated synthetic account');
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error('FAIL: production-built availability journey assertion:', error?.name || 'Error', error?.message || '(details withheld)');
  process.exitCode = 1;
});
