// Run with NODE_PATH pointing to a temporary Playwright installation.
// No video, trace, token, password or clinical request logging.
const { chromium } = require('playwright')
const fs = require('node:fs')
const assert = require('node:assert/strict')
const credentials = JSON.parse(fs.readFileSync('/tmp/tele-tena-demo-credentials.json', 'utf8'))
const base = 'http://127.0.0.1:5173'
const day = new Date(Date.now() + 4 * 86400000).toISOString().slice(0, 10)
const slotStart = day + 'T09:00'
const slotEnd = day + 'T12:00'
let checkpoint = 'launch'

async function main() {
  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext()
  const page = await context.newPage()
  const errors = []
  page.on('pageerror', () => errors.push('Browser page exception'))
  async function settled() { await page.getByRole('status').filter({ hasText: 'Saved successfully' }).waitFor() }
  async function login(kind) {
    checkpoint = 'login ' + kind
    const email = kind + '-demo@example.invalid'
    await page.getByLabel('Email', { exact: true }).fill(email)
    await page.getByLabel('Password', { exact: true }).fill(credentials[email])
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    await page.getByText('Authenticated development account: ' + email).waitFor()
    await settled()
  }
  async function logout() {
    checkpoint = 'logout'
    await page.getByRole('button', { name: 'Sign out', exact: true }).click()
    await page.getByRole('heading', { name: 'Sign in', exact: true }).waitFor()
  }
  async function profile(name) {
    checkpoint = 'profile'
    await page.getByLabel('Display name', { exact: true }).fill(name)
    await page.getByLabel('I am 18 or older').check()
    await page.getByRole('button', { name: 'Save profile', exact: true }).click()
    await settled()
  }
  try {
    await page.goto(base)
    await login('approver')
    await page.getByLabel('Service identifier').fill('general-consultation')
    await page.getByLabel('Service name', { exact: true }).fill('Synthetic general consultation')
    await page.getByRole('button', { name: 'Save service', exact: true }).click(); await settled()
    await logout()
    await login('clinician')
    await profile('Synthetic Clinician')
    await page.getByLabel('Synthetic credential statement').fill('Synthetic demonstration credentials; manual approval test only.')
    await page.getByRole('button', { name: 'Submit for manual approval' }).click(); await settled()
    await page.getByText('Application status: Pending').waitFor()
    await logout()
    await login('approver')
    const application = page.locator('article').filter({ has: page.getByRole('heading', { name: 'clinician-demo@example.invalid', exact: true }) })
    await application.getByRole('button', { name: 'Approve', exact: true }).click(); await settled()
    await application.getByText('Application status: Approved').waitFor()
    await logout()
    await login('clinician')
    checkpoint = 'publish'
    const publish = page.locator('section').filter({ has: page.getByRole('heading', { name: 'Publish an offering (approval required)', exact: true }) })
    await publish.getByLabel('Service', { exact: true }).selectOption('general-consultation')
    await publish.getByLabel('Price in simulated ETB minor units (100 = ETB 1)').fill('5000')
    await publish.getByLabel('Fixed duration in minutes').fill('30')
    await publish.getByRole('button', { name: 'Publish offering', exact: true }).click(); await settled()
    checkpoint = 'availability'
    const availability = page.locator('section').filter({ has: page.getByRole('heading', { name: 'Add availability', exact: true }) })
    await availability.getByLabel('Start (your local timezone)', { exact: true }).fill(slotStart)
    await availability.getByLabel('End (your local timezone)', { exact: true }).fill(slotEnd)
    await availability.getByRole('button', { name: 'Save availability' }).click(); await settled()
    await logout()
    await login('patient')
    await page.getByLabel('Synthetic medical history (optional)').fill('Synthetic withheld history for browser verification')
    await page.getByLabel('Share my display name', { exact: true }).uncheck()
    await page.getByLabel('Share my synthetic history', { exact: true }).uncheck()
    await profile('Synthetic Patient')
    await page.getByRole('button', { name: 'Add simulated ETB 100', exact: true }).click(); await settled()
    checkpoint = 'discovery'
    const discovery = page.locator('section').filter({ has: page.getByRole('heading', { name: 'Find an approved clinician', exact: true }) })
    await discovery.getByRole('button', { name: 'Choose', exact: true }).first().click(); await settled()
    checkpoint = 'preview and book'
    const booking = page.locator('section').filter({ has: page.getByRole('heading', { name: 'Availability (shown in your timezone)', exact: true }) })
    await booking.getByLabel('Start (your local timezone)', { exact: true }).fill(slotStart)
    await booking.getByLabel('Synthetic consultation request', { exact: true }).fill('Synthetic browser consultation request')
    await booking.getByRole('button', { name: 'Preview exact disclosure' }).click(); await settled()
    assert.equal(await booking.locator('dl').innerText(), 'Request\nSynthetic browser consultation request')
    await booking.getByRole('button', { name: 'Confirm appointment and reserve simulated funds' }).click(); await settled()
    await page.getByText('Available: ETB 50.00 · Reserved: ETB 50.00', { exact: true }).waitFor()
    await page.reload()
    await page.getByText('Available: ETB 50.00 · Reserved: ETB 50.00', { exact: true }).waitFor()
    await page.getByRole('heading', { name: 'Synthetic general consultation · Booked' }).waitFor()
    await logout()
    await login('clinician')
    const appointments = page.locator('section').filter({ has: page.getByRole('heading', { name: 'Your appointments', exact: true }) })
    assert.equal(await appointments.locator('dl').innerText(), 'Request\nSynthetic browser consultation request')
    assert.equal(await page.getByText('Synthetic withheld history for browser verification', { exact: true }).count(), 0)
    await page.screenshot({ path: '/tmp/tele-tena-clinician-review.png', fullPage: true })
    await page.getByLabel('Language', { exact: true }).selectOption('am')
    await page.getByRole('heading', { name: 'ቴሌ-ጤና · ሰው ሠራሽ ማሳያ', exact: true }).waitFor()
    await page.locator('header select').selectOption('om')
    await page.getByRole('heading', { name: 'Tele-tena · agarsiisa namtolchee', exact: true }).waitFor()
    await page.locator('header select').selectOption('en')
    await logout()
    await page.setViewportSize({ width: 390, height: 844 })
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true)
    assert.deepEqual(errors, [])
    console.log('PASS: Chromium manual approval, publication, discovery, disclosure preview, booking, reserved funds, reload persistence, clinician privacy, locale switching and 390px login layout')
    console.log('Synthetic review appointment starts ' + slotStart + ' UTC; screenshot /tmp/tele-tena-clinician-review.png')
  } catch (error) {
    await page.screenshot({ path: '/tmp/tele-tena-browser-failure.png', fullPage: true }).catch(() => {})
    console.error('Failed checkpoint: ' + checkpoint + '; ' + error.name + '; ' + (error.message.match(/^[a-zA-Z.]+:/)?.[0] || 'assertion'))
    throw error
  } finally { await context.close(); await browser.close() }
}
main().catch(() => { console.error('Browser journey failed; inspect the UI without logging credentials or request payloads'); process.exit(1) })
