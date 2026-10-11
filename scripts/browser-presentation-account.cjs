// Named presentation site; private credentials, persisted queries, no API mocks.
// Draft-only edits are discarded by navigation; no profile or financial writes.
const fs = require('node:fs'), assert = require('node:assert/strict');
const { chromium } = require('playwright');
const root = '/home/frappe/frappe/frappe-bench/sites/teletena-mvp-presentation.localhost/private';
const seed = JSON.parse(fs.readFileSync(root + '/tele_tena_presentation_seed.json'));
const credentials = JSON.parse(fs.readFileSync(root + '/tele_tena_presentation_accounts.json'));
const build = JSON.parse(fs.readFileSync('tele_tena/public/review/release.json'));
const base = 'http://127.0.0.1:8017/teletena', out = '/tmp/tt-presentation-account';
fs.mkdirSync(out, {recursive:true});
let stage = 'launch', browser;
(async () => { try {
  browser = await chromium.launch();
  for (const role of ['patient', 'clinician']) {
    const context = await browser.newContext({viewport:{width:1440,height:1000}});
    const page = await context.newPage(); page.setDefaultTimeout(15000);
    stage = role + ' sign-in';
    await page.goto(base + '/sign-in');
    await page.getByRole('button',{name:'Use email instead',exact:true}).click();
    await page.getByRole('button',{name:'Use password instead',exact:true}).click();
    await page.getByLabel('Email',{exact:true}).fill(seed.users[role]);
    await page.getByLabel('Password',{exact:true}).fill(credentials[seed.users[role]]);
    await page.getByRole('button',{name:'Sign in',exact:true}).click();
    await page.getByRole('button',{name:'Sign out',exact:true}).waitFor();
    async function query(method) {
      const r = await page.request.get('http://127.0.0.1:8017/api/method/' + method);
      assert.equal(r.status(),200); return (await r.json()).message;
    }
    const before = (await query('tele_tena.api.contact_auth.session')).profile;
    const moneyMethod = role === 'patient' ? 'tele_tena.api.journey.wallet' : 'tele_tena.accounting.clinician_earnings';
    const moneyBefore = await query(moneyMethod);
    async function pair(id,width) {
      await page.evaluate(()=>document.fonts.ready);
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({path:out+'/'+id+'-application-'+width+'.png',fullPage:true});
      const reference = await context.newPage();
      await reference.setViewportSize({width,height:1000});
      await reference.goto('http://127.0.0.1:8044/?embed=1#'+id.toLowerCase());
      await reference.evaluate(()=>document.fonts.ready);
      await reference.screenshot({path:out+'/'+id+'-reference-'+width+'.png',fullPage:true});
      await reference.close();
    }
    for (const width of [390,768,1440]) {
      await page.setViewportSize({width,height:1000});
      stage = role + ' overview ' + width;
      await page.goto(base+'/'+role+'/account');
      await page.getByRole('heading',{name:'Your account',exact:true}).waitFor();
      if (role === 'patient') {
        await pair('H01',width);
        await page.getByRole('button',{name:'Privacy & sharing',exact:true}).click();
        await page.getByRole('heading',{name:'Default disclosure',exact:true}).waitFor();
        assert.equal(await page.getByRole('checkbox',{name:'Share my preferred name by default',exact:true}).isChecked(),Boolean(before.share_name));
        assert.equal(await page.getByRole('checkbox',{name:'Share my saved history by default',exact:true}).isChecked(),Boolean(before.share_history));
        await pair('H03',width);
        stage = 'private draft label and navigation ' + width;
        await page.getByRole('button',{name:'Personal profile',exact:true}).click();
        await page.getByText('Optional saved history',{exact:true}).click();
        const history = page.getByLabel('Information you may choose to share',{exact:true});
        await history.fill('Temporary accessibility check; not saved.');
        await history.press('Tab');
        assert.equal(await history.count(),1);
        assert.equal(await history.getAttribute('aria-describedby'),'account-history-help');
        await page.getByRole('button',{name:'Language & timezone',exact:true}).click();
        await page.getByRole('button',{name:'Personal profile',exact:true}).click();
        await page.getByText('Optional saved history',{exact:true}).click();
        assert.equal(await history.inputValue(),'Temporary accessibility check; not saved.');
        await page.reload();
        await page.getByRole('button',{name:'Privacy & sharing',exact:true}).click();
      } else {
        await page.getByRole('button',{name:'Professional profile & practice',exact:true}).click();
        await page.getByRole('heading',{name:'Public profile',exact:true}).waitFor();
        await pair('H02',width);
      }
      stage = role + ' preferences ' + width;
      await page.getByRole('button',{name:'Language & timezone',exact:true}).click();
      await page.getByRole('heading',{name:'Language and timezone',exact:true}).waitFor();
      if (role === 'patient') await pair('H04',width);
      await page.getByRole('button',{name:'Contact & sign-in',exact:true}).click();
      await page.getByRole('heading',{name:'Contact and sign-in',exact:true}).waitFor();
      if (role === 'patient') await pair('H05',width);
    }
    assert.deepEqual((await query('tele_tena.api.contact_auth.session')).profile,before);
    assert.deepEqual(await query(moneyMethod),moneyBefore);
    await context.close();
  }
  assert.deepEqual(JSON.parse(fs.readFileSync('tele_tena/public/review/release.json')),build,'Build changed during evidence capture');
  fs.writeFileSync(out+'/result.json',JSON.stringify({source:build.source_commit,site:'teletena-mvp-presentation.localhost',widths:[390,768,1440],roles:['patient','clinician'],stable_private_field_label:true,draft_navigation_preserved:true,profile_and_money_unchanged:true,english_only:true,zoom_200_verified:false},null,2));
  console.log('PASS: named-site account sections, private draft accessibility/navigation, unchanged profiles/privacy/funds and paired English captures');
} finally { if (browser) await browser.close(); } })().catch(()=>{console.error('FAIL: account evidence stage '+stage+'; sensitive request contents withheld');process.exit(1)});
