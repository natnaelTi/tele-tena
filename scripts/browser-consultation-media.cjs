// Independent Chromium contexts against a disposable local LiveKit server.
// Fake audio/video devices are used; this is not human/device validation.
const { chromium } = require('playwright')
const fs = require('node:fs')
const assert = require('node:assert/strict')
const fixture = JSON.parse(fs.readFileSync(process.env.TELE_TENA_CALL_FIXTURE, 'utf8'))
fs.mkdirSync('/tmp/tele-tena-presentation-review', {recursive:true})
const base = process.env.TELE_TENA_BROWSER_BASE || 'http://127.0.0.1:5173'
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
    checkpoint = 'sign in through explicit password alternative'
    await page.goto(base + '/sign-in')
    checkpoint = 'wait for configured sign-in form'
    await page.locator('.auth-panel button[type="submit"]:not([disabled])').waitFor()
    const emailChoice = page.getByRole('button', { name: 'Use email instead', exact: true })
    checkpoint = 'choose email sign-in'
    if (await emailChoice.count()) await emailChoice.click()
    const passwordChoice = page.getByRole('button', { name: 'Use password instead', exact: true })
    checkpoint = 'choose password sign-in'
    if (await passwordChoice.count()) await passwordChoice.click()
    checkpoint = 'fill sign-in fields'
    await page.getByLabel('Email', { exact: true }).fill(fixture.users[kind])
    await page.getByLabel('Password', { exact: true }).fill(fixture.password)
    checkpoint = 'submit password sign-in'
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    checkpoint = 'wait for authenticated workspace'
    await page.getByRole('button', { name: 'Sign out', exact: true }).waitFor({ timeout: 15000 })
    checkpoint = 'open consultation detail'
    await page.goto(base + (kind.startsWith('p') ? '/patient' : '/clinician') + '/consultations/' + fixture.appointment_id)
    await page.getByRole('link', {name:'Join consultation', exact:true}).click()
    await page.locator(`[data-appointment-id="${fixture.appointment_id}"] .consultation`).waitFor()
  }

  const card = page => page.locator(`[data-appointment-id="${fixture.appointment_id}"]`)
  const patientCard = () => card(patient)
  const clinicianCard = () => card(clinician)
  const call = page => card(page).locator('.consultation')
  async function capture(page,name,widths=[320,390,768,1440]){
    for(const width of widths){await page.setViewportSize({width,height:960});await page.evaluate(()=>document.fonts.ready);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,`${name} overflows at ${width}`);await page.screenshot({path:`/tmp/tele-tena-presentation-review/${name}-${width}.png`,fullPage:true})}
  }
  async function prepareAndJoin(page) {
    await call(page).getByRole('button', { name: 'Check microphone and camera' }).click()
    let joinResponses = 0
    page.on('response', response => { if (response.url().includes('tele_tena.api.consultations.join')) joinResponses++ })
    const button = call(page).getByRole('button', { name: 'Join consultation' })
    const issuedPromise = page.waitForResponse(response => response.url().includes('tele_tena.api.consultations.join'))
    await button.click()
    const issued = (await (await issuedPromise).json()).message
    assert.equal(issued.audio_only, false, 'video mode must request camera publishing')
    try { await call(page).getByRole('status').filter({ hasText: 'Connected' }).waitFor({ timeout: 45000 }) }
    catch {
      diagnostic = JSON.stringify(await call(page).evaluate(node => ({
        statuses: [...node.querySelectorAll('p')].map(item => item.innerText),
        buttons: [...node.querySelectorAll('button')].map(item => ({ text: item.innerText, disabled: item.disabled })),
      })))
      throw new Error('media reconnect did not reach Connected')
    }
    assert.equal(joinResponses, 1, 'rapid repeated Join must issue one token request')
  }
  async function failPublicationAndCheckCleanup(page) {
    checkpoint = 'publication recovery preflight'
    await call(page).getByRole('button', { name: 'Check microphone and camera' }).click()
    await call(page).getByRole('status').filter({ hasText: 'Devices checked' }).waitFor()
    await call(page).locator('.call-video').evaluate(video => { window.__testFailedPreview = video.srcObject })
    await page.evaluate(() => {
      const devices = navigator.mediaDevices
      Object.defineProperty(devices, 'getUserMedia', { configurable: true, value: constraints => {
        return Promise.reject(new DOMException('synthetic blocked publish', 'NotAllowedError'))
      } })
    })
    checkpoint = 'publication failure response'
    await call(page).getByRole('button', { name: 'Join consultation' }).click()
    try { await call(page).getByRole('status').filter({ hasText: 'Could not connect' }).waitFor({ timeout: 30000 }) }
    catch {
      diagnostic = JSON.stringify(await call(page).evaluate(node => ({
        status: node.querySelector('[role=status]')?.innerText,
        buttons: [...node.querySelectorAll('button')].map(button => button.innerText),
      })))
      throw new Error('publication failure did not cleanly fail')
    }
    checkpoint = 'publication failure stopped local preview tracks'
    assert(await page.evaluate(() => window.__testFailedPreview.getTracks().every(track => track.readyState === 'ended')))
    checkpoint = 'publication failure left no connected controls'
    assert.equal(await call(page).getByRole('button', { name: /Leave/ }).count(), 0)
    await page.evaluate(() => {
      delete navigator.mediaDevices.getUserMedia
      delete window.__testFailedPreview
    })
  }
  async function failConnectionAndCheckCleanup(page) {
    await call(page).getByRole('button', { name: 'Check microphone and camera' }).click()
    await call(page).getByRole('status').filter({ hasText: 'Devices checked' }).waitFor()
    await call(page).locator('.call-video').evaluate(video => { video.__testConnectionPreview = video.srcObject })
    await page.route('**/api/method/tele_tena.api.consultations.join', async route => {
      const response = await route.fetch()
      const result = await response.json()
      result.message.url = 'wss://127.0.0.1:1'
      await route.fulfill({ response, json: result })
    })
    await call(page).getByRole('button', { name: 'Join consultation' }).click()
    await call(page).getByRole('status').filter({ hasText: 'Could not connect' }).waitFor({ timeout: 20000 })
    assert(await call(page).locator('.call-video').evaluate(video => video.__testConnectionPreview.getTracks().every(track => track.readyState === 'ended')))
    assert.equal(await call(page).getByRole('button', { name: /Leave/ }).count(), 0)
    await page.unroute('**/api/method/tele_tena.api.consultations.join')
  }
  async function doubleJoinAndUnmountBeforeToken(page) {
    checkpoint='duplicate join preflight check'
    await call(page).getByRole('button', { name: 'Check microphone and camera' }).click()
    checkpoint='duplicate join media preview ready'
    await call(page).getByRole('status').filter({ hasText: 'Devices checked' }).waitFor()
    await call(page).locator('.call-video').evaluate(video => { window.__lateJoinPreview = video.srcObject })
    let requests = 0
    let enteredResolve
    let releaseResolve
    const entered = new Promise(resolve => { enteredResolve = resolve })
    const held = new Promise(resolve => { releaseResolve = resolve })
    const pattern = '**/api/method/tele_tena.api.consultations.join'
    let livekitSockets = 0
    page.on('websocket', socket => { if (socket.url().includes('livekit')) livekitSockets++ })
    await page.route(pattern, async route => {
      requests++
      const response = await route.fetch()
      const payload = await response.json()
      if (requests === 1) enteredResolve()
      await held
      await route.fulfill({ response, json: payload }).catch(() => undefined)
    })
    checkpoint='issue and hold the duplicated join request'
    const button = call(page).getByRole('button', { name: 'Join consultation' })
    await button.evaluate(node => { node.click(); node.click() })
    await entered
    checkpoint='assert duplicate join was blocked and navigate away'
    await new Promise(resolve => setTimeout(resolve, 250))
    try {
      assert.equal(requests, 1, 'rapid duplicate Join must issue only one token request')
      await page.getByRole('link',{name:'Back to consultation details'}).click()
      checkpoint='call view unmounted'
      await page.getByRole('link',{name:'Back to appointments'}).click()
      await page.getByRole('heading', {name:'Appointments', exact:true}).waitFor()
      checkpoint='late result stopped the preview'
      assert(await page.evaluate(() => window.__lateJoinPreview.getTracks().every(track => track.readyState === 'ended')))
    } finally {
      releaseResolve()
      await page.unroute(pattern).catch(() => undefined)
    }
    await new Promise(resolve => setTimeout(resolve, 1000))
    assert.equal(livekitSockets, 0, 'late token response after component unmount must not connect')
    checkpoint='return to appointment details after the held response'
    await page.goto(base+'/clinician/consultations/'+fixture.appointment_id)
    await page.getByRole('link', {name:'Join consultation', exact:true}).click()
    await call(page).waitFor()
  }
  try {
    await Promise.all([login(patient, 'p1'), login(clinician, 'c1')])
    await patientCard().waitFor()
    await clinicianCard().waitFor()
    if (process.env.TELE_TENA_MEDIA_PHASE === 'end') {
      await prepareAndJoin(patient)
      await prepareAndJoin(clinician)
      await call(patient).getByRole('button', { name: /Leave/ }).click()
      await call(patient).getByRole('status').filter({ hasText: 'You left the consultation' }).waitFor()
      await prepareAndJoin(patient)
      const endButton = call(clinician).getByRole('button', { name: 'End for everyone' })
      try { await endButton.waitFor({ timeout: 10000 }) }
      catch {
        diagnostic = JSON.stringify(await call(clinician).evaluate(node => ({
          text: node.innerText,
          statuses: [...node.querySelectorAll('[role=status]')].map(item => item.innerText),
          buttons: [...node.querySelectorAll('button')].map(item => ({ text: item.innerText, disabled: item.disabled })),
        })))
        throw new Error('clinician End control did not become available')
      }
      let endResponse = null
      clinician.on('response', response => {
        if (response.url().includes('tele_tena.api.consultations.end')) endResponse = response.status()
      })
      await endButton.click()
    await clinician.getByRole('dialog').getByRole('button', { name: 'End for everyone', exact: true }).click()
      try {
        await call(clinician).getByText(/Consultation status:/).filter({ hasText: 'The clinician ended this consultation' }).waitFor({ timeout: 15000 })
        checkpoint = 'patient observes End through lifecycle polling'
        await call(patient).getByText(/Consultation status:/).filter({ hasText: 'The clinician ended this consultation' }).waitFor({ timeout: 15000 })
      } catch {
        diagnostic = JSON.stringify({ endResponse, clinician: await call(clinician).evaluate(node => node.innerText),
          patient: await call(patient).evaluate(node => node.innerText) })
        throw new Error('End did not close both consultation views')
      }
      assert.deepEqual(errors, [])
      console.log('PASS: clinician End closed both sessions after patient Leave/rejoin')
      return
    }
    checkpoint = 'duplicate join is blocked and late response is cleaned on unmount'
    await doubleJoinAndUnmountBeforeToken(clinician)
    await clinicianCard().waitFor()
    checkpoint = 'patient joins'
    checkpoint = 'patient preflight button'
    try { await call(patient).getByRole('button', { name: 'Check microphone and camera' }).click() }
    catch {
      diagnostic = await call(patient).evaluate(node => JSON.stringify({
        statusText: [...node.querySelectorAll('[role=status]')].map(item => item.innerText),
        buttons: [...node.querySelectorAll('button')].map(item => ({ text: item.innerText, disabled: item.disabled })),
      }))
      throw new Error('preflight button was not actionable')
    }
    checkpoint = 'patient local preview stream'
    await call(patient).getByRole('status').filter({ hasText: 'Devices checked' }).waitFor()
    const hasPreview = await call(patient).locator('.call-video').evaluate(video => { window.__testPreview = video.srcObject; return Boolean(video.srcObject) })
    assert(hasPreview)
    checkpoint = 'changing media mode stops preview tracks immediately'
    try { await call(patient).getByRole('checkbox').check() }
    catch {
      diagnostic = await call(patient).evaluate(node => JSON.stringify({
        status: node.querySelector('[role=status]')?.innerText,
        checkbox: [...node.querySelectorAll('input[type=checkbox]')].map(input => ({ checked: input.checked, disabled: input.disabled })),
      }))
      throw new Error('media mode toggle unavailable')
    }
    checkpoint = 'checking stopped preview tracks'
    const previewWasStopped = await patient.evaluate(() => window.__testPreview.getTracks().every(track => track.readyState === 'ended'))
    diagnostic = JSON.stringify(await patient.evaluate(() => ({ tracks: window.__testPreview.getTracks().map(track => track.readyState) })))
    assert(previewWasStopped)
    assert.equal(await call(patient).locator('.call-video').count(), 0)
    await call(patient).getByRole('checkbox').uncheck()
    assert.equal(await call(patient).locator('.call-video').evaluate(video => video.srcObject), null)
    checkpoint = 'connection failure cleans preview and room'
    await failConnectionAndCheckCleanup(patient)
    checkpoint = 'publication failure cleans room and local tracks'
    await failPublicationAndCheckCleanup(patient)
    checkpoint = 'patient joins after clean recovery'
    await prepareAndJoin(patient)
    checkpoint = 'clinician joins'
    await prepareAndJoin(clinician)
    checkpoint = 'capture connected call at responsive widths'
    for (const page of [patient, clinician]) {
      for (const width of [320, 390, 768, 1440]) {
        await page.setViewportSize({ width, height: 960 })
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false)
        await page.screenshot({ path: `/tmp/tele-tena-presentation-review/video-call-${width}-${page === patient ? 'patient' : 'clinician'}.png`, fullPage: true })
      }
    }
    checkpoint = 'two-way remote media'
    diagnostic = JSON.stringify(await Promise.all([patient, clinician].map(async (page) => ({
      status: await call(page).getByRole('status').textContent(),
      remoteElements: await call(page).locator('.call-remote').evaluate(node => [...node.children].map(child => child.tagName)),
    }))))
    for (const [name, page] of [['patient', patient], ['clinician', clinician]]) {
      checkpoint = name + ' remote video track'
      await call(page).locator('.call-remote video').waitFor({ timeout: 45000 })
      checkpoint = name + ' remote audio track'
      const tags = await call(page).locator('.call-remote').evaluate(node => [...node.children].map(child => child.tagName))
      diagnostic = JSON.stringify({ participant: name, remoteElementsAfterWait: tags })
      assert(tags.includes('AUDIO') && tags.includes('VIDEO'))
    }
    checkpoint = 'polling preserves connected media status'
    await new Promise(resolve => setTimeout(resolve, 6000))
    for (const page of [patient, clinician]) assert.match(await call(page).getByRole('status').innerText(), /Connected/)
    checkpoint = 'audio-only presentation derives from existing audio track'
    await call(patient).getByRole('button', {name: 'Audio only', exact: true}).click()
    await call(patient).locator('.audio-participant').waitFor()
    for(const width of [320,390,768,1440]){await patient.setViewportSize({width,height:960});assert.equal(await patient.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);await patient.screenshot({path:`/tmp/tele-tena-presentation-review/audio-only-${width}.png`,fullPage:true})}
    await call(patient).getByRole('button', {name: 'Turn video on', exact: true}).click()
    await call(patient).getByRole('button', {name: 'Check microphone and camera', exact: true}).click()
    await call(patient).getByRole('status').filter({hasText:'Devices checked'}).waitFor()
    await call(patient).getByRole('button', {name:'Join consultation', exact:true}).click()
    await call(patient).getByRole('status').filter({hasText:'Connected'}).waitFor({timeout:45000})
    checkpoint = 'participant leave and rejoin'
    await call(patient).getByRole('button', { name: /Leave/ }).click()
    await call(patient).getByRole('status').filter({ hasText: 'You left the consultation' }).waitFor()
    await prepareAndJoin(patient)
    checkpoint = 'clinician ends both-sided room'
    const endButton = call(clinician).getByRole('button', { name: 'End for everyone' })
    try { await endButton.waitFor({ timeout: 10000 }) }
    catch {
      diagnostic = JSON.stringify(await call(clinician).evaluate(node => ({
        text: node.innerText,
        statuses: [...node.querySelectorAll('[role=status]')].map(item => item.innerText),
        buttons: [...node.querySelectorAll('button')].map(item => ({ text: item.innerText, disabled: item.disabled })),
      })))
      throw new Error('clinician End control did not become available')
    }
    await endButton.click()
    await clinician.getByRole('dialog').getByRole('button', { name: 'End for everyone', exact: true }).click()
    const clinicianStatus = call(clinician).getByText(/Consultation status:/)
    try { await clinicianStatus.filter({ hasText: 'The clinician ended this consultation' }).waitFor({ timeout: 12000 }) }
    catch {
      diagnostic = 'clinician end status: ' + (await clinicianStatus.textContent())
      throw new Error('end status failed')
    }
    checkpoint = 'patient observes End through lifecycle polling'
    await call(patient).getByText(/Consultation status:/).filter({ hasText: 'The clinician ended this consultation' }).waitFor({ timeout: 30000 })
    checkpoint = 'ended sessions have no active media elements or Join controls'
    for (const page of [patient, clinician]) {
      assert.equal(await call(page).getByRole('button', { name: 'Join consultation', exact: true }).count(), 0)
      assert.equal(await call(page).locator('.call-remote audio, .call-remote video').count(), 0)
    }
    checkpoint = 'post-call private note draft and explicit completion'
    await clinician.goto(base+'/clinician/consultations/'+fixture.appointment_id)
    await clinician.getByRole('heading',{name:'Consultation notes',exact:true}).waitFor()
    await capture(clinician,'end-of-call-notes')
    const noteFields=clinician.locator('.note-editor textarea')
    await noteFields.nth(0).fill('Synthetic private consultation note')
    await noteFields.nth(1).fill('Synthetic patient summary and next steps')
    await clinician.getByRole('button',{name:'Preview patient summary',exact:true}).click()
    await clinician.getByText('Synthetic patient summary and next steps',{exact:true}).waitFor()
    clinician.once('dialog',dialog=>dialog.accept())
    await clinician.getByRole('button',{name:'Finalize consultation',exact:true}).click()
    await clinician.getByText('Consultation finalized.',{exact:true}).waitFor()
    await capture(clinician,'completed-consultation-clinician')
    await patient.goto(base+'/patient/consultations/'+fixture.appointment_id)
    await patient.getByText('Synthetic patient summary and next steps',{exact:true}).waitFor()
    assert.equal(await patient.getByText('Synthetic private consultation note',{exact:true}).count(),0)
    await capture(patient,'completed-consultation-patient')
    assert.deepEqual(errors, [])
    console.log('PASS: two independent Chromium contexts exchanged fake-device audio/video; patient leave/rejoin worked; clinician end closed both sessions')
  } finally {
    await browser.close()
  }
}

main().catch(error => {
  // Intentionally omit exception details: SDK/network errors may include URLs or token context.
  const safeReason=error?.name==='AssertionError'?String(error.message).slice(0,180):String(error?.name||'interaction failure')
  console.error(`FAIL: consultation browser checkpoint ${checkpoint} (${safeReason})${diagnostic ? ` ${diagnostic}` : ''}`)
  process.exitCode = 1
})
