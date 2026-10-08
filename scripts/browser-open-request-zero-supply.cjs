// Real Frappe browser journey for an immediate request with no eligible supply.
// Uses only the explicitly seeded synthetic calendar patient and cancels the
// request through the product UI after checking the recovery path.
const { chromium } = require('playwright')
const fs = require('node:fs')
const assert = require('node:assert/strict')

const sitePath = process.env.TELE_TENA_REVIEW_SITE_PATH
assert.ok(sitePath, 'Set TELE_TENA_REVIEW_SITE_PATH to the isolated review site directory')
const base = process.env.TELE_TENA_BROWSER_BASE || 'http://127.0.0.1:8017/teletena'
const seed = JSON.parse(fs.readFileSync(`${sitePath}/private/tele_tena_review_seed.json`, 'utf8'))
const accounts = JSON.parse(fs.readFileSync(`${sitePath}/private/tele_tena_review_accounts.json`, 'utf8'))
const patient = seed.users.calendarpatient
assert.ok(patient && accounts[patient], 'Synthetic calendar patient credentials are unavailable')

let stage = 'launch'
let createdId = null
let cancelled = false
let page

async function requests() {
  return page.evaluate(async () => {
    const response = await fetch('/api/method/tele_tena.api.open_requests.my_requests', { credentials: 'same-origin' })
    if (!response.ok) throw new Error('request query failed')
    return (await response.json()).message || []
  })
}

async function cancelCreatedRequest() {
  if (!createdId || cancelled || !page) return
  const card = page.locator(`.request-card[data-request-id="${createdId}"]`)
  if (await card.count()) {
    await card.getByRole('button', { name: 'Cancel request', exact: true }).click()
  } else {
    await page.evaluate(async id => {
      const csrf = window.frappe?.csrf_token || ''
      await fetch('/api/method/tele_tena.api.open_requests.cancel_request', {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
        body: JSON.stringify({ request_id: id }),
      })
    }, createdId)
  }
  const current = (await requests()).find(item => item.id === createdId)
  assert.equal(current?.state, 'Cancelled')
  cancelled = true
}

;(async () => {
  const browser = await chromium.launch({ headless: true })
  try {
    page = await browser.newPage({ viewport: { width: 390, height: 844 } })
    stage = 'sign in'
    await page.goto(`${base}/sign-in`)
    await page.getByRole('button', { name: 'Use email instead' }).click()
    await page.getByLabel('Email', { exact: true }).fill(patient)
    await page.getByLabel('Password', { exact: true }).fill(accounts[patient])
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    await page.waitForURL(/\/teletena\/patient(?:\/|$)/)

    stage = 'check isolated patient has no active request'
    await page.goto(`${base}/patient/requests`)
    const before = await requests()
    assert.equal(before.some(item => item.state === 'Open'), false,
      'Refusing to publish while the synthetic patient has another open request')

    stage = 'publish a synthetic immediate request'
    await page.getByLabel('Describe what you are looking for').fill(
      'Synthetic browser check: no immediate clinician meets these request constraints.')
    await page.getByLabel('Suggested service category').selectOption({ label: 'Review conversation' })
    await page.getByLabel('Session format').selectOption('audio')
    await page.getByRole('button', { name: 'Publish request' }).click()

    stage = 'confirm persisted request and supply result'
    await page.waitForFunction(async () => {
      const response = await fetch('/api/method/tele_tena.api.open_requests.my_requests')
      const list = (await response.json()).message || []
      return list.some(item => item.state === 'Open')
    })
    const current = await requests()
    const created = current.find(item => item.state === 'Open')
    assert.ok(created)
    createdId = created.id
    assert.equal(created.urgency, 'immediate')
    assert.equal(created.consultation_format, 'audio')

    let noSupplyGuidance = false
    if (created.eligible_supply === 0) {
      stage = 'verify no-supply explanation and alternatives'
      await page.getByText('No clinician met every requirement when you posted.',
        { exact: false }).waitFor()
      await page.getByRole('button', { name: 'Schedule for later', exact: true }).waitFor()
      await page.getByRole('link', { name: 'Browse clinicians', exact: true }).waitFor()
      fs.mkdirSync('docs/screenshots/open-request', { recursive: true })
      await page.locator(`.request-card[data-request-id="${createdId}"]`)
        .screenshot({ path: 'docs/screenshots/open-request/zero-supply-390.png' })
      await page.getByRole('button', { name: 'Schedule for later', exact: true }).click()
      assert.equal(await page.getByLabel('Describe what you are looking for').inputValue(),
        'Synthetic browser check: no immediate clinician meets these request constraints.')
      assert.equal(await page.getByLabel('When would you like care?').inputValue(), 'scheduled')
      assert.equal(await page.getByLabel('Suggested service category').inputValue(), created.service)
      noSupplyGuidance = true
    }

    stage = 'cancel synthetic request and verify persistence'
    await cancelCreatedRequest()
    console.log(JSON.stringify({
      persistedRequest: true,
      eligibleSupply: created.eligible_supply,
      noSupplyGuidance,
      scheduleLaterPreservedInputs: noSupplyGuidance,
      cancellationPersisted: cancelled,
    }))
  } catch (error) {
    try { await cancelCreatedRequest() } catch { /* preserve the original failure stage */ }
    console.error(`FAIL: ${stage} (${error?.name || 'Error'}); request text and credentials withheld`)
    process.exitCode = 1
  } finally {
    await browser.close()
  }
})()
