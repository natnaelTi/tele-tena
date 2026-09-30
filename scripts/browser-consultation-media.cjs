// Independent Chromium contexts against a disposable local LiveKit server.
// Fake audio/video devices are used; this is not human/device validation.
const { chromium } = require('playwright')
const fs = require('node:fs')
const assert = require('node:assert/strict')
const fixture = JSON.parse(fs.readFileSync(process.env.TELE_TENA_CALL_FIXTURE, 'utf8'))
const base = 'http://127.0.0.1:5173'
let checkpoint = 'launch'
let diagnostic = ''

async function main() {
  const browser = await chromium.launch({ headless: true, args: [
    '--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream', '--autoplay-policy=no-user-gesture-required',
  ] })
  const patientContext = await browser.newContext({ timezoneId: 'UTC', permissions: ['camera', 'microphone'] })
  const clinicianContext = await browser.newContext({ timezoneId: 'UTC', permissions: ['camera', 'microphone'] })
  const patient = await patientContext.newPage()
  const clinician = await clinicianContext.newPage()
  const errors = []
  patient.on('pageerror', () => errors.push('patient page exception'))
  clinician.on('pageerror', () => errors.push('clinician page exception'))
  async function login(page, kind) {
    checkpoint = 'login ' + kind
    await page.goto(base)
    await page.getByLabel('Email', { exact: true }).fill(fixture.users[kind])
    await page.getByLabel('Password', { exact: true }).fill(fixture.password)
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    await page.getByText('Authenticated development account', { exact: false }).waitFor()
  }
  const patientCard = () => patient.locator('article').filter({ hasText: fixture.appointment_label }).last()
  const clinicianCard = () => clinician.locator('article').filter({ hasText: fixture.appointment_label }).last()
  const call = page => page.locator('.consultation')
  async function prepareAndJoin(page) {
    await call(page).getByRole('button', { name: 'Check microphone and camera' }).click()
    await call(page).getByRole('button', { name: 'Join consultation' }).click()
    await call(page).getByRole('status').filter({ hasText: 'Connected' }).waitFor({ timeout: 45000 })
  }
  try {
    await Promise.all([login(patient, 'p1'), login(clinician, 'c1')])
    await patientCard().waitFor()
    await clinicianCard().waitFor()
    checkpoint = 'patient joins'
    await prepareAndJoin(patient)
    checkpoint = 'clinician joins'
    await prepareAndJoin(clinician)
    checkpoint = 'two-way remote media'
    diagnostic = JSON.stringify(await Promise.all([patient, clinician].map(async (page) => ({
      status: await call(page).getByRole('status').textContent(),
      remoteElements: await call(page).locator('.call-remote').evaluate(node => [...node.children].map(child => child.tagName)),
    }))))
    for (const [name, page] of [['patient', patient], ['clinician', clinician]]) {
      checkpoint = name + ' remote video track'
      await page.locator('.call-remote video').waitFor({ timeout: 45000 })
      checkpoint = name + ' remote audio track'
      const tags = await page.locator('.call-remote').evaluate(node => [...node.children].map(child => child.tagName))
      assert(tags.includes('AUDIO') && tags.includes('VIDEO'))
    }
    checkpoint = 'participant leave and rejoin'
    await call(patient).getByRole('button', { name: /Leave \(/ }).click()
    await call(patient).getByRole('status').filter({ hasText: 'You left the consultation' }).waitFor()
    await prepareAndJoin(patient)
    checkpoint = 'clinician ends both-sided room'
    const endButton = call(clinician).getByRole('button', { name: 'End consultation for both participants' })
    await endButton.waitFor({ timeout: 10000 })
    await endButton.click()
    const clinicianStatus = call(clinician).getByRole('status')
    try { await clinicianStatus.filter({ hasText: 'The clinician ended this consultation' }).waitFor({ timeout: 12000 }) }
    catch {
      diagnostic = 'clinician end status: ' + (await clinicianStatus.textContent())
      throw new Error('end status failed')
    }
    await call(patient).getByRole('button', { name: 'Refresh call status' }).click()
    await call(patient).getByRole('status').filter({ hasText: 'The clinician ended this consultation' }).waitFor({ timeout: 30000 })
    assert.deepEqual(errors, [])
    console.log('PASS: two independent Chromium contexts exchanged fake-device audio/video; patient leave/rejoin worked; clinician end closed both sessions')
  } finally {
    await browser.close()
  }
}

main().catch(() => {
  // Intentionally omit exception details: SDK/network errors may include URLs or token context.
  console.error(`FAIL: consultation browser checkpoint ${checkpoint}${diagnostic ? ` ${diagnostic}` : ''}`)
  process.exitCode = 1
})
