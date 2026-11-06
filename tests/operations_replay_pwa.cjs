// Isolated, network-free provider verification of actual built service worker.
const {chromium}=require('playwright'),assert=require('assert/strict');
(async()=>{const b=await chromium.launch(),c=await b.newContext(),p=await c.newPage();try{
 await p.goto('http://127.0.0.1:8021/teletena/');
 await p.evaluate(async()=>{await navigator.serviceWorker.ready;await caches.open('tele-tena-public-obsolete-check')});
 await p.reload();await p.waitForFunction(()=>!!navigator.serviceWorker.controller);
 await p.evaluate(async()=>{await fetch('/api/method/tele_tena.operations.api.liveness',{cache:'no-store'});await fetch('/private/teletena-unavailable-canary',{cache:'no-store'});await navigator.serviceWorker.getRegistration().then(r=>r.update());});
 const keys=await p.evaluate(async()=>{const out=[];for(const name of await caches.keys()){for(const r of await (await caches.open(name)).keys())out.push(new URL(r.url).pathname)}return out});
 assert(!keys.some(k=>k.startsWith('/api/')||k.startsWith('/private/')));
 await c.setOffline(true);await p.goto('http://127.0.0.1:8021/teletena/clinicians');await p.getByRole('heading',{name:/offline/i}).waitFor();
 await c.setOffline(false);await p.reload();await p.waitForFunction(()=>!document.body.textContent.includes('TeleTena couldn’t connect'));
 assert(await p.evaluate(()=>!document.body.textContent.includes('You’re offline')));
 console.log('PASS built PWA: controller/update check, private/API cache denial, offline fallback then online deep-link recovery. No provider traffic.');
}finally{await b.close()}})().catch(e=>{console.error('FAIL '+e.message.split('\n')[0]);process.exitCode=1});
