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
;(async () => {
  const browser = await chromium.launch({ headless: true })
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } })
    page.on('pageerror', () => { throw new Error('Browser page error') })
    stage = 'invited-review sign-in'
    await page.goto(`${base}/sign-in`)
    await page.getByRole('button', { name: 'Use email instead', exact: true }).click()
    await page.getByLabel('Email', { exact: true }).fill(patient)
    await page.getByLabel('Password', { exact: true }).fill(accounts[patient])
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    await page.waitForURL(/\/teletena\/patient(?:\/|$)/)

    stage = 'real discovery results and language/format filtering'
    await page.goto(`${base}/patient/discovery`)
    await page.getByLabel('Clinician or service', { exact: true }).fill('Review conversation')
    await page.getByLabel('Service', { exact: true }).selectOption({ label: 'Review conversation' })
    await page.getByLabel('Care language', { exact: true }).selectOption('en')
    await page.getByLabel('Session format', { exact: true }).selectOption('video')
    await page.locator('.clinician-card').first().waitFor()
    const results = page.locator('.clinician-card')
    assert.ok(await results.count() > 0)
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true)
    fs.mkdirSync(output, { recursive: true })
    for (const width of [390, 768, 1440]) {
      await page.setViewportSize({ width, height: 960 })
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true)
      await page.screenshot({ path: `${output}/filtered-${width}.png`, fullPage: true })
    }

    stage = 'server-generated open-slot filter'
    await page.getByLabel('Availability', { exact: true }).selectOption('next14')
    await page.getByText('Checking open times in the next 14 days…', { exact: true }).waitFor({ state: 'detached' })
    assert.equal(await page.getByText('Available times could not be checked. Clear this filter or try again.', { exact: false }).count(), 0)

    stage = 'preserve search and selected filters in request composer'
    await page.getByRole('link', { name: 'Post a request', exact: true }).click()
    await page.getByLabel('Describe what you are looking for', { exact: true }).waitFor()
    assert.equal(await page.getByLabel('Describe what you are looking for', { exact: true }).inputValue(), 'Review conversation')
    assert.equal(await page.getByLabel('Language', { exact: true }).inputValue(), 'en')
    assert.equal(await page.getByLabel('Session format', { exact: true }).inputValue(), 'video')
    assert.notEqual(await page.getByLabel('Suggested service category', { exact: true }).inputValue(), '')
    console.log('PASS: real Frappe discovery filters, server-generated availability query, responsive layout and request-draft preservation; no request published')
  } catch (error) {
    console.error(`FAIL: discovery filter journey at ${stage} (${error?.name || 'Error'}); credentials and patient content withheld`)
    process.exitCode = 1
  } finally {
    await browser.close()
  }
})()
