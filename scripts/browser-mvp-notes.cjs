// Actual persisted note commands on owned disposable fixtures, never API mocks.
// The harness supplies an Ended call fixture; this is not LiveKit End verification.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
const file=process.env.TELE_TENA_NOTES_FIXTURE;
assert.ok(file && (fs.statSync(file).mode&0o077)===0,'Private fixture file required');
const fixture=JSON.parse(fs.readFileSync(file));
assert.equal(fixture.site,'tele-tena-pr12-fresh.localhost');
const base='http://127.0.0.1:8017/teletena/';
const output='/tmp/teletena-mvp-journey-evidence'; fs.mkdirSync(output,{recursive:true});
let stage='launch';
(async()=>{const browser=await chromium.launch();try{
  async function session(role){
    const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage();
    page.setDefaultTimeout(12000);
    await page.goto(base+'sign-in');
    await page.getByRole('button',{name:'Use email instead',exact:true}).click();
    await page.getByRole('button',{name:'Use password instead',exact:true}).click();
    await page.getByLabel('Email',{exact:true}).fill(fixture.users[role]);
    await page.getByLabel('Password',{exact:true}).fill(fixture.password);
    await page.getByRole('button',{name:'Sign in',exact:true}).click();
    await page.getByRole('button',{name:'Sign out',exact:true}).waitFor();
    return {context,page};
  }
  const clinician=await session('c1'),patient=await session('p1');
  async function detail(page){return await page.evaluate(async id=>(await(await fetch('/api/method/tele_tena.api.presentation.appointment_detail?appointment='+encodeURIComponent(id),{cache:'no-store'})).json()).message,fixture.appointment);}
  async function capture(page,context,id,variant){
    for(const width of[390,768,1440]){
      await page.setViewportSize({width,height:1000});await page.evaluate(()=>document.fonts.ready);
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      await page.screenshot({path:path.join(output,`${id}-${variant}-${width}.png`),fullPage:true});
      const ref=await context.newPage();await ref.setViewportSize({width,height:1000});
      await ref.goto('http://127.0.0.1:8044/?embed=1#'+id.toLowerCase());await ref.evaluate(()=>document.fonts.ready);
      await ref.screenshot({path:path.join(output,`${id}-reference-${width}.png`),fullPage:true});await ref.close();
    }
  }
  const page=clinician.page;stage='save actual draft';
  await page.goto(base+'clinician/consultations/'+fixture.appointment);
  await page.getByLabel('Private consultation note',{exact:false}).fill('Fictional private clinician observation — not for patient sharing.');
  await page.getByLabel('Patient summary / next steps',{exact:false}).fill('We agreed to try a short daily check-in and discuss it at a follow-up.');
  await page.getByRole('button',{name:'Preview patient summary',exact:true}).click();
  const previewDialog=page.getByRole('dialog');await previewDialog.waitFor();
  assert.ok(!(await previewDialog.innerText()).includes('Fictional private clinician observation'));
  assert.equal((await detail(page)).documentation_state,'None');
  await previewDialog.getByRole('button',{name:'Back to notes',exact:true}).click();await previewDialog.waitFor({state:'hidden'});
  await page.getByRole('button',{name:'Save draft',exact:true}).click();await page.getByText('Draft saved.',{exact:true}).waitFor();
  await page.reload();
  assert.equal(await page.getByLabel('Private consultation note',{exact:false}).inputValue(),'Fictional private clinician observation — not for patient sharing.');
  assert.equal((await detail(page)).documentation_state,'Draft');
  const patientDraft=await detail(patient.page);assert.ok(!('private_note' in patientDraft));assert.equal(patientDraft.patient_summary_revisions.length,0);
  await capture(page,clinician.context,'E11','application');
  stage='finalize actual encounter';
  await page.getByRole('button',{name:'Finalize consultation',exact:true}).click();
  let dialog=page.getByRole('dialog');await dialog.getByRole('button',{name:'Finalize and publish',exact:true}).click();
  await dialog.waitFor({state:'hidden'});await page.locator('.finalized-note-document').waitFor();
  let completed=await detail(page);assert.equal(completed.status,'Completed');assert.equal(completed.reservation_state,'Consumed');
  assert.equal(completed.private_note.text,'Fictional private clinician observation — not for patient sharing.');
  await page.reload();await page.locator('.finalized-note-document').waitFor();
  await capture(page,clinician.context,'E13','clinician-application');
  stage='patient published summary';
  await patient.page.goto(base+'patient/consultations/'+fixture.appointment);
  await patient.page.locator('.shared-summary-document').waitFor();
  let visible=await detail(patient.page);assert.ok(!('private_note' in visible));assert.ok(!JSON.stringify(visible).includes('Fictional private clinician observation'));
  assert.equal(visible.patient_summary_revisions.length,1);
  assert.equal(await patient.page.locator('.finalized-note-document').count(),0);
  await capture(patient.page,patient.context,'E13','patient-application');
  stage='audited amendment';
  await page.getByRole('button',{name:'Amend consultation notes',exact:true}).click();
  await page.getByLabel('Private consultation note',{exact:false}).fill('Fictional private amendment; original retained.');
  await page.getByLabel('Patient summary / next steps',{exact:false}).fill('Correction: plan a check-in on two days this week.');
  await page.getByRole('button',{name:'Save draft',exact:true}).click();await page.getByText('Draft saved.',{exact:true}).waitFor();
  await page.reload();assert.equal(await page.getByLabel('Patient summary / next steps',{exact:false}).inputValue(),'Correction: plan a check-in on two days this week.');
  assert.equal((await detail(patient.page)).patient_summary_revisions.length,1);
  await page.getByRole('button',{name:'Finalize consultation',exact:true}).click();
  dialog=page.getByRole('dialog');await dialog.getByRole('button',{name:'Finalize and publish',exact:true}).click();await dialog.waitFor({state:'hidden'});
  await page.locator('.finalized-note-document').waitFor();
  await page.getByText('Sharing history',{exact:true}).click();assert.equal(await page.locator('.finalized-note-document details li').count(),2);
  visible=await detail(patient.page);assert.equal(visible.patient_summary_revisions.length,2);assert.ok(!('private_note' in visible));
  stage='reviewer denial';const reviewer=await session('admin');
  const denied=await reviewer.page.evaluate(async id=>{const r=await fetch('/api/method/tele_tena.api.presentation.appointment_detail?appointment='+encodeURIComponent(id),{cache:'no-store'});return r.status;},fixture.appointment);
  assert.ok([403,417].includes(denied));
  console.log('PASS: persisted draft/reload, finalized clinician document, patient-only published summaries, immutable amendment/sharing history and reviewer denial; 390/768/1440 pairs. Ended call was a synthetic fixture, not media/End proof.');
}catch(error){console.error('FAIL: '+stage+' '+error.name+'; private details withheld');process.exitCode=1;}finally{await browser.close();}})();
