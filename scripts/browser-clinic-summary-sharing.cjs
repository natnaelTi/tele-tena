// Persisted, two-account clinic-summary sharing acceptance against packaged Frappe.
// Passwords are read from the site-private review file and never logged.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const site = process.env.TELE_TENA_REVIEW_SITE_PATH;
assert.ok(site && /^tele-tena-[a-z0-9-]+\.localhost$/.test(path.basename(site)));
const accounts = JSON.parse(fs.readFileSync(path.join(site, 'private/tele_tena_review_accounts.json')));
const appointment = process.env.TELE_TENA_SUMMARY_APPOINTMENT;
const clinic = process.env.TELE_TENA_SUMMARY_CLINIC;
const clinicName = process.env.TELE_TENA_SUMMARY_CLINIC_NAME;
const patient = process.env.TELE_TENA_SUMMARY_PATIENT;
const clinician = process.env.TELE_TENA_SUMMARY_CLINICIAN;
const coordinator = process.env.TELE_TENA_SUMMARY_COORDINATOR;
const origin = process.env.TELE_TENA_BROWSER_ORIGIN || 'http://127.0.0.1:8017';
const app = origin + '/teletena';
const output = '/tmp/tele-tena-clinic-summary-browser';
fs.mkdirSync(output, { recursive: true });
let checkpoint = 'launch';

async function signIn(page, user) {
  await page.goto(app + '/sign-in');
  const email = page.getByRole('button', { name: 'Use email instead', exact: true });
  if (await email.count()) await email.click();
  await page.getByLabel('Email', { exact: true }).fill(user);
  await page.getByLabel('Password', { exact: true }).fill(accounts[user]);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('button', { name: 'Sign out', exact: true }).waitFor();
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const managerContext = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const patientContext = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const coordinatorContext = await browser.newContext({ viewport: { width: 390, height: 844 } });
  try {
    const manager = await managerContext.newPage();
    manager.setDefaultTimeout(15000);
    checkpoint = 'clinic manager sign-in and invitation';
    checkpoint = 'clinic manager login screen';
    await signIn(manager, clinician);
    checkpoint = 'clinic manager access page';
    const teamLoaded = manager.waitForResponse(response =>
      new URL(response.url()).pathname.includes('tele_tena.api.clinics.clinic_team'));
    await manager.goto(app + '/clinician/clinic-access');
    await teamLoaded;
    checkpoint = 'clinic team card';
    const team = manager.locator('.clinic-team-card').filter({ has: manager.getByRole('heading', { name: clinicName, exact: true }) });
    const active = team.locator('.clinic-record-row').filter({ hasText: /Care Coordination\s*·\s*Active/i });
    const invited = team.locator('.clinic-record-row').filter({ hasText: /Care Coordination\s*·\s*Invited/i });
    if (!(await active.count()) && !(await invited.count())) {
      checkpoint = 'care coordinator invitation form';
      await team.getByLabel('Team member email', { exact: true }).fill(coordinator);
      await team.getByLabel('Clinic role', { exact: true }).selectOption('Care Coordination');
      const invitedResponse = manager.waitForResponse(response =>
        new URL(response.url()).pathname.includes('tele_tena.api.clinics.clinic_team'));
      await team.getByRole('button', { name: 'Invite team member', exact: true }).click();
      checkpoint = 'care coordinator invitation persistence';
      await invitedResponse;
      await invitedResponse.finished();
      const targetMembership = team.locator('.clinic-record-row').filter({ hasText: /Care Coordination\s*·\s*(Invited|Active)/i });
      await targetMembership.waitFor();
    }

    checkpoint = 'coordinator invitation acceptance';
    const care = await coordinatorContext.newPage();
    care.setDefaultTimeout(15000);
    await signIn(care, coordinator);
    await care.goto(app + '/patient/clinic-access');
    checkpoint = 'coordinator invitation list';
    const invite = care.locator('.clinic-review-card').filter({ has: care.getByRole('heading', { name: clinicName, exact: true }) });
    const ownMembership = care.locator('.clinic-record-row').filter({ hasText: clinicName });
    if (await invite.getByRole('button', { name: 'Accept invitation', exact: true }).count()) {
      await invite.getByRole('button', { name: 'Accept invitation', exact: true }).click();
      await care.getByRole('heading', { name: 'Your clinic memberships', exact: true }).waitFor();
      await care.getByText(clinicName, { exact: true }).waitFor();
    }
    checkpoint = 'active coordinator membership';
    await ownMembership.first().waitFor();
    assert.ok(await ownMembership.first().innerText().then(text => /Care Coordination/i.test(text)),
      'Coordinator membership does not have the expected role');

    checkpoint = 'patient consent and grant';
    const owner = await patientContext.newPage();
    owner.setDefaultTimeout(15000);
    checkpoint = 'patient account sign-in';
    await signIn(owner, patient);
    const apiResults = [];
    owner.on('response', response => {
      if (new URL(response.url()).pathname.includes('tele_tena.api.clinic_access.grant_published_summary_access'))
        apiResults.push({ endpoint: 'grant_published_summary_access', status: response.status() });
    });
    checkpoint = 'patient consultation detail';
    await owner.goto(app + '/patient/consultations/' + encodeURIComponent(appointment));
    const share = owner.locator('.clinic-schedule-sharing');
    checkpoint = 'patient summary consent controls';
    await share.getByRole('heading', { name: 'Share consultation summaries with a clinic', exact: true }).waitFor();
    const activeGrant = share.locator('.clinic-shared-row').filter({ hasText: clinicName });
    // This site is a synthetic review fixture. Revoke only the prior test grant
    // through the patient UI so this run exercises fresh consent and creation.
    if (await activeGrant.count()) {
      await activeGrant.getByRole('button', { name: 'Stop sharing', exact: true }).click();
      await activeGrant.waitFor({ state: 'detached' });
    }
    if (!(await activeGrant.count())) {
      checkpoint = 'patient clinic selection';
      const clinicPicker = share.getByLabel('Choose a verified clinic', { exact: true });
      await clinicPicker.waitFor();
      await clinicPicker.locator(`option[value="${clinic}"]`).waitFor({ state: 'attached' });
      checkpoint = 'patient clinic option selected';
      await clinicPicker.selectOption(clinic);
      checkpoint = 'patient explicit sharing consent';
      await share.getByLabel('I agree to share all summaries my clinician publishes for this consultation with this clinic. I can revoke access; revocation cannot undo earlier viewing.', { exact: true }).check();
      checkpoint = 'patient grant submission';
      await share.getByRole('button', { name: 'Share summary', exact: true }).click();
      await share.getByText('Summaries shared by patient', { exact: true }).waitFor();
      await activeGrant.waitFor();
      assert.ok(apiResults.some(result => result.status === 200), 'Patient grant API did not return success');
    } else {
      await activeGrant.waitFor();
    }
    await share.screenshot({ path: path.join(output, 'patient-consent-390.png') });

    checkpoint = 'clinic workspace load';
    await care.goto(app + '/clinic');
    checkpoint = 'summary section render';
    await care.getByRole('heading', { name: 'Patient-shared consultation summaries', exact: true }).waitFor();
    const card = care.locator('.clinic-shared-schedule').filter({ hasText: clinicName });
    await card.waitFor();
    await card.locator('.patient-shared-summary').waitFor();
    const summaryText = (await card.locator('.patient-shared-summary').innerText()).trim();
    assert.ok(summaryText.length > 0, 'Authorized summary content did not render');
    await card.screenshot({ path: path.join(output, 'care-coordination-390.png') });
    await care.setViewportSize({ width: 1440, height: 960 });
    await card.screenshot({ path: path.join(output, 'care-coordination-1440.png') });

    let sharedResponse;
    care.on('response', async response => {
      const url = new URL(response.url());
      if (url.pathname.includes('tele_tena.api.clinic_access.clinic_shared_summaries')) {
        const body = await response.json().catch(() => null);
        sharedResponse = body?.message;
      }
    });
    await care.reload();
    await card.waitFor();
    await care.waitForTimeout(150);
    assert.ok(Array.isArray(sharedResponse) && sharedResponse.length > 0, 'Shared summaries API response missing');
    const row = sharedResponse.find(item => item.clinic === clinicName);
    assert.ok(row, 'Granted summary was absent from the authorized clinic response');
    for (const forbidden of ['patient', 'email', 'phone', 'private_note', 'request_text', 'disclosure'])
      assert.ok(!(forbidden in row), 'Shared summary exposed a forbidden field: ' + forbidden);
    assert.equal(row.patient_label, 'Private patient', 'Encounter disclosure alias was not preserved');

    const width = await care.evaluate(() => document.documentElement.scrollWidth);
    assert.ok(width <= 1440, 'Clinic summary page overflows at desktop width');
    console.log('PASS: authenticated patient consent → persisted summary grant → separate Care Coordination account reads the published summary; response omits identity/private fields. Screenshots: ' + output);
  } finally {
    await managerContext.close();
    await patientContext.close();
    await coordinatorContext.close();
    await browser.close();
  }
})().catch(error => {
  console.error('FAIL: populated clinic summary browser journey at ' + checkpoint + ' (' + (error?.name || 'Error') + '); credentials and response bodies withheld');
  process.exitCode = 1;
});
