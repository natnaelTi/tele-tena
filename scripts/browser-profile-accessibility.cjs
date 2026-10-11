// Read-only profile layouts, provisional-language glyphs and native browser zoom.
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict'),{chromium}=require('playwright');
const privateRoot='/home/frappe/frappe/frappe-bench/sites/teletena-mvp-presentation.localhost/private';
const seed=JSON.parse(fs.readFileSync(privateRoot+'/tele_tena_presentation_seed.json'));
const passwords=JSON.parse(fs.readFileSync(privateRoot+'/tele_tena_presentation_accounts.json'));
const base='http://127.0.0.1:8017/teletena',out='/tmp/tt-profile-accessibility';
fs.mkdirSync(out,{recursive:true});
let browser,zoomContext,zoomRoot,stage='launch';
async function signIn(p){
 p.setDefaultTimeout(15000);await p.goto(base+'/sign-in');
 await p.getByRole('button',{name:'Use email instead',exact:true}).click();
 await p.getByRole('button',{name:'Use password instead',exact:true}).click();
 await p.getByLabel('Email',{exact:true}).fill(seed.users.clinician);
 await p.getByLabel('Password',{exact:true}).fill(passwords[seed.users.clinician]);
 await p.getByRole('button',{name:'Sign in',exact:true}).click();
 await p.getByRole('button',{name:'Sign out',exact:true}).waitFor();
 await p.goto(base+'/clinician/account');
 await p.getByRole('button',{name:'Professional profile & practice',exact:true}).click();
 await p.getByLabel('Introduction',{exact:true}).waitFor();
}
async function viewportShot(ctx,p,name){
 const cdp=await ctx.newCDPSession(p);
 const shot=await cdp.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});
 const bytes=Buffer.from(shot.data,'base64');assert.equal(bytes.readUInt32BE(16),1440);
 fs.writeFileSync(out+'/'+name+'.png',bytes);await cdp.detach();
}
(async()=>{try{
 browser=await chromium.launch();const ctx=await browser.newContext({viewport:{width:1440,height:1000}}),p=await ctx.newPage();
 await signIn(p);stage='keyboard control order';
 const intro=p.getByLabel('Introduction',{exact:true});await intro.focus();await p.keyboard.press('Tab');
 assert.ok(await p.getByRole('checkbox',{name:'English',exact:true}).evaluate(el=>el===document.activeElement));
 for(const width of [320,390,768,1440]){
  await p.setViewportSize({width,height:1000});
  for(const locale of ['am','om']){
   stage='language layout '+locale+' '+width;
   await p.getByLabel('Language / ቋንቋ / Afaan',{exact:true}).selectOption(locale);
   await p.waitForFunction(value=>document.documentElement.lang===value,locale);await p.evaluate(()=>document.fonts.ready);
   assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   if(locale==='am'){assert.ok(await p.evaluate(()=>document.fonts.check('16px "Noto Sans Ethiopic"','የሙያ መለያ')));await p.getByRole('heading',{name:'ግንኙነቶች',exact:true}).waitFor();await p.getByRole('link',{name:'አገልግሎቶችና ዋጋ',exact:true}).waitFor();}
   await p.screenshot({path:`${out}/H02-application-${locale}-${width}.png`,fullPage:true});
  }
 }
 await ctx.close();
 stage='native browser zoom';zoomRoot=fs.mkdtempSync(path.join(os.tmpdir(),'tt-profile-zoom-'));const extension=path.join(zoomRoot,'extension');fs.mkdirSync(extension);
 fs.writeFileSync(extension+'/manifest.json',JSON.stringify({manifest_version:3,name:'Local profile zoom check',version:'1.0',permissions:['tabs'],background:{service_worker:'worker.js'}}));
 fs.writeFileSync(extension+'/worker.js',"chrome.tabs.onUpdated.addListener((id,change,tab)=>{if(change.status==='complete'&&/^http:\\/\\/127\\.0\\.0\\.1:(8017|8044)\\//.test(tab.url||''))chrome.tabs.setZoom(id,2)});");
 zoomContext=await chromium.launchPersistentContext(zoomRoot+'/profile',{channel:'chromium',viewport:null,args:['--window-size=1440,1000','--disable-extensions-except='+extension,'--load-extension='+extension]});
 const z=await zoomContext.newPage();await signIn(z);await z.waitForFunction(()=>devicePixelRatio===2&&visualViewport.scale===1);
 assert.deepEqual(await z.evaluate(()=>[outerWidth,innerWidth]),[1440,720]);assert.ok(await z.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await z.evaluate(()=>document.fonts.ready);await viewportShot(zoomContext,z,'H02-application-200-percent');
 const ref=await zoomContext.newPage();await ref.goto('http://127.0.0.1:8044/?embed=1#h02');await ref.waitForFunction(()=>devicePixelRatio===2&&visualViewport.scale===1);await ref.evaluate(()=>document.fonts.ready);await viewportShot(zoomContext,ref,'H02-reference-200-percent');
 await z.getByLabel('Introduction',{exact:true}).scrollIntoViewIfNeeded();await viewportShot(zoomContext,z,'H02-application-200-percent-introduction');
 await ref.locator('textarea').scrollIntoViewIfNeeded();await viewportShot(zoomContext,ref,'H02-reference-200-percent-introduction');
 fs.writeFileSync(out+'/result.json',JSON.stringify({source:JSON.parse(fs.readFileSync('tele_tena/public/review/release.json')).source_commit,site:'teletena-mvp-presentation.localhost',real_backend:true,read_only:true,keyboard_control_order:true,language_layouts:['am','om'],widths:[320,390,768,1440],actual_200_percent_zoom:true,outer_width:1440,inner_width:720,dpr:2,visual_scale:1,native_language_review:false,reference_language:'English; provisional language layouts have no same-language reference'},null,2));
 console.log('PASS: real profile keyboard order, narrow/provisional language layouts and actual200% Chromium zoom; no settings saved. Native-language/owner review pending.');
}catch(error){console.error('FAIL: '+stage+' ('+error.name+'); private details withheld');process.exitCode=1}
finally{await zoomContext?.close();await browser?.close();if(zoomRoot)fs.rmSync(zoomRoot,{recursive:true,force:true})}})();
