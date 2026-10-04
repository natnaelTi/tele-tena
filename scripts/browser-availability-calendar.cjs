// Production Frappe SPA interaction regression; uses synthetic review account.
const { chromium } = require('playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const root = process.env.TELE_TENA_REVIEW_SITE_PATH;
assert.ok(root?.endsWith('/tele-tena-pr2-test.localhost'));
const credentials = JSON.parse(fs.readFileSync(root + '/private/tele_tena_review_accounts.json', 'utf8'));
const user = Object.keys(credentials).find(value => value.includes('clinician'));
const base = 'http://127.0.0.1:8017/teletena';
(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 980 } });
    await page.goto(base + '/sign-in');
    const email = page.getByRole('button', { name: 'Use email instead', exact: true });
    if (await email.count()) await email.click();
    const password = page.getByRole('button', { name: 'Use password instead', exact: true });
    if (await password.count()) await password.click();
    await page.getByLabel('Email', { exact: true }).fill(user);
    await page.getByLabel('Password', { exact: true }).fill(credentials[user]);
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await page.getByRole('button', { name: 'Sign out', exact: true }).waitFor();
    await page.goto(base + '/clinician/availability');
    await page.getByRole('heading', { name: 'Weekly availability' }).waitFor();
    await page.getByRole('button', { name: 'Edit Monday availability 09:00 to 17:00' }).click();
    const focusedEditor = page.locator('[data-selected="true"] input[type="time"]').first();
    await focusedEditor.waitFor();
    assert.equal(await focusedEditor.evaluate(element => document.activeElement === element), true);
    const copyControls = page.locator('details.schedule-copy-controls');
    if (!(await copyControls.evaluate(element => element.open))) await copyControls.locator(':scope > summary').click();
    await page.getByLabel('Copy intervals from', { exact: true }).selectOption('0');
    await page.getByLabel('Copy to days', { exact: true }).selectOption('2');
    await page.getByRole('button', { name: 'Copy Monday times', exact: true }).click();
    assert.equal(await page.getByLabel('Wednesday starts', { exact: true }).inputValue(), '09:00');
    assert.equal(await page.getByLabel('Wednesday ends', { exact: true }).inputValue(), '17:00');
    await page.getByLabel('Calendar edit mode').selectOption('date');
    const monday = page.locator('.calendar-day-track').first();
    const dayLabel = await monday.getAttribute('aria-label');
    await monday.getByRole('button', { name: /10:00/ }).click();
    assert.equal(await page.getByLabel('Date', { exact: true }).inputValue(), dayLabel.match(/\d{4}-\d\d-\d\d/)[0]);
    assert.equal(await page.getByLabel('Starts', { exact: true }).inputValue(), '10:00');
    assert.equal(await page.getByLabel('Ends', { exact: true }).inputValue(), '11:00');
    await page.getByRole('button', { name: 'Add exception', exact: true }).click();
    await page.getByText('Date exceptions and breaks', { exact: true }).click();
    await page.getByText(new RegExp(dayLabel.match(/\d{4}-\d\d-\d\d/)[0] + ' · replace')).waitFor();
    const status = await page.locator('p[role="status"]').innerText();
    assert.match(status, /Unsaved changes/);
    await page.screenshot({ path: '/tmp/tele-tena-calendar-date-edit-1440.png', fullPage: true });
    console.log('PASS: date-only calendar click prepares a local replacement exception; form preserves exact date/time without saving implicitly');
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error('FAIL: production calendar interaction assertion:', error?.name || 'Error', error?.message || '(details withheld)');
  process.exitCode = 1;
});
