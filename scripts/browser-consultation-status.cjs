// Built Frappe route regression for the ended-call, documentation-pending state.
// Uses an isolated synthetic clinician account and mocks only appointment detail.
const { chromium } = require('playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');

const root = process.env.TELE_TENA_REVIEW_SITE_PATH;
assert.ok(root && /^tele-tena-[a-z0-9-]+\.localhost$/.test(require('node:path').basename(root)));
const seed = JSON.parse(fs.readFileSync(root + '/private/tele_tena_review_seed.json', 'utf8'));
const credentials = JSON.parse(fs.readFileSync(root + '/private/tele_tena_review_accounts.json', 'utf8'));
const base = process.env.TELE_TENA_BROWSER_BASE || 'http://127.0.0.1:8017/teletena';

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
    await page.goto(base + '/sign-in');
    if (await page.getByRole('button', { name: 'Use email instead', exact: true }).count())
      await page.getByRole('button', { name: 'Use email instead', exact: true }).click();
    if (await page.getByRole('button', { name: 'Use password instead', exact: true }).count())
      await page.getByRole('button', { name: 'Use password instead', exact: true }).click();
    await page.getByLabel('Email', { exact: true }).fill(seed.users.clinician);
    await page.getByLabel('Password', { exact: true }).fill(credentials[seed.users.clinician]);
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await page.getByRole('button', { name: 'Sign out', exact: true }).waitFor();

    await page.route('**/api/method/tele_tena.api.presentation.appointment_detail**', async route => {
      const response = await route.fetch();
      const body = await response.json();
      body.message.status = 'Booked';
      body.message.call_state = 'Ended';
      body.message.documentation_state = 'DraftSaved';
      body.message.can_join = false;
      body.message.private_note = null;
      body.message.patient_summary_revisions = [];
      body.message.timeline = [];
      await route.fulfill({ response, body: JSON.stringify(body) });
    });
    const appointment = seed.appointment;
    await page.goto(base + '/clinician/consultations/' + appointment);
    await page.getByRole('heading', { name: 'Consultation notes' }).waitFor();
    const state = await page.locator('.summary-list dd').first().innerText();
    const endedLabels = await page.getByText('Call ended', { exact: true }).count();
    const completedLabels = await page.getByText('Completion pending', { exact: true }).count();
    const bookedLabels = await page.getByText('Booked', { exact: true }).count();
    if (state !== 'Completion pending' || completedLabels !== 1 || bookedLabels !== 0)
      throw new Error(`unexpected lifecycle presentation: state=${state}; pending=${completedLabels}; ended=${endedLabels}; booked=${bookedLabels}`);

    const screenshotDir = '/tmp/tele-tena-presentation-review';
    fs.mkdirSync(screenshotDir, { recursive: true });
    for (const width of [390, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.screenshot({ path: `${screenshotDir}/completion-pending-${width}.png`, fullPage: true });
    }
    console.log('PASS: built consultation detail distinguishes ended call from pending appointment completion');
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error('FAIL: consultation lifecycle presentation check (' + (error?.name || 'Error') + '); credentials and response bodies withheld');
  process.exitCode = 1;
});
