// Two independent, synthetic sessions: publish an immediate request and prove
// the eligible Review Clinician sees its authorized card in the built app.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const site = process.env.TELE_TENA_REVIEW_SITE_PATH;
assert.ok(site && /^tele-tena-[a-z0-9-]+\.localhost$/.test(path.basename(site)));
const seed = JSON.parse(fs.readFileSync(path.join(site, 'private/tele_tena_review_seed.json'), 'utf8'));
const passwords = JSON.parse(fs.readFileSync(path.join(site, 'private/tele_tena_review_accounts.json'), 'utf8'));
const patientEmail = seed.users.patient;
const clinicianEmail = seed.users.clinician;
assert.ok(patientEmail && passwords[patientEmail] && clinicianEmail && passwords[clinicianEmail]);
const app = (process.env.TELE_TENA_BROWSER_ORIGIN || 'http://127.0.0.1:8017') + '/teletena';
const requestText = 'Synthetic browser check: looking for an adult conversation about stress and relationships.';
let stage = 'launch';
let requestId = null;
let patientPage;
let clinicianPage;
let originalReady = null;
let presenceChanged = false;
let requestCancelled = false;
let safeReadiness = '';

async function signIn(page, email) {
  await page.goto(app + '/sign-in');
  if (await page.getByRole('button', { name: 'Use email instead', exact: true }).count())
    await page.getByRole('button', { name: 'Use email instead', exact: true }).click();
  await page.getByLabel('Email', { exact: true }).fill(email);
  await page.getByLabel('Password', { exact: true }).fill(passwords[email]);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('button', { name: 'Sign out', exact: true }).waitFor();
  await page.getByLabel('Language / ቋንቋ / Afaan').selectOption('en');
}

async function setPresence(ready) {
  if (!clinicianPage) return;
  const region = clinicianPage.getByRole('region', { name: 'Request availability' });
  const button = region.getByRole('button', { name: ready ? 'Go available' : 'Pause', exact: true });
  if (await button.count()) await button.click();
  await region.getByText(ready ? 'Available for requests' : 'Requests paused', { exact: true }).waitFor({ timeout: 10000 });
}

async function myRequests() {
  return patientPage.evaluate(async () => {
    const response = await fetch('/api/method/tele_tena.api.open_requests.my_requests', { credentials: 'same-origin', cache: 'no-store' });
    if (!response.ok) throw new Error('Patient request query failed');
    return (await response.json()).message || [];
  });
}

async function cleanup() {
  if (requestId && !requestCancelled && patientPage) {
    const card = patientPage.locator(`.request-card[data-request-id="${requestId}"]`);
    if (await card.count()) {
      await card.getByRole('button', { name: 'Cancel request', exact: true }).click();
    } else {
      await patientPage.evaluate(async id => {
        await fetch('/api/method/tele_tena.api.open_requests.cancel_request', {
          method: 'POST', credentials: 'same-origin',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': window.frappe?.csrf_token || '' },
          body: JSON.stringify({ request_id: id }),
        });
      }, requestId);
    }
    const row = (await myRequests()).find(item => item.id === requestId);
    assert.equal(row?.state, 'Cancelled');
    requestCancelled = true;
  }
  if (presenceChanged) {
    await setPresence(Boolean(originalReady));
    presenceChanged = false;
  }
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const clinicianContext = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const patientContext = await browser.newContext({ viewport: { width: 390, height: 844 } });
  try {
    clinicianPage = await clinicianContext.newPage();
    stage = 'clinician sign-in';
    await signIn(clinicianPage, clinicianEmail);
    stage = 'load clinician request workspace';
    await clinicianPage.goto(app + '/clinician/requests');
    const readiness = clinicianPage.getByRole('region', { name: 'Request availability' });
    await readiness.waitFor();
    const readinessText = await readiness.innerText();
    safeReadiness = readinessText.replace(/[\w.+-]+@[\w.-]+/g, '[account]');
    stage = 'verify clinician request readiness';
    originalReady = readinessText.includes('Available for requests');
    if (readinessText.includes('Requests paused')) {
      const go = readiness.getByRole('button', { name: 'Go available', exact: true });
      assert.equal(await go.isDisabled(), false, `Clinician setup is not ready: ${readinessText.slice(0, 240)}`);
      await setPresence(true);
      presenceChanged = true;
    }
    assert.match(await readiness.innerText(), /Available for requests/);

    patientPage = await patientContext.newPage();
    stage = 'patient sign-in and preflight cleanup check';
    await signIn(patientPage, patientEmail);
    await patientPage.goto(app + '/patient/requests');
    const before = await myRequests();
    assert.equal(before.some(item => item.state === 'Open'), false,
      'Refusing to create a second active request for the synthetic patient');
    const previousIds = new Set(before.map(item => item.id));

    stage = 'publish immediate request through patient UI';
    await patientPage.getByLabel('Describe what you are looking for').fill(requestText);
    await patientPage.getByLabel('Suggested service category').selectOption({ label: 'Review conversation' });
    await patientPage.getByLabel('When would you like care?').selectOption('immediate');
    await patientPage.getByLabel('Language', { exact: true }).selectOption('en');
    await patientPage.getByLabel('Session format').selectOption('video');
    await patientPage.getByRole('button', { name: 'Publish request', exact: true }).click();
    await patientPage.getByText('Your request is saved.', { exact: false }).waitFor({ timeout: 10000 });
    await patientPage.waitForFunction(async ids => {
      const response = await fetch('/api/method/tele_tena.api.open_requests.my_requests', { cache: 'no-store' });
      const rows = (await response.json()).message || [];
      return rows.some(item => !ids.includes(item.id));
    }, [...previousIds], { timeout: 10000 });
    const created = (await myRequests()).find(item => !previousIds.has(item.id));
    assert.ok(created);
    requestId = created.id;
    assert.equal(created.urgency, 'immediate');
    assert.equal(created.state, 'Open');
    assert.ok(created.eligible_supply > 0, 'No clinician satisfied the published hard requirements');

    stage = 'clinician inbox fetch and visible authorized request card';
    const card = clinicianPage.locator('.clinician-request').filter({ hasText: requestText });
    await card.waitFor({ timeout: 15000 });
    assert.match(await card.innerText(), /As soon as possible/);
    assert.match(await card.innerText(), /Review conversation/);
    assert.match(await card.innerText(), /EN · video/);
    assert.equal((await card.innerText()).includes(patientEmail), false, 'Request card exposed the patient account email');
    const inboxRows = await clinicianPage.evaluate(async () => {
      const response = await fetch('/api/method/tele_tena.api.open_requests.clinician_requests', { credentials: 'same-origin', cache: 'no-store' });
      return response.ok ? (await response.json()).message || [] : [];
    });
    assert.ok(inboxRows.some(item => item.id === requestId), 'Authenticated inbox API did not return this published request');
    fs.mkdirSync('docs/screenshots/open-request-routed', { recursive: true });
    for (const width of [390, 768, 1440]) {
      await clinicianPage.setViewportSize({ width, height: 960 });
      await clinicianPage.evaluate(() => document.fonts.ready);
      assert.equal(await clinicianPage.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
      await card.screenshot({ path: `docs/screenshots/open-request-routed/review-clinician-${width}.png` });
    }

    stage = 'cancel request and pause clinician presence';
    await patientPage.reload();
    await patientPage.locator(`.request-card[data-request-id="${requestId}"]`).getByRole('button', { name: 'Cancel request', exact: true }).click();
    const cancelled = (await myRequests()).find(item => item.id === requestId);
    assert.equal(cancelled?.state, 'Cancelled');
    requestCancelled = true;
    if (presenceChanged) {
      await setPresence(Boolean(originalReady));
      presenceChanged = false;
    }
    console.log(JSON.stringify({
      patientRequestPublished: true,
      eligibleSupplyAtPublication: created.eligible_supply,
      clinicianInboxApiReturnedRequest: true,
      clinicianRenderedRequestCard: true,
      accountEmailOmitted: true,
      testRequestCancelled: requestCancelled,
      clinicianPresenceRestored: originalReady === null || !presenceChanged,
    }));
  } catch (error) {
    try { await cleanup(); } catch { /* keep the failing checkpoint visible */ }
    console.error(`FAIL: routed inbox checkpoint ${stage}; synthetic values and response bodies withheld; ${error?.name || 'Error'}${stage === 'verify clinician request readiness' ? `; readiness=${safeReadiness.slice(0, 320)}` : ''}`);
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(`FAIL: routed inbox setup; credentials and response bodies withheld; ${error?.name || 'Error'}`);
  process.exitCode = 1;
});
