// Synthetic authenticated journey against the production-built Frappe app.
// Credentials are read locally from the mode-600 review account file and never logged.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const site = process.env.TELE_TENA_REVIEW_SITE_PATH;
assert.ok(site && /^tele-tena-[a-z0-9-]+\.localhost$/.test(path.basename(site)));
const marker = JSON.parse(fs.readFileSync(path.join(site, 'private/tele_tena_review_seed.json')));
const passwords = JSON.parse(fs.readFileSync(path.join(site, 'private/tele_tena_review_accounts.json')));
const base = process.env.TELE_TENA_BROWSER_ORIGIN || 'http://127.0.0.1:8017';
const app = base + '/teletena';
const clinicName = 'Synthetic clinic review ' + Date.now();
const jurisdiction = 'Synthetic test jurisdiction';
const registration = 'TT-UI-' + Date.now().toString(36);
const screenshots = '/tmp/tele-tena-clinic-review';
let checkpoint = 'launch';

async function signIn(page, user) {
  await page.goto(app + '/sign-in');
  await page.getByLabel('Email', { exact: true }).waitFor();
  await page.getByLabel('Email', { exact: true }).fill(user);
  await page.getByLabel('Password', { exact: true }).fill(passwords[user]);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('button', { name: 'Sign out', exact: true }).waitFor();
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    page.setDefaultTimeout(12000);
    checkpoint = 'clinician sign-in'; await signIn(page, marker.users.clinician);
    checkpoint = 'clinic application form';
    await page.goto(app + '/clinician/affiliations');
    await page.getByRole('heading', { name: 'Clinics and affiliations' }).waitFor();
    await page.getByLabel('Clinic name', { exact: true }).fill(clinicName);
    await page.getByLabel('Registered legal name', { exact: true }).fill('Synthetic Care Organization');
    await page.getByLabel('Registration reference', { exact: true }).fill(registration);
    await page.getByLabel('Jurisdiction', { exact: true }).fill(jurisdiction);
    await page.getByRole('button', { name: 'Submit for verification' }).click();
    await page.getByText(clinicName, { exact: true }).waitFor();
    fs.mkdirSync(screenshots, { recursive: true });
    await page.screenshot({ path: path.join(screenshots, 'clinician-clinic-application.png'), fullPage: true });

    checkpoint = 'reviewer sign-in'; await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await signIn(page, marker.users.reviewer);
    checkpoint = 'reviewer clinic queue';
    await page.goto(app + '/admin/clinics');
    await page.getByRole('heading', { name: 'Clinic verification' }).waitFor();
    const clinicCard = page.locator('.clinic-review-card').filter({ has: page.getByRole('heading', { name: clinicName }) });
    await clinicCard.getByLabel('Decision reason', { exact: true }).fill('Synthetic registration evidence reviewed in browser acceptance.');
    await clinicCard.getByRole('button', { name: 'Verify registration' }).click();
    await page.screenshot({ path: path.join(screenshots, 'reviewer-clinic-approval.png'), fullPage: true });

    checkpoint = 'clinician affiliation form'; await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await signIn(page, marker.users.clinician);
    await page.goto(app + '/clinician/affiliations');
    await page.getByLabel('Verified clinic', { exact: true }).selectOption({ label: clinicName + ' · ' + jurisdiction });
    await page.getByLabel('Professional role at this clinic', { exact: true }).fill('Synthetic independent clinician');
    await page.getByLabel('Affiliation evidence summary', { exact: true }).fill('Synthetic affiliation review fixture; no patient information.');
    await page.getByRole('button', { name: 'Submit affiliation' }).click();
    await page.getByText('Submitted', { exact: true }).first().waitFor();
    await page.screenshot({ path: path.join(screenshots, 'clinician-affiliation-submitted.png'), fullPage: true });

    checkpoint = 'reviewer affiliation queue'; await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await signIn(page, marker.users.reviewer);
    await page.goto(app + '/admin/clinics');
    const affiliationSection = page.locator('section').filter({ has: page.getByRole('heading', { name: 'Clinician affiliations' }) });
    const affiliationCard = affiliationSection.locator('.clinic-review-card').filter({ hasText: clinicName });
    await affiliationCard.getByLabel('Decision reason', { exact: true }).fill('Synthetic professional affiliation reviewed.');
    await affiliationCard.getByRole('button', { name: 'Verify affiliation' }).click();
    await page.screenshot({ path: path.join(screenshots, 'reviewer-affiliation-approval.png'), fullPage: true });
    console.log('PASS: real clinician clinic submission → reviewer verification → clinician affiliation → separate reviewer decision; screenshots in ' + screenshots);
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error('FAIL: authenticated clinic workflow at ' + checkpoint + ' (' + (error?.name || 'Error') + '); account credentials and response bodies withheld');
  process.exitCode = 1;
});
