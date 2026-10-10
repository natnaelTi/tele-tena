// Read-only review of the owned presentation encounter. No clinical mutations.
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
const site=process.env.TELE_TENA_TEST_SITE;
assert.equal(site,'teletena-mvp-presentation.localhost');
const root=path.resolve(__dirname,'../../../sites',site,'private');
function read(file){const stat=fs.lstatSync(file);assert.ok(!stat.isSymbolicLink()&&(stat.mode&0o077)===0);return JSON.parse(fs.readFileSync(file));}
const users=read(root+'/tele_tena_presentation_seed.json').users,passwords=read(root+'/tele_tena_presentation_accounts.json');
const appointment=read(process.env.TELE_TENA_CONSULTATION_FIXTURE).appointment;
const base='http://127.0.0.1:8017/teletena/',output=process.env.TELE_TENA_EVIDENCE_DIR||'/tmp/tt-call-final-review';fs.mkdirSync(output,{recursive:true});
const scratch=fs.mkdtempSync(path.join(os.tmpdir(),'tt-call-zoom-'));let browser,zoom;
(async()=>{try{
 browser=await chromium.launch({args:['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream']});
 async function login(role,context){const page=await context.newPage();await page.goto(base+'sign-in');await page.getByRole('button',{name:'Use email instead',exact:true}).click();await page.getByRole('button',{name:'Use password instead',exact:true}).click();await page.getByLabel('Email',{exact:true}).fill(users[role]);await page.getByLabel('Password',{exact:true}).fill(passwords[users[role]]);await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.getByRole('button',{name:'Sign out',exact:true}).waitFor();return page;}
 async function command(page,method,args){return page.evaluate(async({method,args})=>{const csrf=(await(await fetch('/api/method/tele_tena.api.journey.session')).json()).message.csrf_token;const r=await fetch('/api/method/'+method,{method:'POST',headers:{'Content-Type':'application/json','X-Frappe-CSRF-Token':csrf},body:JSON.stringify(args)});const body=await r.json();return {status:r.status,category:body.tele_tena_error};},{method,args});}
 const guest=await browser.newContext();const denied=await guest.request.get('http://127.0.0.1:8017/api/method/tele_tena.api.consultations.consultation',{params:{appointment}});assert.equal(denied.status(),403);await guest.close();
 for(const role of ['patient','clinician','reviewer']){
  const context=await browser.newContext({viewport:{width:1440,height:1000},permissions:['camera','microphone']}),page=await login(role,context);
  for(const table of ['tt_consultation_note','tt_note_revision'])assert.notEqual((await page.request.get('http://127.0.0.1:8017/api/resource/'+table)).status(),200);
  if(role==='reviewer'){
   for(const method of ['tele_tena.api.consultations.consultation','tele_tena.api.presentation.appointment_detail'])assert.equal((await page.request.get('http://127.0.0.1:8017/api/method/'+method,{params:{appointment}})).status(),403);
   assert.equal((await command(page,'tele_tena.api.consultations.join',{appointment})).status,403);
  }else{
   await page.goto(base+role+'/consultations/'+appointment);await page.getByRole('heading',{name:'Consultation record',exact:true}).waitFor();
   for(const width of [320,390,768,1440]){await page.setViewportSize({width,height:1000});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:`${output}/E13-${role}-application-${width}.png`,fullPage:true});}
   const events=await page.locator('.consultation-timeline strong').allTextContents();assert.equal(events.filter(value=>value==='Consultation completed').length,1);assert.equal(events.filter(value=>value==='Documentation published').length,1);
   const inactive=await command(page,'tele_tena.api.consultations.join',{appointment});assert.equal(inactive.category,'appointment_inactive');
   const appointments=(await(await page.request.get('http://127.0.0.1:8017/api/method/tele_tena.api.journey.appointments')).json()).message;
   const future=appointments.find(item=>item.state==='Booked'&&Date.parse(item.start)>Date.now()+60*60*1000);
   assert.ok(future,'Existing future presentation encounter required');
   const outside=await command(page,'tele_tena.api.consultations.join',{appointment:future.id});assert.equal(outside.category,'outside_join_window');
   await page.goto(base+'consultation/'+future.id+'/room');await page.getByRole('button',{name:'Join consultation',exact:true}).waitFor();assert.equal(await page.getByRole('button',{name:'Join consultation',exact:true}).isDisabled(),true);
   await page.evaluate(()=>{window.__previewTracks=[];const original=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);navigator.mediaDevices.getUserMedia=async options=>{const stream=await original(options);window.__previewTracks.push(...stream.getTracks());return stream;};});
   await page.getByRole('button',{name:'Check microphone and camera',exact:true}).click();await page.getByRole('status').filter({hasText:'Devices checked'}).waitFor();assert.equal(await page.getByRole('button',{name:'Join consultation',exact:true}).isDisabled(),true);
   await page.waitForFunction(()=>document.querySelector('.device-check-preview video')?.srcObject);
   if(role==='patient')for(const width of [320,390,768,1440]){await page.setViewportSize({width,height:1000});await page.screenshot({path:`${output}/E05-application-${width}.png`,fullPage:true});const ref=await context.newPage();await ref.setViewportSize({width,height:1000});await ref.goto('http://127.0.0.1:8044/?embed=1#e05');await ref.screenshot({path:`${output}/E05-reference-${width}.png`,fullPage:true});await ref.close();}
   await page.getByRole('checkbox',{name:/Audio only/}).check();assert.equal(await page.evaluate(()=>window.__previewTracks.every(track=>track.readyState==='ended')),true);
   await page.getByRole('link',{name:'Back to consultation details',exact:true}).click();assert.equal(await page.evaluate(()=>window.__previewTracks.every(track=>track.readyState==='ended')),true);

  }
  await context.close();
 }
 const extension=path.join(scratch,'extension');fs.mkdirSync(extension);fs.writeFileSync(extension+'/manifest.json',JSON.stringify({manifest_version:3,name:'Local consultation zoom check',version:'1.0',permissions:['tabs'],background:{service_worker:'zoom.js'}}));fs.writeFileSync(extension+'/zoom.js',"chrome.tabs.onUpdated.addListener((id,change,tab)=>{if(change.status==='complete'&&/^http:\\/\\/127\\.0\\.0\\.1:(8017|8044)\\//.test(tab.url||''))chrome.tabs.setZoom(id,2)});");
 zoom=await chromium.launchPersistentContext(path.join(scratch,'profile'),{channel:'chromium',viewport:null,args:['--window-size=1440,1000','--disable-extensions-except='+extension,'--load-extension='+extension]});const page=await login('patient',zoom);await page.goto(base+'patient/consultations/'+appointment);await page.waitForFunction(()=>devicePixelRatio===2&&visualViewport.scale===1);assert.deepEqual(await page.evaluate(()=>[outerWidth,innerWidth]),[1440,720]);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:output+'/E13-patient-application-200-percent.png',fullPage:true});const reference=await zoom.newPage();await reference.goto('http://127.0.0.1:8044/?embed=1#e13');await reference.waitForFunction(()=>devicePixelRatio===2&&visualViewport.scale===1);await reference.screenshot({path:output+'/E13-reference-200-percent.png',fullPage:true});
 console.log('PASS: guest/reviewer/generic denial, completed Join denial, real future-window denial, terminal timeline, 320/390/768/1440 and actual Chrome 200% zoom. No records mutated.');
}catch(error){console.error('FAIL: read-only consultation review ('+error.name+'); credentials and private details withheld');process.exitCode=1;}finally{if(zoom)await zoom.close();if(browser)await browser.close();fs.rmSync(scratch,{recursive:true,force:true});}})();
