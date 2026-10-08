// Production-built /teletena/ transaction detail flow using a private synthetic account file.
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
let checkpoint = 'launch';
(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await context.newPage();
    await page.goto(app + '/sign-in');
    checkpoint = 'patient reviewer sign-in';
    if (await page.getByRole('button', { name: 'Use email instead' }).count()) {
      // Review access intentionally avoids unconfigured SMS/email delivery;
      // this uses the visible email/password alternative, not an OTP bypass.
      await page.getByRole('button', { name: 'Use email instead' }).click();
    }
    await page.getByLabel('Email', { exact: true }).fill(seed.users.patient);
    await page.getByLabel('Password', { exact: true }).fill(passwords[seed.users.patient]);
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await page.getByRole('button', { name: 'Sign out', exact: true }).waitFor();
    checkpoint = 'persisted payment activity';
    await page.goto(app + '/patient/payments');
    const detailLink = page.locator('a[href*="/patient/payments/transactions/"]').first();
    await detailLink.waitFor({ timeout: 12000 });
    const detailPath = await detailLink.getAttribute('href');
    assert.ok(detailPath && detailPath.startsWith('/teletena/patient/payments/transactions/'));
    checkpoint = 'owner-scoped transaction detail';
    await page.goto(origin + detailPath);
    await page.getByRole('heading', { name: 'Transaction details' }).waitFor();
    await page.getByText(/ETB/).first().waitFor();
    checkpoint = 'direct navigation and reload';
    await page.reload();
    await page.getByRole('heading', { name: 'Transaction details' }).waitFor();
    fs.mkdirSync('docs/screenshots/financial-activity', { recursive: true });
    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({ width, height: 960 });
      await page.evaluate(() => document.fonts.ready);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
      await page.screenshot({ path: `docs/screenshots/financial-activity/transaction-detail-${width}.png`, fullPage: true });
    }
    checkpoint = 'unknown activity privacy response';
    await page.goto(app + '/patient/payments/transactions/00000000-0000-4000-8000-000000000000');
    await page.getByText('Transaction unavailable.').waitFor();
    checkpoint = 'clinician-owned earnings detail';
    await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await page.waitForURL(/\/teletena\/sign-in(?:\?.*)?$/);
    if (await page.getByRole('button', { name: 'Use email instead' }).count()) {
      await page.getByRole('button', { name: 'Use email instead' }).click();
    }
    await page.getByLabel('Email', { exact: true }).fill(seed.users.clinician);
    await page.getByLabel('Password', { exact: true }).fill(passwords[seed.users.clinician]);
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await page.getByRole('button', { name: 'Sign out', exact: true }).waitFor();
    await page.goto(app + '/clinician/earnings');
    const earningLink = page.locator('a[href*="/clinician/earnings/transactions/"]').first();
    await earningLink.waitFor({ timeout: 12000 });
    await page.goto(origin + await earningLink.getAttribute('href'));
    await page.getByRole('heading', { name: 'Transaction details' }).waitFor();
    await page.reload();
    await page.getByRole('heading', { name: 'Transaction details' }).waitFor();
    for (const width of [390, 1440]) {
      await page.setViewportSize({ width, height: 960 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
      await page.screenshot({ path: `docs/screenshots/financial-activity/clinician-transaction-${width}.png`, fullPage: true });
    }
    console.log('PASS: production-built patient and clinician transaction detail, reload, responsive widths, and generic unknown-record denial');
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(`FAIL: financial activity browser checkpoint ${checkpoint}; account values and response bodies withheld`);
  process.exitCode = 1;
});
