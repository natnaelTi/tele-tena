// Confirms invited-review authentication stays password-only on its isolated site.
const { chromium } = require('playwright')
const assert = require('node:assert/strict')
const base = process.env.TELE_TENA_TEST_BASE || 'http://127.0.0.1:8017/teletena'

async function main() {
  const browser = await chromium.launch()
  try {
    const page = await browser.newPage()
    await page.goto(base + '/sign-in')
    const options = await page.evaluate(async () => {
      const response = await fetch('/api/method/tele_tena.api.contact_auth.sign_in_options')
      return (await response.json()).message
    })
    assert.equal(options.phone_otp, false)
    assert.equal(options.patient_registration, false)
    assert.equal(options.clinician_registration, false)
    await page.getByLabel('Email', { exact: true }).waitFor()
    await page.getByLabel('Password', { exact: true }).waitFor()
    assert.equal(await page.getByLabel('Phone number', { exact: true }).count(), 0)
    assert.equal(await page.getByLabel('Verification code', { exact: true }).count(), 0)
    console.log('PASS: invited-review site exposes email/password access only; phone OTP and public registration remain disabled')
  } finally {
    await browser.close()
  }
}

main().catch(() => {
  console.error('FAIL: invited-review authentication policy did not match the disabled-access fixture')
  process.exitCode = 1
})
