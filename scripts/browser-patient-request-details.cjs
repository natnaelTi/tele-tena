const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

const base = (process.env.TELE_TENA_REVIEW_URL || 'http://127.0.0.1:8017/teletena').replace(/\/$/, '');
const accountFile = process.env.TELE_TENA_REVIEW_ACCOUNTS_FILE;
if (!accountFile) throw new Error('Set TELE_TENA_REVIEW_ACCOUNTS_FILE to the private local review-account file.');
const accounts = JSON.parse(fs.readFileSync(path.resolve(accountFile), 'utf8'));
const entry = Object.entries(accounts).find(([email]) => /patient/i.test(email));
if (!entry || typeof entry[1] !== 'string') throw new Error('Patient review account is missing.');
const [email, password] = entry;
let checkpoint = 'launch';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  page.setDefaultTimeout(12000);
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  try {
    checkpoint = 'patient sign-in';
    await page.goto(base + '/sign-in');
    const emailChoice = page.getByRole('button', { name: 'Use email instead' });
    if (await emailChoice.count()) await emailChoice.click();
    const passwordChoice = page.getByRole('button', { name: 'Use password instead' });
    if (await passwordChoice.count()) await passwordChoice.click();
    await page.getByLabel('Email', { exact: true }).fill(email);
    await page.getByLabel('Password', { exact: true }).fill(password);
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await page.waitForURL('**/teletena/patient');

    checkpoint = 'load owner requests';
    const requests = await page.evaluate(async () => {
      const response = await fetch('/api/method/tele_tena.api.open_requests.my_requests', { credentials: 'same-origin' });
      const result = await response.json();
      if (!response.ok || result.exc) throw new Error('Could not load the signed-in patient request list.');
      return result.message;
    });
    if (!Array.isArray(requests) || requests.length === 0) throw new Error('The synthetic patient has no persisted request for this journey.');
    const request = requests.find(item => item.state === 'Matched' || item.offers?.length) || requests[0];
    if (!request.request_text || !request.id) throw new Error('The selected persisted request is incomplete.');

    checkpoint = 'open direct request route';
    const detailUrl = base + '/patient/requests/' + encodeURIComponent(request.id);
    await page.goto(detailUrl);
    await page.getByRole('heading', { name: 'Request details', exact: true }).waitFor();
    await page.getByText(request.request_text, { exact: true }).waitFor();
    await page.reload();
    await page.getByText(request.request_text, { exact: true }).waitFor();
    const screenshotDir = path.resolve('docs/screenshots/request-details');
    fs.mkdirSync(screenshotDir, { recursive: true });
    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({ width, height: 920 });
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
      if (overflow) throw new Error('Request details overflow at ' + width + ' CSS px.');
      if (width === 390 || width === 1440) {
        await page.screenshot({ path: path.join(screenshotDir, 'patient-detail-' + width + '.png'), fullPage: true });
      }
    }
    const language = page.getByLabel('Language / ቋንቋ / Afaan');
    for (const [locale, heading] of [['am', 'የጥያቄ ዝርዝሮች'], ['om', "Bal'ina gaaffii"]]) {
      await language.selectOption(locale);
      await page.getByRole('heading', { name: heading, exact: true }).waitFor();
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
      if (overflow) throw new Error('Localized request details overflow in ' + locale + '.');
    }
    await language.selectOption('en');
    checkpoint = 'return to request list';
    await page.getByRole('link', { name: /Back to requests/ }).click();
    await page.getByRole('heading', { name: 'Your requests', exact: true }).waitFor();
    checkpoint = 'open request from persisted list';
    const listCard = page.locator('.request-card').filter({ hasText: request.request_text }).first();
    if (!(await listCard.isVisible())) {
      const history = page.locator('details.request-history');
      if (await history.count()) await history.locator('summary').click();
    }
    if (await listCard.count() === 0) throw new Error('The request is not present on the patient list page.');
    if (await listCard.getByRole('link', { name: 'Open request details', exact: true }).count() === 0) {
      throw new Error('The matched request card has no details link.');
    }
    await listCard.getByRole('link', { name: 'Open request details', exact: true }).click();
    await page.waitForURL('**/teletena/patient/requests/' + encodeURIComponent(request.id));
    await page.getByRole('heading', { name: 'Request details', exact: true }).waitFor();

    if (Array.isArray(request.offers) && request.offers.length) {
      checkpoint = 'open owner-scoped offer details';
      const offer = request.offers[0];
      await page.goto(base + '/patient/requests/' + encodeURIComponent(request.id) + '/offers/' + encodeURIComponent(offer.id));
      await page.getByRole('heading', { name: 'Review offer details', exact: true }).waitFor();
      await page.getByText(offer.clinician_name, { exact: true }).waitFor();
      await page.getByText(offer.specialty, { exact: true }).waitFor();
      for (const value of Object.values(request.disclosure_snapshot || {})) {
        await page.getByText(value, { exact: true }).waitFor();
      }
      await page.reload();
      await page.getByRole('heading', { name: 'Review offer details', exact: true }).waitFor();
      for (const width of [320, 390, 768, 1440]) {
        await page.setViewportSize({ width, height: 920 });
        const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
        if (overflow) throw new Error('Offer details overflow at ' + width + ' CSS px.');
        if (width === 390 || width === 1440) {
          await page.screenshot({ path: path.join(screenshotDir, 'offer-detail-' + width + '.png'), fullPage: true });
        }
      }
      await page.getByRole('link', { name: /Back to request/ }).click();
      await page.getByRole('heading', { name: 'Request details', exact: true }).waitFor();
    }

    checkpoint = 'verify unknown request isolation';
    const privateText = request.request_text;
    await page.goto(base + '/patient/requests/00000000-0000-0000-0000-000000000000');
    await page.getByText('Request unavailable.', { exact: true }).waitFor();
    if ((await page.locator('body').innerText()).includes(privateText)) throw new Error('An unavailable request leaked the prior request narrative.');
    if (pageErrors.length) throw new Error('The request detail journey raised a browser exception.');
    console.log('PASS: synthetic patient opens an owner-scoped persisted request detail by opaque ID, reloads it, returns to the list, and receives a generic unavailable state for an unknown ID. Responsive checks passed at 320/390/768/1440 CSS px; Amharic and Afaan Oromo headings render. Screenshots captured; account data and request content are withheld.');
  } finally {
    await context.close();
    await browser.close();
  }
})().catch(error => {
  console.error('Request detail browser check failed at ' + checkpoint + ': ' + String(error.message).split('\n')[0]);
  process.exitCode = 1;
});
