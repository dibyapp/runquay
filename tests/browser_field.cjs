const {chromium}=require('playwright');
const fs=require('fs'),assert=require('assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.RUNQUAY_BROWSER_EXECUTABLE || undefined});
 try {
  const out=process.env.RUNQUAY_BROWSER_ARTIFACTS,url=JSON.parse(fs.readFileSync(out+'/browser-control.json','utf8')).url;
  const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'no-preference'});
  const page=await context.newPage(),errors=[],consoleErrors=[],posted=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text())});page.on('request',r=>{if(r.method()==='POST')posted.push(new URL(r.url()).pathname)});
  await page.goto(url);await page.locator('[data-learning-topic]').first().waitFor();
  assert.match(await page.locator('#connection').innerText(),/Connected/);
  assert.equal(posted.length,0,'Opening Learnings must not start analysis');
  await page.evaluate(()=>location.hash='#projects');
  const draftTarget=await page.locator('#request-target option').nth(1).getAttribute('value');
  await page.locator('#request-target').selectOption(draftTarget);
  await page.locator('.request-options>summary').click();
  await page.locator('#request-provider').selectOption('claude');
  await page.locator('.request-options>summary').click();
  await page.locator('#request-text').fill('A private unsent draft');
  await page.reload();await page.locator('#request-text').waitFor();
  await page.waitForFunction(()=>document.querySelector('#request-text').value==='A private unsent draft');
  assert.equal(await page.locator('#request-target').inputValue(),draftTarget);
  assert.equal(await page.locator('#request-provider').inputValue(),'claude');
  assert.equal(await page.locator('#request-discard').isVisible(),true);
  await page.locator('#request-discard').click();
  assert.equal(await page.locator('#request-text').inputValue(),'');
  assert.equal(await page.evaluate(()=>sessionStorage.getItem('runquay.request.draft.v1')),null);
  await page.locator('#request-target').selectOption('');
  await page.locator('.request-options>summary').click();
  await page.locator('#request-provider').selectOption('codex');
  await page.locator('.request-options>summary').click();
  await page.evaluate(()=>location.hash='#learnings');
  await page.locator('[data-learning-topic]').first().waitFor();
  assert.equal(await page.locator('#field-total').innerText(),'26');
  assert.equal(await page.locator('.learning-card:visible').count(),0);
  assert.equal(await page.locator('aside:not(.flight-deck)').count(),0);
  assert.equal(await page.evaluate(()=>RunquayField.status.frameActive),true);
  // Topic labels are separate, real hit targets, not painted text or overlapping controls.
  const boxes=await page.locator('[data-learning-topic]').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}}));
  for(let a=0;a<boxes.length;a++)for(let b=a+1;b<boxes.length;b++){const x=boxes[a],y=boxes[b];assert.equal(x.x<y.x+y.w&&x.x+x.w>y.x&&x.y<y.y+y.h&&x.y+x.h>y.y,false,'overlapping topics');}
  await page.getByRole('button',{name:'Pause animation',exact:true}).click();
  assert.equal(await page.evaluate(()=>RunquayField.status.frameActive),false);
  const stopped=await page.evaluate(()=>RunquayField.status.canvasDraws);await page.waitForTimeout(180);assert.equal(await page.evaluate(()=>RunquayField.status.canvasDraws),stopped);
  await page.locator('#field-library-trigger').click();
  assert.equal(await page.locator('#learning-library-dialog').evaluate(n=>getComputedStyle(n).opacity),'1');
  await page.locator('[data-close="learning-library-dialog"]').click();
  await page.getByRole('button',{name:'Enable animation',exact:true}).click();
  await page.locator('[data-learning-topic="SEO"]').click();
  await page.locator('#learning-preview-dialog[open]').waitFor();
  assert.equal(posted.filter(p=>p==='/api/learnings/collect').length,0);
  assert.equal(await page.locator('.learning-preview-source').count(),20);
  await page.locator('[data-exclude-source]').first().click();
  await page.waitForFunction(()=>document.querySelectorAll('.learning-preview-source').length===19);
  await page.locator('#learning-confirm').click();
  await page.waitForFunction(()=>state.learnings.cards.length===2);
  assert.equal(await page.locator('#field-library-count').innerText(),'2');
  assert.equal(await page.locator('.learning-index-row:visible').count(),0);
  await page.locator('#field-library-trigger').click();
  await page.locator('.learning-index-open').filter({hasText:'Validate canonical'}).click();
  await page.locator('#learning-insight-dialog[open]').waitFor();
  assert.equal(await page.locator('.insight-context[open]').count(),0);
  await page.locator('.insight-context>summary').click();
  assert.equal(await page.locator('.insight-context li').count(),19);
  await page.locator('.insight-actions [data-learning-action="use"]').click();
  await page.waitForFunction(()=>location.hash==='#projects'&&!document.querySelector('#request-learning-chip').hidden);
  assert.equal(await page.locator('#project-dialog[open]').count(),0,'Using a lesson should stay in the everyday composer');
  await page.locator('.request-options>summary').click();await page.locator('#request-provider').selectOption('codex');await page.locator('.request-options>summary').click();
  await page.locator('#request-text').fill('Create a fictional SEO release checklist');
  await page.locator('#request-text').press('Control+Enter');
  await page.waitForFunction(()=>state.projects.some(p=>p.name==='Create a fictional SEO release checklist'&&p.state==='complete'));
  const result=await page.evaluate(()=>state.projects.find(p=>p.name==='Create a fictional SEO release checklist'));
  const lesson=JSON.parse(result.learning_context)[0];assert.ok(lesson.lesson);assert.equal('source_ids' in lesson,false);assert.equal('sources' in lesson,false);
  assert.equal(await page.evaluate(()=>state.running),false);
  assert.equal(await page.locator('#request-learning-chip').isHidden(),true);
  await page.locator(`#work-${result.id} [data-action="result"]`).click();
  await page.locator('#result-dialog[open]').waitFor();assert.match(await page.locator('#result-instructions').innerText(),/Open index.html/);
  await page.locator('[data-close="result-dialog"]').click();
  await page.locator(`#work-${result.id} .work-more>summary`).click();
  await page.locator(`#work-${result.id} [data-work-reuse]`).click();
  assert.equal(await page.locator('#request-text').inputValue(),result.goal);
  await page.locator('#request-discard').click();
  await page.locator('#workspace-more').click();await page.locator('#work-library-dialog[open]').waitFor();
  assert.ok(await page.locator('#everyday-list>.work-card').count()>4);
  await page.locator('#work-filter').selectOption('finished');
  assert.ok(await page.locator('#everyday-list>.work-card').count()>=1);
  await page.locator('#work-filter').selectOption('all');
  await page.locator('#everyday-list [data-work-pin]').first().click();
  await page.locator('#work-filter').selectOption('pinned');
  assert.equal(await page.locator('#everyday-list>.work-card').count(),1);
  await page.locator('#work-clear').click();
  assert.equal(await page.locator('#work-filter').inputValue(),'all');
  for(const width of [320,390,768,1440]) {
    await page.setViewportSize({width,height:950});
    const layout=await page.locator('#work-library-dialog').evaluate(d=>({outer:d.scrollWidth-d.clientWidth,inner:d.querySelector('#work-library-scroll').scrollWidth-d.querySelector('#work-library-scroll').clientWidth}));
    assert.ok(layout.outer<=1 && layout.inner<=1,`work library horizontal overflow at ${width}`);
  }
  await page.setViewportSize({width:1440,height:1000});
  await page.locator('[data-close="work-library-dialog"]').click();await page.waitForFunction(()=>document.querySelectorAll('#work-surface-list .work-card').length===4);
  // Native previews retain their real project context without resuming a vendor chat.
  await page.keyboard.press('Control+k');await page.locator('#command-dialog[open]').waitFor();
  await page.locator('#command-input').fill('SEO deployment for Product 01');await page.keyboard.press('Enter');
  await page.locator('#work-library-dialog[open]').waitFor();
  await page.locator('.history-title').filter({hasText:'SEO deployment for Product 01'}).click();
  await page.locator('#saved-conversation-dialog[open]').waitFor();assert.match(await page.locator('#saved-conversation-note').innerText(),/original conversation/);
  await page.locator('[data-close="saved-conversation-dialog"]').click();await page.locator('[data-close="work-library-dialog"]').click();
  await page.keyboard.press('Control+k');await page.locator('#command-input').fill('connections');await page.keyboard.press('ArrowDown');await page.keyboard.press('Enter');
  await page.waitForFunction(()=>location.hash==='#accounts');assert.equal(await page.evaluate(()=>RunquayField.status.frameActive),false);
  await page.evaluate(()=>location.hash='#projects');await page.waitForTimeout(150);
  await page.locator('.request-options>summary').click();await page.locator('#request-provider').selectOption('claude');
  await page.locator('#request-text').fill('Draft a fictional field design review');await page.locator('#request-send').click();
  await page.waitForFunction(()=>state.decisions.some(d=>d.kind==='external_run'&&d.state==='pending'));
  await page.evaluate(()=>location.hash='#learnings');await page.waitForTimeout(120);
  assert.equal(await page.locator('#field-approval-trigger').isVisible(),true);
  await page.locator('#field-approval-trigger').click();assert.equal(await page.locator('#approvals').isVisible(),true);
  await page.locator('[data-action="decline-reset"]').filter({hasText:'Decline run'}).click();
  await page.waitForFunction(()=>!state.decisions.some(d=>d.kind==='external_run'&&d.state==='pending'));
  assert.equal(await page.locator('#field-approvals-dialog').isHidden(),true);
  // Real provider text stays escaped in the detail sheet.
  await page.locator('#field-library-trigger').click();await page.locator('.learning-index-open').filter({hasText:'Test a migration'}).click();
  assert.equal(await page.locator('#insight-content img').count(),0);assert.equal(await page.evaluate(()=>Boolean(window.BAD)),false);
  await page.locator('[data-close="learning-insight-dialog"]').click();
  const layouts=[];
  for(const width of [320,390,768,1024,1440]) {
    await page.setViewportSize({width,height:950});
    for(const route of ['#learnings','#projects','#accounts','#settings','#advisor']) {
      await page.evaluate(hash=>location.hash=hash,route);await page.waitForTimeout(100);
      const size=await page.evaluate(()=>({w:innerWidth,scroll:document.documentElement.scrollWidth}));assert.ok(size.scroll<=size.w,route+' overflow '+width);
      if(route==='#learnings') {
        const outside=await page.locator('[data-learning-topic]').evaluateAll(nodes=>nodes.some(n=>{const r=n.getBoundingClientRect();return r.left<0 || r.right>innerWidth}));assert.equal(outside,false,'topic outside viewport '+width);
      }
    }
    layouts.push(width);
  }
  await page.setViewportSize({width:1440,height:1000});await page.evaluate(()=>location.hash='#learnings');await page.waitForTimeout(180);
  await page.screenshot({path:out+'/verified-learnings-desktop.png',fullPage:true,animations:'disabled'});
  await page.locator('#field-library-trigger').click();await page.locator('.learning-index-open').first().click();
  await page.screenshot({path:out+'/verified-insight.png',fullPage:true,animations:'disabled'});await page.locator('[data-close="learning-insight-dialog"]').click();
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:out+'/verified-learnings-mobile.png',fullPage:true,animations:'disabled'});
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.waitForFunction(()=>!RunquayField.status.frameActive&&!RunquayField.status.motionEnabled);
  assert.equal(await page.locator('.core-shell').first().evaluate(n=>getComputedStyle(n).animationName),'none');
  assert.equal(await page.locator('[data-learning-topic]').first().evaluate(n=>getComputedStyle(n).animationName),'none');
  const emptyPage=await context.newPage();
  await emptyPage.route('**/api/state',async route=>{const response=await route.fetch();const data=await response.json();data.profiles=[];await route.fulfill({response,json:data});});
  await emptyPage.goto(url);await emptyPage.locator('[data-learning-topic]').first().waitFor();
  await emptyPage.locator('[data-learning-topic]').first().click();
  await emptyPage.waitForFunction(()=>location.hash==='#accounts');await emptyPage.close();
  assert.deepEqual(errors,[]);assert.deepEqual(consoleErrors,[]);
  fs.writeFileSync(out+'/browser-result.json',JSON.stringify({passed:true,layouts,real_http_worker:true,real_ai_calls:0,fictional_context_only:true,model_calls_on_navigation:0,checks:['interactive real topic nodes','no overlapping desktop nodes','animation pause','canvas stops off-page','system reduced motion','explicit context approval','inline exclusion','on-demand library and insights','escaped provider content','approved lesson attachment','request-to-result','fixed context without source histories','native preview via command search','keyboard command navigation','global vendor approval and decline','all five pages at five widths','strict CSP without violations'],browser_errors:errors,console_errors:consoleErrors},null,2));
  console.log('Field walkthrough passed: knowledge → reviewed context → insight → attached request → result; keyboard, motion, global approvals and responsive pages verified.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
