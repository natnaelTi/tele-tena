import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import vm from "node:vm";

const source=await readFile(new URL("../frontend/public/sw.js",import.meta.url),"utf8");
const handlers={};const cached=[];let cacheHit=null;
const caches={
  open:async()=>({addAll:async()=>{},put:async(request)=>cached.push(new URL(request.url).pathname)}),
  keys:async()=>["tele-tena-public-v1"],delete:async()=>true,
  match:async(value)=>typeof value==="string"&&value==="/offline.html"?{offline:true}:cacheHit,
};
const self={location:{origin:"https://tele-tena.test"},addEventListener:(name,callback)=>handlers[name]=callback,clients:{claim:async()=>{}},skipWaiting:async()=>{}};
vm.runInNewContext(source,{self,caches,URL,Promise,fetch:async request=>{if(String(request.url).includes("/assets/"))return new Response("public asset",{status:200});throw new Error("offline");}});
const request=(path,options={})=>({method:options.method||"GET",url:"https://tele-tena.test"+path,mode:options.mode||"cors",headers:new Headers(options.headers||{})});

let apiResponse;
handlers.fetch({request:request("/api/method/tele_tena.api.presentation.appointment_detail"),respondWith:value=>apiResponse=value});
assert.equal(apiResponse,undefined,"authenticated APIs are outside service-worker cache handling");

let staticResponse;
handlers.fetch({request:request("/assets/app-hash.js"),respondWith:value=>staticResponse=value});
assert.ok(staticResponse,"hashed public assets use the cache-first handler");

let privateAssetResponse;
handlers.fetch({request:request("/assets/app-hash.js",{headers:{Authorization:"Bearer secret"}}),respondWith:value=>privateAssetResponse=value});
assert.equal(privateAssetResponse,undefined,"authorized responses bypass the cache");

let offlineResponse;
handlers.fetch({request:request("/clinician/care",{mode:"navigate"}),respondWith:value=>offlineResponse=value});
assert.deepEqual(await offlineResponse,{offline:true},"navigation falls back to the public offline page");
assert.equal(cached.some(path=>path.startsWith("/api/")),false,"no API response entered the cache");
console.log("PASS: service worker excludes APIs and authorization headers, caches public assets only, and serves an offline state for navigation");

self.location.pathname='/teletena/sw.js';
vm.runInNewContext(source,{self,caches,URL,Promise,fetch:async()=>{throw new Error('offline')}});
for (const path of ['/api/method/login','/private/files/resume.pdf','/assets/frappe/test.js','/app','/login','/teletena/private.pdf']) {
 let handled;
 handlers.fetch({request:request(path),respondWith:value=>handled=value});
 assert.equal(handled,undefined,'packaged worker bypasses '+path);
}
let assetHandled;
cacheHit={public:true};
handlers.fetch({request:request('/assets/tele_tena/review/assets/app-hash.js'),respondWith:value=>assetHandled=value});
assert.deepEqual(await assetHandled,{public:true});
console.log('PASS: packaged worker owns only TeleTena public assets and app navigation, not framework/private routes');
