const {chromium}=require('playwright'),fs=require('fs'),assert=require('assert/strict');
(async()=>{const browser=await chromium.launch({headless:true});try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));await page.goto(JSON.parse(fs.readFileSync(process.env.RUNQUAY_BROWSER_ARTIFACTS+'/browser-control.json','utf8')).url.replace('#learnings','#projects'));
 await page.locator('#request-send:not([disabled])').waitFor();
 const go=async hash=>{await page.evaluate(h=>location.hash=h,hash);await page.waitForTimeout(100)};
 await go('#projects');await page.locator('.request-options>summary').click();await page.locator('#request-provider').selectOption('codex');
 await page.locator('#request-text').fill('Browser slow task: verify live progress and pause');await page.locator('#request-send').click();
 await page.waitForFunction(()=>state.projects.some(p=>p.name.startsWith('Browser slow task')&&p.state==='running'));
 const id=await page.evaluate(()=>state.projects.find(p=>p.name.startsWith('Browser slow task')).id);
 await page.locator(`#work-${id} [data-action=log]`).first().click();await page.locator('#log-dialog[open]').waitFor();
 assert.ok(await page.locator('#session-status').innerText());assert.equal(await page.locator('#session-diagnostics[open]').count(),0);
 await page.locator('[data-close=log-dialog]').click();await page.locator(`#work-${id} .work-more>summary`).click();await page.locator(`#work-${id} [data-action=pause-project]`).click();
 console.log('Running conversation opened and pause requested.');
 await page.waitForFunction(id=>state.projects.find(p=>p.id===id).state==='paused'&&!state.projects.find(p=>p.id===id).run_requested,id);
 await page.locator(`#work-${id} [data-work-start]`).click();await page.waitForFunction(id=>state.projects.find(p=>p.id===id).state==='running',id);
 console.log('Paused task resumed.');
 if(!await page.locator(`#work-${id} .work-more`).evaluate(n=>n.open))await page.locator(`#work-${id} .work-more>summary`).click();
 await page.locator(`#work-${id} [data-action=cancel-project]`).click();await page.waitForFunction(id=>state.projects.find(p=>p.id===id).state==='cancelled',id);
 // Global start/pause controls work independently of scoped requests.
 await page.locator('#workspace-controls>summary').click();await page.locator('#start').click();await page.waitForFunction(()=>state.running);
 await go('#advisor');await page.locator('#advisor-target').selectOption('product-0');await page.locator('#advisor-form [name=focus]').fill('A fictional improvement');
 await page.locator('#generate-ideas').click();await page.waitForFunction(()=>state.suggestions.some(s=>s.payload.title==='Fixture idea'));
 await page.locator('#advisor-target').selectOption('');await page.locator('[data-idea-filter=new]').click();await page.locator('[data-action=review-suggestion]').first().click();
 assert.equal(await page.locator('#project-form [name=name]').inputValue(),'Fixture idea');await page.getByRole('button',{name:'Close task form',exact:true}).click();
 await page.locator('[data-action=dismiss-suggestion]').first().click();await page.waitForFunction(()=>state.suggestions.every(s=>s.state==='dismissed'));
 await go('#projects');await page.locator('#pause').click();await page.waitForFunction(()=>!state.running);
 // Approval handling is exercised only against the fake fixture, never a vendor CLI.
 await page.locator('#request-provider').selectOption('claude');await page.locator('#request-text').fill('Fictional one-run approval interface check');await page.locator('#request-send').click();
 await page.waitForFunction(()=>state.decisions.some(d=>d.kind==='external_run'&&d.state==='pending'));
 await go('#approvals');await page.locator('#field-approvals-dialog[open]').waitFor();await page.locator('[data-action=review-external]').click();
 await page.locator('#approve-external').click();assert.equal(await page.locator('#external-dialog').isVisible(),true);
 await page.locator('#external-ack').check();await page.locator('#approve-external').click();await page.locator('#external-dialog').waitFor({state:'hidden'});
 await page.waitForFunction(()=>state.decisions.some(d=>d.kind==='external_run'&&d.state==='consumed'));
 if(await page.locator('#field-approvals-dialog').isVisible())await page.locator('[data-close=field-approvals-dialog]').click();
 await go('#accounts');const count=await page.locator('.account').count();const details=page.locator('.account-details').last();await details.locator('summary').click();await details.locator('[data-action=remove-profile]').click();
 await page.waitForFunction(n=>state.profiles.length===n-1,count);
 assert.deepEqual(errors,[]);console.log('Task controls passed: running progress, pause, resume, cancel, global start/pause, advisor ideas/review/dismiss, bookmarked approvals, billing acknowledgement, one-run consumption and connection removal.');
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exit(1)});
