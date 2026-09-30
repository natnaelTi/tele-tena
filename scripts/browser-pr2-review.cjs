// Isolated synthetic fixtures provided by check_review_browser.py; no retained demo edits.
const { chromium } = require('playwright')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const fixtures = JSON.parse(fs.readFileSync(process.env.TELE_TENA_BROWSER_FIXTURES, 'utf8'))
let checkpoint = 'launch'
async function main() {
  const browser = await chromium.launch()
  const context = await browser.newContext({ timezoneId: 'UTC' })
  const page = await context.newPage()
  async function settled() { await page.getByRole('status').filter({ hasText: 'Saved successfully' }).waitFor() }
  async function login(kind) {
    checkpoint = 'login ' + kind
    await page.getByLabel('Email', { exact: true }).fill(fixtures.users[kind])
    await page.getByLabel('Password', { exact: true }).fill(fixtures.password)
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    await settled()
  }
  async function logout() {
    await page.getByRole('button', { name: 'Sign out', exact: true }).click()
    await page.getByRole('heading', { name: 'Sign in', exact: true }).waitFor()
  }
  const profile = () => page.locator('section').filter({ has: page.getByRole('heading', { name: 'Your profile · Patient', exact: true }) })
  const discovery = () => page.locator('section').filter({ has: page.getByRole('heading', { name: 'Find an approved clinician', exact: true }) })
  const booking = () => page.locator('section').filter({ has: page.getByRole('heading', { name: 'Availability (shown in your timezone)', exact: true }) })
  try {
    await page.goto('http://127.0.0.1:5173')
    await login('admin')
    checkpoint = 'native scope controls'
    await page.getByLabel('Service scope to review', { exact: true }).selectOption(fixtures.service)
    const application = page.locator('article').filter({ has: page.getByRole('heading', { name: fixtures.users.c1, exact: true }) })
    await application.getByRole('button', { name: 'Revoke service scope', exact: true }).click(); await settled()
    await logout()
    await login('p1')
    await discovery().getByLabel('Service', { exact: true }).selectOption(fixtures.service); await settled()
    // c1 is generally approved, but only c2 should appear while c1's scope is revoked.
    assert.equal(await discovery().getByRole('button', { name: 'Choose', exact: true }).count(), 1)
    await logout()
    await login('admin')
    await page.getByLabel('Service scope to review', { exact: true }).selectOption(fixtures.service)
    await application.getByRole('button', { name: 'Approve service scope', exact: true }).click(); await settled()
    await logout()
    await login('p1')
    checkpoint = 'global defaults and request override'
    await profile().getByLabel('Share my display name', { exact: true }).uncheck()
    await profile().getByLabel('Share my synthetic history', { exact: true }).uncheck()
    await profile().getByRole('button', { name: 'Save profile', exact: true }).click(); await settled()
    await page.getByRole('button', { name: 'Add simulated ETB 100', exact: true }).click(); await settled()
    await discovery().getByLabel('Service', { exact: true }).selectOption(fixtures.service); await settled()
    assert.equal(await discovery().getByRole('button', { name: 'Choose', exact: true }).count(), 2)
    await discovery().getByRole('button', { name: 'Choose', exact: true }).first().click(); await settled()
    await booking().getByLabel('Start (your local timezone)', { exact: true }).fill(fixtures.start)
    await booking().getByLabel('Synthetic consultation request', { exact: true }).fill('Synthetic PR2 browser request')
    await booking().getByLabel('Share my display name', { exact: true }).check()
    await booking().getByLabel('Share my synthetic history', { exact: true }).check()
    assert.equal(await profile().getByLabel('Share my display name', { exact: true }).isChecked(), false)
    assert.equal(await profile().getByLabel('Share my synthetic history', { exact: true }).isChecked(), false)
    // Save an unrelated profile edit while a request override is selected.
    await profile().getByLabel('Display name', { exact: true }).fill('Synthetic PR2 Edited')
    await profile().getByRole('button', { name: 'Save profile', exact: true }).click(); await settled()
    assert.equal(await booking().getByLabel('Share my display name', { exact: true }).isChecked(), true)
    assert.equal(await booking().getByLabel('Share my synthetic history', { exact: true }).isChecked(), true)
    await booking().getByRole('button', { name: 'Preview exact disclosure' }).click(); await settled()
    assert.equal(await booking().locator('dd').count(), 3)
    checkpoint = 'outside-window error regression'
    await booking().getByLabel('Start (your local timezone)', { exact: true }).fill(fixtures.start.slice(0, 10) + 'T23:00')
    await booking().getByRole('button', { name: 'Preview exact disclosure' }).click(); await settled()
    await booking().getByRole('button', { name: 'Confirm appointment and reserve simulated funds' }).click()
    await page.getByRole('status').filter({ hasText: 'This session does not fit within the clinician’s availability.' }).waitFor()
    await page.getByText('Available: ETB 100.00 · Reserved: ETB 0.00', { exact: true }).waitFor()
    await booking().getByLabel('Start (your local timezone)', { exact: true }).fill(fixtures.start)
    await booking().getByRole('button', { name: 'Preview exact disclosure' }).click(); await settled()
    checkpoint = 'booking reservation and persisted defaults'
    await booking().getByRole('button', { name: 'Confirm appointment and reserve simulated funds' }).click(); await settled()
    await page.getByText('Available: ETB 94.00 · Reserved: ETB 6.00', { exact: true }).waitFor()
    const defaults = await page.evaluate(async () => (await (await fetch('/api/method/tele_tena.api.journey.session', { cache: 'no-store' })).json()).message.profile)
    assert.equal(defaults.share_name, 0); assert.equal(defaults.share_history, 0)
    await discovery().getByRole('button', { name: 'Choose', exact: true }).first().click(); await settled()
    assert.equal(await booking().getByLabel('Share my display name', { exact: true }).isChecked(), false)
    assert.equal(await booking().getByLabel('Share my synthetic history', { exact: true }).isChecked(), false)
    await page.reload()
    await page.getByText('Available: ETB 94.00 · Reserved: ETB 6.00', { exact: true }).waitFor()
    assert.equal(await profile().getByLabel('Share my display name', { exact: true }).isChecked(), false)
    await logout()
    await login('c1')
    const appointments = page.locator('section').filter({ has: page.getByRole('heading', { name: 'Your appointments', exact: true }) })
    assert.equal(await appointments.locator('dd').count(), 3)
    await page.getByLabel('Language', { exact: true }).selectOption('am')
    await page.getByRole('heading', { name: 'ቴሌ-ጤና · ሰው ሠራሽ ማሳያ', exact: true }).waitFor()
    await page.locator('header select').selectOption('om')
    await page.getByRole('heading', { name: 'Tele-tena · agarsiisa namtolchee', exact: true }).waitFor()
    await page.locator('header select').selectOption('en')
    await logout()
    console.log('PASS: Chromium native scope revoke/approve, filtered discovery, independent privacy defaults/overrides, unrelated profile save, preview, booking, persisted reservation and clinician disclosure, outside-window error, locale switching')
  } catch (error) { console.error('Browser review failed at ' + checkpoint + ' (' + error.name + ')'); throw error }
  finally { await context.close(); await browser.close() }
}
main().catch(() => { process.exit(1) })
