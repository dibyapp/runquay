"use strict";
// Opt-in source review and a local library of user-reviewed lessons.
window.RunquayLearnings = (() => {
  const get = id => document.getElementById(id);
  let current, sources = [], loaded = false, loading = false, selected = new Set(), preview, selectedCard, initialized=false;
  const text = value => String(value ?? "");
  function matches(source) {
    const query = get("learning-source-search").value.trim().toLocaleLowerCase();
    return (!query || `${source.title} ${source.project} ${source.summary}`.toLocaleLowerCase().includes(query)) &&
      (!get("learning-source-tool").value || source.provider === get("learning-source-tool").value);
  }
  function renderSources() {
    const visible = sources.filter(matches).slice(0,100);
    get("learning-source-count").textContent = `${selected.size} selected · ${sources.length} available`;
    replaceCards("learning-source-list", visible.length ? visible.map(s => `<div class="learning-source"><label class="check"><input type="checkbox" data-learning-source="${esc(s.id)}" ${selected.has(s.id) ? "checked" : ""}><span><strong>${esc(s.title || "Untitled work")}</strong><small>${esc(s.project)} · ${esc(s.tool)} · ${esc(s.kind)}</small></span></label><details data-key="learning-source-${esc(s.id)}"><summary>Read source summary</summary><p class="learning-copy">${esc(s.summary || "No summary available; title only.")}</p></details></div>`).join("") : '<p class="hint">No matching work found. Refresh task history in Tasks, or import another tool’s history there.</p>');
    get("learning-source-note").textContent = loading ? "Loading local summaries…" : sources.filter(matches).length > 100 ? "Showing the first 100 matches. Narrow the search to find more." : "Only selected summaries are included. Full native conversations and raw logs are not read.";
    get("learning-prepare").disabled = !selected.size || !get("learning-provider").value || loading;
  }
  async function loadSources() {
    if (loading || !current) return;
    loading = true; renderSources();
    try {
      sources = (await api("/api/learnings/sources")).sources;
      selected = new Set([...selected].filter(id => sources.some(s=>s.id===id)));
      loaded = true;
    } catch(error) { toast(error.message); }
    finally { loading=false; renderSources(); }
  }
  function renderCards() {
    if (!current) return;
    const cards = current.learnings?.cards || [], query = get("learning-search").value.trim().toLocaleLowerCase(), tag = get("learning-tag").value, view = get("learning-view").value;
    const filtered = cards.filter(c=>(!tag || c.payload.tags.includes(tag)) && (!view || c.state===view) &&
      (!query || `${c.payload.title} ${c.payload.lesson} ${c.payload.tags.join(" ")}`.toLocaleLowerCase().includes(query)));
    get("learning-library-count").textContent = `${cards.filter(c=>c.state==="saved").length} saved · ${cards.filter(c=>c.state==="review").length} to review`;
    replaceCards("learning-card-list", filtered.length ? filtered.map(c => {
      const p=c.payload;
      return `<article class="learning-card panel"><div class="project-top"><h3>${esc(p.title)}</h3><span class="badge ${c.state==="saved" ? "complete" : "attention"}">${c.state==="saved" ? "Saved by you" : "Review AI suggestion"}</span></div><div class="learning-tags">${p.tags.map(t=>`<button class="learning-tag" type="button" data-learning-tag="${esc(t)}">#${esc(t)}</button>`).join("")}</div><p class="learning-copy">${esc(p.lesson)}</p><details data-key="learning-${esc(c.id)}"><summary>When to use it, caveats and sources</summary><h4>Use when</h4><p class="learning-copy">${esc(p.apply_when)}</p><h4>Keep in mind</h4><p class="learning-copy">${esc(p.caveats)}</p><p class="hint">${p.confidence==="hypothesis" ? "AI hypothesis — needs testing." : "Based on reported work — not independently verified."}</p><h4>Source work</h4><ul>${c.sources.map(s=>`<li>${esc(s.title)}<small>${esc(s.project)} · ${esc(s.tool)} · ${esc(s.kind)}</small></li>`).join("")}</ul></details><div class="controls">${c.state==="review" ? `<button data-learning-action="approve" data-id="${esc(c.id)}">Save learning</button>` : `<button data-learning-action="use" data-id="${esc(c.id)}">Use in a new task</button>`}<button class="secondary" data-learning-action="edit" data-id="${esc(c.id)}">Edit</button><button class="text-button" data-learning-action="dismiss" data-id="${esc(c.id)}">Dismiss</button></div></article>`;
    }).join("") : empty(cards.length ? "No matching learnings" : "Your experience becomes reusable here", cards.length ? "Try another tag, search or review filter." : "Collect lessons from past work, review what the AI suggests, then use saved lessons in future tasks."));
  }
  function render(value) {
    current=value;
    const analyzers=(value.tools || []).filter(t=>t.advisor && value.profiles.some(p=>p.provider===t.id && p.enabled));
    const options=analyzers.map(t=>`<option value="${esc(t.id)}">${esc(t.name)}</option>`).join("") || '<option value="">Connect an analysis tool first</option>';
    if(get("learning-provider")._options!==options) {
      const previous=get("learning-provider").value;
      get("learning-provider").innerHTML=options;get("learning-provider")._options=options;
      get("learning-provider").value=analyzers.some(t=>t.id===previous) ? previous : analyzers.find(t=>t.id===RunquayUI.recommendedTool(value))?.id || analyzers[0]?.id || "";
    }
    get("learning-connect-note").hidden=Boolean(analyzers.length);
    const cards=value.learnings?.cards || [], allTags=[...new Set(cards.flatMap(c=>c.payload.tags))].sort();
    if(!initialized) {get('learning-collector').open=!cards.length;initialized=true;}
    const old=get("learning-tag").value, tagOptions='<option value="">All topics</option>'+allTags.map(t=>`<option value="${esc(t)}">${esc(t)}</option>`).join("");
    if(get("learning-tag")._options!==tagOptions) {get("learning-tag").innerHTML=tagOptions;get("learning-tag")._options=tagOptions;get("learning-tag").value=allTags.includes(old) ? old : "";}
    replaceCards("learning-batches", (value.learnings?.batches || []).map(b=>`<article class="learning-batch"><div><strong>${esc(b.topic)}</strong> ${badge(b.state)}<p class="hint">${esc(b.source_count)} sources · ${esc(value.tools.find(t=>t.id===b.provider)?.name || b.provider)} · ${esc(when(b.created))}</p><p>${esc(b.summary || b.note || (b.state==="queued" ? value.running ? "Waiting for the worker, account checks or approval." : "Saved. Start work when ready; this also runs other queued tasks." : "Analyzing the reviewed summaries…"))}</p></div><div class="controls">${b.state==="queued" && !value.running ? '<button data-learning-action="start">Start queued work</button>' : ""}${["queued","running","attention","paused"].includes(b.state) ? `<button class="text-button" data-learning-action="cancel" data-id="${esc(b.id)}">Cancel analysis</button>` : ""}</div></article>`).join(""));
    const picker=get("task-learning-ids"), picked=[...picker.querySelectorAll("input:checked")].map(o=>o.value);
    const saved=cards.filter(c=>c.state==="saved"), savedOptions=saved.map(c=>`<label class="check"><input type="checkbox" name="learning_ids" value="${esc(c.id)}"><span>${esc(c.payload.tags[0])}: ${esc(c.payload.title)}</span></label>`).join("");
    if(picker._options!==savedOptions) {picker.innerHTML=savedOptions;picker._options=savedOptions;for(const o of picker.querySelectorAll("input"))o.checked=picked.includes(o.value);}
    get("task-learning-empty").hidden=Boolean(saved.length);
    renderCards(); renderSources();
    if(location.hash==="#learnings" && !loaded && !loading) void loadSources();
  }
  get("learning-source-search").oninput=renderSources;
  get("learning-source-tool").onchange=get("learning-provider").onchange=renderSources;
  get("learning-refresh-sources").onclick=()=>void loadSources();
  get("learning-select-shown").onclick=()=>{for(const s of sources.filter(matches).slice(0,100)) {if(selected.size>=100)break;selected.add(s.id);}renderSources();};
  get("learning-clear-sources").onclick=()=>{selected.clear();renderSources();};
  get("learning-source-list").onchange=event=>{const id=event.target.dataset.learningSource;if(!id)return;if(event.target.checked && selected.size>=100){event.target.checked=false;return toast("Choose up to 100 sources per collection.");}event.target.checked ? selected.add(id) : selected.delete(id);get("learning-source-list")._rendered=get("learning-source-list").innerHTML;get("learning-source-count").textContent=`${selected.size} selected · ${sources.length} available`;get("learning-prepare").disabled=!selected.size || !get("learning-provider").value;};
  get("learning-search").oninput=get("learning-tag").onchange=get("learning-view").onchange=renderCards;
  get("learning-form").onsubmit=async event=>{
    event.preventDefault();const button=get("learning-prepare");button.disabled=true;
    try {
      const input={topic:get("learning-topic").value,focus:get("learning-focus").value,provider:get("learning-provider").value,source_ids:[...selected]};
      const result=await api("/api/learnings/preview",input);
      preview={...input,digest:result.digest,request_key:crypto.randomUUID()};
      get("learning-preview-label").textContent=`${result.sources.length} selected summaries will go to ${current.tools.find(t=>t.id===input.provider)?.name || input.provider}. Topic: ${result.topic}. Nothing has been sent yet.`;
      get("learning-preview-data").textContent=JSON.stringify({topic:result.topic,focus:result.focus,provider:result.provider,sources:result.sources},null,2);
      get("learning-send-ack").checked=false;get("learning-confirm").disabled=true;
      get("learning-preview-dialog").showModal();
    } catch(error) {toast(error.message);} finally {button.disabled=false;}
  };
  get("learning-send-ack").onchange=event=>get("learning-confirm").disabled=!event.target.checked;
  get("learning-confirm").onclick=async()=>{
    if(!preview || !get("learning-send-ack").checked)return;
    const button=get("learning-confirm");button.disabled=true;
    try {await api("/api/learnings/collect",{...preview,acknowledged:true});get("learning-preview-dialog").close();get('learning-collector').open=false;toast("Collection queued. Lessons will appear here for your review.");await refresh();}
    catch(error){toast(error.message);}finally{button.disabled=false;}
  };
  document.addEventListener("click",async event=>{
    const tag=event.target.closest("[data-learning-tag]");if(tag){get("learning-tag").value=tag.dataset.learningTag;renderCards();return;}
    const button=event.target.closest("[data-learning-action]");if(!button)return;
    const action=button.dataset.learningAction,id=button.dataset.id,card=current?.learnings?.cards.find(c=>c.id===id);
    if(action==="start")return void act("/api/control",{action:"start"});
    if(action==="cancel")return void act("/api/project",{id,action:"cancel"});
    if(!card)return;
    if(action==="use") {showProjectForm();for(const o of get("task-learning-ids").querySelectorAll("input"))o.checked=o.value===id;get("task-learning-details").open=true;return;}
    if(action==="edit") {
      selectedCard=id;const form=get("learning-edit-form");for(const key of ["title","lesson","apply_when","caveats"])form.elements[key].value=card.payload[key];form.elements.tags.value=card.payload.tags.join(", ");get("learning-edit-dialog").showModal();return;
    }
    button.disabled=true;try{await api("/api/learnings/review",{id,action});await refresh();toast(action==="approve" ? "Learning saved. Choose it when creating a task." : "Learning dismissed.");}catch(error){toast(error.message);}finally{button.disabled=false;}
  });
  get("learning-edit-form").onsubmit=async event=>{
    event.preventDefault();const data=Object.fromEntries(new FormData(event.target)),button=event.target.querySelector('[type="submit"]');button.disabled=true;
    try {await api("/api/learnings/review",{...data,id:selectedCard,action:"edit",tags:data.tags.split(",").map(t=>t.trim()).filter(Boolean)});get("learning-edit-dialog").close();await refresh();toast("Changes saved for review. Select Save learning when ready.");}
    catch(error){toast(error.message);}finally{button.disabled=false;}
  };
  window.addEventListener("hashchange",()=>{if(location.hash==="#learnings" && current && !loaded)void loadSources();});
  return {render};
})();
