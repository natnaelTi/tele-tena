// LiveKit Cloud cached-token revocation using two independent browser contexts.
// Synthetic identities only. Tokens stay in process memory and are never logged.
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
  const contexts = [
    await browser.newContext({ timezoneId: 'UTC', permissions: ['camera', 'microphone'] }),
    await browser.newContext({ timezoneId: 'UTC', permissions: ['camera', 'microphone'] }),
  ]
  const pages = await Promise.all(contexts.map(context => context.newPage()))
  const errors = []
  pages.forEach(page => page.on('pageerror', () => errors.push('page exception')))
  async function login(page, kind) {
    await page.goto(base)
    await page.getByLabel('Email', { exact: true }).fill(fixture.users[kind])
    await page.getByLabel('Password', { exact: true }).fill(fixture.password)
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    try { await page.getByText('Authenticated development account', { exact: false }).waitFor({ timeout: 15000 }) }
    catch {
      diagnostic = JSON.stringify(await page.evaluate(() => ({
        headings: [...document.querySelectorAll('h1,h2')].map(node => node.innerText),
        status: [...document.querySelectorAll('[role=status]')].map(node => node.innerText),
      })))
      throw new Error('synthetic login did not complete')
    }
    await page.getByRole('button', { name: 'Appointments', exact: true }).click()
  }
  const card = page => page.locator(`[data-appointment-id="${fixture.appointment_id}"]`)
  const call = page => card(page).locator('.consultation')
  async function join(page) {
    await call(page).getByRole('button', { name: 'Check microphone and camera' }).click()
    const responsePromise = page.waitForResponse(response => response.url().includes('tele_tena.api.consultations.join'))
    await call(page).getByRole('button', { name: 'Join consultation' }).click()
    const result = (await (await responsePromise).json()).message
    assert.equal(typeof result.token, 'string')
    await call(page).getByRole('status').filter({ hasText: 'Connected' }).waitFor({ timeout: 45000 })
    return { url: result.url, token: result.token }
  }
  async function refreshToken(page) {
    const csrf = await page.evaluate(async () => {
      const response = await fetch('/api/method/tele_tena.api.journey.session', { credentials: 'same-origin' })
      return (await response.json()).message.csrf_token
    })
    return page.evaluate(async ({ appointment, csrf }) => {
      const response = await fetch('/api/method/tele_tena.api.consultations.join', {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
        body: JSON.stringify({ appointment, audio_only: 0 }),
      })
      if (!response.ok) throw new Error('refresh token request failed')
      const result = (await response.json()).message
      return { url: result.url, token: result.token }
    }, { appointment: fixture.appointment_id, csrf })
  }
  async function oldTokenRejected(page, issued, sdkUrl) {
    return page.evaluate(async ({ issued, sdkUrl }) => {
      const { Room } = await import(sdkUrl)
      const room = new Room()
      let task
      try {
        task = room.connect(issued.url, issued.token)
        const connected = await Promise.race([
          task.then(() => true, () => false),
          new Promise(resolve => setTimeout(() => resolve(null), 15000)),
        ])
        await room.disconnect()
        if (task) await task.catch(() => undefined)
        return connected === false
      } catch {
        await room.disconnect().catch(() => undefined)
        return true
      }
    }, { issued, sdkUrl })
  }
  try {
    checkpoint = 'authenticate synthetic participants'
    await Promise.all([login(pages[0], 'p1'), login(pages[1], fixture.clinician_kind || 'c1')])
    await Promise.all(pages.map(page => card(page).waitFor()))
    checkpoint = 'both participants connect'
    const [patientToken, clinicianToken] = await Promise.all(pages.map(join))
    checkpoint = 'both participants receive refreshed tokens'
    const [patientRefreshedToken, clinicianRefreshedToken] = await Promise.all(pages.map(refreshToken))
    const sdkUrl = await pages[0].evaluate(() => performance.getEntriesByType('resource')
      .map(entry => entry.name).find(url => url.includes('livekit-client') && url.includes('/node_modules/')))
    assert.ok(sdkUrl, 'LiveKit browser SDK module should be loaded')

    checkpoint = 'patient leaves before End'
    await call(pages[0]).getByRole('button', { name: /Leave \(/ }).click()
    await call(pages[0]).getByRole('status').filter({ hasText: 'You left the consultation' }).waitFor()
    checkpoint = 'clinician Ends and Cloud revokes both aliases'
    const endResponsePromise = pages[1].waitForResponse(response => response.url().includes('tele_tena.api.consultations.end'))
    await call(pages[1]).getByRole('button', { name: 'End consultation for both participants' }).click()
    const endResponse = await endResponsePromise
    let endError = ''
    if (!endResponse.ok()) {
      const result = await endResponse.json().catch(() => ({}))
      endError = result.tele_tena_error || 'http_error'
    }
    try { await call(pages[1]).getByText(/Consultation status:/).filter({ hasText: 'The clinician ended this consultation' }).waitFor({ timeout: 30000 }) }
    catch {
      diagnostic = JSON.stringify({ endHttpStatus: endResponse.status(), endError,
        lifecycle: await call(pages[1]).getByText(/Consultation status:/).innerText(),
        media: await call(pages[1]).getByRole('status').innerText() })
      throw new Error('End did not finish')
    }

    checkpoint = 'departed patient original cached token cannot reconnect through SDK'
    assert.equal(await oldTokenRejected(pages[0], patientToken, sdkUrl), true)
    checkpoint = 'departed patient refreshed cached token cannot reconnect through SDK'
    assert.equal(await oldTokenRejected(pages[0], patientRefreshedToken, sdkUrl), true)
    checkpoint = 'clinician original cached token cannot reconnect through SDK'
    assert.equal(await oldTokenRejected(pages[1], clinicianToken, sdkUrl), true)
    checkpoint = 'clinician refreshed cached token cannot reconnect through SDK'
    assert.equal(await oldTokenRejected(pages[1], clinicianRefreshedToken, sdkUrl), true)
    assert.deepEqual(errors, [])
    console.log('PASS: LiveKit Cloud rejected direct SDK reconnect with original and refreshed tokens for both identities after End; patient had left before End')
  } finally {
    await browser.close()
  }
}

main().catch(() => {
  console.error(`FAIL: hosted LiveKit revocation checkpoint ${checkpoint}${diagnostic ? ` ${diagnostic}` : ''}`)
  process.exitCode = 1
})
