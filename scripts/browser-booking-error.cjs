// Retained synthetic fixtures; rejects an invalid booking without changing funds.
const { chromium } = require('playwright')
const fs = require('node:fs')
const assert = require('node:assert/strict')

async function main() {
  const browser = await chromium.launch()
  const context = await browser.newContext({ timezoneId: 'Africa/Nairobi' })
  const page = await context.newPage()
  try {
    await page.goto('http://127.0.0.1:5173')
    const email = 'patient-demo@example.invalid'
    const credentials = JSON.parse(fs.readFileSync('/tmp/tele-tena-demo-credentials.json', 'utf8'))
    await page.getByLabel('Email', { exact: true }).fill(email)
    await page.getByLabel('Password', { exact: true }).fill(credentials[email])
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    await page.getByText('Saved successfully', { exact: true }).waitFor()
    async function financialState() {
      return page.evaluate(async () => {
        const get = async method => (await (await fetch('/api/method/tele_tena.api.journey.' + method, { cache: 'no-store' })).json()).message
        const wallet = await get('wallet')
        const appointments = await get('appointments')
        return { wallet, count: appointments.length }
      })
    }
    const before = await financialState()
    const discovery = page.locator('section').filter({ has: page.getByRole('heading', { name: 'Find an approved clinician', exact: true }) })
    await discovery.getByRole('button', { name: 'Choose', exact: true }).first().click()
    await page.getByText('Dates and times use: Africa/Nairobi', { exact: true }).waitFor()
    const booking = page.locator('section').filter({ has: page.getByRole('heading', { name: 'Availability (shown in your timezone)', exact: true }) })
    await booking.getByLabel('Start (your local timezone)', { exact: true }).fill('2026-10-04T12:30')
    await booking.getByLabel('Synthetic consultation request', { exact: true }).fill('Synthetic invalid-window regression request')
    await booking.getByRole('button', { name: 'Preview exact disclosure' }).click()
    await booking.getByRole('heading', { name: 'This is exactly what the clinician will see' }).waitFor()
    await booking.getByRole('button', { name: 'Confirm appointment and reserve simulated funds' }).click()
    await page.getByRole('status').filter({ hasText: 'This session does not fit within the clinician’s availability.' }).waitFor()
    assert.deepEqual(await financialState(), before)
    await booking.getByLabel('Start (your local timezone)', { exact: true }).fill('2026-10-04T10:00')
    assert.equal(await booking.getByRole('heading', { name: 'This is exactly what the clinician will see' }).count(), 0)
    await booking.getByRole('button', { name: 'Preview exact disclosure' }).click()
    await booking.getByRole('button', { name: 'Confirm appointment and reserve simulated funds' }).waitFor()
    // Do not consume the user's suggested review slot.
    await page.getByRole('button', { name: 'Sign out', exact: true }).click()
    await page.getByRole('heading', { name: 'Sign in', exact: true }).waitFor()
    console.log('PASS: Nairobi timezone shown; outside-window booking has specific error; wallet and appointments unchanged; changing time clears preview')
  } finally { await context.close(); await browser.close() }
}
main().catch(() => { console.error('Booking error browser regression failed (payloads withheld)'); process.exit(1) })
