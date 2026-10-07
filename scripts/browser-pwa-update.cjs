// Exercise the built app's user-initiated update prompt with a controlled waiting worker.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const base=process.env.TELE_TENA_BROWSER_BASE||'http://127.0.0.1:8024/teletena';
let checkpoint='launch';
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844}});
  await page.addInitScript(()=>{
   const serviceWorker=new EventTarget();
   serviceWorker.controller={state:'activated'};
   const waiting=new EventTarget();
   waiting.state='installed';
   waiting.postMessage=(message)=>{
    sessionStorage.setItem('teletena-test-update-message',String(message));
    registration.waiting=null;
    setTimeout(()=>serviceWorker.dispatchEvent(new Event('controllerchange')),0);
   };
   const registration=new EventTarget();
   registration.waiting=waiting;
   registration.installing=null;
   registration.update=()=>Promise.resolve();
   serviceWorker.register=async()=>registration;
   Object.defineProperty(navigator,'serviceWorker',{configurable:true,value:serviceWorker});
   const loads=Number(sessionStorage.getItem('teletena-test-load-count')||'0')+1;
   sessionStorage.setItem('teletena-test-load-count',String(loads));
  });
  checkpoint='homepage load';
  await page.goto(base+'/',{waitUntil:'domcontentloaded'});
  const notice=page.getByRole('status').filter({hasText:'A TeleTena update is ready'});
  checkpoint='update notice';
  await notice.waitFor();
  checkpoint='user initiated update';
  await page.getByRole('button',{name:'Refresh to update'}).click();
  checkpoint='controlled reload';
  await page.waitForFunction(()=>sessionStorage.getItem('teletena-test-load-count')==='2');
  checkpoint='activation message';
  assert.equal(await page.evaluate(()=>sessionStorage.getItem('teletena-test-update-message')),'SKIP_WAITING');
  checkpoint='post update home';
  assert.equal(await page.getByRole('heading',{name:'Find support. Make time for care.'}).count(),1);
  console.log('PASS: built app detects a waiting worker, waits for explicit refresh, and reloads after activation');
 }finally{await browser.close()}
})().catch(error=>{console.error('FAIL: PWA update interaction at '+checkpoint+' ('+(error?.name||'Error')+'); details withheld');process.exitCode=1});
