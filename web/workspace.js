"use strict";
// The everyday surface: a request, its progress, and its result.
window.RunquayWorkspace = (() => {
  let limit=4, expanded=false, sending=false, retry=null, selectedHistory="", attachedLearning=null, activeWorkflow='';
  // Keep the form select as the source of truth; the visible picker is portable,
  // searchable and does not depend on an operating system's popup colors.
  function projectPicker() {
    const select=$("request-target"), label=select.parentElement;
    select.classList.add("picker-native");select.tabIndex=-1;select.setAttribute("aria-hidden","true");
    const trigger=document.createElement("button");trigger.type="button";trigger.id="project-picker-trigger";
    trigger.className="project-picker-trigger";trigger.setAttribute("aria-haspopup","dialog");
    trigger.setAttribute("aria-controls","project-picker-dialog");trigger.setAttribute("aria-expanded","false");
    label.replaceWith(Object.assign(document.createElement("div"),{className:"request-target project-picker"}));
    select.parentElement?.removeChild(select);
    document.querySelector(".project-picker").append(select,trigger);
    const dialog=document.createElement("dialog");dialog.id="project-picker-dialog";dialog.className="project-picker-dialog";
    dialog.setAttribute("aria-labelledby","project-picker-title");
    dialog.innerHTML='<div class="dialog-title"><h2 id="project-picker-title">Where shall we work?</h2><button type="button" class="icon" data-close="project-picker-dialog" aria-label="Close project picker">×</button></div><label class="sr-only" for="project-picker-search">Find a project</label><input id="project-picker-search" type="search" placeholder="Find a project…" autocomplete="off"><div id="project-picker-options" role="group" aria-label="Projects"></div><p id="project-picker-empty" hidden>No matching projects. Try another name.</p>';
    document.body.append(dialog);
    const search=$("project-picker-search"),list=$("project-picker-options");
    function update() {
      const query=search.value.trim().toLocaleLowerCase();
      list.innerHTML=Array.from(select.options).filter(o=>!query || o.text.toLocaleLowerCase().includes(query)).map(o=>
        `<button type="button" data-project-choice="${esc(o.value)}" aria-pressed="${o.selected}"><span>${esc(o.text)}</span><span aria-hidden="true">${o.selected?'✓':'↗'}</span></button>`).join("");
      $("project-picker-empty").hidden=!!list.childElementCount;
      trigger.textContent=select.selectedOptions[0]?.text || "New project";
      trigger.setAttribute("aria-label","Project: "+trigger.textContent);
    }
    trigger.onclick=()=>{search.value="";update();dialog.showModal();trigger.setAttribute("aria-expanded","true");search.focus();};
    search.oninput=update;
    dialog.addEventListener("close",()=>trigger.setAttribute("aria-expanded","false"));
    dialog.addEventListener("click",event=>{
      const choice=event.target.closest("[data-project-choice]");if(!choice)return;
      select.value=choice.dataset.projectChoice;select.dispatchEvent(new Event("change",{bubbles:true}));trigger.setAttribute("aria-expanded","false");dialog.close();trigger.focus();
    });
    dialog.addEventListener("keydown",event=>{
      if(event.key==="Escape") {
        event.preventDefault();trigger.setAttribute("aria-expanded","false");dialog.close();trigger.focus();return;
      }
      const buttons=Array.from(list.querySelectorAll("button")),index=buttons.indexOf(document.activeElement);
      if(["ArrowDown","ArrowUp"].includes(event.key)) {
        event.preventDefault();const step=event.key==="ArrowDown"?1:-1;
        buttons[index<0 ? (step>0?0:buttons.length-1) : (index+step+buttons.length)%buttons.length]?.focus();
      }else if(event.key==="Enter" && event.target===search && buttons.length===1){event.preventDefault();buttons[0].click();}
    });
    select.addEventListener("change",update);
    return update;
  }
  const updateProjectPicker=projectPicker();
  function navigate(page) {
    const workspace=$("everyday-work");
    if(["overview","projects"].includes(page)) {
      document.querySelector(`.page[data-page="${page}"]`).prepend(workspace);
      document.querySelector('[data-workspace-link]').setAttribute("aria-current","page");
      document.querySelector('[data-workspace-link]').classList.add("active");
    }
  }
  function syncSelect(id, options) {
    const select=$(id), value=select.value;
    const html=options.map(([key,label])=>`<option value="${esc(key)}">${esc(label)}</option>`).join("");
    if(select._options!==html) {
      select.innerHTML=html;select._options=html;
      if(options.some(([key])=>key===value)) select.value=value;
    }
  }
  function updateContext() {
    if(!state) return;
    const folder=state.catalog.find(p=>p.id===$("request-target").value);
    const tool=state.tools.find(t=>t.id===$("request-provider").value);
    $("request-context").title=`${folder ? "Works in "+folder.name : "A new folder on this computer"} · ${tool?.name || "Connect an AI to begin"}`;
    const auto=$("request-provider").value==='auto', team=auto ? (state.team_tools || []) : [tool?.id].filter(Boolean);
    const contextHtml=team.map(p=>RunquayUI.toolMark(p,'ambient')).join('')+`<span>${esc(auto?'Auto team':tool?.name || 'Choose an AI')}</span>`;
    if($('request-context')._html!==contextHtml){$('request-context').innerHTML=contextHtml;$('request-context')._html=contextHtml;}
    const signal=document.querySelector('.creation-signal');
    const signalHtml=team.map(p=>RunquayUI.toolMark(p,'ambient')).join('<span class="tool-link" aria-hidden="true">·</span>');
    if(signal._html!==signalHtml){signal.innerHTML=signalHtml;signal._html=signalHtml;}
    let preview=$('request-team-preview');
    if(!preview){preview=document.createElement('p');preview.id='request-team-preview';preview.className='request-team-preview';$('request-context').parentElement.after(preview);}
    preview.hidden=!auto;
    const names=team.map(p=>state.tools.find(t=>t.id===p)?.name || p);
    preview.textContent=team.length ? `Plan → Build: ${names[0]} · Review: ${names[1] || names[0]}. Project files and handoffs are shared with these tools. Charges always ask first.` : 'Connect a supported tool to assemble your team.';
    $("request-text").placeholder=folder ? `What’s next for ${folder.name}?` : "What are we making?";
  }
  function render(s) {
    if(!window.RunquayField && $("approvals").parentElement!==$("workspace-decisions")) $("workspace-decisions").append($("approvals"));
    if($("workspace-controls").parentElement!==$("workspace-extra")) $("workspace-extra").append($("workspace-controls"));
    if($("workspace-library").parentElement!==$("workspace-extra")) $("workspace-extra").append($("workspace-library"));
    const pending=s.decisions.some(d=>["pending","uncertain","redeeming"].includes(d.state));
    $("approvals").hidden=!pending;
    const profiles=s.profiles.filter(p=>p.enabled);
    const providers=[...new Set(profiles.map(p=>p.provider))].sort((a,b)=>Number(b==="codex")-Number(a==="codex"));
    // The displayed team is fixed into the request; changed membership requires a retry.
    syncSelect("request-provider",[...(s.team_tools?.length ? [['auto','Auto team · plan, build, review']] : []),...providers.map(p=>[p,s.tools.find(t=>t.id===p)?.name || p])]);
    if(!$("request-provider").value && providers.length) $("request-provider").value=providers.includes("codex") ? "codex" : providers[0];
    syncSelect("request-target",[["","New project"],...s.catalog.filter(p=>!p.is_supervisor && p.details.exists).map(p=>[p.id,p.name])]);
    // Do not rebuild focused picker choices during the dashboard's polling.
    if(!$("project-picker-dialog").open) updateProjectPicker();
    $("workspace-connect").hidden=profiles.length>0;
    $("request-send").disabled=sending || !profiles.length;
    updateContext();
    const query=$("workspace-search").value.trim().toLocaleLowerCase();
    const work=s.projects.map(p=>({kind:"work",item:p,time:Date.parse(s.runs.find(r=>r.project_id===p.id)?.started || p.created)||0,active:["running","attention"].includes(p.state) || p.state==="queued" && (s.running || p.run_requested)}));
    const history=(s.history_tasks || []).map(t=>({kind:"history",item:t,time:typeof t.updated_at==="number" ? t.updated_at*1000 : Date.parse(t.updated_at)||0,active:false}));
    const all=[...work,...history].filter(row=>!query || `${row.item.name || row.item.title} ${row.item.project_name || ""}`.toLocaleLowerCase().includes(query))
      .sort((a,b)=>Number(b.active)-Number(a.active) || b.time-a.time);
    replaceCards("everyday-list",all.length ? all.slice(0,limit).map(row=>row.kind==="work" ? workCard(row.item,s) : historyCard(row.item)).join("") :
      `<div class="workspace-empty"><span aria-hidden="true">✧</span><h3>${query ? "No matching work" : "Your next idea starts here"}</h3><p>${query ? "Try another name." : "Describe something above. Your progress and results will appear here."}</p></div>`);
    $("orbit-work-count").textContent=all.length ? String(all.length).padStart(2,"0") : "";
    $("workspace-more").hidden=expanded || all.length<=limit;
    $("work-library-more").hidden=!expanded || all.length<=limit;
    renderAttachment();
    if(flowDialog.open && activeWorkflow)showWorkflow(activeWorkflow);
  }
  function workCard(p,s) {
    const run=s.runs.find(r=>r.project_id===p.id && Date.parse(r.started)>=Date.parse(p.created));
    const status=RunquayUI.workStatus(p,s);
    const primary=p.state==='complete' ? `<button data-action="result" data-id="${p.id}" aria-label="View result" title="View result">↗</button>` :
      p.state==='attention' ? `<button data-action="resume" data-id="${p.id}" aria-label="Reply to your AI" title="Reply">↩</button>` :
      ['paused','cancelled'].includes(p.state) || p.state==='queued' && !s.running && !p.run_requested ? `<button data-work-start="${p.id}" aria-label="${p.state==='queued'?'Start':'Continue'}" title="${p.state==='queued'?'Start':'Continue'}">▷</button>` :
      status.label==='Connect your AI' ? '<a class="text-button" href="#accounts" aria-label="Connect your AI">↗</a>' :
      run ? `<button data-action="log" data-id="${run.id}" aria-label="See progress" title="See progress">↗</button>` : '';
    return `<article class="work-card" id="work-${p.id}" tabindex="-1"><div class="work-card-icon" role="img" aria-label="${esc(s.tools.find(t=>t.id===p.provider)?.name || p.provider)}">${RunquayUI.toolMark(p.provider,p.state==='running'?'working':'idle')}</div><div class="work-card-body"><h3 title="${esc(p.name)}">${esc(p.name)}</h3>${p.workflow?.phase?`<button class="workflow-trail" data-workflow="${p.id}">${esc(({plan:"Plan",build:"Build",review:"Review",repair:"Improve",done:"Finished"})[p.workflow.phase])} <span>· View handoffs ↗</span></button>`:""}${p.state==='attention' ? `<p class="work-question">${esc(p.checkpoint.question || p.note || 'Reply to continue.')}</p>` : ''}</div><span class="work-status ${esc(p.state)}" title="${esc(status.text)}">${esc(status.label)}</span><div class="work-card-actions">${primary}${p.state==='complete'?`<button data-action="resume" data-id="${p.id}" aria-label="Ask for a change" title="Ask for a change">✎</button>`:''}<details data-key="work-more-${p.id}" class="work-more"><summary aria-label="More actions for ${esc(p.name)}">···</summary><div>${p.state==='complete'?`<button class="text-button" data-action="resume" data-id="${p.id}">Ask for a change</button>`:''}${['running','queued'].includes(p.state)?`<button class="text-button" data-action="pause-project" data-id="${p.id}">Pause</button>`:''}${!['complete','cancelled'].includes(p.state)?`<button class="text-button" data-action="cancel-project" data-id="${p.id}">Stop this task</button>`:''}${run?`<button class="text-button" data-action="log" data-id="${run.id}">Conversation</button>`:''}<p>${esc(status.text)}</p><p>${esc(p.checkpoint.tests || 'No checks reported yet.')}</p>${p.note?`<p>${esc(p.note)}</p>`:''}<p>${esc(p.path)}</p></div></details></div></article>`;
  }
  const flowDialog=document.createElement('dialog');flowDialog.id='workflow-dialog';flowDialog.className='field-sheet';
  flowDialog.innerHTML='<div class="dialog-title"><h2>How your tools worked</h2><button type="button" class="icon" data-close="workflow-dialog" aria-label="Close workflow">×</button></div><div id="workflow-content"></div>';
  document.body.append(flowDialog);
  function showWorkflow(id) {
    const p=state.projects.find(p=>p.id===id);if(!p?.workflow?.phase)return;
    activeWorkflow=id;
    const f=p.workflow, name=provider=>state.tools.find(t=>t.id===provider)?.name || provider;
    const flowHtml=`<p>${esc(p.name)}</p><p class="workflow-team">${RunquayUI.toolMark(f.lead)}${esc(name(f.lead))} <span>→</span> ${RunquayUI.toolMark(f.reviewer)}${esc(name(f.reviewer))}</p><p>${esc(p.note || 'Your plan, build and review appear here as each step finishes.')}</p>`+
      (f.history || []).map(h=>`<section class="workflow-entry"><h3>${RunquayUI.toolMark(h.provider)}${esc(name(h.provider))} · ${esc(h.phase)}</h3>${RunquayUI.markdown(h.summary)}<details><summary>Checks and next steps</summary>${RunquayUI.markdown(h.tests)}${RunquayUI.markdown(h.next_step)}${RunquayUI.markdown(h.question)}</details></section>`).join('');
    if($('workflow-content')._html!==flowHtml){$('workflow-content').innerHTML=flowHtml;$('workflow-content')._html=flowHtml;}
    if(!flowDialog.open)flowDialog.showModal();
  }
  function historyCard(t) {
    return `<article class="work-card history-work" id="history-${esc(t.key)}" tabindex="-1"><div class="work-card-icon"><img src="${RunquayUI.toolIcon(t.provider)}" alt="${esc(t.tool || t.provider)}" width="24" height="24"></div><div class="work-card-body"><button class="history-title" data-work-history="${esc(t.key)}">${esc(t.title)}</button><p class="work-status-note">${esc(t.project_name || 'Saved conversation')} · ${esc(t.tool || t.provider)}</p></div><button class="text-button" data-work-history="${esc(t.key)}" aria-label="View ${esc(t.title)}" title="View saved preview">↗</button></article>`;
  }
  function openLibrary() {
    expanded=true;limit=Math.max(limit,30);
    $('work-library-content').append($('workspace-search').parentElement,$('everyday-list'));
    if(state)render(state);
    if(!$('work-library-dialog').open)$('work-library-dialog').showModal();
  }
  $('work-library-dialog').addEventListener('close',()=>{
    expanded=false;limit=4;
    document.querySelector('.recent-work>.section-title').append($('workspace-search').parentElement);
    $('work-surface-list').append($('everyday-list'));
    if(state)render(state);
  });
  function revealWork(id,kind='work') {
    location.hash='#projects';navigate('projects');
    const item=kind==='history'?state.history_tasks.find(t=>t.key===id):state.projects.find(p=>p.id===id);
    if(!item)return;
    $('workspace-search').value=item.name || item.title;openLibrary();
    document.getElementById((kind==='history'?'history-':'work-')+id)?.focus();
  }
  function renderAttachment() {
    const chip=$('request-learning-chip');chip.hidden=!attachedLearning;
    if(attachedLearning) {
      const html=`<span aria-hidden="true">✧</span><span>With: ${esc(attachedLearning.payload.title)}</span><button type="button" id="remove-request-learning" aria-label="Remove attached learning">×</button>`;
      if(chip._html!==html){chip.innerHTML=html;chip._html=html;}
    }else{chip.innerHTML='';chip._html='';}
  }
  function attachLearning(card) {
    attachedLearning=card;renderAttachment();focusRequest();
  }
  function focusRequest(catalogId="",text="") {
    location.hash="#projects";navigate("projects");
    $("request-target").value=catalogId;
    updateProjectPicker();
    if(text) $("request-text").value=text;
    updateContext();$("request-text").focus();$("everyday-work").scrollIntoView({block:"start"});
  }
  $("request-target").onchange=updateContext;$("request-provider").onchange=updateContext;
  $("workspace-search").oninput=()=>{limit=expanded?30:4;if(state) render(state);};
  $("workspace-more").onclick=openLibrary;
  $("work-library-more").onclick=()=>{limit+=30;render(state);};
  $("request-form").onsubmit=async event=>{
    event.preventDefault();if(sending || !state) return;
    const fields={text:$("request-text").value.trim(),catalog_id:$("request-target").value,provider:$("request-provider").value};
    if(!fields.text) return $("request-text").focus();
    if(fields.provider==='auto')fields.team_tools=state.team_tools;
    if(attachedLearning)fields.learning_ids=[attachedLearning.id];
    const signature=JSON.stringify(fields);
    if(retry?.signature!==signature) retry={signature,key:crypto.randomUUID()};
    sending=true;$("request-send").disabled=true;$("request-send").textContent="Sending…";$("request-error").hidden=true;
    try {
      const result=await api("/api/requests",{...fields,request_key:retry.key});
      retry=null;$("request-text").value="";$("workspace-search").value="";limit=expanded?30:4;attachedLearning=null;renderAttachment();
      $("request-receipt").hidden=false;$("request-receipt").textContent="Got it. We’ll take it from here. Progress appears below.";
      await refresh();$("work-"+result.id)?.focus({preventScroll:true});
    } catch(error) {$("request-error").hidden=false;$("request-error").textContent=error.message+" Your words are still here; you can try again.";}
    finally {sending=false;$("request-send").disabled=!state.profiles.some(p=>p.enabled);$("request-send").innerHTML='<span class="sr-only">Let’s do it</span><span aria-hidden="true">↑</span>';}
  };
  document.addEventListener("click",async event=>{
    const menu=event.target.closest('.work-more');
    if(menu && event.target.closest('button,a'))menu.open=false;
    document.querySelectorAll('.work-more[open],.request-options[open]').forEach(open=>{
      if(!open.contains(event.target))open.open=false;
    });
    if(event.target.closest("#remove-request-learning")){attachedLearning=null;renderAttachment();return;}
    const example=event.target.closest("[data-request-example]");if(example) focusRequest("",example.dataset.requestExample);
    const workflow=event.target.closest('[data-workflow]');if(workflow)showWorkflow(workflow.dataset.workflow);
    const start=event.target.closest("[data-work-start]");
    if(start) {
      const p=state.projects.find(p=>p.id===start.dataset.workStart);if(!p) return;
      start.disabled=true;
      await act("/api/project",{id:p.id,action:"resume",run_now:true,max_steps:Math.min(200,Math.max(p.max_steps,p.steps+10))});
      start.disabled=false;
    }
    const history=event.target.closest("[data-work-history]");
    if(history) {
      const t=state.history_tasks.find(t=>t.key===history.dataset.workHistory);if(!t) return;
      selectedHistory=t.key;$("saved-conversation-title").textContent=t.title;
      $("saved-conversation-preview").textContent=t.preview || "This tool has not saved a preview here.";
      $("saved-conversation-note").textContent=`Saved in ${t.tool || t.provider}. This is a local preview. Continue the original conversation in that tool.`;
      const folder=state.catalog.find(p=>p.id===t.catalog_id && !p.is_supervisor && p.details.exists);
      $("saved-conversation-work").hidden=!folder;$("saved-conversation-work").textContent="Work on "+(folder?.name || "this project");
      $("saved-conversation-dialog").showModal();
    }
  });
  document.addEventListener('keydown',event=>{
    if(event.key!=='Escape' || document.querySelector('dialog[open]'))return;
    const menu=document.querySelector('.work-more[open],.request-options[open]');
    if(menu){menu.open=false;menu.querySelector('summary')?.focus();}
  });
  $("saved-conversation-work").onclick=()=>{
    const t=state.history_tasks.find(t=>t.key===selectedHistory);if(!t) return;
    $("saved-conversation-dialog").close();focusRequest(t.catalog_id);
  };
  // Older entry points lead to the same composer rather than another wizard.
  $("home-new").onclick=()=>focusRequest();$("new-project").onclick=()=>focusRequest();
  $("home-existing").onclick=()=>{focusRequest();$("project-picker-trigger").click();};
  navigate(RunquayUI.pageFor(location.hash));
  return {render,navigate,focusRequest,revealWork,attachLearning};
})();
