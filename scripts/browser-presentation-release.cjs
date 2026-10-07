// Real UI/API flows with isolated synthetic fixture users. Only delivery-request UI is mocked.
const { chromium } = require('playwright')
const fs = require('node:fs')
const assert = require('node:assert/strict')
const fixture = JSON.parse(fs.readFileSync(process.env.TELE_TENA_REDESIGN_FIXTURE, 'utf8'))
const base = process.env.TELE_TENA_TEST_BASE || 'http://127.0.0.1:5173'
const output = '/tmp/tele-tena-presentation-review'
fs.mkdirSync(output, { recursive: true })
let checkpoint = 'launch'
let diagnostic = ''
function mark(step) { checkpoint = step; console.log('STEP: ' + step) }
async function main() {
  const browser = await chromium.launch({ args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'] })
  const contexts = []
  const errors = []
  async function pageFor(kind) {
    const context = await browser.newContext({ permissions: ['camera', 'microphone'], timezoneId: 'Africa/Addis_Ababa' })
    contexts.push(context)
    const page = await context.newPage()
    page.setDefaultTimeout(15000)
    page.setDefaultNavigationTimeout(20000)
    page.on('pageerror', () => errors.push('page exception'))
    // This visual fixture mocks delivery capabilities along with its OTP send;
    // backend provider readiness is covered separately.
    await page.route('**/api/method/tele_tena.api.contact_auth.sign_in_options', route => route.fulfill({json:{message:{phone_otp:true,email_otp:true,patient_registration:true,clinician_registration:true}}}))
    if (kind) {
      if(kind==='admin') await page.route('**/api/method/tele_tena.api.journey.applications*',async route=>{const response=await route.fetch();const body=await response.json();body.message=(body.message||[]).filter(item=>item.user===fixture.users.reviewapplicant);await route.fulfill({response,json:body})})
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
  async function capture(page, name, widths = [320, 390, 768, 1440]) {
    // Frappe may keep authenticated/realtime requests active. Callers assert
    // their screen's critical content before capture; DOM readiness plus the
    // per-viewport font wait is stable without requiring network quiescence.
    await page.waitForLoadState('domcontentloaded')
    for (const width of widths) {
      await page.setViewportSize({ width, height: 960 })
      await page.evaluate(() => document.fonts.ready)
      await page.screenshot({ path: `${output}/${name}-${width}.png`, fullPage: true })
      const overflow=await page.evaluate(()=>({width:document.documentElement.scrollWidth,offenders:[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.right>innerWidth+1||r.left< -1}).slice(0,12).map(e=>({tag:e.tagName,cls:String(e.className).slice(0,80),text:e.innerText?.slice(0,80),left:Math.round(e.getBoundingClientRect().left),right:Math.round(e.getBoundingClientRect().right)}))}))
      assert.equal(overflow.width > width + 1, false, `${name} overflows at ${width}: ${JSON.stringify(overflow)}`)
    }
  }
  try {
    const guest = await pageFor()
    mark('homepage screenshots')
    await guest.goto(base)
    if (new URL(base).pathname === '/teletena') {
      await guest.waitForURL(url => new URL(url).pathname === '/teletena/')
    }
    await guest.getByRole('heading', { name: 'Find support. Make time for care.' }).waitFor()
    await guest.getByRole('heading', { name: 'Talk to someone who fits your needs.' }).waitFor()
    await capture(guest, 'homepage', [320, 390, 768, 1440])
    const manifest=await guest.locator('link[rel="manifest"]').getAttribute('href')
    assert.ok(['/manifest.webmanifest','/assets/tele_tena/review/manifest.webmanifest'].includes(manifest),
      `manifest must resolve in the active Vite or built Frappe deployment: ${manifest}`)
    mark('service worker installation readiness')
    await Promise.race([
      guest.evaluate(async()=>{await navigator.serviceWorker.ready}),
      new Promise((_, reject) => setTimeout(() => reject(new Error('service worker did not become ready')), 15000))
    ])
    mark('service worker controls first page')
    await guest.reload()
    await guest.waitForFunction(()=>Boolean(navigator.serviceWorker.controller), null, {timeout:15000})
    mark('offline navigation fallback')
    await guest.context().setOffline(true)
    const offlineNavigation = await guest.goto(base+'/').then(response => ({ ok: true, status: response?.status() ?? null })).catch(() => ({ ok: false, status: null }))
    const offlineState = await guest.evaluate(() => ({
      heading: document.querySelector('h1')?.textContent?.trim() ?? '',
      controlled: Boolean(navigator.serviceWorker.controller),
      pathInScope: location.pathname.startsWith(new URL(navigator.serviceWorker.controller?.scriptURL ?? location.href).pathname.replace(/sw\.js$/, '')),
    }))
    console.log(`OFFLINE_FALLBACK_DIAGNOSTIC: navigation=${offlineNavigation.ok ? 'resolved' : 'rejected'}; status=${offlineNavigation.status ?? 'none'}; heading=${offlineState.heading === 'You’re offline' ? 'expected' : 'missing'}; controller=${offlineState.controlled ? 'present' : 'missing'}; path=${offlineState.pathInScope ? 'in-scope' : 'out-of-scope'}`)
    assert.equal(offlineState.heading, 'You’re offline', 'offline fallback heading was not rendered')
    await guest.screenshot({path:`${output}/offline-state-390.png`,fullPage:true})
    await guest.context().setOffline(false)
    mark('phone entry is one field and expected guest is signed out')
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
    mark('patient onboarding save and resume')
    const newcomer = await pageFor('newpatient')
    mark('patient onboarding draft loaded')
    await newcomer.getByLabel('Preferred name or alias', { exact: true }).fill('Synthetic newcomer')
    const saveResponsePromise = newcomer.waitForResponse(response =>
      new URL(response.url()).pathname.endsWith('tele_tena.api.contact_auth.save_onboarding'), { timeout: 15000 }
    ).catch(() => null)
    await newcomer.getByRole('button', { name: 'Save for later', exact: true }).click()
    const saveResponse = await saveResponsePromise
    const saveBody = saveResponse ? await saveResponse.json().catch(() => ({})) : {}
    console.log(`ONBOARDING_SAVE_DIAGNOSTIC: response=${saveResponse ? saveResponse.status() : 'missing'}; serverError=${saveBody.exc_type ? 'present' : 'none'}`)
    await newcomer.getByText('Progress saved. You can return to this step.').waitFor()
    mark('patient onboarding draft saved')
    await newcomer.reload()
    await newcomer.waitForFunction(()=>[...document.querySelectorAll('input')].some(input=>input.labels?.[0]?.innerText.includes('Preferred name or alias')&&input.value==='Synthetic newcomer'),null,{timeout:15000}).catch(async()=>{diagnostic=await newcomer.evaluate(()=>{const field=[...document.querySelectorAll('input')].find(input=>input.labels?.[0]?.innerText.includes('Preferred name or alias'));return `path=${location.pathname.startsWith('/teletena/')?'app':'unexpected'}; heading=${Boolean(document.querySelector('h1'))}; field=${field?'present':'missing'}; valuePersisted=${field?.value==='Synthetic newcomer'}; alert=${Boolean(document.querySelector('[role=alert]'))}; status=${Boolean(document.querySelector('[role=status]'))}`});console.log(`ONBOARDING_RELOAD_DIAGNOSTIC: ${diagnostic}`);throw new Error('saved onboarding value did not reload')})
    mark('patient onboarding draft reloaded')
    await capture(newcomer, 'patient-onboarding')
    mark('patient onboarding first step verified')
    await newcomer.getByRole('button', { name: 'Continue', exact: true }).click()
    await newcomer.getByLabel('I am 18 or older.', { exact: true }).check()
    await newcomer.getByLabel('I consent to storing my profile and the information I choose to share for this care journey.').check()
    await newcomer.getByRole('button', { name: 'Continue', exact: true }).click()
    mark('patient onboarding consent saved')
    await newcomer.getByRole('button', { name: 'Continue', exact: true }).click()
    mark('patient onboarding privacy step saved')
    await newcomer.getByRole('button', { name: 'Find care', exact: true }).waitFor({ state: 'visible' })
    mark('patient onboarding completion action ready')
    const sidBefore = (await newcomer.context().cookies()).find(cookie => cookie.name === 'sid')?.value || ''
    const completionResponsePromise = newcomer.waitForResponse(response =>
      new URL(response.url()).pathname.endsWith('tele_tena.api.contact_auth.save_onboarding'), { timeout: 15000 }
    ).catch(() => null)
    const sessionResponsePromise = newcomer.waitForResponse(response =>
      new URL(response.url()).pathname.endsWith('tele_tena.api.contact_auth.session'), { timeout: 15000 }
    ).catch(() => null)
    await newcomer.getByRole('button', { name: 'Find care', exact: true }).click()
    const completionResponse = await completionResponsePromise
    const completionBody = completionResponse ? await completionResponse.json().catch(() => ({})) : {}
    const sidAfter = (await newcomer.context().cookies()).find(cookie => cookie.name === 'sid')?.value || ''
    const responseSetCookie = completionResponse?.headers()['set-cookie'] || ''
    console.log(`ONBOARDING_COMPLETE_DIAGNOSTIC: response=${completionResponse ? completionResponse.status() : 'missing'}; serverError=${completionBody.exc_type ? 'present' : 'none'}; completed=${typeof completionBody.message?.completed === 'boolean' ? completionBody.message.completed : 'unknown'}; sessionCookiePreserved=${Boolean(sidBefore && sidAfter && sidBefore === sidAfter)}; sessionCookieOpaque=${sidAfter.length >= 32}; responseSetSessionCookie=${/sid=/i.test(responseSetCookie)}`)
    await newcomer.waitForURL('**/patient', { timeout: 15000 }).catch(async () => {
      const sessionResponse = await sessionResponsePromise
      const sessionBody = sessionResponse ? await sessionResponse.json().catch(() => ({})) : {}
      const sessionMessage = sessionBody.message || {}
      const safeErrorCode = typeof sessionBody.tele_tena_error === 'string' && /^[a-z_]{1,40}$/.test(sessionBody.tele_tena_error) ? sessionBody.tele_tena_error : 'none'
      const safeException = typeof sessionBody.exc_type === 'string' && /^[A-Za-z_]{1,60}$/.test(sessionBody.exc_type) ? sessionBody.exc_type : 'none'
      const safeKeys = Object.keys(sessionBody).filter(key => /^[a-z_]{1,40}$/.test(key)).sort().join(',') || 'none'
      diagnostic = await newcomer.evaluate(() => `path=${location.pathname.includes('/onboarding') ? 'onboarding' : 'other'}; alert=${Boolean(document.querySelector('[role=alert]'))}; status=${Boolean(document.querySelector('[role=status]'))}`)
      console.log(`ONBOARDING_COMPLETE_STATE: ${diagnostic}; sessionResponse=${sessionResponse ? sessionResponse.status() : 'missing'}; sessionError=${safeErrorCode}; exception=${safeException}; responseKeys=${safeKeys}; authenticated=${sessionMessage.authenticated === true}; profile=${Boolean(sessionMessage.profile)}; patientRole=${Array.isArray(sessionMessage.roles) && sessionMessage.roles.includes('Tele Tena Patient')}`)
      throw new Error('patient registration did not reach patient workspace')
    })
    mark('patient onboarding completed')
    mark('clinician onboarding')
    const applicant = await pageFor('newclinician')
    mark('clinician onboarding draft loaded')
    await applicant.getByLabel('Professional name', { exact: true }).waitFor()
    mark('clinician onboarding form ready')
    await capture(applicant, 'clinician-onboarding')
    mark('clinician onboarding initial state verified')
    mark('patient workspace and discovery')
    mark('sign in existing patient fixture')
    const patient = await pageFor('p1')
    await patient.getByRole('heading', { name: 'Your next appointment' }).waitFor()
    mark('existing patient home loaded')
    await capture(patient, 'patient-home')
    await patient.getByRole('button', {name: 'Take a quick tour', exact: true}).click()
    await patient.getByRole('dialog', {name: /Find care/}).waitFor()
    await capture(patient, 'tour-patient')
    await patient.getByRole('button',{name:'Next',exact:true}).click()
    mark('patient tour next step')
    await patient.getByRole('dialog',{name:/Choose a time/}).waitFor()
    await patient.getByRole('button',{name:'Next',exact:true}).click()
    mark('patient tour appointment navigation')
    await patient.waitForURL('**/patient/appointments')
    mark('patient tour reached appointments')
    await patient.getByRole('dialog',{name:/Appointments/}).waitFor()
    mark('patient tour appointments step')
    await patient.getByRole('button',{name:'Back',exact:true}).click()
    await patient.waitForURL('**/patient/discovery')
    mark('patient tour returned to discovery')
    await patient.getByRole('button', {name: 'Skip', exact: true}).click()
    mark('patient tour dismissed')
    await patient.reload()
    await patient.getByRole('button',{name:'Help & tours',exact:true}).click()
    mark('patient tour replay requested')
    await patient.getByRole('dialog',{name:/Find care/}).waitFor()
    mark('patient tour replay opened')
    await patient.evaluate(()=>document.querySelector('[data-tour="patient-discovery"]')?.removeAttribute('data-tour'))
    await patient.waitForTimeout(500)
    const targetState=await patient.evaluate(()=>({targetPresent:Boolean(document.querySelector('[data-tour="patient-discovery"]')),missingNotice:[...document.querySelectorAll('[role="status"]')].some(node=>node.textContent?.includes('not available'))}))
    console.log(`TOUR_TARGET_DIAGNOSTIC: target=${targetState.targetPresent?'present':'missing'}; notice=${targetState.missingNotice?'present':'missing'}`)
    await patient.getByRole('status').filter({hasText:'This feature is not available in the current view'}).waitFor()
    mark('patient tour missing target recovery')
    await patient.getByRole('button',{name:'Skip',exact:true}).click()
    await patient.goto(base + '/patient/discovery')
    await patient.getByRole('heading', { name: 'Find the right conversation for you.' }).waitFor()
    await patient.getByLabel('Clinician or service', { exact: true }).fill('Synthetic test consultation')
    await capture(patient, 'discovery')
    mark('persisted booking and privacy choices')
    mark('offering loads persisted availability')
    await patient.goto(base + '/patient/book/' + fixture.offering)
    try { await patient.getByRole('group', { name: 'Available times' }).waitFor({ timeout: 10000 }) } catch { diagnostic = JSON.stringify(await patient.evaluate(() => ({ path: location.pathname, headings: [...document.querySelectorAll('h1,h2')].map(x => x.innerText), notices: [...document.querySelectorAll('[role=alert],[role=status]')].map(x => x.innerText) }))); throw new Error('booking calendar unavailable') }
    await patient.getByRole('button', { name: /\d{4}-\d{2}-\d{2}/ }).first().click()
    await patient.getByRole('group', { name: 'Available times' }).getByRole('button').first().click()
    mark('choose available time and inspect schedule editor')
    const clinician = await pageFor('c1')
    await clinician.goto(base + '/clinician/availability')
    await clinician.getByRole('heading', { name: /Availability/ }).waitFor()
    await capture(clinician, 'availability-editor')
    await clinician.goto(base + '/clinician')
    await clinician.getByRole('button', {name: 'Take a quick tour', exact: true}).click()
    await clinician.getByRole('dialog', {name: /Your practice/}).waitFor()
    await capture(clinician, 'tour-clinician')
    await clinician.getByRole('button', {name: 'Skip', exact: true}).click()
    await clinician.goto(base + '/clinician')
    mark('choose available start time')
    await patient.getByRole('button', { name: 'Continue', exact: true }).click()
    mark('enter request and sharing choices')
    await patient.getByLabel('What would you like to talk about?', { exact: true }).fill('Synthetic redesign request')
    await patient.getByLabel('Share my preferred name', { exact: true }).check()
    mark('request-specific privacy preview')
    await patient.getByRole('button', { name: 'Preview and continue', exact: true }).click()
    await patient.getByRole('heading', { name: 'Review your session', exact: true }).waitFor()
    await capture(patient, 'booking-preview')
    mark('confirm appointment and reserve simulated balance')
    await patient.getByRole('button', { name: /Confirm session/ }).click()
    await patient.waitForURL('**/patient/appointments')
    await capture(patient, 'appointments')
    mark('profile defaults unaffected')
    await patient.goto(base + '/patient/account')
    await patient.getByRole('button', {name: 'Privacy & sharing', exact: true}).click()
    await patient.getByLabel('Share my preferred name by default', { exact: true }).waitFor()
    assert.equal(await patient.getByLabel('Share my preferred name by default').isChecked(), false)
    await capture(patient, 'profile-privacy')
    await patient.goto(base + '/patient/payments')
    await patient.getByRole('heading', { name: 'Payments', exact: true }).waitFor()
    await capture(patient, 'payments')
    mark('clinician Today and practice screens')
    // Reuse the authenticated clinician context from the schedule screenshot.
    await clinician.getByRole('heading', { name: 'Today', exact: true }).waitFor()
    await capture(clinician, 'clinician-today')
    for (const route of ['availability', 'services', 'care']) { await clinician.goto(base + '/clinician/' + route); await capture(clinician, 'clinician-' + route) }
    await clinician.getByRole('link',{name:'View record',exact:true}).first().click()
    await clinician.getByRole('link',{name:'Open consultation',exact:true}).waitFor()
    assert.equal((await clinician.locator('body').innerText()).includes(fixture.users.p1),false,'care record must not expose the patient account identifier')
    await capture(clinician,'care-record')
    mark('consultation preflight')
    await patient.goto(base + '/patient/consultations/' + fixture.appointment_id)
    await patient.getByRole('heading', {name: 'Synthetic test consultation', exact: true}).waitFor()
    await capture(patient, 'consultation-detail')
    await patient.getByRole('link', {name: 'Join consultation', exact: true}).click()
    await capture(patient, 'call-preflight-screen')
    const checkDevices = patient.getByRole('button', { name: /Check microphone and camera|Check microphone/ })
    if (!await checkDevices.count()) diagnostic=JSON.stringify(await patient.evaluate(()=>({path:location.pathname,buttons:[...document.querySelectorAll('button')].map(b=>b.innerText),text:document.body.innerText.slice(-1200)})))
    await checkDevices.click()
    await patient.getByRole('status').filter({ hasText: 'Devices checked' }).waitFor()
    await capture(patient, 'consultation-preflight')
    mark('administrative review')
    const admin = await pageFor('admin')
    await admin.getByRole('heading', { name: 'Application review' }).waitFor()
    await capture(admin, 'administrator-review')
    await admin.getByRole('button', {name: 'Take a quick tour', exact: true}).click()
    await admin.getByRole('dialog', {name: /Application queue/}).waitFor()
    await capture(admin, 'tour-administrator')
    mark('showcase scripts keyboard dialogs and zoom')
    await guest.goto(base + '/showcase')
    if (new URL(base).pathname.startsWith('/teletena')) {
      await guest.getByRole('heading', { name: 'Find support. Make time for care.' }).waitFor()
      assert.equal(await guest.getByRole('tab').count(), 0, 'development showcase must not be exposed in the production package')
      mark('development-only component showcase is not exposed by production package')
    } else {
      await capture(guest, 'showcase', [320, 390, 768, 1440])
      mark('showcase rendered responsively')
      const firstTab = guest.getByRole('tab', { name: 'Overview', exact: true })
      await firstTab.focus()
      await guest.keyboard.press('ArrowRight')
      await guest.waitForFunction(() => document.getElementById('tab-privacy')?.getAttribute('aria-selected') === 'true')
      mark('showcase keyboard tab interaction')
      await guest.getByRole('button', { name: 'Open dialog', exact: true }).click()
      await guest.getByRole('dialog').waitFor()
      assert.equal(await guest.evaluate(() => document.querySelector('[role=dialog]').contains(document.activeElement)), true)
      await guest.keyboard.press('Escape')
      assert.equal(await guest.getByRole('dialog').count(), 0)
      mark('showcase dialog focus and escape')
      await guest.locator('main').getByLabel('Language / ቋንቋ / Afaan').selectOption('am')
      await capture(guest, 'showcase-amharic', [390, 768, 1440])
      mark('showcase Amharic layout')
      await guest.locator('main').getByLabel('Language / ቋንቋ / Afaan').selectOption('om')
      await capture(guest, 'showcase-oromo', [390])
      mark('showcase Afaan Oromo layout')
      await guest.emulateMedia({ reducedMotion: 'reduce' })
      await guest.setViewportSize({ width: 384, height: 960 })
      await guest.screenshot({ path: `${output}/showcase-200-percent-equivalent-384px.png`, fullPage: true })
      assert.equal(await guest.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false)
      mark('showcase zoom and reduced motion')
    }
    assert.deepEqual(errors, [])
    console.log('PASS: public/auth steps, resumable onboarding, real booking/privacy flow, portals, preflight, responsive screenshots, keyboard dialog, scripts and 200% zoom; no live delivery sent')
  } finally { await browser.close() }
}
main().catch(error => { console.error('FAIL: redesign checkpoint ' + checkpoint + ' — ' + error.message + (diagnostic ? ' ' + diagnostic : ''));  process.exitCode = 1 })
