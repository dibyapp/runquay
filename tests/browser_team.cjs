const {chromium}=require('playwright'),fs=require('fs'),assert=require('assert/strict');
(async()=>{const browser=await chromium.launch({headless:true});try {
  const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(JSON.parse(fs.readFileSync(process.env.RUNQUAY_BROWSER_ARTIFACTS+'/browser-control.json','utf8')).url.replace('#learnings','#projects'));
  await page.locator('#request-send:not([disabled])').waitFor();
  assert.equal(await page.locator('#request-provider').inputValue(),'auto');
  assert.match(await page.locator('#request-team-preview').innerText(),/Codex.*Claude Code/);
  assert.equal(await page.locator('.creation-signal .tool-emblem').count(),2);
  await page.locator('#request-text').fill('Coordinate a fictional checklist');await page.locator('#request-send').click();
  await page.waitForFunction(()=>state.projects.some(p=>p.name==='Coordinate a fictional checklist'&&p.workflow?.phase==='review'));
  const id=await page.evaluate(()=>state.projects.find(p=>p.name==='Coordinate a fictional checklist').id);
  assert.equal(await page.evaluate(id=>state.projects.find(p=>p.id===id).state,id),'queued');
  await page.waitForFunction(()=>state.decisions.some(d=>d.kind==='external_run'&&d.state==='pending'));
  await page.locator(`[data-workflow="${id}"]`).click();await page.locator('#workflow-dialog[open]').waitFor();
  assert.equal(await page.locator('.workflow-entry').count(),2);
  await page.locator('[data-close=workflow-dialog]').click();
  await page.locator('#field-approval-trigger').click();await page.locator('[data-action=review-external]').click();
  await page.locator('#external-ack').check();await page.locator('#approve-external').click();
  await page.waitForFunction(id=>state.projects.find(p=>p.id===id).state==='complete',id);
  await page.reload();await page.waitForFunction(id=>state?.projects.some(p=>p.id===id&&p.workflow?.phase==='done'),id);
  await page.locator(`[data-workflow="${id}"]`).click();assert.equal(await page.locator('.workflow-entry').count(),3);
  assert.match(await page.locator('.workflow-entry').last().innerText(),/Claude Code.*review/);
  await page.locator('[data-close=workflow-dialog]').click();
  // Previous runs must keep their original tool even after a handoff.
  const first=await page.evaluate(id=>state.runs.filter(r=>r.project_id===id).at(-1).id,id);
  await page.evaluate(async id=>{activeLog=id;await loadLog(id);document.getElementById("log-dialog").showModal();},first);
  await page.locator('#log-dialog[open]').waitFor();assert.match(await page.locator('#log-meta').innerText(),/Codex/);
  await page.locator('[data-close=log-dialog]').click();
  // A follow-up returns a finished workflow to the builder, not to a completed stage.
  await page.locator(`#work-${id} [data-action=resume]`).first().click();
  await page.locator('#resume-form [name=guidance]').fill('Add a fictional improvement');await page.locator('#resume-form [type=submit]').click();
  await page.waitForFunction(id=>state.projects.find(p=>p.id===id).workflow.history.length===4,id);
  assert.equal(await page.evaluate(id=>state.projects.find(p=>p.id===id).workflow.phase,id),'review');
  await page.waitForFunction(id=>state.decisions.some(d=>d.kind==='external_run'&&d.state==='pending'&&JSON.parse(d.payload).project_id===id),id);
  await page.locator('#field-approval-trigger').click();await page.locator('[data-action=decline-reset]').filter({hasText:'Decline run'}).click();
  await page.waitForFunction(id=>state.projects.find(p=>p.id===id).state==='attention',id);
  // Narrow widths expose text clipping that scroll-width checks alone miss.
  await page.evaluate(()=>location.hash='#learnings');await page.locator('.node-title').first().waitFor();
  await page.locator('.node-title').first().evaluate(n=>n.textContent='Analysis and practical product improvements');
  for(const width of [320,390,768,1024,1440]) {
    await page.setViewportSize({width,height:1000});
    const bounds=await page.locator('.learning-topic-choice').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect(),t=n.querySelector('.node-title'),s=getComputedStyle(t);return {x:r.x,y:r.y,w:r.width,h:r.height,clipped:t.scrollWidth>t.clientWidth+1||t.scrollHeight>t.clientHeight+1,overflow:s.overflow,whiteSpace:s.whiteSpace}}));
    for(const b of bounds){assert.ok(b.x>=0&&b.x+b.w<=width+1);assert.equal(b.clipped,false);assert.notEqual(b.whiteSpace,'nowrap');}
    for(let a=0;a<bounds.length;a++)for(let b=a+1;b<bounds.length;b++){const x=bounds[a],y=bounds[b];assert.equal(x.x<y.x+y.w&&x.x+x.w>y.x&&x.y<y.y+y.h&&x.y+x.h>y.y,false);}
    await page.screenshot({path:process.env.RUNQUAY_BROWSER_ARTIFACTS+`/team-labels-${width}.png`,animations:'disabled'});
  }
  await page.emulateMedia({reducedMotion:'reduce'});
  assert.equal(await page.locator('#learning-tool-indicator img').evaluate(n=>getComputedStyle(n).animationName),'none');
  assert.deepEqual(errors,[]);
  console.log('Auto team passed: plan/build, approval-gated second-tool review, persisted handoffs and original run identity. Topic labels fit at five widths and tool motion respects reduced motion.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});
