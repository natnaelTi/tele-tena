// Explicit fictional presentation profile edit through the real owner UI.
const fs=require('node:fs'),assert=require('node:assert/strict'),{chromium}=require('playwright');
const root='/home/frappe/frappe/frappe-bench/sites/teletena-mvp-presentation.localhost/private';
const seed=JSON.parse(fs.readFileSync(root+'/tele_tena_presentation_seed.json'));
const credentials=JSON.parse(fs.readFileSync(root+'/tele_tena_presentation_accounts.json'));
const base='http://127.0.0.1:8017/teletena',output='/tmp/tt-public-introduction';
fs.mkdirSync(output,{recursive:true});
let stage='launch';
async function signIn(page,user){
  await page.goto(base+'/sign-in');
  await page.getByRole('button',{name:'Use email instead',exact:true}).click();
  await page.getByRole('button',{name:'Use password instead',exact:true}).click();
  await page.getByLabel('Email',{exact:true}).fill(user);
  await page.getByLabel('Password',{exact:true}).fill(credentials[user]);
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await page.getByRole('button',{name:'Sign out',exact:true}).waitFor();
}
async function pair(context,page,id,width){
  await page.setViewportSize({width,height:1000});
  await page.evaluate(()=>document.fonts.ready);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:`${output}/${id}-application-${width}.png`,fullPage:true});
  const reference=await context.newPage();
  await reference.setViewportSize({width,height:1000});
  await reference.goto('http://127.0.0.1:8044/?embed=1#'+id.toLowerCase());
  await reference.evaluate(()=>document.fonts.ready);
  await reference.screenshot({path:`${output}/${id}-reference-${width}.png`,fullPage:true});
  await reference.close();
}
(async()=>{
 const browser=await chromium.launch();
 try{
  const clinician=await browser.newContext({viewport:{width:1440,height:1000}}),page=await clinician.newPage();
  page.setDefaultTimeout(15000);
  stage='approved owner account'; await signIn(page,seed.users.clinician);
  const before=await page.evaluate(async()=>(await(await fetch('/api/method/tele_tena.api.journey.session')).json()).message);
  stage='account route'; await page.goto(base+'/clinician/account');
  await page.getByRole('button',{name:'Professional profile & practice',exact:true}).click();
  stage='introduction field'; const field=page.getByLabel('Introduction',{exact:true});
  const introduction=(await field.inputValue())||'I offer a supportive space for adults to talk through stress, life changes and relationship concerns. We can explore what matters to you and practical next steps together.';
  await field.fill(introduction);
  stage='owner save';
  const saved=page.waitForResponse(r=>r.url().includes('tele_tena.api.journey.save_profile'));
  await page.getByRole('button',{name:'Save profile and languages',exact:true}).click();
  assert.equal((await saved).status(),200);
  await page.reload();
  await page.getByRole('button',{name:'Professional profile & practice',exact:true}).click();
  assert.equal(await field.inputValue(),introduction);
  const after=await page.evaluate(async()=>(await(await fetch('/api/method/tele_tena.api.journey.session')).json()).message);
  assert.deepEqual(after.roles,before.roles);
  for(const key of ['history','display_name','share_name','share_history','languages','public_id']) assert.equal(after.profile[key],before.profile[key]);
  for(const width of [390,768,1440])await pair(clinician,page,'H02',width);
  const patient=await browser.newContext({viewport:{width:1440,height:1000}}),p=await patient.newPage();
  p.setDefaultTimeout(15000);
  stage='patient public profile';await signIn(p,seed.users.patient);
  await p.goto(base+'/patient/clinicians/'+after.profile.public_id);
  await p.getByRole('heading',{name:after.profile.display_name,exact:true}).first().waitFor();
  assert.equal(await p.locator('.public-profile-introduction').textContent(),introduction);
  const publicProfile=await p.evaluate(async id=>(await(await fetch('/api/method/tele_tena.api.open_requests.clinician_profile?clinician_id='+id)).json()).message,after.profile.public_id);
  for(const key of ['user','email','history','statement'])assert.ok(!(key in publicProfile));
  for(const width of [390,768,1440])await pair(patient,p,'C04',width);
  const manifest=JSON.parse(fs.readFileSync('tele_tena/public/review/release.json'));
  fs.writeFileSync(output+'/result.json',JSON.stringify({source:manifest.source_commit,site:'teletena-mvp-presentation.localhost',real_backend:true,owner_save_reload:true,public_introduction:true,private_fields_omitted:true,roles_other_profile_fields_unchanged:true,viewports:[390,768,1440],visual_acceptance:'Comparison pending; screenshot capture is not acceptance'},null,2));
  console.log('PASS: owner introduction persisted after reload, separate patient sees only explicit public content; roles/private profile unchanged. Paired H02/C04 captured.');
 }catch(error){console.error('FAIL: '+stage+' ('+error.name+'); private details withheld');process.exitCode=1}
 finally{await browser.close()}
})();
