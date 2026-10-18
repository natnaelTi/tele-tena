// Read-only browser check against a separate invited-review fixture.
const {chromium}=require('playwright'),assert=require('assert/strict');
const base=process.env.TELE_TENA_DISABLED_BASE||'http://127.0.0.1:8030/teletena';
assert(['127.0.0.1','localhost'].includes(new URL(base).hostname));
(async()=>{const browser=await chromium.launch();try{const p=await browser.newPage();p.setDefaultTimeout(15000);
 await p.goto(base+'/sign-in?mode=register&intent=patient');await p.getByText('Patient registration is unavailable on this site.',{exact:true}).waitFor();assert.equal(await p.getByRole('link',{name:'Create an account',exact:true}).count(),0);
 await p.getByRole('button',{name:'Use email instead',exact:true}).click();await p.getByRole('button',{name:'Use password instead',exact:true}).click();await p.getByLabel('Password',{exact:true}).waitFor();
 const options=(await(await p.request.get(new URL('/api/method/tele_tena.api.contact_auth.sign_in_options',base).href)).json()).message;assert(!options.patient_registration&&!options.clinician_registration&&!options.phone_otp&&!options.email_otp);
 await p.goto(base+'/sign-in?mode=register&intent=clinician');await p.getByText('Clinician applications are unavailable on this site.',{exact:true}).waitFor();assert.equal(await p.getByRole('link',{name:'Apply as a clinician',exact:true}).count(),0);
 console.log('PASS real invited-review configuration: both registrations and delivery methods disabled;password alternative remains explicit.');
}finally{await browser.close();}})().catch(error=>{console.error(error.message.split('\n')[0]);process.exitCode=1;});
