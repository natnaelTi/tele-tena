// Isolated persisted-backend checks. Never prints credentials, IDs or file bytes.
const {chromium}=require('playwright'),fs=require('fs'),assert=require('assert/strict');
const root=process.env.TELE_TENA_PRIVATE_DIR,base=process.env.TELE_TENA_BROWSER_BASE;
assert(root&&base&&/^http:\/\/127\.0\.0\.1:/.test(base),'Explicit local disposable target required');
const records=JSON.parse(fs.readFileSync(root+'/tt-demo-mvp-v2-records.json')),passwords=JSON.parse(fs.readFileSync(root+'/tt-demo-mvp-v2-accounts.json'));
const api='/api/method/tele_tena.api.history_documents.',png='iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAIAAAD8GO2jAAAALUlEQVR4nGP88OMrAy0BE01NH7Vg1IJRC0YtGLVg1IJRC0YtGLVg1IJRC6gIAEQdAx0xnM0mAAAAAElFTkSuQmCC';
(async()=>{let browser,owner,id;const contexts=[];try{
 browser=await chromium.launch();
 async function login(key){const context=await browser.newContext();contexts.push(context);const page=await context.newPage();await page.goto(base+'/sign-in');await page.getByRole('button',{name:'Use email instead',exact:true}).waitFor();await page.waitForLoadState('networkidle');const response=await context.request.post(new URL('/api/method/login',base).href,{data:{usr:records.users[key],pwd:passwords[records.users[key]]}});assert.equal(response.status(),200,'Existing login');const session=await context.request.get(new URL('/api/method/tele_tena.api.contact_auth.session',base).href);const state=(await session.json()).message;assert(state.authenticated,'Authenticated cookie session after existing login');return {context,csrf:state.csrf_token};}
 owner=await login('patient');
 const origin=new URL(base).origin;
 const command=(method,data)=>owner.context.request.post(origin+api+method,{data,headers:{'X-Frappe-CSRF-Token':owner.csrf}});
 const before=(await (await owner.context.request.get(origin+api+'list_documents')).json()).message.documents.length;
 for(const data of [{filename:'disallowed.exe',content_base64:png},{filename:'mismatch.pdf',content_base64:png},{filename:'bad.pdf',content_base64:Buffer.from('%PDF-broken').toString('base64')},{filename:'oversized.png',content_base64:Buffer.alloc(5*1024*1024+1).toString('base64')}]){
  const response=await command('upload',data);assert.equal(response.status(),417,'Server file validation');assert.equal((await response.json()).tele_tena_error,'history_file_invalid');
 }
 const uploaded=await command('upload',{filename:'fictional-incremental-http.png',content_base64:png});assert.equal(uploaded.status(),200);id=(await uploaded.json()).message.id;
 for(const key of ['private_patient','counselor','reviewer']){
  const other=await login(key);assert.equal((await other.context.request.get(origin+api+'download?id='+encodeURIComponent(id))).status(),403,'Non-owner download denied');
  assert([403,404].includes((await other.context.request.get(origin+'/api/resource/File/'+encodeURIComponent(id))).status()),'No generic File bypass');
 }
 const guest=await browser.newContext();contexts.push(guest);assert([401,403].includes((await guest.request.get(origin+api+'download?id='+encodeURIComponent(id))).status()),'Guest denied');
 const download=await owner.context.request.get(origin+api+'download?id='+encodeURIComponent(id));assert.equal(download.status(),200);assert.match(download.headers()['cache-control'],/\bprivate\b/);assert.match(download.headers()['cache-control'],/\bno-store\b/);assert.equal(download.headers()['x-content-type-options'],'nosniff');assert.match(download.headers()['content-disposition'],/^attachment/);assert.match(download.headers()['content-security-policy'],/sandbox/);
 assert.equal((await command('remove',{id})).status(),200);id=null;
 assert.equal((await (await owner.context.request.get(origin+api+'list_documents')).json()).message.documents.length,before);
 console.log('PASS real HTTP/session/CSRF: existing credentials; server extension/type/malformed/5MB restrictions; owner download; other patient/clinician/reviewer/guest denial; no generic File bypass; private/no-store/attachment/nosniff/sandbox; own fixture cleaned.');
 }catch(error){console.error('FAIL '+error.name+': '+error.message.split('\n')[0]);process.exitCode=1;}finally{
  if(id&&owner)await owner.context.request.post(new URL(api+'remove',base).href,{data:{id},headers:{'X-Frappe-CSRF-Token':owner.csrf}}).catch(()=>{});
  for(const context of contexts)await context.close();await browser?.close();
 }})();
