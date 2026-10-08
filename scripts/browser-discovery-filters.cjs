// Connected browser acceptance for persisted discovery language/format/slot filters.
// Credentials come from the isolated local fixture and are never logged.
const { chromium } = require('playwright')
const fs = require('node:fs')
const path = require('node:path')
const assert = require('node:assert/strict')

const sitePath = process.env.TELE_TENA_REVIEW_SITE_PATH
assert.ok(sitePath, 'Set TELE_TENA_REVIEW_SITE_PATH to the isolated review site directory')
const seed = JSON.parse(fs.readFileSync(`${sitePath}/private/tele_tena_review_seed.json`, 'utf8'))
const accounts = JSON.parse(fs.readFileSync(`${sitePath}/private/tele_tena_review_accounts.json`, 'utf8'))
const patient = seed.users.patient
assert.ok(patient && accounts[patient], 'Synthetic patient credentials are unavailable')
const base = process.env.TELE_TENA_BROWSER_BASE || 'http://127.0.0.1:8017/teletena'
const output = path.resolve('docs/screenshots/discovery-filters')

let stage = 'launch'
let page
;(async () => {
  const browser = await chromium.launch({ headless: true })
  try {
    page = await browser.newPage({ viewport: { width: 390, height: 844 } })
    page.on('pageerror', () => { throw new Error('Browser page error') })
    stage = 'invited-review sign-in'
    await page.goto(`${base}/sign-in`)
    await page.getByRole('button', { name: 'Use email instead', exact: true }).click()
    await page.getByLabel('Email', { exact: true }).fill(patient)
    await page.getByLabel('Password', { exact: true }).fill(accounts[patient])
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    await page.waitForURL(/\/teletena\/patient(?:\/|$)/)

    stage = 'load discovery route'
    await page.goto(`${base}/patient/discovery`)
    stage = 'enter service search'
    await page.getByLabel('Clinician or service', { exact: true }).fill('Review conversation')
    stage = 'load service options'
    const serviceSelect = page.getByLabel('Service', { exact: true })
    await page.waitForFunction(() => Array.from(document.querySelectorAll('select')).some(select =>
      Array.from(select.options).some(option => option.textContent.trim() === 'Review conversation')))
    const serviceValue = await serviceSelect.locator('option').evaluateAll(options =>
      options.find(option => option.textContent.trim() === 'Review conversation')?.value)
    assert.ok(serviceValue, 'Expected synthetic service option was not present')
    stage = 'select service'
    await serviceSelect.selectOption(serviceValue)
    stage = 'select care language'
    await page.getByLabel('Care language', { exact: true }).selectOption('en')
    stage = 'select session format'
    await page.getByLabel('Session format', { exact: true }).selectOption('video')
    stage = 'wait for matching offering'
    await page.locator('.clinician-card').first().waitFor()
    const results = page.locator('.clinician-card')
    assert.ok(await results.count() > 0)
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true)

    stage = 'server-generated open-slot filter'
    await page.getByLabel('Availability', { exact: true }).selectOption('next14')
    await page.getByText('Checking open times in the next 14 days…', { exact: true }).waitFor({ state: 'detached' })
    assert.equal(await page.getByText('Available times could not be checked. Clear this filter or try again.', { exact: false }).count(), 0)
    assert.ok(await results.count() > 0)
    fs.mkdirSync(output, { recursive: true })
    for (const width of [390, 768, 1440]) {
      await page.setViewportSize({ width, height: 960 })
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true)
      await page.screenshot({ path: `${output}/filtered-${width}.png`, fullPage: true })
    }

    stage = 'open request composer'
    await page.getByRole('link', { name: 'Post a request', exact: true }).click()
    await page.waitForURL(/\/teletena\/patient\/requests(?:\?.*)?$/)
    stage = 'request composer fields'
    const narrativeField = page.locator('textarea').first()
    await narrativeField.waitFor()
    assert.ok(await page.locator('label').allTextContents().then(labels => labels.some(label => label.includes('Describe what you are looking for'))))
    stage = 'preserved request narrative'
    assert.equal(await narrativeField.inputValue(), 'Review conversation')
    stage = 'preserved request language'
    assert.equal(await page.getByLabel('Language', { exact: true }).inputValue(), 'en')
    stage = 'preserved request format'
    assert.equal(await page.getByLabel('Session format', { exact: true }).inputValue(), 'video')
    stage = 'preserved request service category'
    assert.notEqual(await page.getByLabel('Suggested service category', { exact: true }).inputValue(), '')
    console.log('PASS: real Frappe discovery filters, server-generated availability query, responsive layout and request-draft preservation; no request published')
  } catch (error) {
    console.error(`FAIL: discovery filter journey at ${stage} (${error?.name || 'Error'}); current route=${new URL(page.url()).pathname}; credentials and patient content withheld`)
    process.exitCode = 1
  } finally {
    await browser.close()
  }
})()
