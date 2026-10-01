// Real UI/API flows with isolated synthetic fixture users. Only delivery-request UI is mocked.
const { chromium } = require('playwright')
const fs = require('node:fs')
const assert = require('node:assert/strict')
const fixture = JSON.parse(fs.readFileSync(process.env.TELE_TENA_REDESIGN_FIXTURE, 'utf8'))
const base = 'http://127.0.0.1:5173'
const output = '/tmp/tele-tena-redesign-review'
fs.mkdirSync(output, { recursive: true })
let checkpoint = 'launch'
let diagnostic = ''
async function main() {
  const browser = await chromium.launch({ args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'] })
  const contexts = []
  const errors = []
  async function pageFor(kind) {
    const context = await browser.newContext({ permissions: ['camera', 'microphone'], timezoneId: 'Africa/Addis_Ababa' })
    contexts.push(context)
    const page = await context.newPage()
    page.on('pageerror', () => errors.push('page exception'))
    if (kind) {
      await page.goto(base + '/sign-in')
      await page.getByRole('button', { name: 'Use email instead', exact: true }).click()
      await page.getByRole('button', { name: 'Use password instead', exact: true }).click()
      await page.getByLabel('Email', { exact: true }).fill(fixture.users[kind])
      await page.getByLabel('Password', { exact: true }).fill(fixture.password)
      await page.getByRole('button', { name: 'Sign in', exact: true }).click()
      await page.waitForURL(/\/(patient|clinician|admin|onboarding)(\?|$)/)
    }
    return page
  }
  async function capture(page, name, widths = [390, 768, 1440]) {
    await page.waitForLoadState('networkidle')
    for (const width of widths) {
      await page.setViewportSize({ width, height: 960 })
      await page.evaluate(() => document.fonts.ready)
      await page.screenshot({ path: `${output}/${name}-${width}.png`, fullPage: true })
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false, `${name} overflows at ${width}`)
    }
  }
  try {
    const guest = await pageFor()
    checkpoint = 'homepage screenshots'
    await guest.goto(base)
    await guest.getByRole('heading', { name: 'Find someone you feel comfortable talking to.' }).waitFor()
    await capture(guest, 'homepage', [320, 390, 768, 1440])
    checkpoint = 'phone entry is one field and expected guest is signed out'
    await guest.goto(base + '/sign-in')
    await guest.getByLabel('Phone number', { exact: true }).waitFor()
    assert.equal(await guest.locator('main input').count(), 1)
    assert.equal(await guest.getByRole('alert').count(), 0)
    await capture(guest, 'phone-entry')
    // Browser-only transport mock: no production OTP bypass, no SMS sent.
    await guest.route('**/api/method/tele_tena.api.contact_auth.request_code', route => route.fulfill({ json: { message: { challenge_id: 'synthetic-ui-only', delivery_state: 'accepted', message: 'The mail provider accepted the code; delivery to your inbox is not guaranteed.' } } }))
    await guest.getByLabel('Phone number', { exact: true }).fill('0910000000')
    await guest.getByRole('button', { name: 'Continue', exact: true }).click()
    await guest.getByLabel('Verification code', { exact: true }).fill('123456')
    assert.equal(await guest.locator('main input').count(), 1)
    await capture(guest, 'code-entry')
    await guest.getByRole('button', { name: 'Change number', exact: true }).click()
    await guest.getByRole('button', { name: 'Use email instead', exact: true }).click()
    assert.equal(await guest.getByLabel('Password', { exact: true }).count(), 0)
    await capture(guest, 'email-alternative')
    await guest.unroute('**/api/method/tele_tena.api.contact_auth.request_code')
    checkpoint = 'patient onboarding save and resume'
    const newcomer = await pageFor('newpatient')
    await newcomer.getByLabel('Preferred name or alias', { exact: true }).fill('Synthetic newcomer')
    await newcomer.getByRole('button', { name: 'Save for later', exact: true }).click()
    await newcomer.getByText('Progress saved. You can return to this step.').waitFor()
    await newcomer.reload()
    await newcomer.getByLabel('Preferred name or alias', { exact: true }).waitFor()
    assert.equal(await newcomer.getByLabel('Preferred name or alias', { exact: true }).inputValue(), 'Synthetic newcomer')
    await capture(newcomer, 'patient-onboarding')
    await newcomer.getByRole('button', { name: 'Continue', exact: true }).click()
    await newcomer.getByLabel('I am 18 or older.', { exact: true }).check()
    await newcomer.getByLabel('I consent to storing my profile and the information I choose to share for this care journey.').check()
    await newcomer.getByRole('button', { name: 'Continue', exact: true }).click()
    await newcomer.getByRole('button', { name: 'Continue', exact: true }).click()
    await newcomer.getByRole('button', { name: 'Find care', exact: true }).click()
    await newcomer.waitForURL('**/patient')
    checkpoint = 'clinician onboarding'
    const applicant = await pageFor('newclinician')
    await capture(applicant, 'clinician-onboarding')
    checkpoint = 'patient workspace and discovery'
    const patient = await pageFor('p1')
    await patient.getByRole('heading', { name: 'Your next appointment' }).waitFor()
    await capture(patient, 'patient-home')
    await patient.goto(base + '/patient/discovery')
    await patient.getByRole('heading', { name: 'Find the right conversation for you.' }).waitFor()
    await patient.getByLabel('Clinician or service', { exact: true }).fill('Synthetic test consultation')
    await capture(patient, 'discovery')
    checkpoint = 'persisted booking and privacy choices'
    checkpoint = 'offering loads persisted availability'
    await patient.goto(base + '/patient/book/' + fixture.offering)
    try { await patient.getByLabel('Session starts', { exact: true }).waitFor({ timeout: 10000 }) } catch { diagnostic = JSON.stringify(await patient.evaluate(() => ({ path: location.pathname, headings: [...document.querySelectorAll('h1,h2')].map(x => x.innerText), notices: [...document.querySelectorAll('[role=alert],[role=status]')].map(x => x.innerText) }))); throw new Error('booking form unavailable') }
    await patient.getByLabel('Session starts', { exact: true }).fill(fixture.booking_start.slice(0, 16))
    // datetime-local is interpreted in Addis; adjust the UTC fixture to local UI time.
    await patient.getByLabel('Session starts', { exact: true }).fill(await patient.evaluate(value => { const d = new Date(value); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}T${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}` }, fixture.booking_start))
    checkpoint = 'choose available start time'
    await patient.getByRole('button', { name: 'Continue', exact: true }).click()
    checkpoint = 'enter request and sharing choices'
    await patient.getByLabel('What would you like to talk about?', { exact: true }).fill('Synthetic redesign request')
    await patient.getByLabel('Share my preferred name', { exact: true }).check()
    checkpoint = 'request-specific privacy preview'
    await patient.getByRole('button', { name: 'Preview and continue', exact: true }).click()
    await patient.getByRole('heading', { name: 'Review your session', exact: true }).waitFor()
    await capture(patient, 'booking-preview')
    checkpoint = 'confirm appointment and reserve simulated balance'
    await patient.getByRole('button', { name: /Confirm session/ }).click()
    await patient.waitForURL('**/patient/appointments')
    await capture(patient, 'appointments')
    checkpoint = 'profile defaults unaffected'
    await patient.goto(base + '/patient/account')
    await patient.getByLabel('Preferred name', { exact: true }).waitFor()
    assert.equal(await patient.getByLabel('Share my preferred name by default').isChecked(), false)
    await capture(patient, 'profile-privacy')
    await patient.goto(base + '/patient/payments')
    await patient.getByRole('heading', { name: 'Payments', exact: true }).waitFor()
    await capture(patient, 'payments')
    checkpoint = 'clinician Today and practice screens'
    const clinician = await pageFor('c1')
    await clinician.getByRole('heading', { name: 'Today', exact: true }).waitFor()
    await capture(clinician, 'clinician-today')
    for (const route of ['availability', 'services', 'care']) { await clinician.goto(base + '/clinician/' + route); await capture(clinician, 'clinician-' + route) }
    checkpoint = 'consultation preflight'
    await patient.goto(base + '/patient/consultations/' + fixture.appointment_id)
    await patient.getByRole('button', { name: 'Check microphone and camera', exact: true }).click()
    await patient.getByRole('status').filter({ hasText: 'Devices checked' }).waitFor()
    await capture(patient, 'consultation-preflight')
    checkpoint = 'administrative review'
    const admin = await pageFor('admin')
    await admin.getByRole('heading', { name: 'Application review' }).waitFor()
    await capture(admin, 'administrator-review')
    checkpoint = 'showcase scripts keyboard dialogs and zoom'
    await guest.goto(base + '/showcase')
    await capture(guest, 'showcase', [320, 390, 768, 1440])
    const firstTab = guest.getByRole('tab', { name: 'Overview', exact: true })
    await firstTab.focus()
    await guest.keyboard.press('ArrowRight')
    assert.equal(await guest.getByRole('tab', { name: 'Privacy', exact: true }).getAttribute('aria-selected'), 'true')
    await guest.getByRole('button', { name: 'Open dialog', exact: true }).click()
    await guest.getByRole('dialog').waitFor()
    assert.equal(await guest.evaluate(() => document.querySelector('[role=dialog]').contains(document.activeElement)), true)
    await guest.keyboard.press('Escape')
    assert.equal(await guest.getByRole('dialog').count(), 0)
    await guest.locator('main').getByLabel('Language / ቋንቋ / Afaan').selectOption('am')
    await capture(guest, 'showcase-amharic', [390, 768, 1440])
    await guest.locator('main').getByLabel('Language / ቋንቋ / Afaan').selectOption('om')
    await capture(guest, 'showcase-oromo', [390])
    await guest.emulateMedia({ reducedMotion: 'reduce' })
    await guest.setViewportSize({ width: 384, height: 960 })
    await guest.screenshot({ path: `${output}/showcase-200-percent-equivalent-384px.png`, fullPage: true })
    assert.equal(await guest.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false)
    assert.deepEqual(errors, [])
    console.log('PASS: public/auth steps, resumable onboarding, real booking/privacy flow, portals, preflight, responsive screenshots, keyboard dialog, scripts and 200% zoom; no live delivery sent')
  } finally { await browser.close() }
}
main().catch(error => { console.error('FAIL: redesign checkpoint ' + checkpoint + (error.name === 'AssertionError' ? ' — ' + error.message : ' — UI interaction did not complete') + (diagnostic ? ' ' + diagnostic : ''));  process.exitCode = 1 })
