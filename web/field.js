"use strict";
window.RunquayField = (() => {
  const get=id=>document.getElementById(id);
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const stage=get('knowledge-stage'),canvas=get('knowledge-lines'),ctx=canvas.getContext('2d');
  let current=null,route=RunquayUI.pageFor(location.hash),choices=[],frame=0,lastFrame=0,draws=0;
  let width=0,height=0,points=[],center={x:0,y:0},highlight=-1,paused=false;
  try{paused=localStorage.getItem('runquay.motion')==='paused';}catch{/* Preference storage is optional. */}
  const stars=Array.from({length:34},(_,i)=>({x:((i*47+13)%101)/101,y:((i*i*17+23)%97)/97,r:i%7===0?1:.55,phase:i*.83}));
  const motionAllowed=()=>!paused && !reduced.matches;
  function measure() {
    const rect=stage.getBoundingClientRect();width=rect.width;height=rect.height;
    const scale=Math.min(window.devicePixelRatio || 1,1.5);
    canvas.width=Math.max(1,Math.round(width*scale));canvas.height=Math.max(1,Math.round(height*scale));
    ctx?.setTransform(scale,0,0,scale,0,0);
    const core=stage.querySelector('.core-caption').getBoundingClientRect();
    center={x:core.left+core.width/2-rect.left,y:core.top+core.height/2-rect.top};
    points=[...stage.querySelectorAll('.node-light')].map(node=>{
      const r=node.getBoundingClientRect();return {x:r.left+r.width/2-rect.left,y:r.top+r.height/2-rect.top};
    });
    draw(0);
  }
  function draw(time) {
    if(!ctx || !width || !height)return;
    draws++;ctx.clearRect(0,0,width,height);
    const t=motionAllowed()?time*.00022:0;
    for(const star of stars) {
      const alpha=.13+(Math.sin(t+star.phase)+1)*.09;
      ctx.fillStyle=`rgba(174,180,215,${alpha})`;
      ctx.beginPath();ctx.arc(star.x*width,star.y*height,star.r,0,Math.PI*2);ctx.fill();
    }
    points.forEach((point,index)=>{
      const active=index===highlight;
      const gradient=ctx.createLinearGradient(center.x,center.y,point.x,point.y);
      gradient.addColorStop(0,'rgba(169,152,224,0)');gradient.addColorStop(.45,active?'rgba(182,171,237,.19)':'rgba(145,143,181,.04)');gradient.addColorStop(1,active?'rgba(186,191,234,.32)':'rgba(145,143,181,.1)');
      ctx.strokeStyle=gradient;ctx.lineWidth=active?1:.65;
      ctx.beginPath();ctx.moveTo(center.x,center.y);ctx.quadraticCurveTo(center.x+(point.x-center.x)*.62,point.y+(center.y-point.y)*.24,point.x,point.y);ctx.stroke();
    });
  }
  function tick(time) {
    frame=0;
    if(route!=='learnings' || document.hidden || !motionAllowed())return;
    if(time-lastFrame>40){lastFrame=time;if(!document.querySelector('dialog[open]'))draw(time);}
    frame=requestAnimationFrame(tick);
  }
  function syncMotion() {
    document.body.classList.toggle('motion-paused',!motionAllowed() || document.hidden);
    const button=get('field-motion');button.disabled=reduced.matches;
    button.setAttribute('aria-pressed',String(!motionAllowed()));
    const label=reduced.matches?'Reduced motion follows your system setting':paused?'Enable animation':'Pause animation';
    button.setAttribute('aria-label',label);button.title=label;
    button.innerHTML=`<span aria-hidden="true">${motionAllowed()?'Ⅱ':'▷'}</span>`;
    if(frame){cancelAnimationFrame(frame);frame=0;}
    if(route==='learnings' && !document.hidden){measure();if(motionAllowed())frame=requestAnimationFrame(tick);}
  }
  function navigate(page) {
    route=page;document.body.dataset.scene=page;
    document.querySelectorAll('.nav-more').forEach(menu=>{menu.open=false;});
    if(location.hash==='#approvals' && !get('field-approvals-dialog').open)get('field-approvals-dialog').showModal();
    syncMotion();
  }
  function render(value) {
    current=value;
    if(get('approvals').parentElement!==get('field-approval-content'))get('field-approval-content').append(get('approvals'));
    const pending=value.decisions.filter(d=>['pending','uncertain','redeeming'].includes(d.state));
    get('field-approval-trigger').hidden=!pending.length;
    get('field-approval-label').textContent=pending.length===1?'Your decision is needed':`${pending.length} decisions need you`;
    get('approvals').hidden=!pending.length;
    if(!pending.length && get('field-approvals-dialog').open)get('field-approvals-dialog').close();
    if(get('command-dialog').open)renderCommands();
  }
  function renderCommands() {
    choices=RunquayUI.commandChoices(current || {},get('command-input').value);
    replaceCards('command-results',choices.length ? choices.map((item,index)=>`<button type="button" class="command-result" role="listitem" data-field-command="${index}"><span aria-hidden="true">${esc(item.symbol)}</span><div><strong>${esc(item.label)}</strong><small>${esc(item.detail)}</small></div><span aria-hidden="true">↗</span></button>`).join('') : '<p class="command-empty">No match. Try a project name or another word.</p>');
  }
  function openCommands() {
    if(document.querySelector('dialog[open]:not(#command-dialog)'))return;
    get('command-input').value='';renderCommands();
    if(!get('command-dialog').open)get('command-dialog').showModal();
    get('command-input').focus();
  }
  function choose(index) {
    const item=choices[index];if(!item)return;
    get('command-dialog').close();
    if(item.kind==='route'){location.hash='#'+item.id;if(item.id==='projects')window.RunquayWorkspace.focusRequest();}
    if(item.kind==='work' || item.kind==='history')window.RunquayWorkspace.revealWork(item.id,item.kind);
    if(item.kind==='insight'){location.hash='#learnings';window.RunquayLearnings.openInsight(item.id);}
  }
  get('command-launch').onclick=openCommands;
  get('command-input').oninput=renderCommands;
  get('command-results').onclick=event=>{const item=event.target.closest('[data-field-command]');if(item)choose(Number(item.dataset.fieldCommand));};
  get('command-dialog').addEventListener('keydown',event=>{
    const buttons=[...get('command-results').querySelectorAll('button')];
    if(event.key==='ArrowDown' || event.key==='ArrowUp') {
      event.preventDefault();const at=buttons.indexOf(document.activeElement);
      if(buttons.length)buttons[(at+(event.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length].focus();
    }
    if(event.key==='Enter' && event.target===get('command-input') && choices.length){event.preventDefault();choose(0);}
  });
  document.addEventListener('keydown',event=>{
    if((event.ctrlKey || event.metaKey) && !event.altKey && event.key.toLowerCase()==='k'){event.preventDefault();get('command-dialog').open?get('command-dialog').close():openCommands();}
  });
  get('command-shortcut').textContent=/mac/i.test(navigator.platform)?'⌘ K':'Ctrl K';
  get('field-approval-trigger').onclick=()=>{if(!get('field-approvals-dialog').open)get('field-approvals-dialog').showModal();};
  get('field-motion').onclick=()=>{
    paused=!paused;try{localStorage.setItem('runquay.motion',paused?'paused':'enabled');}catch{/* No storage is required. */}
    syncMotion();
  };
  reduced.addEventListener('change',syncMotion);
  document.addEventListener('visibilitychange',syncMotion);
  stage.addEventListener('pointerover',event=>{
    const node=event.target.closest('[data-learning-topic]');
    highlight=node?[...stage.querySelectorAll('[data-learning-topic]')].indexOf(node):-1;
    if(!motionAllowed())draw(0);
  });
  stage.addEventListener('pointerleave',()=>{highlight=-1;if(!motionAllowed())draw(0);});
  stage.addEventListener('focusin',event=>{highlight=[...stage.querySelectorAll('[data-learning-topic]')].indexOf(event.target);draw(0);});
  new ResizeObserver(measure).observe(stage);
  new MutationObserver(measure).observe(get('learning-topic-suggestions'),{childList:true});
  document.querySelectorAll('dialog.field-sheet, #command-dialog').forEach(dialog=>dialog.addEventListener('click',event=>{
    if(event.target!==dialog)return;
    const r=dialog.getBoundingClientRect();
    if(event.clientX<r.left || event.clientX>r.right || event.clientY<r.top || event.clientY>r.bottom)dialog.close();
  }));
  window.addEventListener('pagehide',()=>{if(frame){cancelAnimationFrame(frame);frame=0;}});
  window.addEventListener('pageshow',syncMotion);
  navigate(route);
  return {render,navigate,openCommands,refreshScene:measure,
    get status(){return {route,motionEnabled:motionAllowed(),frameActive:Boolean(frame),canvasDraws:draws};}};
})();
