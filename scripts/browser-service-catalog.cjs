// Reviewer-facing service draft editor on the packaged Frappe /teletena/ app.
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
const key = 'browser-catalog-' + Date.now().toString(36);
let stage = 'launch';
let page;
(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    page = await context.newPage();
    await page.goto(app + '/sign-in');
    stage = 'reviewer sign-in';
    if (await page.getByRole('button', { name: 'Use email instead' }).count())
      await page.getByRole('button', { name: 'Use email instead' }).click();
    await page.getByLabel('Email', { exact: true }).fill(seed.users.reviewer);
    await page.getByLabel('Password', { exact: true }).fill(passwords[seed.users.reviewer]);
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await page.getByRole('button', { name: 'Sign out', exact: true }).waitFor();
    stage = 'service catalog route';
    await page.goto(app + '/admin/services');
    await page.getByRole('heading', { name: 'Service catalog' }).waitFor();
    stage = 'new draft action';
    await page.getByRole('button', { name: 'New draft' }).click();
    stage = 'draft form fields';
    stage = 'stable service key';
    await page.getByLabel('Stable service code').fill(key);
    stage = 'definition version';
    await page.getByLabel('Definition version').fill('browser-test-1');
    stage = 'patient-facing service name';
    await page.getByLabel('Patient-facing name (English)').fill('Synthetic browser catalog draft');
    stage = 'service category';
    await page.getByLabel('Service category').selectOption('counseling');
    stage = 'professional description';
    await page.getByLabel('Professional description').fill('Synthetic browser verification; not a clinical definition.');
    stage = 'participant structure';
    await page.getByLabel('Participant structure').selectOption('individual');
    await page.getByText('Professional eligibility and workflow rules', { exact: true }).click();
    stage = 'source reference';
    await page.getByLabel('Clinical/source references').fill('Synthetic browser regression fixture only.');
    stage = 'persist draft';
    await page.getByRole('button', { name: 'Save draft definition' }).click();
    await page.getByText('Draft definition saved. It is not bookable.').first().waitFor({timeout:5000});
    stage = 'reload persisted draft';
    await page.reload();
    await page.getByRole('button', { name: new RegExp(key) }).waitFor();
    await page.getByRole('button', { name: new RegExp(key) }).click();
    assert.ok((await page.getByLabel('Stable service code').inputValue()) === key, 'stable code did not reload');
    assert.ok((await page.getByLabel('Patient-facing name (English)').inputValue()) === 'Synthetic browser catalog draft', 'service label did not reload');
    stage = 'draft responsive rendering';
    fs.mkdirSync('docs/screenshots/service-catalog', { recursive: true });
    for (const width of [390, 768, 1440]) {
      await page.setViewportSize({ width, height: 960 });
      await page.evaluate(() => document.fonts.ready);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
      await page.screenshot({ path: `docs/screenshots/service-catalog/reviewer-draft-${width}.png`, fullPage: true });
    }
    stage = 'terminology review lock';
    await page.getByRole('button', { name: 'Request clinical review' }).click();
    await page.getByText('In review', { exact: true }).first().waitFor();
    assert.equal(await page.getByRole('button', { name: 'Save draft definition' }).count(), 0);
    console.log('PASS: packaged reviewer catalog draft create/reload, non-bookable status, responsive widths, and review lock; synthetic draft retained for review');
  } finally { await browser.close(); }
})().catch(error => {
  const visible = page ? page.locator('[role="alert"]').allTextContents().catch(() => []) : Promise.resolve([]);
  Promise.resolve(visible).then(messages => console.error(`FAIL: catalog browser checkpoint ${stage}; no credentials or response bodies printed; ${error.message.split('\n')[0]}; visible error: ${messages.join(' ').slice(0, 240)}`));
  process.exitCode = 1;
});
