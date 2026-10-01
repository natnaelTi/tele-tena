// Presentation-only browser check. All API responses are synthetic and mocked.
// Run with NODE_PATH=/tmp/tele-tena-browser/node_modules node scripts/browser-design-system.cjs.
const { chromium } = require('playwright')
const assert = require('node:assert/strict')

const base = process.env.TELE_TENA_BROWSER_BASE || 'http://127.0.0.1:5173'
let account = ''

function response(data) { return { status: 200, contentType: 'application/json', body: JSON.stringify({ message: data }) } }

async function main() {
  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } })
  const errors = []
  page.on('pageerror', () => errors.push('page exception'))
  await page.route('**/api/method/**', async route => {
    const url = new URL(route.request().url())
    const method = url.pathname.split('.').at(-1)
    const body = route.request().postDataJSON() || {}
    if (method === 'login') { account = body.usr || ''; return route.fulfill(response({})) }
    if (method === 'logout') { account = ''; return route.fulfill(response({})) }
    if (method === 'session') {
      const clinician = account.includes('clinician')
      const admin = account.includes('admin')
      const patient = account.includes('patient')
      return route.fulfill(response({
        user: account || 'Guest', roles: admin ? ['Tele Tena Approver'] : clinician ? ['Tele Tena Clinician'] : patient ? ['Tele Tena Patient'] : [],
        profile: clinician ? { kind: 'clinician', display_name: 'Synthetic Clinician', history: '', share_name: false, share_history: false }
          : patient ? { kind: 'patient', display_name: 'Synthetic Patient', history: '', share_name: false, share_history: false } : null,
        csrf_token: 'synthetic-csrf', simulation: true,
      }))
    }
    if (method === 'services') return route.fulfill(response([{ id: 'general-consultation', label: 'General consultation' }]))
    if (method === 'discover') return route.fulfill(response([{ id: 'offer-demo', display_name: 'Synthetic clinician', label: 'General consultation', price: 5000, minutes: 30 }]))
    if (method === 'wallet') return route.fulfill(response({ available: 10000, reserved: 0 }))
    if (method === 'applications') return route.fulfill(response([]))
    if (method === 'service_scopes') return route.fulfill(response([]))
    if (method === 'appointments') return route.fulfill(response([]))
    if (method === 'windows') return route.fulfill(response({ windows: [{ start: '2030-01-01T09:00:00Z', end: '2030-01-01T12:00:00Z' }], busy: [] }))
    return route.fulfill(response({ saved: true }))
  })
  let checkpoint = 'load public page'
  try {
    await page.goto(base)
    await page.getByRole('heading', { name: 'Phone access and signup' }).waitFor()
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true)

    async function login(email) {
      await page.getByLabel('Email', { exact: true }).fill(email)
      await page.getByLabel('Password', { exact: true }).fill('synthetic-password')
      await page.getByRole('button', { name: 'Sign in', exact: true }).click()
      await page.getByText(email).waitFor()
    }

    checkpoint = 'patient workspace'; await login('patient@example.invalid')
    await page.getByRole('heading', { name: 'Patient workspace' }).waitFor()
    await page.getByRole('navigation', { name: 'Your workspace' }).getByRole('button', { name: 'Find care' }).click()
    await page.getByRole('heading', { name: 'Find an approved clinician' }).waitFor()
    await page.getByRole('button', { name: 'Choose' }).click()
    await page.getByText('Times shown in').waitFor()
    await page.getByText('Demonstration only · simulated funds').waitFor()
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true)
    await page.getByRole('navigation', { name: 'Your workspace' }).getByRole('button', { name: 'Appointments' }).click()
    await page.getByRole('heading', { name: 'Your appointments' }).waitFor()
    await page.getByText('No records yet').waitFor()

    checkpoint = 'patient logout'; await page.getByRole('button', { name: 'Sign out' }).click()
    await page.getByRole('heading', { name: 'Sign in', exact: true }).waitFor()
    checkpoint = 'clinician workspace'; await login('clinician@example.invalid')
    await page.getByRole('heading', { name: 'Clinician workspace' }).waitFor()
    await page.getByRole('navigation', { name: 'Your workspace' }).getByRole('button', { name: 'Practice setup' }).click()
    await page.getByRole('heading', { name: 'Publish an offering' }).waitFor()
    await page.getByText('Times shown in').waitFor()

    checkpoint = 'clinician logout'; await page.getByRole('button', { name: 'Sign out' }).click()
    await page.getByRole('heading', { name: 'Sign in', exact: true }).waitFor()
    checkpoint = 'administrator workspace'; await login('admin@example.invalid')
    await page.getByRole('heading', { name: 'Administrator workspace' }).waitFor()
    await page.getByRole('navigation', { name: 'Your workspace' }).getByRole('button', { name: 'Applications and approvals' }).click()
    await page.getByRole('heading', { name: 'Manual clinician approvals' }).waitFor()
    await page.getByRole('navigation', { name: 'Your workspace' }).getByRole('button', { name: 'Service catalog' }).click()
    await page.getByRole('heading', { name: 'Service catalog' }).waitFor()

    checkpoint = 'translation and viewport'; await page.locator('header select').selectOption('am')
    await page.getByRole('heading', { name: 'ቴሌ-ጤና · ሰው ሠራሽ ማሳያ' }).waitFor()
    await page.locator('header select').selectOption('om')
    await page.getByRole('heading', { name: 'Tele-tena · agarsiisa namtolchee' }).waitFor()
    assert.deepEqual(errors, [])
    console.log('PASS: mocked presentation only; patient, clinician and administrator navigation, persisted journey entry points, locale switching and 390px layout')
  } catch (error) {
    console.error('Failed checkpoint: ' + checkpoint + '; ' + error.name + '; ' + String(error.message).split('\n')[0])
    throw error
  } finally { await browser.close() }
}

main().catch(error => { console.error('Design-system browser check failed: ' + error.name + '; ' + String(error.message).split('\n')[0]); process.exitCode = 1 })
