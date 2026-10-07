// Fault-injection check for clinician availability feedback on the built app.
// Authentication is real; only the readiness query and validation response are
// controlled so an administrator policy change is not needed for this UI test.
const { chromium } = require('playwright')
const fs = require('node:fs')
const assert = require('node:assert/strict')

const site = process.env.TELE_TENA_REVIEW_SITE_PATH
assert.ok(site && /^tele-tena-[a-z0-9-]+\.localhost$/.test(require('node:path').basename(site)))
const base = process.env.TELE_TENA_BROWSER_ORIGIN || 'http://127.0.0.1:8017'
const app = base + '/teletena'
const seed = JSON.parse(fs.readFileSync(site + '/private/tele_tena_review_seed.json', 'utf8'))
const credentials = JSON.parse(fs.readFileSync(site + '/private/tele_tena_review_accounts.json', 'utf8'))
const account = seed.users.clinician

;(async () => {
  const browser = await chromium.launch({ headless: true })
  try {
    const context = await browser.newContext()
    const page = await context.newPage()
    await page.route('**/api/method/tele_tena.api.open_requests.request_presence**', route =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
        message: { ready: false, configured: true, reasons: [] },
      }) }))
    await page.route('**/api/method/tele_tena.api.open_requests.set_request_presence', route =>
      route.fulfill({ status: 422, contentType: 'application/json', body: JSON.stringify({
        tele_tena_error: 'immediate_policy_required', exc_type: 'ValidationError',
        message: 'Operation unavailable',
      }) }))

    await page.goto(app + '/sign-in')
    await page.getByRole('button', { name: 'Use email instead' }).click()
    await page.getByLabel('Email', { exact: true }).fill(account)
    await page.getByLabel('Password', { exact: true }).fill(credentials[account])
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    await page.waitForURL(/\/teletena\/clinician(?:\/|$)/)
    await page.getByRole('button', { name: 'Go available', exact: true }).click()
    const alert = page.getByRole('alert').filter({ hasText: 'Could not update request availability.' })
    await alert.waitFor()
    assert.equal(await page.getByText('Connection interrupted; request availability may expire.').count(), 0)
    assert.equal(await page.getByText('Operation unavailable').count(), 0)
    console.log('PASS: authenticated built-app validation failure is actionable and is not mislabeled as a connection outage')
    await context.close()
  } finally {
    await browser.close()
  }
})().catch(error => {
  console.error('FAIL: availability error-state browser assertion (' + (error?.name || 'Error') + '); credentials and response bodies withheld')
  process.exitCode = 1
})
