"use strict";
window.RunquayLearnings = (() => {
  const get = id => document.getElementById(id);
  let current, sources=[], discovery={}, loaded=false, loading=false, busy=false, loadedAt=0;
  let selected=new Set(), preview=null, selectedCard='', manual=false, toolChosen=false;
  const savedCards=()=> (current?.learnings?.cards || []).filter(c=>c.state==='saved');
  function matches(s) {
    const q=get('learning-source-search').value.trim().toLocaleLowerCase();
    return (!q || `${s.title} ${s.project} ${s.summary}`.toLocaleLowerCase().includes(q)) &&
      (!get('learning-source-tool').value || s.provider===get('learning-source-tool').value);
  }
  function renderSources() {
    const visible=sources.filter(matches).slice(0,100);
    get('learning-source-count').textContent=manual ? `${selected.size} chosen by you` : 'Runquay will choose matching work';
    replaceCards('learning-source-list',visible.map(s=>`<div class="learning-source"><label class="check"><input type="checkbox" data-learning-source="${esc(s.id)}" ${selected.has(s.id)?'checked':''}><span><strong>${esc(s.title)}</strong><small>${esc(s.project)} · ${esc(s.tool)}</small></span></label><details data-key="source-${esc(s.id)}"><summary>Read summary</summary><p class="learning-copy">${esc(s.summary || 'Title only; no outcome recorded.')}</p></details></div>`).join('') || '<p class="hint">No matching work. Try another search.</p>');
    get('learning-source-note').textContent=loading ? 'Finding your local work…' : `${sources.length} summaries available. Showing up to 100 matches.`;
    get('learning-prepare').disabled=busy || loading || !loaded || !sources.length || !get('learning-provider').value || manual && !selected.size;
  }
  function renderDiscovery() {
    get('learning-connected').textContent=loading ? 'Finding local work…' : sources.length ? `${discovery.project_count} projects · ${discovery.tool_count} tools` : 'Your experience starts with your first completed task.';
    const groups=discovery.topics || [];
    replaceCards('learning-topic-suggestions',groups.map((t,index)=>{
      return `<button type="button" class="learning-topic-choice" data-learning-topic="${esc(t.topic)}" aria-label="Explore ${esc(t.topic)}, ${t.count} matching summaries"><span class="node-light" aria-hidden="true"></span><span class="node-title">${esc(t.topic)}</span><small>${t.count} related ${t.count===1?'summary':'summaries'}</small></button>`;
    }).join(''));
    get('learning-topics-label').hidden=!groups.length;
    get('field-total').textContent=loaded ? String(sources.length) : '—';
    get('field-unit').textContent=sources.length===1 ? 'work summary' : 'work summaries';
    const provider=get('learning-provider').value;
    const name=current?.tools.find(t=>t.id===provider)?.name;
    get('learning-auto-note').textContent=name ? `${name} · ${manual ? 'Your chosen context' : 'Automatic context'}` : 'Connect an AI to explore';
    get('learning-prepare').innerHTML=busy ? '<span class="send-thinking" aria-hidden="true">···</span>' : '<span aria-hidden="true">↑</span>';
    get('learning-prepare').setAttribute('aria-label',busy ? 'Finding matching work' : 'Find learnings');
  }
  async function loadSources() {
    if(loading || !current)return;
    loading=true; renderSources();renderDiscovery();
    try {
      discovery=await api('/api/learnings/sources');sources=discovery.sources;loaded=true;loadedAt=Date.now();
      selected=new Set([...selected].filter(id=>sources.some(s=>s.id===id)));
      if(!toolChosen && discovery.recommended_provider && [...get('learning-provider').options].some(o=>o.value===discovery.recommended_provider))get('learning-provider').value=discovery.recommended_provider;
      get('learning-error').textContent='';
    }catch(error){get('learning-error').textContent=error.message;}
    finally{loading=false;renderSources();renderDiscovery();}
  }
  function openInsight(id) {
    const card=current?.learnings?.cards.find(c=>c.id===id);if(!card)return;
    const p=card.payload;
    if(get('learning-library-dialog').open)get('learning-library-dialog').close();
    get('insight-content').innerHTML=`<p class="eyebrow">${card.state==='saved'?'KEPT BY YOU':'AI DRAFT · REVIEW BEFORE USE'}</p><h2 id="insight-title">${esc(p.title)}</h2><p class="insight-lesson">${esc(p.lesson)}</p><div class="learning-tags">${p.tags.map(t=>`<button class="learning-tag" type="button" data-learning-tag="${esc(t)}">${esc(t)}</button>`).join('')}</div><details class="insight-context"><summary>${card.sources.length} supporting ${card.sources.length===1?'summary':'summaries'} · explore context</summary><h3>Use this when</h3><p>${esc(p.apply_when)}</p><h3>What to watch for</h3><p>${esc(p.caveats)}</p><p class="hint">${p.confidence==='hypothesis'?'A hypothesis to test.':'From reported work; not independently verified.'}</p><ul>${card.sources.map(source=>`<li>${esc(source.title)}<small>${esc(source.project)} · ${esc(source.tool)}</small></li>`).join('')}</ul></details><div class="insight-actions"><button type="button" data-learning-action="use" data-id="${esc(card.id)}">Use this <span aria-hidden="true">↗</span></button>${card.state==='review'?`<button type="button" data-learning-action="approve" data-id="${esc(card.id)}">Keep</button>`:''}<details class="learning-card-menu"><summary aria-label="More insight actions">•••</summary><button type="button" data-learning-action="edit" data-id="${esc(card.id)}">Edit</button><button type="button" data-learning-action="dismiss" data-id="${esc(card.id)}">Hide</button></details></div>`;
    get('learning-insight-dialog').showModal();
  }
  function renderCards() {
    if(!current)return;
    const cards=current.learnings?.cards || [],query=get('learning-search').value.trim().toLocaleLowerCase(),tag=get('learning-tag').value,view=get('learning-view').value;
    const filtered=cards.filter(c=>(!tag || c.payload.tags.includes(tag)) && (!view || c.state===view) && (!query || `${c.payload.title} ${c.payload.lesson} ${c.payload.tags.join(' ')}`.toLocaleLowerCase().includes(query)));
    get('field-library-count').textContent=String(cards.length);
    get('learning-library-count').textContent=cards.length ? `${cards.filter(c=>c.state==='saved').length} kept · ${cards.filter(c=>c.state==='review').length} to explore` : 'The useful parts of your experience.';
    replaceCards('learning-card-list',filtered.length ? filtered.map(c=>{
      const p=c.payload;
      return `<article class="learning-index-row"><button type="button" class="learning-index-open" data-learning-open="${esc(c.id)}"><span class="learning-index-meta"><i class="${c.state==='saved'?'':'is-draft'}" aria-hidden="true"></i>${c.state==='saved'?'Kept by you':'AI draft'} · ${c.sources.length} ${c.sources.length===1?'source':'sources'}</span><h3>${esc(p.title)}</h3></button><div class="learning-index-bottom"><div class="learning-tags">${p.tags.map(t=>`<button class="learning-tag" type="button" data-learning-tag="${esc(t)}">${esc(t)}</button>`).join('')}</div><button type="button" class="text-button learning-index-arrow" data-learning-open="${esc(c.id)}" aria-label="Read ${esc(p.title)}">↗</button></div></article>`;
    }).join('') : `<div class="learning-empty"><span class="learning-empty-mark" aria-hidden="true">✧</span><h3>${cards.length?'No matching insight.':'Nothing here. Yet.'}</h3><p>${cards.length?'Try another topic.':'Explore a topic in your knowledge field. Useful lessons will land here.'}</p>${!cards.length?'<button type="button" class="text-button" data-learning-action="focus">Find a first connection ↗</button>':''}</div>`);
  }
  function renderBatches() {
    const batches=current.learnings?.batches || [],active=batches.filter(b=>['queued','running','attention','paused'].includes(b.state));
    const shown=active.length ? active : batches.slice(0,1);
    get('knowledge-stage').dataset.phase=active.some(b=>b.state==='running')?'running':'idle';
    replaceCards('learning-batches',shown.map(b=>{
      const paused=b.state==='paused' || b.state==='queued' && !b.run_now && !current.running;
      const label=paused?'Analysis paused':b.state==='running'?'Connecting the dots':b.state==='queued'?'Ready to analyze':b.state==='complete'?'Your learnings are ready':b.state==='cancelled'?'Analysis cancelled':'Needs your attention';
      const note=paused?'Continue just this analysis; your other paused tasks stay paused.':b.state==='queued' ? b.note || 'Waiting for the worker and an available account. No need to start other tasks.' : b.state==='running'?'Looking for patterns, useful checks and lessons worth keeping. You can leave this page.':b.summary || b.note;
      return `<article class="learning-batch"><span class="learning-progress-icon ${!paused && ['queued','running'].includes(b.state)?'is-working':''}" aria-hidden="true">${b.state==='complete'?'✓':'✧'}</span><div><strong>${esc(label)}</strong><p>${esc(b.topic)}</p><details><summary>Details</summary><small>${esc(note)} · ${b.source_count} summaries</small></details></div><div class="controls">${paused || b.state==='attention'?`<button class="secondary" data-learning-action="continue" data-id="${esc(b.id)}">Continue analysis</button>`:''}${['queued','running','attention','paused'].includes(b.state)?`<button class="text-button" data-learning-action="cancel" data-id="${esc(b.id)}">Cancel</button>`:''}</div></article>`;
    }).join(''));
  }
  function render(value) {
    current=value;
    const analyzers=value.tools.filter(t=>t.advisor && value.profiles.some(p=>p.provider===t.id && p.enabled));
    const options=analyzers.map(t=>`<option value="${esc(t.id)}">${esc(t.name)}</option>`).join('') || '<option value="">Connect an AI tool</option>';
    const select=get('learning-provider');
    if(select._options!==options){const prior=select.value;select.innerHTML=options;select._options=options;select.value=analyzers.some(t=>t.id===prior)?prior:analyzers.find(t=>t.id===RunquayUI.recommendedTool(value))?.id || analyzers[0]?.id || '';}
    get('learning-connect-note').hidden=Boolean(analyzers.length);
    const cards=value.learnings?.cards || [],allTags=[...new Set(cards.flatMap(c=>c.payload.tags))].sort();
    const old=get('learning-tag').value,tagOptions='<option value="">Every topic</option>'+allTags.map(t=>`<option value="${esc(t)}">${esc(t)}</option>`).join('');
    if(get('learning-tag')._options!==tagOptions){get('learning-tag').innerHTML=tagOptions;get('learning-tag')._options=tagOptions;get('learning-tag').value=allTags.includes(old)?old:'';}
    const picker=get('task-learning-ids'),picked=[...picker.querySelectorAll('input:checked')].map(o=>o.value);
    const savedOptions=savedCards().map(c=>`<label class="check"><input type="checkbox" name="learning_ids" value="${esc(c.id)}"><span>${esc(c.payload.tags[0])}: ${esc(c.payload.title)}</span></label>`).join('');
    if(picker._options!==savedOptions){picker.innerHTML=savedOptions;picker._options=savedOptions;for(const o of picker.querySelectorAll('input'))o.checked=picked.includes(o.value);}
    get('task-learning-empty').hidden=Boolean(savedCards().length);
    renderCards();renderBatches();renderSources();renderDiscovery();
    if(location.hash==='#learnings' && (!loaded || Date.now()-loadedAt>60000) && !loading && !get('learning-preview-dialog').open)void loadSources();
  }
  function showPreview(result) {
    preview={topic:result.topic,focus:result.focus,provider:result.provider,source_ids:result.sources.map(s=>s.id),digest:result.digest,request_key:crypto.randomUUID()};
    const name=current.tools.find(t=>t.id===result.provider)?.name || result.provider;
    get('learning-preview-label').textContent=`${result.sources.length} relevant summaries → ${name}`;
    get('learning-preview-topic').textContent=result.topic;
    get('learning-preview-focus').textContent=result.focus;
    get('learning-preview-focus').hidden=!result.focus;
    get('learning-preview-explainer').textContent=`${result.automatic?'Runquay found the matching work for you. ':'You chose this work. '}Check what will be sent. Remove any summary you prefer to keep private.`;
    get('learning-preview-sources').innerHTML=result.sources.map(s=>`<article class="learning-preview-source"><div><h3>${esc(s.title)}</h3><small>${esc(s.project)} · ${esc(s.tool)}</small></div><button type="button" class="text-button" data-exclude-source="${esc(s.id)}" aria-label="Exclude ${esc(s.title)}">Remove</button><p class="learning-copy">${esc(s.summary || 'Only the title is available. No result is recorded.')}</p></article>`).join('');
    get('learning-confirm').textContent=`Analyze with ${name}`;get('learning-confirm').disabled=false;
    get('learning-preview-error').textContent='';
    if(!get('learning-preview-dialog').open)get('learning-preview-dialog').showModal();
  }
  async function prepare() {
    if(busy)return;
    if(!get('learning-provider').value){location.hash='#accounts';return;}
    busy=true;get('learning-error').textContent='';renderSources();renderDiscovery();
    try {
      const data={topic:get('learning-topic').value.trim(),focus:get('learning-focus').value,provider:get('learning-provider').value};
      if(manual){if(!data.topic)data.topic='Patterns across my work';data.source_ids=[...selected];}
      const result=await api(manual?'/api/learnings/preview':'/api/learnings/recommend',data);
      showPreview(result);
    }catch(error){get('learning-error').textContent=error.message;}
    finally{busy=false;renderSources();renderDiscovery();}
  }
  get('learning-form').onsubmit=e=>{e.preventDefault();void prepare();};
  get('learning-topic').oninput=()=>{manual=false;selected.clear();renderSources();renderDiscovery();};
  get('learning-provider').onchange=()=>{toolChosen=true;renderSources();renderDiscovery();};
  get('learning-source-search').oninput=get('learning-source-tool').onchange=renderSources;
  get('learning-refresh-sources').onclick=()=>void loadSources();
  get('learning-select-shown').onclick=()=>{manual=true;for(const s of sources.filter(matches).slice(0,100)){if(selected.size>=100)break;selected.add(s.id);}renderSources();};
  get('learning-clear-sources').onclick=()=>{manual=false;selected.clear();renderSources();};
  get('learning-source-list').onchange=event=>{const id=event.target.dataset.learningSource;if(!id)return;if(event.target.checked && selected.size>=100){event.target.checked=false;return toast('Choose up to 100 summaries.');}manual=true;event.target.checked?selected.add(id):selected.delete(id);renderSources();};
  get('learning-search').oninput=get('learning-tag').onchange=get('learning-view').onchange=renderCards;
  get('learning-confirm').onclick=async()=>{
    if(!preview || busy)return;
    busy=true;get('learning-confirm').disabled=true;get('learning-preview-error').textContent='';
    try {await api('/api/learnings/collect',{...preview,acknowledged:true,run_now:true});get('learning-preview-dialog').close();await refresh();get('learning-batches').scrollIntoView({behavior:'smooth',block:'center'});toast('On it. Your learnings will appear here.');}
    catch(error){get('learning-preview-error').textContent=error.message;}
    finally{busy=false;get('learning-confirm').disabled=false;}
  };
  get('learning-preview-sources').onclick=async event=>{
    const button=event.target.closest('[data-exclude-source]');if(!button || busy)return;
    const ids=preview.source_ids.filter(id=>id!==button.dataset.excludeSource);
    if(!ids.length){get('learning-preview-error').textContent='Keep at least one summary, or go back to choose another topic.';return;}
    busy=true;get('learning-confirm').disabled=true;
    try{showPreview(await api('/api/learnings/preview',{...preview,source_ids:ids}));}
    catch(error){get('learning-preview-error').textContent=error.message;}
    finally{busy=false;get('learning-confirm').disabled=false;}
  };
  get('field-library-trigger').onclick=()=>get('learning-library-dialog').showModal();
  document.addEventListener('click',async event=>{
    const insight=event.target.closest('[data-learning-open]');if(insight){openInsight(insight.dataset.learningOpen);return;}
    const topic=event.target.closest('[data-learning-topic]');
    if(topic){get('learning-topic').value=topic.dataset.learningTopic;manual=false;selected.clear();renderSources();renderDiscovery();void prepare();return;}
    const tag=event.target.closest('[data-learning-tag]');if(tag){get('learning-tag').value=tag.dataset.learningTag;renderCards();if(get('learning-insight-dialog').open)get('learning-insight-dialog').close();if(!get('learning-library-dialog').open)get('learning-library-dialog').showModal();return;}
    const button=event.target.closest('[data-learning-action]');if(!button)return;
    const action=button.dataset.learningAction,id=button.dataset.id;
    if(action==='focus'){if(get('learning-library-dialog').open)get('learning-library-dialog').close();get('learning-topic').focus();get('learning-topic').scrollIntoView({behavior:'smooth',block:'center'});return;}
    if(action==='cancel')return void act('/api/project',{id,action:'cancel'});
    if(action==='continue')return void act('/api/learnings/run',{id});
    const card=current?.learnings?.cards.find(c=>c.id===id);if(!card)return;
    if(get('learning-insight-dialog').open)get('learning-insight-dialog').close();
    if(action==='edit'){selectedCard=id;const form=get('learning-edit-form');for(const key of ['title','lesson','apply_when','caveats'])form.elements[key].value=card.payload[key];form.elements.tags.value=card.payload.tags.join(', ');get('learning-edit-dialog').showModal();return;}
    button.disabled=true;
    try {
      if(action==='use'){
        if(card.state!=='saved'){await api('/api/learnings/review',{id,action:'approve'});await refresh();}
        window.RunquayWorkspace.attachLearning(card);
      }else{await api('/api/learnings/review',{id,action});await refresh();toast(action==='approve'?'Kept. Ready for your next task.':'Lesson hidden.');}
    }catch(error){toast(error.message);}finally{button.disabled=false;}
  });
  get('learning-edit-form').onsubmit=async event=>{
    event.preventDefault();const data=Object.fromEntries(new FormData(event.target)),button=event.target.querySelector('[type="submit"]');button.disabled=true;
    try{await api('/api/learnings/review',{...data,id:selectedCard,action:'edit',tags:data.tags.split(',').map(t=>t.trim()).filter(Boolean)});get('learning-edit-dialog').close();await refresh();toast('Updated. Check the lesson before using it.');}
    catch(error){toast(error.message);}finally{button.disabled=false;}
  };
  window.addEventListener('hashchange',()=>{if(location.hash==='#learnings' && current && !loaded)void loadSources();});
  return {render,openInsight};
})();
