// Actual built application, existing browser session, offline recovery and release update.
const fs=require('node:fs'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {chromium}=require('playwright');
const origin='http://127.0.0.1:8017',base=origin+'/teletena';
const root='/home/frappe/frappe/frappe-bench/sites/teletena-mvp-presentation.localhost/private';
let browser,stage='launch';
(async()=>{try{
 browser=await chromium.launch();const context=await browser.newContext();const page=await context.newPage();page.setDefaultTimeout(20000);
 await page.goto(base+'/');await page.evaluate(async()=>{await navigator.serviceWorker.ready});await page.reload();
 assert.ok(await page.evaluate(()=>!!navigator.serviceWorker.controller));
 const initial=(await(await page.request.get(origin+'/assets/tele_tena/review/release.json')).json()).source_commit;
 stage='offline navigation and recovery';await context.setOffline(true);await page.goto(base+'/patient/appointments');await page.getByRole('heading',{name:'You’re offline',exact:true}).waitFor();
 await context.setOffline(false);await page.getByRole('link',{name:'Try again',exact:true}).click();await page.getByRole('link',{name:'Sign in',exact:true}).first().waitFor();
 if(process.env.TELE_TENA_WAIT_FOR_BUILD==='1'){
   stage='waiting for actual new build';fs.writeFileSync('/tmp/tt-preview-browser-ready','ready');
   let changed=false;for(let i=0;i<360;i++){await new Promise(r=>setTimeout(r,1000));const sha=(await(await page.request.get(origin+'/assets/tele_tena/review/release.json')).json()).source_commit;if(sha!==initial){changed=true;break}}
   assert.ok(changed,'No new release published during the bounded update test');
   await page.evaluate(async()=>{const r=await navigator.serviceWorker.getRegistration();await r.update()});
   await page.getByRole('button',{name:'Refresh to update',exact:true}).click();await page.waitForLoadState('domcontentloaded');
 }
 stage='authenticated deep link';const seed=JSON.parse(fs.readFileSync(root+'/tele_tena_presentation_seed.json'));const file=root+'/tele_tena_presentation_accounts.json';assert.equal(fs.statSync(file).mode&0o077,0);const accounts=JSON.parse(fs.readFileSync(file));
 await page.goto(base+'/sign-in');await page.getByRole('button',{name:'Use email instead',exact:true}).click();await page.getByRole('button',{name:'Use password instead',exact:true}).click();await page.getByLabel('Email',{exact:true}).fill(seed.users.patient);await page.getByLabel('Password',{exact:true}).fill(accounts[seed.users.patient]);await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.getByRole('button',{name:'Sign out',exact:true}).waitFor();
 await page.goto(base+'/patient/appointments');await page.getByRole('heading',{name:'Your appointments',exact:true}).waitFor();await page.reload();await page.getByRole('heading',{name:'Your appointments',exact:true}).waitFor();
 assert.equal((await page.request.get(origin+'/api/method/tele_tena.api.presentation.wallet_summary')).status(),200);
 assert.equal((await page.request.get(origin+'/api/method/tele_tena.api.journey.applications')).status(),403);
 stage='asset identities and private cache exclusions';const manifest=await(await page.request.get(origin+'/assets/tele_tena/review/release.json')).json();
 for(const [name,digest] of Object.entries(manifest.files)){if(!/\.(js|css)$/.test(name))continue;const response=await page.request.get(origin+'/assets/tele_tena/review/'+name);assert.ok(response.ok());assert.equal(crypto.createHash('sha256').update(await response.body()).digest('hex'),digest)}
 const keys=await page.evaluate(async()=>{const result=[];for(const k of await caches.keys())for(const req of await(await caches.open(k)).keys())result.push(new URL(req.url).pathname);return result});assert.equal(keys.some(p=>p.startsWith('/api/')||p.startsWith('/private/')||p.includes('/sign-in')),false);
 await page.getByRole('button',{name:'Sign out',exact:true}).click();assert.equal((await page.request.get(origin+'/api/method/tele_tena.api.presentation.wallet_summary')).status(),403);
 fs.writeFileSync('/tmp/tt-preview-recovery-result.json',JSON.stringify({source:manifest.source_commit,site:'teletena-mvp-presentation.localhost',offline_fallback_recovery:true,existing_session_release_update:process.env.TELE_TENA_WAIT_FOR_BUILD==='1',authenticated_deep_link_refresh:true,guest_private_denied:true,unrelated_role_denied:true,asset_hashes_verified:true,sensitive_cache_exclusion:true},null,2));console.log('PASS: offline recovery, actual packaged hashes, persisted password session/deep-link refresh, permission denial and cache exclusion');
 }catch(e){console.error('FAIL:',stage,e.message);process.exitCode=1}finally{await browser?.close()}})();
