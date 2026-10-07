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
    fs.mkdirSync(screenshots, { recursive: true });

    checkpoint = 'clinician clinic registration';
    await signIn(page, marker.users.clinician);
    await page.goto(app + '/clinician/affiliations');
    await page.getByLabel('Clinic name', { exact: true }).fill(clinicName);
    await page.getByLabel('Registered legal name', { exact: true }).fill('Synthetic Membership Care Ltd');
    await page.getByLabel('Registration reference', { exact: true }).fill('TT-MEM-' + Date.now().toString(36));
    await page.getByLabel('Jurisdiction', { exact: true }).fill('Synthetic jurisdiction');
    await page.getByRole('button', { name: 'Submit for verification' }).click();
    await page.getByText(clinicName, { exact: true }).waitFor();

    checkpoint = 'reviewer registration decision';
    await switchUser(page, marker.users.reviewer);
    await page.goto(app + '/admin/clinics');
    const registrationCard = page.locator('.clinic-review-card').filter({ has: page.getByRole('heading', { name: clinicName }) });
    await registrationCard.getByLabel('Decision reason', { exact: true }).fill('Synthetic clinic registry evidence reviewed.');
    await registrationCard.getByRole('button', { name: 'Verify registration' }).click();

    checkpoint = 'manager invitation';
    await switchUser(page, marker.users.clinician);
    await page.goto(app + '/clinician/clinic-access');
    await page.getByRole('heading', { name: 'Clinic access' }).waitFor();
    const teamCard = page.locator('.clinic-team-card').filter({ has: page.getByRole('heading', { name: clinicName }) });
    await teamCard.getByLabel('Team member email', { exact: true }).fill(inviteEmail);
    await teamCard.getByLabel('Clinic role', { exact: true }).selectOption('Scheduling');
    await teamCard.getByRole('button', { name: 'Invite team member' }).click();
    await teamCard.getByText('Invited', { exact: true }).waitFor();
    await page.screenshot({ path: path.join(screenshots, 'manager-invitation.png'), fullPage: true });

    checkpoint = 'verified invitee acceptance';
    await switchUser(page, marker.users.patient);
    await page.goto(app + '/patient/clinic-access');
    const invitationCard = page.locator('.clinic-review-card').filter({ has: page.getByRole('heading', { name: clinicName }) });
    await invitationCard.getByRole('button', { name: 'Accept invitation' }).click();
    await page.getByText('Scheduling', { exact: true }).waitFor();
    await page.screenshot({ path: path.join(screenshots, 'invitee-membership.png'), fullPage: true });

    checkpoint = 'manager revocation';
    await switchUser(page, marker.users.clinician);
    await page.goto(app + '/clinician/clinic-access');
    const activeTeam = page.locator('.clinic-team-card').filter({ has: page.getByRole('heading', { name: clinicName }) });
    await activeTeam.getByText('Active', { exact: true }).waitFor();
    await activeTeam.getByLabel('Reason to revoke access', { exact: true }).fill('Synthetic browser verification complete.');
    await activeTeam.getByRole('button', { name: 'Revoke access' }).click();
    await activeTeam.getByText('Revoked', { exact: true }).waitFor();
    await page.screenshot({ path: path.join(screenshots, 'manager-revocation.png'), fullPage: true });

    console.log('PASS: built Frappe clinic registration → reviewer verification → manager invite → verified patient acceptance → manager revocation. Synthetic screenshots: ' + screenshots);
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error('FAIL: clinic membership browser journey at ' + checkpoint + ' (' + (error?.name || 'Error') + '); credentials and response bodies withheld');
  process.exitCode = 1;
});
