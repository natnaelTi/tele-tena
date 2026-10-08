// Fault-injection check for clinician availability feedback on the built app.
// Authentication is real; only the readiness query and validation response are
// controlled so an administrator policy change is not needed for this UI test.
const { chromium } = require('playwright')
const fs = require('node:fs')
const path = require('node:path')
const assert = require('node:assert/strict')

const site = process.env.TELE_TENA_REVIEW_SITE_PATH
assert.ok(site && /^tele-tena-[a-z0-9-]+\.localhost$/.test(require('node:path').basename(site)))
const base = process.env.TELE_TENA_BROWSER_ORIGIN || 'http://127.0.0.1:8017'
const app = base + '/teletena'
const seed = JSON.parse(fs.readFileSync(site + '/private/tele_tena_review_seed.json', 'utf8'))
const credentials = JSON.parse(fs.readFileSync(site + '/private/tele_tena_review_accounts.json', 'utf8'))
const account = seed.users.clinician

let checkpoint = 'launch'
;(async () => {
  const browser = await chromium.launch({ headless: true })
  try {
    const actualContext = await browser.newContext()
    const actualPage = await actualContext.newPage()
    await actualPage.route('**/api/method/tele_tena.api.open_requests.request_presence**', route =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
        message: { ready: false, configured: false, reasons: ['language_required', 'immediate_policy_required', 'no_immediate_capacity'] },
      }) }))
    checkpoint = 'real clinician sign-in page'
    await actualPage.goto(app + '/sign-in')
    checkpoint = 'select email sign-in'
    await actualPage.getByRole('button', { name: 'Use email instead' }).click()
    checkpoint = 'enter clinician credentials'
    await actualPage.getByLabel('Email', { exact: true }).fill(account)
    await actualPage.getByLabel('Password', { exact: true }).fill(credentials[account])
    checkpoint = 'submit clinician credentials'
    await actualPage.getByRole('button', { name: 'Sign in', exact: true }).click()
    checkpoint = 'wait for clinician workspace'
    await actualPage.waitForURL(/\/teletena\/clinician(?:\/|$)/)
    checkpoint = 'set review language for assertions'
    await actualPage.getByLabel('Language / ቋንቋ / Afaan').selectOption('en')
    checkpoint = 'wait for live readiness reasons'
    await actualPage.screenshot({ path: '/tmp/tele-tena-presentation-review/request-readiness/live-state.png', fullPage: true })
    await actualPage.getByRole('link', { name: 'Add a care language', exact: true }).waitFor()
    checkpoint = 'wait for immediate policy setup link'
    await actualPage.getByRole('link', { name: 'Ask a reviewer to enable immediate requests for a service', exact: true }).waitFor()
    assert.equal(await actualPage.getByRole('button', { name: 'Go available', exact: true }).isDisabled(), true)
    assert.equal(await actualPage.getByText('Requests paused', { exact: true }).count(), 1)
    await actualPage.setViewportSize({ width: 320, height: 900 })
    const mobileNav = actualPage.getByRole('navigation', { name: 'Mobile workspace', exact: true })
    checkpoint = 'show mobile workspace navigation'
    await mobileNav.waitFor({ state: 'visible' })
    checkpoint = 'find mobile availability shortcut'
    await mobileNav.getByRole('link', { name: 'Availability', exact: true }).waitFor()
    const moreButton = mobileNav.getByRole('button', { name: 'More', exact: true })
    checkpoint = 'open mobile more menu'
    await moreButton.click()
    const moreDialog = actualPage.getByRole('dialog', { name: 'More workspace links', exact: true })
    checkpoint = 'inspect mobile more menu'
    await moreDialog.getByRole('link', { name: 'Care records', exact: true }).waitFor()
    await moreDialog.screenshot({ path: '/tmp/tele-tena-presentation-review/request-readiness/mobile-more-menu.png' })
    checkpoint = 'close mobile more menu'
    await actualPage.keyboard.press('Escape')
    await moreDialog.waitFor({ state: 'detached' })
    checkpoint = 'restore mobile menu focus'
    assert.equal(await moreButton.evaluate(element => element === document.activeElement), true)
    const screenshots = '/tmp/tele-tena-presentation-review/request-readiness'
    fs.mkdirSync(screenshots, { recursive: true })
    const translations = {
      en: ['Add a care language', 'Ask a reviewer to enable immediate requests for a service', 'Review availability'],
      am: ['የእንክብካቤ ቋንቋ ያክሉ', 'ገምጋሚውን ለአገልግሎት ፈጣን ጥያቄዎችን እንዲያነቃ ይጠይቁ', 'የሚገኙበትን ጊዜ ይመልከቱ'],
      om: ['Afaan tajaajilaa dabali', 'Gamaaggamaa tajaajilaaf gaaffii ariifataa akka banu gaafadhu', 'Yeroo argamuu ilaali'],
    }
    for (const [locale, labels] of Object.entries(translations)) {
      checkpoint = `readiness copy ${locale}`
      await actualPage.getByLabel('Language / ቋንቋ / Afaan').selectOption(locale)
      for (const label of labels) await actualPage.getByRole('link', { name: label, exact: true }).waitFor()
      for (const width of [320, 390, 768, 1440]) {
        checkpoint = `readiness layout ${locale} ${width}`
        await actualPage.setViewportSize({ width, height: 900 })
        await actualPage.screenshot({ path: path.join(screenshots, `blocked-${locale}-${width}.png`), fullPage: true })
        const overflow = await actualPage.evaluate(() => ({
          documentWidth: document.documentElement.scrollWidth,
          viewportWidth: innerWidth,
          elements: [...document.querySelectorAll('body *')].map(element => {
            const rect = element.getBoundingClientRect()
            const chain = []
            for (let current = element, n = 0; current && n < 5; current = current.parentElement, n++) {
              const box = current.getBoundingClientRect(), style = getComputedStyle(current)
              chain.push({ tag: current.tagName.toLowerCase(), className: String(current.className || '').slice(0, 55), left: Math.round(box.left), right: Math.round(box.right), width: Math.round(box.width), overflow: style.overflowX })
            }
            return { tag: element.tagName.toLowerCase(), className: String(element.className || '').slice(0, 70), right: Math.round(rect.right), width: Math.round(rect.width), chain }
          }).filter(item => item.right > innerWidth + 1 && item.width > 0).slice(0, 8),
        }))
        if (overflow.documentWidth > width + 1) console.log(`OVERFLOW_DIAGNOSTIC: ${locale} ${width} ${JSON.stringify(overflow)}`)
        assert.equal(overflow.documentWidth > width + 1, false)
      }
    }
    await actualContext.close()

    const capacityContext = await browser.newContext()
    const capacityPage = await capacityContext.newPage()
    checkpoint = 'capacity-specific readiness sign-in'
    await capacityPage.route('**/api/method/tele_tena.api.open_requests.request_presence**', route =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
        message: { ready: false, configured: false, reasons: ['no_immediate_capacity'] },
      }) }))
    await capacityPage.goto(app + '/sign-in')
    await capacityPage.getByRole('button', { name: 'Use email instead' }).click()
    await capacityPage.getByLabel('Email', { exact: true }).fill(account)
    await capacityPage.getByLabel('Password', { exact: true }).fill(credentials[account])
    await capacityPage.getByRole('button', { name: 'Sign in', exact: true }).click()
    await capacityPage.waitForURL(/\/teletena\/clinician(?:\/|$)/)
    checkpoint = 'specific no-capacity guidance'
    await capacityPage.getByText('No complete session fits the next 30 minutes', { exact: true }).waitFor()
    assert.equal(await capacityPage.getByRole('button', { name: 'Go available', exact: true }).isDisabled(), true)
    const reviewAvailability = capacityPage.getByRole('link', { name: 'Review availability', exact: true })
    await reviewAvailability.waitFor()
    await reviewAvailability.click()
    await capacityPage.waitForURL('**/teletena/clinician/availability')
    await capacityContext.close()

    const context = await browser.newContext()
    const page = await context.newPage()
    checkpoint = 'controlled failure sign-in'
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
    checkpoint = 'controlled validation response'
    const alert = page.getByRole('alert').filter({ hasText: 'Could not update request availability.' })
    await alert.waitFor()
    assert.equal(await page.getByText('Connection interrupted; request availability may expire.').count(), 0)
    assert.equal(await page.getByText('Operation unavailable').count(), 0)
    console.log('PASS: real seeded clinician sees both unmet setup requirements and cannot appear available; authenticated validation failure is not mislabeled as a connection outage')
    await context.close()
  } finally {
    await browser.close()
  }
})().catch(error => {
  console.error('FAIL: ' + checkpoint + ' (' + (error?.name || 'Error') + '); credentials and response bodies withheld')
  process.exitCode = 1
})
