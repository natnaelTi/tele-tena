// Reviewer reconciliation queue on the production-built Frappe /teletena/ app.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const site = process.env.TELE_TENA_REVIEW_SITE_PATH;
assert.ok(site && /^tele-tena-[a-z0-9-]+\.localhost$/.test(path.basename(site)));
const seed = JSON.parse(fs.readFileSync(path.join(site, 'private/tele_tena_review_seed.json'), 'utf8'));
const passwords = JSON.parse(fs.readFileSync(path.join(site, 'private/tele_tena_review_accounts.json'), 'utf8'));
const origin = process.env.TELE_TENA_BROWSER_ORIGIN || 'http://127.0.0.1:8017';
const app = origin + '/teletena';
let stage = 'launch';
(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    await page.goto(app + '/sign-in');
    stage = 'reviewer sign-in';
    if (await page.getByRole('button', { name: 'Use email instead' }).count())
      await page.getByRole('button', { name: 'Use email instead' }).click();
    await page.getByLabel('Email', { exact: true }).fill(seed.users.reviewer);
    await page.getByLabel('Password', { exact: true }).fill(passwords[seed.users.reviewer]);
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await page.getByRole('button', { name: 'Sign out', exact: true }).waitFor();
    stage = 'financial review page';
    await page.goto(app + '/admin/financial-disputes');
    await page.getByRole('heading', { name: 'Financial disputes' }).waitFor();
    await page.getByRole('heading', { name: 'Wallet reconciliation' }).waitFor();
    stage = 'case visibility';
    await page.getByText('Review required', { exact: true }).first().waitFor({ timeout: 10000 });
    await page.getByRole('button', { name: 'Accept unchanged snapshot' }).first().waitFor();
    assert.equal((await page.locator('main').innerText()).includes('@example.invalid'), false, 'account email leaked into reviewer queue');
    // Never accept existing site records in a visual verification.
    assert.equal(await page.getByLabel('Reviewer decision reason').count() > 0, true);
    fs.mkdirSync('docs/screenshots/financial-reconciliation', { recursive: true });
    for (const width of [390, 768, 1440]) {
      await page.setViewportSize({ width, height: 960 });
      await page.evaluate(() => document.fonts.ready);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
      await page.screenshot({ path: `docs/screenshots/financial-reconciliation/queue-${width}.png`, fullPage: true });
    }
    console.log('PASS: packaged authorized reviewer route rendered held synthetic reconciliation cases at mobile/tablet/desktop; no decision was submitted');
  } finally { await browser.close(); }
})().catch(error => {
  console.error(`FAIL: reconciliation browser checkpoint ${stage}; credentials and response bodies withheld; ${error.message.split('\n')[0]}`);
  process.exitCode = 1;
});
