// Actual Chromium200% zoom; local private fictional accounts, no workflow mutations.
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict'),{chromium}=require('playwright');
const privateRoot='/home/frappe/frappe/frappe-bench/sites/teletena-mvp-presentation.localhost/private';
const seed=JSON.parse(fs.readFileSync(privateRoot+'/tele_tena_presentation_seed.json'));assert.equal(seed.fictional,true);
const credentials=JSON.parse(fs.readFileSync(privateRoot+'/tele_tena_presentation_accounts.json'));
const build=JSON.parse(fs.readFileSync('tele_tena/public/review/release.json')).source_commit;
const out='/tmp/tt-scope-zoom',base='http://127.0.0.1:8017/teletena';fs.mkdirSync(out,{recursive:true});
let root,context,stage='launch';
(async()=>{try{
 root=fs.mkdtempSync(path.join(os.tmpdir(),'tt-scope-zoom-'));const extension=path.join(root,'extension');fs.mkdirSync(extension);
 fs.writeFileSync(extension+'/manifest.json',JSON.stringify({manifest_version:3,name:'Local visual acceptance zoom',version:'1.0',permissions:['tabs'],background:{service_worker:'worker.js'}}));
 fs.writeFileSync(extension+'/worker.js',"chrome.tabs.onUpdated.addListener((id,change,tab)=>{if(change.status==='complete'&&/^http:\\/\\/127\\.0\\.0\\.1:(8017|8044)\\//.test(tab.url||''))chrome.tabs.setZoom(id,2)});");
 context=await chromium.launchPersistentContext(path.join(root,'profile'),{channel:'chromium',viewport:null,args:['--window-size=1440,1000','--disable-extensions-except='+extension,'--load-extension='+extension]});
 const page=await context.newPage();page.setDefaultTimeout(15000);
 for(const [role,route,id] of [['patient','/patient','C01'],['second_clinician','/clinician/vetting','B09'],['reviewer','/admin/services','I08']]) {
  stage=role+' sign-in';await page.goto(base+'/sign-in');await page.getByRole('button',{name:'Use email instead',exact:true}).click();await page.getByRole('button',{name:'Use password instead',exact:true}).click();await page.getByLabel('Email',{exact:true}).fill(seed.users[role]);await page.getByLabel('Password',{exact:true}).fill(credentials[seed.users[role]]);await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.getByRole('button',{name:'Sign out',exact:true}).waitFor();
  await page.goto(base+route);
  if(role==='patient')await page.locator('.patient-home-hero').waitFor();
  if(role==='second_clinician')await page.getByRole('heading',{name:'Choose your service scopes',exact:true}).waitFor();
  if(role==='reviewer'){const catalog=await page.request.get('http://127.0.0.1:8017/api/method/tele_tena.api.service_catalog.definitions');assert.equal(catalog.status(),200);const definition=(await catalog.json()).message.definitions.find(item=>item.vetting_required&&item.catalog_status==='Draft');assert.ok(definition);await page.goto(base+'/admin/services/'+encodeURIComponent(definition.id)+'/edit');await page.getByLabel('Patient-facing name (English)',{exact:true}).waitFor();}
  stage=role+' actual zoom';await page.waitForFunction(()=>devicePixelRatio===2&&visualViewport.scale===1);assert.deepEqual(await page.evaluate(()=>[outerWidth,innerWidth]),[1440,720]);await page.evaluate(()=>document.fonts.ready);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:out+'/'+id+'-application-200-percent.png',fullPage:true});
  const reference=await context.newPage();await reference.goto('http://127.0.0.1:8044/?embed=1#'+id.toLowerCase());await reference.waitForFunction(()=>devicePixelRatio===2&&visualViewport.scale===1);assert.deepEqual(await reference.evaluate(()=>[outerWidth,innerWidth]),[1440,720]);await reference.evaluate(()=>document.fonts.ready);await reference.screenshot({path:out+'/'+id+'-reference-200-percent.png',fullPage:true});await reference.close();
  await page.getByRole('button',{name:'Sign out',exact:true}).click();await page.getByRole('button',{name:'Sign out',exact:true}).waitFor({state:'hidden'});
 }
 assert.equal(JSON.parse(fs.readFileSync('tele_tena/public/review/release.json')).source_commit,build);fs.writeFileSync(out+'/result.json',JSON.stringify({source:build,site:'teletena-mvp-presentation.localhost',actual_browser_zoom:2,outer_width:1440,inner_width:720,real_backend:true,reference_ids:['C01','B09','I08'],no_page_overflow:true,visual_inspection_required:true},null,2));console.log('PASS: patient Home, clinician scopes and reviewer definition at actual200% zoom with paired reference captures.');
}catch(error){console.error('FAIL: '+stage+' ('+error.name+'); private details withheld');process.exitCode=1;}finally{await context?.close();if(root)fs.rmSync(root,{recursive:true,force:true});}})();
