// Browser acceptance for verified-email clinic invitations on the built Frappe app.
// Credentials are read locally and never printed. All created clinic details are synthetic.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const site = process.env.TELE_TENA_REVIEW_SITE_PATH;
assert.ok(site && /^tele-tena-[a-z0-9-]+\.localhost$/.test(path.basename(site)));
const marker = JSON.parse(fs.readFileSync(path.join(site, 'private/tele_tena_review_seed.json')));
const passwords = JSON.parse(fs.readFileSync(path.join(site, 'private/tele_tena_review_accounts.json')));
const app = (process.env.TELE_TENA_BROWSER_ORIGIN || 'http://127.0.0.1:8017') + '/teletena';
const screenshots = path.resolve('docs/screenshots/clinic-membership');
const clinicName = 'Synthetic membership clinic ' + Date.now();
const inviteEmail = marker.users.patient;
let checkpoint = 'launch';

async function signIn(page, user) {
  await page.goto(app + '/sign-in');
  await page.getByLabel('Email', { exact: true }).waitFor();
  await page.getByLabel('Email', { exact: true }).fill(user);
  await page.getByLabel('Password', { exact: true }).fill(passwords[user]);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('button', { name: 'Sign out', exact: true }).waitFor();
}

async function switchUser(page, user) {
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await signIn(page, user);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    page.setDefaultTimeout(15000);
    page.on('response', response => {
      const url = new URL(response.url());
      if (url.pathname.includes('/api/method/tele_tena.api.clinics.'))
        console.log('Clinic API', url.pathname.split('.').pop(), response.status());
    });
    fs.mkdirSync(screenshots, { recursive: true });

    checkpoint = 'clinician clinic registration';
    console.log('Browser checkpoint: clinician registration');
    await signIn(page, marker.users.clinician);
    await page.goto(app + '/clinician/affiliations');
    await page.getByLabel('Clinic name', { exact: true }).fill(clinicName);
    await page.getByLabel('Registered legal name', { exact: true }).fill('Synthetic Membership Care Ltd');
    await page.getByLabel('Registration reference', { exact: true }).fill('TT-MEM-' + Date.now().toString(36));
    await page.getByLabel('Jurisdiction', { exact: true }).fill('Synthetic jurisdiction');
    await page.getByRole('button', { name: 'Submit for verification' }).click();
    await page.getByText(clinicName, { exact: true }).waitFor();

    checkpoint = 'reviewer registration decision';
    console.log('Browser checkpoint: reviewer decision');
    await switchUser(page, marker.users.reviewer);
    await page.goto(app + '/admin/clinics');
    const registrationCard = page.locator('.clinic-review-card').filter({ has: page.getByRole('heading', { name: clinicName }) });
    await registrationCard.getByLabel('Decision reason', { exact: true }).fill('Synthetic clinic registry evidence reviewed.');
    await registrationCard.getByRole('button', { name: 'Verify registration' }).click();

    checkpoint = 'manager invitation';
    console.log('Browser checkpoint: manager portal');
    await switchUser(page, marker.users.clinician);
    await page.goto(app + '/clinician/clinic-access');
    await page.getByRole('heading', { name: 'Clinic access' }).waitFor();
    checkpoint = 'manager clinic card';
    const teamCard = page.locator('.clinic-team-card').filter({ has: page.getByRole('heading', { name: clinicName }) });
    await teamCard.getByLabel('Team member email', { exact: true }).fill(inviteEmail);
    await teamCard.getByLabel('Clinic role', { exact: true }).selectOption('Scheduling');
    checkpoint = 'manager invitation submit';
    await teamCard.getByRole('button', { name: 'Invite team member' }).click();
    const invitedRow = teamCard.locator('.clinic-record-row').filter({ hasText: 'Scheduling · Invited' });
    await invitedRow.waitFor();
    for (const width of [320, 390, 768, 1440]) {
      checkpoint = 'manager responsive width ' + width;
      await page.setViewportSize({ width, height: 900 });
      const pageWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      assert.ok(pageWidth <= width, 'Unexpected horizontal page overflow at ' + width + 'px');
      if (width === 390 || width === 1440)
        await teamCard.screenshot({ path: path.join(screenshots, 'manager-invitation-' + width + '.png') });
    }

    checkpoint = 'verified invitee acceptance';
    console.log('Browser checkpoint: invitee acceptance');
    await switchUser(page, marker.users.patient);
    await page.goto(app + '/patient/clinic-access');
    const invitationCard = page.locator('.clinic-review-card').filter({ has: page.getByRole('heading', { name: clinicName }) });
    await invitationCard.getByRole('button', { name: 'Accept invitation' }).click();
    const membershipSection = page.locator('.clinic-record-section').filter({ has: page.getByRole('heading', { name: 'Your clinic memberships' }) });
    const acceptedRow = membershipSection.locator('.clinic-record-row').filter({ hasText: clinicName });
    await acceptedRow.getByText('Active', { exact: true }).waitFor();
    checkpoint = 'role-scoped clinic workspace navigation';
    await page.getByRole('link', { name: 'Clinic workspace', exact: true }).click();
    await page.getByRole('heading', { name: 'Clinic workspace', exact: true }).waitFor();
    assert.match(page.url(), /\/teletena\/clinic$/);
    await page.getByRole('heading', { name: 'Your clinic memberships', exact: true }).waitFor();
    for (const width of [320, 390, 768, 1440]) {
      checkpoint = 'clinic workspace responsive width ' + width;
      await page.setViewportSize({ width, height: 900 });
      const pageWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      assert.ok(pageWidth <= width, 'Unexpected horizontal page overflow at ' + width + 'px');
      if (width === 390 || width === 1440)
        await page.locator('.clinic-access-page').screenshot({ path: path.join(screenshots, 'staff-workspace-' + width + '.png') });
    }

    checkpoint = 'manager revocation';
    console.log('Browser checkpoint: manager revocation');
    await switchUser(page, marker.users.clinician);
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(app + '/clinician/clinic-access');
    const activeTeam = page.locator('.clinic-team-card').filter({ has: page.getByRole('heading', { name: clinicName }) });
    const activeRow = activeTeam.locator('.clinic-record-row').filter({ hasText: 'Scheduling · Active' });
    await activeRow.waitFor();
    await activeRow.getByLabel('Reason to revoke access', { exact: true }).fill('Synthetic browser verification complete.');
    await activeRow.getByRole('button', { name: 'Revoke access' }).click();
    await activeTeam.locator('.clinic-record-row').filter({ hasText: 'Scheduling · Revoked' }).waitFor();
    await activeTeam.screenshot({ path: path.join(screenshots, 'manager-revocation.png') });

    console.log('PASS: built Frappe clinic registration → reviewer verification → manager invite → verified patient acceptance → membership-scoped clinic workspace → manager revocation. Synthetic screenshots: ' + screenshots);
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error('FAIL: clinic membership browser journey at ' + checkpoint + ' (' + (error?.name || 'Error') + '); credentials and response bodies withheld');
  process.exitCode = 1;
});
