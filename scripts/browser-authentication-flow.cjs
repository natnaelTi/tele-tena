// Built-app sign-in regression on the isolated invited-review site.
// Credentials are read locally and are never written to output or screenshots.
const { chromium } = require('playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');

const root = process.env.TELE_TENA_REVIEW_SITE_PATH;
assert.ok(root?.endsWith('/tele-tena-pr2-test.localhost'));
const seed = JSON.parse(fs.readFileSync(root + '/private/tele_tena_review_seed.json', 'utf8'));
const credentials = JSON.parse(fs.readFileSync(root + '/private/tele_tena_review_accounts.json', 'utf8'));
const base = process.env.TELE_TENA_BROWSER_BASE || 'http://127.0.0.1:8017/teletena';

async function useEmailPassword(page) {
  await page.getByRole('button', { name: 'Use email instead', exact: true }).click();
  await page.getByLabel('Email', { exact: true }).waitFor();
  await page.getByLabel('Password', { exact: true }).waitFor();
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const invited = await browser.newPage();
    await invited.goto(base + '/sign-in');
    await invited.getByLabel('Phone number', { exact: true }).waitFor();
    assert.equal(await invited.getByRole('button', { name: 'Continue', exact: true }).isDisabled(), true);
    await invited.getByText('Phone-code sign-in is not enabled on this site. Choose email instead.', { exact: true }).waitFor();
    await useEmailPassword(invited);

    for (const [role, destination] of [['patient', '/patient'], ['clinician', '/clinician']]) {
      const page = role === 'patient' ? invited : await browser.newPage();
      if (role === 'clinician') {
        await page.goto(base + '/sign-in');
        await useEmailPassword(page);
      }
      const email = seed.users[role];
      await page.getByLabel('Email', { exact: true }).fill(email);
      await page.getByLabel('Password', { exact: true }).fill(credentials[email]);
      await page.getByRole('button', { name: 'Sign in', exact: true }).click();
      await page.getByRole('button', { name: 'Sign out', exact: true }).waitFor();
      assert.ok(new URL(page.url()).pathname.startsWith('/teletena' + destination));
    }

    const otp = await browser.newPage();
    await otp.route('**/api/method/tele_tena.api.contact_auth.sign_in_options**', route => route.fulfill({
      status: 200, contentType: 'application/json', body: JSON.stringify({ message: {
        phone_otp: true, email_otp: true, patient_registration: false, clinician_registration: false,
      } }),
    }));
    await otp.route('**/api/method/tele_tena.api.contact_auth.request_code**', route => route.fulfill({
      status: 200, contentType: 'application/json', body: JSON.stringify({ message: {
        challenge_id: '00000000-0000-4000-8000-000000000001',
        delivery_state: 'accepted', message: 'Provider accepted; delivery is not confirmed.',
      } }),
    }));
    await otp.goto(base + '/sign-in');
    await otp.getByLabel('Phone number', { exact: true }).fill('+251911234567');
    await otp.getByRole('button', { name: 'Continue', exact: true }).click();
    await otp.getByLabel('Verification code', { exact: true }).waitFor();
    await otp.getByRole('button', { name: 'Change number', exact: true }).click();
    await otp.getByRole('button', { name: 'Use email instead', exact: true }).click();
    await otp.getByLabel('Email', { exact: true }).waitFor();
    await otp.getByRole('button', { name: 'Continue', exact: true }).waitFor();
    await otp.getByRole('button', { name: 'Use password instead', exact: true }).click();
    await otp.getByLabel('Password', { exact: true }).waitFor();
    await otp.getByRole('button', { name: 'Use an email code instead', exact: true }).click();
    await otp.getByLabel('Email', { exact: true }).fill('synthetic@example.invalid');
    await otp.getByRole('button', { name: 'Continue', exact: true }).click();
    await otp.getByLabel('Verification code', { exact: true }).waitFor();
    await otp.route('**/api/method/tele_tena.api.contact_auth.verify_code**', route => route.fulfill({
      status: 417, contentType: 'application/json', body: JSON.stringify({
        message: 'Invalid verification', tele_tena_error: 'otp_invalid',
      }),
    }));
    await otp.getByLabel('Verification code', { exact: true }).fill('123456');
    await otp.getByRole('button', { name: 'Verify and continue', exact: true }).click();
    await otp.getByText('That code is incorrect, expired, or already used. Request a new code and try again.', { exact: true }).waitFor();
    assert.equal(await otp.getByText(/Codes expire after five minutes/).count(), 0);
    console.log('PASS: invited phone-first fallback, patient/clinician local accounts, enabled phone→email OTP/password choices, and accurate OTP error copy');
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error('FAIL: built authentication flow check (' + (error?.name || 'Error') + '); account details and response bodies withheld');
  process.exitCode = 1;
});
