// Role-gated, built-app clinic calendar checks. Credentials come from a private
// review file; neither credentials nor appointment response bodies are logged.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const sitePath = process.env.TELE_TENA_REVIEW_SITE_PATH;
assert.ok(sitePath && /^tele-tena-[a-z0-9-]+\.localhost$/.test(path.basename(sitePath)));
const accounts = JSON.parse(fs.readFileSync(path.join(sitePath, 'private/tele_tena_review_accounts.json')));
const seed = JSON.parse(fs.readFileSync(path.join(sitePath, 'private/tele_tena_review_seed.json')));
const origin = process.env.TELE_TENA_BROWSER_ORIGIN || 'http://127.0.0.1:8017';
const app = origin + '/teletena';
const output = '/tmp/tele-tena-clinic-calendar';
fs.mkdirSync(output, { recursive: true });
let stage = 'launch';

async function signIn(page, email) {
    await page.goto(app + '/sign-in');
    const language = page.getByLabel('Language / ቋንቋ / Afaan');
    if (await language.count()) await language.selectOption('en');
  const useEmail = page.getByRole('button', { name: 'Use email instead', exact: true });
  if (await useEmail.count()) await useEmail.click();
  const usePassword = page.getByRole('button', { name: 'Use password instead', exact: true });
  if (await usePassword.count()) await usePassword.click();
  await page.getByLabel('Email', { exact: true }).fill(email);
  await page.getByLabel('Password', { exact: true }).fill(accounts[email]);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('button', { name: 'Sign out', exact: true }).waitFor();
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await context.newPage();
    page.setDefaultTimeout(15000);
    stage = 'clinic owner sign-in';
    await signIn(page, seed.users.clinician);
    stage = 'direct calendar route';
    const currentQuery = page.waitForResponse(response =>
      new URL(response.url()).pathname.includes('tele_tena.api.clinic_access.clinic_schedule_week'));
    await page.goto(app + '/clinic/calendar');
    await page.getByRole('heading', { name: 'Clinic calendar', exact: true }).waitFor();
    const currentResponse = await currentQuery;
    assert.equal(currentResponse.status(), 200, 'authorized clinic schedule query must succeed');
    const current = (await currentResponse.json()).message;
    assert.match(current.week_start, /^\d{4}-\d{2}-\d{2}$/);
    assert.ok(Array.isArray(current.appointments));
    for (const item of current.appointments) {
      for (const forbidden of ['appointment', 'access', 'patient', 'email', 'phone', 'disclosure', 'history', 'private_note', 'price'])
        assert.ok(!(forbidden in item), 'calendar exposed forbidden field: ' + forbidden);
    }
    if (current.appointments.length === 0)
      await page.getByText('No patient-shared appointments this week.', { exact: true }).waitFor();
    else
      await page.locator('.clinic-calendar-event').first().waitFor();
    await page.screenshot({ path: path.join(output, 'clinic-calendar-390.png'), fullPage: true });

    stage = 'next week navigation';
    const nextQuery = page.waitForResponse(response =>
      new URL(response.url()).pathname.includes('tele_tena.api.clinic_access.clinic_schedule_week'));
    await page.getByRole('button', { name: 'Next week', exact: true }).click();
    assert.equal((await nextQuery).status(), 200);

    stage = 'timezone update';
    const timezone = page.getByLabel('Display timezone', { exact: true });
    await timezone.fill('UTC');
    const utcQuery = page.waitForResponse(async response => {
      if (!new URL(response.url()).pathname.includes('tele_tena.api.clinic_access.clinic_schedule_week')) return false;
      const body = await response.json().catch(() => null);
      return body?.message?.display_timezone === 'UTC';
    });
    await page.getByRole('button', { name: 'Update calendar', exact: true }).click();
    assert.equal((await utcQuery).status(), 200);
    await timezone.fill('Not/A_Timezone');
    await page.getByRole('button', { name: 'Update calendar', exact: true }).click();
    await page.getByText('Enter a valid IANA timezone, such as Africa/Addis_Ababa.', { exact: true }).waitFor();

    stage = 'responsive layouts';
    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      const dimensions = await page.evaluate(() => ({
        clientWidth: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
      }));
      assert.ok(dimensions.scrollWidth <= dimensions.clientWidth,
        `calendar page overflows at ${width}px`);
      if (width === 1440)
        await page.screenshot({ path: path.join(output, 'clinic-calendar-1440.png'), fullPage: true });
    }
    await context.close();

    stage = 'patient denial';
    const patientContext = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const patientPage = await patientContext.newPage();
    patientPage.setDefaultTimeout(15000);
    await signIn(patientPage, seed.users.patient);
    const denial = await patientPage.evaluate(async () => {
      const query = new URLSearchParams({ week_start: '2026-10-05', display_timezone: 'Africa/Addis_Ababa' });
      const response = await fetch('/api/method/tele_tena.api.clinic_access.clinic_schedule_week?' + query, { credentials: 'same-origin' });
      return { status: response.status };
    });
    assert.equal(denial.status, 403, 'patient account must be denied by the backend calendar API');
    await patientContext.close();
    console.log(`PASS: built clinic calendar route, authorized API, ${current.appointments.length} current-week appointment(s), week navigation, timezone validation, responsive widths and patient API denial. Screenshots: ${output}`);
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error('FAIL: clinic calendar browser journey at ' + stage + ' (' + (error?.name || 'Error') + '); credentials and response bodies withheld');
  process.exitCode = 1;
});
