// Built frontend only; no Vite server or mocked product APIs.
const { chromium } = require('playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const root = process.env.TELE_TENA_REVIEW_SITE_PATH;
assert.ok(root.endsWith('/tele-tena-pr2-test.localhost'));
const fixture = JSON.parse(fs.readFileSync(root+'/private/tele_tena_review_seed.json','utf8'));
const credentials = JSON.parse(fs.readFileSync(root+'/private/tele_tena_review_accounts.json','utf8'));
const base='http://127.0.0.1:8017';
(async()=>{
 const browser=await chromium.launch({headless:true});
 try {
  const context=await browser.newContext();const page=await context.newPage();
  const errors=[];page.on('pageerror',()=>errors.push('page error'));
  await page.goto(base+'/teletena/');
  await page.getByRole('heading',{name:'Find someone you feel comfortable talking to.'}).waitFor();
  assert.ok((await page.locator('img').first().getAttribute('src')).startsWith('/assets/tele_tena/review/'));
  await page.goto(base+'/teletena/patient/appointments');
  await page.waitForURL('**/teletena/sign-in');
  // Invited review sites now show password entry directly when neither OTP
  // delivery provider is enabled. Both account and logout checks remain real.
  if(await page.getByRole('button',{name:'Use email instead',exact:true}).count())
    await page.getByRole('button',{name:'Use email instead',exact:true}).click();
  if(await page.getByRole('button',{name:'Use password instead',exact:true}).count())
    await page.getByRole('button',{name:'Use password instead',exact:true}).click();
  await page.getByLabel('Email',{exact:true}).fill(fixture.users.patient);
  await page.getByLabel('Password',{exact:true}).fill(credentials[fixture.users.patient]);
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await page.getByRole('button',{name:'Sign out',exact:true}).waitFor();
  await page.goto(base+'/teletena/patient/consultations/'+fixture.appointment);
  await page.getByText('Synthetic shared next step',{exact:true}).waitFor();
  await page.reload();await page.getByText('Synthetic shared next step',{exact:true}).waitFor();
  assert.ok(!(await page.locator('body').innerText()).includes('PRIVATE SYNTHETIC'));
  fs.mkdirSync('/tmp/tele-tena-package-review',{recursive:true});
  for(const width of [390,768,1440]){
   await page.setViewportSize({width,height:960});await page.evaluate(()=>document.fonts.ready);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
   await page.screenshot({path:`/tmp/tele-tena-package-review/built-detail-${width}.png`,fullPage:true});
  }
  const scope=await page.evaluate(async()=>{const r=await navigator.serviceWorker.ready;return r.scope});
  assert.equal(scope,base+'/teletena/');
  const manifest=await (await context.request.get(base+'/assets/tele_tena/review/manifest.webmanifest')).json();
  assert.equal(manifest.start_url,'/teletena/');assert.equal(manifest.scope,'/teletena/');
  const cached=await page.evaluate(async()=>{const out=[];for(const key of await caches.keys()){for(const r of await (await caches.open(key)).keys())out.push(r.url)}return out});
  assert.ok(cached.every(url=>url.startsWith(base+'/assets/tele_tena/review/')));
  await page.getByRole('button',{name:'Sign out',exact:true}).click();
  await page.waitForURL('**/teletena/sign-in');
  await page.goto(base+'/teletena/patient/appointments');await page.waitForURL('**/teletena/sign-in');
  await context.setOffline(true);await page.goto(base+'/teletena/patient/appointments');
  await page.getByRole('heading',{name:'You’re offline'}).waitFor();
  assert.equal(await page.getByRole('link',{name:'Try again'}).getAttribute('href'),'/teletena/');
  assert.deepEqual(errors,[]);
  console.log('PASS: built browser guest/password session/deep-link reload/signout, rendered widths, scoped PWA and offline state; no Vite');
 } finally {await browser.close()}
})().catch(()=>{console.error('FAIL: built review browser assertion (credentials withheld)');process.exitCode=1});
