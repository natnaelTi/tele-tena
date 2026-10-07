// Authenticated browser journey for private applicant/reviewer scope evidence.
// It uses one synthetic fixture generated locally on an isolated review site.
const { chromium } = require('playwright')
const fs = require('node:fs')
const path = require('node:path')
const assert = require('node:assert/strict')

const sitePath = process.env.TELE_TENA_REVIEW_SITE_PATH
assert.ok(sitePath && /^tele-tena-[a-z0-9-]+\.localhost$/.test(path.basename(sitePath)))
const base = process.env.TELE_TENA_BROWSER_ORIGIN || 'http://127.0.0.1:8017'
const app = base + '/teletena'
const seed = JSON.parse(fs.readFileSync(path.join(sitePath, 'private/tele_tena_review_seed.json')))
const credentials = JSON.parse(fs.readFileSync(path.join(sitePath, 'private/tele_tena_review_accounts.json')))
const applicantFixture = JSON.parse(fs.readFileSync(path.join(sitePath, 'private/scope-evidence-browser-account.json')))
const screenshotDir = '/tmp/tele-tena-presentation-review/scope-evidence'
fs.mkdirSync(screenshotDir, { recursive: true })

async function signIn(page, email, password) {
  await page.goto(app + '/sign-in')
  await page.getByRole('button', { name: 'Use email instead' }).click()
  await page.getByLabel('Email', { exact: true }).fill(email)
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await page.waitForURL(/\/teletena\/(?:clinician|admin)(?:\/|$)/)
}

let checkpoint = 'launch'
;(async () => {
  const browser = await chromium.launch({ headless: true })
  try {
    const applicantContext = await browser.newContext({ acceptDownloads: true })
    const applicant = await applicantContext.newPage()
    checkpoint = 'synthetic applicant sign-in'
    await signIn(applicant, applicantFixture.email, applicantFixture.password)
    await applicant.goto(app + '/clinician/vetting')
    await applicant.getByLabel('Language / ቋንቋ / Afaan').selectOption('en')
    const draft = applicant.locator('.scope-application-row').filter({ hasText: 'Draft' }).first()
    if (await draft.count()) {
      await draft.getByRole('heading', { name: 'Evidence for this service', exact: true }).waitFor()
      checkpoint = 'upload first private scope evidence revision'
      const pdf = { name: 'synthetic-scope-evidence.pdf', mimeType: 'application/pdf',
        buffer: Buffer.from('%PDF-1.4\nSynthetic scope evidence for browser verification.\n%%EOF') }
      await draft.getByLabel('Upload PDF evidence', { exact: true }).setInputFiles(pdf)
      await draft.getByText('synthetic-scope-evidence.pdf · v1').waitFor()
      checkpoint = 'append replacement evidence revision'
      await draft.getByLabel('Upload PDF evidence', { exact: true }).setInputFiles({ ...pdf, name: 'synthetic-scope-evidence-revised.pdf' })
      await draft.getByText('synthetic-scope-evidence-revised.pdf · v2').waitFor()
      assert.equal(await draft.getByText('synthetic-scope-evidence.pdf · v1').count(), 1)
      await applicant.screenshot({ path: path.join(screenshotDir, 'applicant-revisions.png'), fullPage: true })
      checkpoint = 'submit synthetic service-scope application through UI'
      await applicant.getByLabel('Service scope', { exact: true }).selectOption(applicantFixture.service)
      await applicant.getByLabel('Professional category', { exact: true }).fill('Synthetic counselor')
      await applicant.getByLabel('Relevant qualification', { exact: true }).fill('Synthetic qualification')
      await applicant.getByLabel('Issuing institution', { exact: true }).fill('Synthetic institution')
      await applicant.getByLabel('My application is limited to adult care.', { exact: true }).check()
      await applicant.getByRole('button', { name: 'Submit for review', exact: true }).click()
      await applicant.getByText('Submitted', { exact: true }).waitFor()
    } else {
      // This isolated account already completed the mutation journey on a prior
      // pass; retain the record and verify its submitted evidence read state.
      const submitted = applicant.locator('.scope-application-row').filter({ hasText: 'Submitted' }).first()
      await submitted.getByText('synthetic-scope-evidence-revised.pdf · v2').waitFor()
      await applicant.screenshot({ path: path.join(screenshotDir, 'applicant-revisions.png'), fullPage: true })
    }
    await applicantContext.close()

    const reviewerContext = await browser.newContext({ acceptDownloads: true })
    const reviewer = await reviewerContext.newPage()
    checkpoint = 'authorized reviewer sign-in'
    const reviewerEmail = seed.users.reviewer
    await signIn(reviewer, reviewerEmail, credentials[reviewerEmail])
    await reviewer.goto(app + '/admin/vetting')
    await reviewer.getByLabel('Language / ቋንቋ / Afaan').selectOption('en')
    const reviewCard = reviewer.locator('.scope-review-card').filter({ hasText: 'Synthetic Evidence Applicant' }).last()
    checkpoint = 'reviewer sees submitted scope evidence'
    await reviewCard.getByText('synthetic-scope-evidence-revised.pdf · v2', { exact: false }).waitFor()
    checkpoint = 'authorized reviewer opens private evidence'
    const downloadPromise = reviewer.waitForEvent('download')
    await reviewCard.getByRole('button', { name: 'Open private evidence', exact: true }).first().click()
    const download = await downloadPromise
    assert.equal(download.suggestedFilename(), 'synthetic-scope-evidence-revised.pdf')
    await reviewer.screenshot({ path: path.join(screenshotDir, 'reviewer-evidence.png'), fullPage: true })
    console.log('PASS: authenticated applicant uploads/revises scope evidence, submits the application, and authorized reviewer downloads the private revision')
    await reviewerContext.close()
  } finally {
    await browser.close()
  }
})().catch(error => {
  console.error('FAIL: ' + checkpoint + ' (' + (error?.name || 'Error') + '); credentials and response bodies withheld')
  process.exitCode = 1
})
