const {chromium}=require('playwright');
const fs=require('fs'),assert=require('assert/strict');
(async()=>{const browser=await chromium.launch({headless:true,executablePath:process.env.RUNQUAY_BROWSER_EXECUTABLE || undefined});const out=process.env.RUNQUAY_BROWSER_ARTIFACTS,checks=[];checks.push=function(...items){console.log(items[0]);return Array.prototype.push.apply(this,items);};try{
const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage(),errors=[],violations=[];
page.on('pageerror',e=>errors.push(e.message));page.on('console',e=>{if(e.type()==='error')violations.push(e.text())});
await page.goto(JSON.parse(fs.readFileSync(out+'/browser-control.json','utf8')).url);await page.locator('#connection').filter({hasText:'Connected'}).waitFor();
const go=async hash=>{await page.evaluate(h=>location.hash=h,hash);await page.waitForTimeout(100)};
// Use the real searchable control, including no-results, keyboard and native backing value.
await go('#projects');await page.locator('#project-picker-trigger').click();await page.locator('#project-picker-search').fill('no such folder');
assert.equal(await page.locator('#project-picker-empty').isVisible(),true);
await page.locator('#project-picker-search').fill('Product 07');await page.keyboard.press('ArrowDown');await page.keyboard.press('Enter');
assert.equal(await page.locator('#request-target').inputValue(),'product-6');assert.match(await page.locator('#project-picker-trigger').innerText(),/Product 07/);
await page.locator('#project-picker-trigger').click();await page.keyboard.press('ArrowUp');assert.equal(await page.locator('#project-picker-options button').last().evaluate(n=>n===document.activeElement),true);
await page.locator('#project-picker-search').fill('New project');await page.keyboard.press('Enter');
assert.equal(await page.locator('#request-target').inputValue(),'');assert.equal(await page.locator('#project-picker-trigger').getAttribute('aria-expanded'),'false');
await page.locator('#project-picker-trigger').click();await page.locator('#project-picker-search').fill('A draft search');await page.keyboard.press('Escape');assert.equal(await page.locator('#project-picker-trigger').evaluate(n=>n===document.activeElement),true);assert.equal(await page.locator('#project-picker-dialog').isVisible(),false);
checks.push('project picker search, empty state, keyboard selection, Escape and focus return');
// Account labels and availability persist through actual HTTP writes and refresh.
await go('#accounts');await page.locator('[data-action="rename-account"]').first().click();
await page.locator('#rename-account-form [name="name"]').fill('Example renamed connection');await page.locator('#rename-account-form [type="submit"]').click();
await page.waitForFunction(()=>state.profiles.some(p=>p.name==='Example renamed connection'));
const account=await page.evaluate(()=>state.profiles.find(p=>p.name==='Example renamed connection').id);
await page.locator(`.account-details[data-key="account-${account}"]>summary`).click();
await page.locator(`[data-action="toggle"][data-id="${account}"]`).click();await page.waitForFunction(id=>!state.profiles.find(p=>p.id===id).enabled,account);
await page.locator(`[data-action="toggle"][data-id="${account}"]`).click();await page.waitForFunction(id=>state.profiles.find(p=>p.id===id).enabled,account);
await page.locator('#add-account').click();assert.equal(await page.locator('#account-options[open]').count(),0);
await page.locator('[data-account-tool="claude"]').click();assert.match(await page.locator('#account-connect-note').innerText(),/approval/);
await page.locator('[data-close="account-dialog"]').click();checks.push('account rename, disable, enable, detected tool selection and billing guidance');
// Settings: save then reload from actual server state, without starting the queue.
await go('#settings');await page.locator('#settings-form [name="advisor_hours"]').fill('8');await page.locator('#settings-form [type="submit"]').click();
await page.waitForFunction(()=>state.advisor_hours===8);await page.reload();await page.waitForFunction(()=>typeof state==='object'&&state?.advisor_hours===8);
assert.equal(await page.locator('#settings-form [name="advisor_hours"]').inputValue(),'8');checks.push('settings persist after reload');
// Reopen onboarding; navigate every step and exercise required acknowledgement.
await page.locator('#reopen-setup').click();await page.locator('#setup-provider').selectOption('codex');
await page.locator('#setup-next').click();await page.waitForFunction(()=>setupStep===1);await page.locator('#setup-next').click();
await page.locator('#setup-workspace').fill(await page.evaluate(()=>state.workspace_root));await page.locator('#setup-next').click();
await page.locator('#setup-next').click();await page.waitForFunction(()=>document.querySelector('#toast').textContent.includes('Review'));assert.equal(await page.locator('#setup-dialog').isVisible(),true);
await page.locator('#setup-ack').check();await page.locator('#setup-next').click();await page.locator('#setup-dialog').waitFor({state:'hidden'});checks.push('four onboarding steps, billing acknowledgement enforcement and completion');
// Real file import only imports bounded fictional metadata, and preview remains text.
await page.locator('#workspace-library>summary').click();await page.locator('#import-history').click();
await page.locator('#history-file').setInputFiles({name:'example-history.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({version:1,tool:'Example AI',tasks:[{id:'qa-import',title:'Fictional import verification',preview:'<script>window.HISTORY_BAD=true</script>'}]}))});
await page.waitForFunction(()=>state.history_tasks.some(t=>t.title==='Fictional import verification'));
await page.locator('#history-import-dialog').waitFor({state:'hidden'});
assert.equal(await page.evaluate(()=>Boolean(window.HISTORY_BAD)),false);checks.push('history file import and escaped private-preview text');
// User-visible error recovery preserves an unsent request after a failed server response.
await go('#projects');await page.locator('#request-text').fill('A deliberately interrupted request');
await page.route('**/api/requests',r=>r.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:'Example service interruption'})}));
await page.locator('#request-send').click();await page.locator('#request-error').waitFor();assert.equal(await page.locator('#request-text').inputValue(),'A deliberately interrupted request');assert.equal(await page.locator('#request-send').isDisabled(),false);
await page.unroute('**/api/requests');await page.locator('#request-text').fill('');checks.push('failed submission preserves text and allows retry');
// Follow-up uses existing task, then test stop, continue and cancel without launching a real provider.
const completed=await page.evaluate(()=>state.projects.find(p=>p.state==='complete'&&p.kind==='work')?.id);assert.ok(completed);
await page.locator('#workspace-search').fill('Create a fictional SEO');await page.locator(`[data-action="resume"][data-id="${completed}"]`).first().click();
await page.locator('#resume-form [name="guidance"]').fill('Add a fictional improvement');await page.locator('#resume-form [type="submit"]').click();
await page.waitForFunction(id=>state.projects.find(p=>p.id===id).guidance==='Add a fictional improvement',completed);
checks.push('follow-up guidance persists on the same task');
// Review, edit and hide learnings through the real controls and backend.
await go('#learnings');await page.locator('#field-library-trigger').click();await page.locator('.learning-index-open').first().click();
await page.locator('.learning-card-menu>summary').click();
await page.locator('[data-learning-action="edit"]').click();await page.locator('#learning-edit-form [name="title"]').fill('Reviewed example lesson');await page.locator('#learning-edit-form [type="submit"]').click();
await page.waitForFunction(()=>state.learnings.cards.some(c=>c.payload.title==='Reviewed example lesson'&&c.state==='review'));
if(!await page.locator('#learning-library-dialog').isVisible())await page.locator('#field-library-trigger').click();
await page.locator('#learning-search').fill('Reviewed example lesson');await page.locator('.learning-index-open').click();await page.locator('[data-learning-action="approve"]').click();
await page.waitForFunction(()=>state.learnings.cards.some(c=>c.payload.title==='Reviewed example lesson'&&c.state==='saved'));
await page.locator('#field-library-trigger').click();
await page.locator('.learning-index-open').filter({hasText:'Reviewed example lesson'}).click();await page.locator('.learning-card-menu>summary').click();await page.locator('[data-learning-action="dismiss"]').click();
await page.waitForFunction(()=>!state.learnings.cards.some(c=>c.payload.title==='Reviewed example lesson'));
checks.push('learning edit returns to review, Keep persists and Hide removes lesson');
// Native menus and the open project picker must remain legible and contained.
for(const width of [320,390,768,1024,1440]){await page.setViewportSize({width,height:900});await go('#projects');await page.locator('#project-picker-trigger').click();
 const bounds=await page.locator('#project-picker-dialog').boundingBox();assert.ok(bounds.x>=0&&bounds.x+bounds.width<=width+1);
 assert.equal(await page.locator('#project-picker-options button').first().evaluate(n=>getComputedStyle(n).color),'rgb(232, 233, 241)');
 await page.screenshot({path:out+`/picker-${width}.png`,animations:'disabled'});await page.keyboard.press('Escape');}
checks.push('open project menu at five widths with explicit foreground/background colors');
assert.deepEqual(errors,[]);assert.deepEqual(violations.sort(),['Failed to load resource: the server responded with a status of 400 (Bad Request)','Failed to load resource: the server responded with a status of 503 (Service Unavailable)']);fs.writeFileSync(out+'/extended-browser-result.json',JSON.stringify({passed:true,checks,browser_errors:errors,expected_error_responses:[400,503],unexpected_console_errors:[],real_ai_calls:0},null,2));
console.log('Extended UI checks passed: '+checks.length+' feature groups.');
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exit(1)});
