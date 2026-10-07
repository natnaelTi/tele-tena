// Packaged frontend with real site capabilities; only the SMS send is mocked.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const base = process.env.TELE_TENA_BROWSER_BASE || 'http://127.0.0.1:8017';
const output = '/tmp/tele-tena-hosted-phone-review';
fs.mkdirSync(output, {recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  const context=await browser.newContext();
  const page=await context.newPage();
  const pageErrors=[];page.on('pageerror',()=>pageErrors.push('page error'));
  const policy=await (await context.request.get(base+'/api/method/tele_tena.api.contact_auth.sign_in_options')).json();
  assert.equal(policy.message.phone_otp,true);
  assert.equal(policy.message.email_otp,false);
  assert.equal(policy.message.patient_registration,true);
  assert.equal(policy.message.clinician_registration,true);
  await page.goto(base+'/teletena/sign-in');
  await page.getByLabel('Phone number',{exact:true}).waitFor();
  assert.equal(await page.locator('main input').count(),1);
  for(const width of [390,768,1440]){
   await page.setViewportSize({width,height:850});
   await page.evaluate(()=>document.fonts.ready);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
   await page.screenshot({path:`${output}/phone-entry-${width}.png`,fullPage:true});
  }
  await page.route('**/api/method/tele_tena.api.contact_auth.request_code',route=>route.fulfill({json:{message:{challenge_id:'synthetic-ui-only',delivery_state:'accepted',message:'Provider accepted; delivery unverified'}}}));
  await page.getByLabel('Phone number',{exact:true}).fill('0910000000');
  await page.getByRole('button',{name:'Continue',exact:true}).click();
  await page.getByLabel('Verification code',{exact:true}).waitFor();
  assert.equal(await page.locator('main input').count(),1);
  await page.setViewportSize({width:390,height:850});
  await page.screenshot({path:`${output}/code-entry-390.png`,fullPage:true});
  await page.getByRole('button',{name:'Change number',exact:true}).click();
  await page.getByRole('button',{name:'Use email instead',exact:true}).click();
  await page.getByLabel('Email',{exact:true}).waitFor();
  await page.getByLabel('Password',{exact:true}).waitFor();
  assert.equal(await page.getByRole('button',{name:'Use an email code instead'}).count(),0);
  await page.screenshot({path:`${output}/email-password-390.png`,fullPage:true});
  assert.deepEqual(pageErrors,[]);
  console.log('PASS: packaged phone-first entry, OTP step and SMTP-aware password alternative at 390/768/1440; SMS send mocked');
 }finally{await browser.close()}
})().catch(()=>{console.error('FAIL: hosted phone browser assertion (values withheld)');process.exitCode=1});
