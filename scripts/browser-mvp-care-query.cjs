// Real built-app access; synthetic care intent is never logged or persisted.
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const site=process.env.TELE_TENA_REVIEW_SITE_PATH;
assert.ok(site && /^tele-tena-[a-z0-9-]+\.localhost$/.test(path.basename(site)));
const seed=JSON.parse(fs.readFileSync(path.join(site,'private/tele_tena_review_seed.json'),'utf8'));
const passwords=JSON.parse(fs.readFileSync(path.join(site,'private/tele_tena_review_accounts.json'),'utf8'));
const origin=process.env.TELE_TENA_BROWSER_ORIGIN||'http://127.0.0.1:8017';
const app=origin+'/teletena';
let stage='launch';
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  const context=await browser.newContext({viewport:{width:390,height:844}});
  const page=await context.newPage();
  const query='Synthetic care continuity';
  const urls=[];page.on('request',req=>urls.push(req.url()));
  async function passwordLogin(){
   await page.getByRole('button',{name:'Use email instead',exact:true}).click();
   const passwordChoice=page.getByRole('button',{name:'Use password instead',exact:true});
   if(await passwordChoice.count())await passwordChoice.click();
   await page.getByLabel('Email',{exact:true}).fill(seed.users.patient);
   await page.getByLabel('Password',{exact:true}).fill(passwords[seed.users.patient]);
   await page.getByRole('button',{name:'Sign in',exact:true}).click();
  }
  stage='landing care intent';await page.goto(app+'/');
  await page.getByLabel('What would you like support with?',{exact:true}).fill(query);
  await page.locator('.patient-care-entry').getByRole('button',{name:'Find care',exact:true}).click();
  await page.waitForURL(/\/sign-in\?/);
  stage='existing patient authentication';await passwordLogin();
  await page.waitForURL(/\/patient\/discovery$/);
  await page.getByLabel('Clinician or service',{exact:true}).waitFor();
  assert.equal(await page.getByLabel('Clinician or service',{exact:true}).inputValue(),query);
  async function privateIntent(){
   assert.equal(new URL(page.url()).search,'');
   assert.ok(!urls.some(url=>url.includes(encodeURIComponent(query))||url.includes('Synthetic%20care')));
   assert.equal(await page.evaluate(text=>[JSON.stringify(history.state),JSON.stringify(localStorage),JSON.stringify(sessionStorage)].some(x=>x.includes(text)),query),false);
  }
  await privateIntent();
  stage='patient home search';await page.getByRole('link',{name:'Home',exact:true}).first().click();
  await page.getByLabel('Search available support',{exact:true}).fill(query);
  await page.locator('.care-search').getByRole('button',{name:'Find care',exact:true}).click();
  await page.waitForURL(/\/patient\/discovery$/);
  assert.equal(await page.getByLabel('Clinician or service',{exact:true}).inputValue(),query);
  await privateIntent();
  stage='clear on sign-out';await page.getByRole('button',{name:'Sign out',exact:true}).first().click();
  await page.waitForURL(/\/sign-in/);
  stage='sign back in after clearing intent';await passwordLogin();
  await page.waitForURL(/\/patient(?:\/discovery)?$/);
  if(new URL(page.url()).pathname.endsWith('/patient')) {
   await page.getByRole('link',{name:'Find care',exact:true}).first().click();
  }
  await page.waitForURL(/\/patient\/discovery$/);
  assert.equal(await page.getByLabel('Clinician or service',{exact:true}).inputValue(),'');
  await privateIntent();
  console.log('PASS: landing→password sign-in→discovery, patient home search, no query in URL/history/storage, clear on sign-out; no data/fund mutations. Onboarding/OTP continuity requires separate acceptance.');
 }catch(error){console.error('FAIL: MVP care-query browser at '+stage+'; '+error.name+'; credentials and response bodies withheld');process.exitCode=1;}
 finally{await browser.close();}
})().catch(error=>{console.error('FAIL: browser setup; '+error.name);process.exitCode=1;});
