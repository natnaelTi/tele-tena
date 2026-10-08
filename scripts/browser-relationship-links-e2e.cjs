// Two-context acceptance journey for mutually consented links on built Frappe.
// Credentials are read from a mode-600, site-private fixture and never logged.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const fixturePath = process.env.TELE_TENA_RELATIONSHIP_BROWSER_FIXTURE;
assert.ok(fixturePath);
const fixture = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));
const [inviter, invitee] = fixture.users;
assert.ok(inviter.email && inviter.password && inviter.display_name);
assert.ok(invitee.email && invitee.password && invitee.display_name);
const app = (process.env.TELE_TENA_BROWSER_ORIGIN || 'http://127.0.0.1:8017') + '/teletena';
const output = process.env.TELE_TENA_SCREENSHOT_DIR || 'docs/screenshots/adult-relationship-links';
let stage = 'launch';

async function signIn(page, account) {
  if (!new URL(page.url()).pathname.endsWith('/sign-in')) await page.goto(app + '/sign-in');
  if (await page.getByRole('button', { name: 'Use email instead', exact: true }).count()) {
    await page.getByRole('button', { name: 'Use email instead', exact: true }).click();
  }
  if (await page.getByRole('button', { name: 'Use password instead', exact: true }).count()) {
    await page.getByRole('button', { name: 'Use password instead', exact: true }).click();
  }
  await page.getByLabel('Email', { exact: true }).fill(account.email);
  await page.getByLabel('Password', { exact: true }).fill(account.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.waitForURL(/\/teletena\/(?:patient(?:\/|$)|relationship-invitation(?:\/|$))/, { timeout: 15000 });
}

async function checkedNoOverflow(page) {
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const contextA = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const contextB = await browser.newContext({ viewport: { width: 390, height: 844 } });
  try {
    const pageA = await contextA.newPage();
    const pageB = await contextB.newPage();
    const errors = [];
    pageA.on('pageerror', error => errors.push(error.name));
    pageB.on('pageerror', error => errors.push(error.name));
    stage = 'inviter sign-in';
    await signIn(pageA, inviter);
    stage = 'inviter page';
    await pageA.goto(app + '/patient/relationships', { waitUntil: 'networkidle' });
    await pageA.getByRole('heading', { name: 'Shared care' }).waitFor();
    await pageA.getByLabel('I confirm that I am 18 or older and agree to create this link.').check();
    await pageA.getByRole('button', { name: 'Create invitation link', exact: true }).click();
    const field = pageA.getByLabel('Private invitation link', { exact: true });
    await field.waitFor();
    const invitationUrl = await field.inputValue();
    const parsed = new URL(invitationUrl);
    assert.equal(parsed.search, '', 'Invitation token must not be in a query string');
    assert.match(parsed.hash, /^#invite=[A-Za-z0-9_-]{40,64}$/);
    await checkedNoOverflow(pageA);
    await pageA.screenshot({ path: path.join(output, 'patient-invitation-created-390.png'), fullPage: true });

    stage = 'invitee sign-in and preview';
    stage = 'invitee opens link';
    await pageB.goto(invitationUrl, { waitUntil: 'networkidle' });
    stage = 'invitee follows sign-in';
    await pageB.getByRole('button', { name: 'Sign in to review invitation', exact: true }).click();
    stage = 'invitee authentication';
    await signIn(pageB, invitee);
    stage = 'invitee authorized preview';
    await pageB.getByText(inviter.display_name, { exact: true }).waitFor();
    assert.equal((await pageB.locator('main').innerText()).includes(inviter.email), false);
    stage = 'invitee adult consent';
    await pageB.getByLabel('I confirm that I am 18 or older and choose to create this relationship link.').check();
    await pageB.screenshot({ path: path.join(output, 'invitee-consent-preview-390.png'), fullPage: true });

    stage = 'mutual acceptance';
    stage = 'invitee accepts';
    await pageB.getByRole('button', { name: 'Accept invitation', exact: true }).click();
    await pageB.getByText('You are now linked. No appointments or records were shared.', { exact: true }).waitFor();
    await pageB.goto(app + '/patient/relationships', { waitUntil: 'networkidle' });
    await pageB.getByText(inviter.display_name, { exact: true }).waitFor();
    await pageA.reload({ waitUntil: 'networkidle' });
    await pageA.getByText(invitee.display_name, { exact: true }).waitFor();
    assert.equal((await pageA.locator('main').innerText()).includes(invitee.email), false);
    await checkedNoOverflow(pageB);
    await pageB.screenshot({ path: path.join(output, 'patient-links-active-390.png'), fullPage: true });

    stage = 'revocation';
    await pageA.getByRole('button', { name: 'Revoke link', exact: true }).click();
    stage = 'inviter revocation confirmation';
    await pageA.getByText('Relationship link revoked.', { exact: true }).waitFor();
    stage = 'inviter revoked state';
    await pageA.getByText('Revoked', { exact: true }).waitFor();
    stage = 'invitee revoked state';
    await pageB.reload({ waitUntil: 'networkidle' });
    await pageB.getByText('Revoked', { exact: true }).waitFor();
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({
      separateSessions: true,
      invitationCreatedAndAccepted: true,
      patientOnlyNamesDisplayed: true,
      revokeVisibleToBoth: true,
      tokenInFragment: true,
      responsiveWidth: 390,
      pageErrors: errors.length,
      screenshots: output,
    }));
  } catch (error) {
    console.error(`FAIL: relationship browser journey at ${stage}; account data and response bodies withheld; ${error.name}`);
    process.exitCode = 1;
  } finally {
    await contextA.close();
    await contextB.close();
    await browser.close();
  }
})().catch(error => {
  console.error(`FAIL: relationship browser setup; credentials and response data withheld; ${error.name}`);
  process.exitCode = 1;
});
