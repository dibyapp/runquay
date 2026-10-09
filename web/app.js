"use strict";
let state, token, resetDecision, activeLog, pollPromise = null, previousPending = new Set();
let taskFilter = "active";
let ideaFilter = "all", catalogSignature = "", ideaSignature = "";
const $ = id => document.getElementById(id);
const esc = text => String(text ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const badge = text => `<span class="badge ${esc(text)}">${esc(RunquayUI.label(text))}</span>`;
const when = value => value ? new Date(typeof value === "number" ? value * 1000 : value).toLocaleString(undefined, {dateStyle:"medium",timeStyle:"short"}) : "Not yet";
const empty = (title, sub) => `<div class="empty"><b>${esc(title)}</b><p>${esc(sub)}</p></div>`;
function toast(message) { $("toast").textContent = message; $("toast").style.display = "block"; clearTimeout(toast.timer); toast.timer = setTimeout(() => $("toast").style.display = "none", 6000); }
async function api(path, data) {
  const response = await fetch(path, data === undefined ? {} : {method:"POST",headers:{"Content-Type":"application/json","X-AutoWork-CSRF":token},body:JSON.stringify(data)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Request failed");
  return result;
}
async function act(path, data) { try { await api(path, data); await refresh(); return true; } catch(error) { toast(error.message); return false; } }
function meter(window, label) {
  if (!window || typeof window.usedPercent !== "number") return `<div class="meter-label"><span>${label}</span><span>Unknown</span></div><div class="meter"></div>`;
  const used = Math.max(0, Math.min(100, window.usedPercent));
  return `<div class="meter-label"><span>${label} · ${used}% used</span><span>${100-used}% left</span></div><progress class="meter" max="100" value="${used}" aria-label="${label} usage"></progress><div class="account-check">Refreshes ${esc(when(window.resetsAt))}</div>`;
}
function showProjectForm(catalogId = "", suggestionId = "") {
  if (!state) return toast("Wait for the local app to connect.");
  const form = $("project-form"); form.reset();
  form.querySelectorAll("details").forEach(d => d.open = false);
  const suggestion = state.suggestions?.find(s => s.id === suggestionId);
  const payload = suggestion?.payload;
  const selected = state.catalog?.find(p => p.id === (payload?.catalog_id || catalogId));
  form.elements.catalog_id.value = selected?.id || "";
  form.elements.suggestion_id.value = suggestionId;
  form.elements.name.value = payload?.title || selected?.name || "";
  form.elements.goal.value = payload ? `${payload.goal}\n\nFirst step: ${payload.first_milestone}\n\nProject evidence: ${payload.evidence}` : "";
  form.elements.provider.value = payload?.provider || state.advisor_provider || "codex";
  $("project-dialog-title").textContent = suggestion ? "Review this idea" : selected ? "Add a task to " + selected.name : "New task";
  $("project-workspace").textContent = selected ? "Uses your existing " + selected.name + " folder. Files stay in place." : "Creates a separate folder for this project.";
  $("project-submit-note").textContent = state.running ? "Work can start after you add this task. Publishing and purchases need separate action." : "Saved tasks wait until you choose Start work. Publishing and purchases need separate action.";
  $("project-dialog").showModal();
}
function replaceCards(id, html) {
  const container = $(id);
  if (container._rendered === html) return;
  const opened = new Set([...container.querySelectorAll("details[open][data-key]")].map(d => d.dataset.key));
  container.innerHTML = html; container._rendered = html;
  container.querySelectorAll("details[data-key]").forEach(d => d.open = opened.has(d.dataset.key));
}
function setTaskFilter(filter) {
  taskFilter = filter;
  document.querySelectorAll("[data-task-filter]").forEach(b => {const active = b.dataset.taskFilter === filter; b.classList.toggle("active",active); b.setAttribute("aria-pressed",String(active));});
  if (state) renderTasks();
}
function renderTasks() {
  const tasks = RunquayUI.visibleTasks(state.projects,taskFilter);
  const emptyTitle = taskFilter === "finished" ? "No finished tasks yet" : taskFilter === "active" ? "Nothing is waiting" : "Your first task starts here";
  const emptyText = taskFilter === "finished" ? "Completed and cancelled tasks will appear here." : "Create a new task, or pick an existing project below.";
  replaceCards("project-list", tasks.length ? tasks.map(p => {
    const run = state.runs.find(r => r.project_id === p.id);
    const explanation = p.state === "queued" ? state.running ? "Waiting for the worker, an available account, or your approval." : "Saved. Start work from Home when you are ready." : p.state === "complete" ? "Review the files and checks before accepting the result." : p.state === "paused" ? "Your files are saved. Continue when you are ready." : "";
    return `<article class="project"><div class="project-top"><h3>${esc(p.name)}</h3>${badge(p.state)}</div>${p.checkpoint.summary ? `<div class="project-detail">${esc(p.checkpoint.summary)}</div>` : `<p>${esc(p.goal.slice(0,180))}${p.goal.length > 180 ? "…" : ""}</p>`}${explanation ? `<p class="task-explanation">${esc(explanation)}</p>` : ""}${p.note && !/^none\.?$/i.test(p.note.trim()) ? `<p class="project-detail">${esc(p.note)}</p>` : ""}<details data-key="task-${p.id}"><summary>Task details and checks</summary><p class="project-goal">${esc(p.goal)}</p>${p.checkpoint.tests ? `<p>Checks: ${esc(p.checkpoint.tests)}</p>` : ""}<div class="project-meta"><span>${p.steps} / ${p.max_steps} steps</span><span>${esc(state.tools.find(t=>t.id===p.provider)?.name || "Codex")}</span><span>${esc(p.model || "Default model")}</span><span>${esc(p.path)}</span></div></details><div class="project-actions">${p.state === "complete" ? `<button data-action="result" data-id="${p.id}">See what was made</button>` : ""}${["paused","attention","complete","cancelled"].includes(p.state) ? `<button class="secondary" data-action="resume" data-id="${p.id}">${p.state === "complete" ? "Add follow-up" : "Continue"}</button>` : ""}${["running","queued"].includes(p.state) ? `<button class="secondary" data-action="pause-project" data-id="${p.id}">Pause task</button>` : ""}${run ? `<button class="text-button" data-action="log" data-id="${run.id}">View output</button>` : ""}${!["cancelled","complete"].includes(p.state) ? `<button class="text-button" data-action="cancel-project" data-id="${p.id}">Cancel task</button>` : ""}</div></article>`;
  }).join("") : empty(emptyTitle,emptyText) + (taskFilter === "active" && state.projects.some(p=>["complete","cancelled"].includes(p.state)) ? '<div class="controls"><button class="text-button" data-show-finished>View finished tasks</button></div>' : ""));
}
function renderNextStep() {
  const next = RunquayUI.nextStep(state);
  replaceCards("next-step", `<h2>${esc(next.title)}</h2><p>${esc(next.text)}</p>${next.href ? `<a class="button" href="${next.href}">${esc(next.label)}</a>` : `<button data-next-action="${next.action}">${esc(next.label)}</button>`}`);
}

function renderBrain() {
  const library = state.catalog || [];
  $("project-count").textContent = library.length;
  $("queue-count").textContent = state.projects.length;
  $("catalog-error").textContent = state.catalog_error || "Saved Codex folders refresh automatically. You can connect folders from any tool.";
  const signature = JSON.stringify(library);
  if (catalogSignature !== signature) {
    catalogSignature = signature;
    replaceCards("catalog-list",library.length ? library.map(p=>`<article class="catalog-card"><div class="project-top"><h3>${esc(p.name)}</h3>${p.is_supervisor ? badge("app") : !p.details.exists ? badge("missing") : ""}</div><details data-key="folder-${p.id}"><summary>Folder details</summary><div class="catalog-path">${esc(p.path)}</div><div class="catalog-files">${esc(p.details.files.slice(0,7).join(" · ") || "No files found")}</div></details><div class="controls"><button class="secondary" data-action="work-existing" data-id="${esc(p.id)}" ${p.is_supervisor || !p.details.exists ? "disabled" : ""}>${p.is_supervisor ? "This app" : "Add task"}</button><button class="text-button" data-action="advise-project" data-id="${esc(p.id)}">Find ideas</button></div></article>`).join("") : empty("Connect an existing project","Choose Connect folder above to add a project you already have."));
    const selected = $("advisor-target").value;
    $("advisor-target").innerHTML = '<option value="">All my projects</option>' + library.map(p=>`<option value="${esc(p.id)}">${esc(p.name)}</option>`).join("");
    if(library.some(p=>p.id===selected)) $("advisor-target").value = selected;
  }
  const advisor = state.advisor;
  const busy = advisor && ["queued","running"].includes(advisor.state);
  $("advisor-status").textContent = advisor?.state === "running" ? "Finding ideas" : advisor?.state === "queued" ? "Waiting" : advisor?.state === "attention" ? "Needs you" : state.advisor_completed ? "Ideas ready" : "Ready";
  $("advisor-status").className = "badge " + (advisor?.state || "ready");
  $("generate-ideas").disabled = Boolean(busy);
  $("generate-ideas").textContent = advisor?.state === "running" ? "Finding ideas…" : advisor?.state === "queued" ? "Request saved" : "Get ideas";
  $("advisor-start").hidden = !(advisor?.state === "queued" && !state.running);
  $("advisor-detail").textContent = busy ? advisor.state === "running" ? "Reading the selected project context. You can keep using the app." : state.running ? "Your request will run when the worker and an account are available." : "Your request is saved. Start work below to get your ideas." : advisor?.state === "attention" ? advisor.note : state.advisor_summary || "Choose a project and ask for useful next steps.";
  const ideas = RunquayUI.visibleIdeas(state.suggestions || [],ideaFilter,$("advisor-target").value);
  replaceCards("suggestion-list",ideas.length ? ideas.map(s=>{const p=s.payload; const target=library.find(c=>c.id===p.catalog_id);return `<article class="suggestion"><div class="idea-meta">${badge(p.kind === "new" ? "New project" : "Improvement")}<span>${esc(target?.name || "New project")}</span><span>${esc(p.effort)}</span></div><h3>${esc(p.title)}</h3><p>${esc(p.why)}</p><div class="first-step">First step: ${esc(p.first_milestone)}</div><details data-key="idea-${s.id}"><summary>Why this idea?</summary><p>${esc(p.evidence)}</p><p>${esc(p.goal)}</p></details><div class="controls"><button data-action="review-suggestion" data-id="${s.id}">Review idea</button><button class="text-button" data-action="dismiss-suggestion" data-id="${s.id}">Dismiss</button></div></article>`;}).join("") : empty(busy ? "Your ideas are on the way" : "No ideas in this view",busy ? "The AI is preparing suggestions from the selected context." : "Choose a project and select Get ideas above."));
}
function render() {
  const running = state.projects.find(p=>p.state === "running");
  const advising = state.advisor?.state === "running";
  $("status").textContent = !state.running ? "Paused" : running ? "Working" : advising ? "Planning" : "Ready";
  $("status-detail").textContent = running ? running.name : advising ? "Finding your next task" : state.running ? "Ready for your next task" : "Work is paused";
  $("pause").hidden = !state.running;
  $("start").hidden = state.running;
  $("queued").textContent = state.projects.filter(p=>p.state === "queued").length;
  $("ready").innerHTML = `${state.profiles.filter(p=>p.eligible && p.enabled).length} <em>/ ${state.profiles.length}</em>`;
  $("completed").textContent = state.projects.filter(p=>p.state === "complete").length;
  renderBrain(); renderTasks(); renderNextStep();
  if(typeof beginnerNote === "function") beginnerNote();
  if (typeof renderSetup === "function") renderSetup();
  $("connection").innerHTML = '<span class="dot"></span> Connected';
  $("binary").textContent = "Codex executable: " + (state.binary || "Not found");
  replaceCards("account-list",state.profiles.length ? state.profiles.map(p=>{
    const account=p.snapshot.account || {}, limits=p.snapshot.limits || {};
    const bucket=(limits.rateLimitsByLimitId || {}).codex || limits.rateLimits || {};
    const tool=state.tools.find(t=>t.id===p.provider)?.name || "Codex";
    const status=!p.enabled ? "Disabled" : p.eligible ? "Ready" : p.provider !== "codex" ? "Approval needed per run" : account.type !== "chatgpt" ? "Sign-in needed" : "Waiting for allowance";
    return `<article class="account"><div class="account-head"><h3>${esc(p.name)}</h3>${badge(status)}</div><p>${esc(tool)}${account.planType ? " · " + esc(account.planType) : ""}</p><p class="account-reason">${esc(p.reason)}</p><div class="account-actions"><button class="secondary" data-action="login-guide" data-id="${p.id}">${p.eligible ? "Connection details" : "How to sign in"}</button></div><details class="account-details" data-key="account-${p.id}"><summary>Usage and account options</summary>${p.provider === "codex" ? meter(bucket.primary,"Short usage window") + meter(bucket.secondary,"Long usage window") : '<p>Installation, authentication and billing need a vendor account check before approving a run.</p>'}<p class="account-check">Earned resets: ${limits.rateLimitResetCredits?.availableCount ?? "unknown"} · Checked ${esc(when(p.checked))}</p><div class="controls"><button class="text-button" data-action="toggle" data-id="${p.id}">${p.enabled ? "Disable account" : "Enable account"}</button><button class="text-button" data-action="remove-profile" data-id="${p.id}">Remove connection</button></div></details></article>`;
  }).join("") : empty("Connect your first account","Choose Add account. Sign in through the official AI tool; Runquay does not ask for your password."));
  const decisions=state.decisions.filter(d=>["pending","uncertain","redeeming"].includes(d.state));
  $("approval-count").textContent=decisions.length || "";
  document.title=(decisions.length ? `(${decisions.length}) Your decision needed · ` : running ? "Working · " : "") + "Runquay";
  replaceCards("decision-list",decisions.length ? decisions.map(d=>{
    const profile=state.profiles.find(p=>p.id===d.profile_id);
    if(d.kind === "external_run") {const payload=JSON.parse(d.payload);return `<div class="decision"><h3>Allow one run with ${esc(profile?.name || "this tool")}?</h3><p>${esc(payload.project)} · ${esc(payload.provider)}</p><p>This tool's billing is unverified. Review your vendor account before continuing.</p><div class="controls"><button class="secondary" data-action="decline-reset" data-id="${d.id}">Decline run</button><button data-action="review-external" data-id="${d.id}">Review request</button></div></div>`;}
    return `<div class="decision"><h3>${esc(profile?.name || "This account")} · use one earned reset?</h3><p>${d.state === "uncertain" ? "The previous result is uncertain. A retry uses the same request ID to avoid a second redemption." : "Keep waiting for allowance to refresh, or choose to redeem an existing reset."}</p><div class="controls"><button class="secondary" data-action="decline-reset" data-id="${d.id}">Wait for refresh</button><button data-action="review-reset" data-id="${d.id}" ${d.state === "redeeming" ? "disabled" : ""}>Review reset</button></div></div>`;
  }).join("") : '<p class="hint">Nothing needs your approval right now.</p>');
  for(const d of decisions) if(!previousPending.has(d.id) && window.Notification && Notification.permission === "granted") new Notification("Runquay: your decision is needed",{body:"Open Home to review a tool run or earned reset. You can keep waiting."});
  previousPending=new Set(decisions.map(d=>d.id));
  replaceCards("run-list",state.runs.length ? state.runs.map(r=>`<div class="activity-row"><div class="row-content">${esc(state.projects.find(p=>p.id===r.project_id)?.name || (r.project_id.startsWith("advisor-") ? "Project ideas" : r.project_id))} ${badge(r.state)}<small>${esc(when(r.started))}</small></div><button class="text-button" data-action="log" data-id="${r.id}">View output</button></div>`).join("") : '<p class="hint">Your runs will appear here.</p>');
  replaceCards("event-list",state.events.map(e=>`<div class="activity-row"><div class="row-content">${esc(e.message)}<small>${esc(when(e.at))}</small></div></div>`).join(""));
  if(!$("settings-form").contains(document.activeElement)) for(const key of ["quota_ceiling","turn_minutes","keep_awake","advisor_auto","advisor_hours"]) {const input=$("settings-form").elements[key]; input[input.type === "checkbox" ? "checked" : "value"]=state[key];}
}
function refresh(force=false) {
  if(pollPromise) return force ? pollPromise.then(()=>refresh(true)) : pollPromise;
  pollPromise=(async()=>{
    try { state = await api("/api/state"); token = state.csrf; render(); if(activeLog && $("log-dialog").open) await loadLog(activeLog); }
    catch(error) { $("connection").textContent = "Disconnected · refresh to reconnect"; }
  })().finally(()=>{pollPromise=null;});
  return pollPromise;
}
async function loadLog(id) {
  const data = await api("/api/run/" + id);
  $("log-meta").textContent = `${data.run.state} · ${when(data.run.started)} · ${data.run.profile_id}`;
  const log = $("log-content");
  const atBottom = log.scrollHeight - log.scrollTop - log.clientHeight < 80;
  log.textContent = data.log;
  if(atBottom) log.scrollTop = log.scrollHeight;
}
$("start").onclick = () => act("/api/control", {action:"start"});
$("pause").onclick = () => act("/api/control", {action:"pause"});
$("refresh").onclick = async () => { if(await act("/api/accounts/refresh", {})) toast("Checking accounts…"); };
$("new-project").onclick = () => showProjectForm();
$("home-new").onclick = () => showProjectForm();
$("home-existing").onclick = () => {$("project-library").open = true; location.hash = "#projects";};
$("advisor-start").onclick = () => act("/api/control",{action:"start"});
$("sync-projects").onclick = async () => { if(await act("/api/catalog/refresh", {})) toast("Saved projects refreshed"); };
$("advisor-target").onchange = () => { if(state) renderBrain(); };
$("advisor-form").onsubmit = async event => { event.preventDefault(); const data = Object.fromEntries(new FormData(event.target)); await act("/api/advisor", data); };
$("project-form").onsubmit = async event => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.target));
  try { await api(data.suggestion_id ? "/api/suggestion" : "/api/projects", data.suggestion_id ? {...data,id:data.suggestion_id,action:"start"} : data); $("project-dialog").close(); event.target.reset(); toast(state.running ? "Task added. Work can start when an account is available." : "Task saved. Choose Start work on Home when ready."); setTaskFilter("active"); location.hash="#projects"; await refresh(); } catch(error) { toast(error.message); }
};
$("resume-form").onsubmit = async event => { event.preventDefault(); const data = Object.fromEntries(new FormData(event.target)); try { await api("/api/project", {...data,action:"resume"}); $("resume-dialog").close(); setTaskFilter("active"); await refresh(); } catch(error) { toast(error.message); } };
$("settings-form").onsubmit = async event => {event.preventDefault(); const data = Object.fromEntries(new FormData(event.target)); if(await act("/api/settings", {...data, keep_awake:event.target.elements.keep_awake.checked,advisor_auto:event.target.elements.advisor_auto.checked})) toast("Settings saved");};
$("notifications").onclick = async () => {if(!window.Notification) return toast("This browser does not support notifications"); const permission = await Notification.requestPermission(); toast(permission === "granted" ? "Notifications enabled while this dashboard is open" : "Notifications were not enabled");};
document.addEventListener("click", async event => {
  const taskTab = event.target.closest("[data-task-filter]");
  if(taskTab) setTaskFilter(taskTab.dataset.taskFilter);
  if(event.target.closest('#next-step a[href="#projects"]')) setTaskFilter("active");
  if(event.target.closest("[data-show-finished]")) {setTaskFilter("finished"); location.hash="#projects";}
  const next = event.target.closest("[data-next-action]");
  if(next) {if(next.dataset.nextAction === "new") showBeginner(); if(next.dataset.nextAction === "account") showAccount(); if(next.dataset.nextAction === "start") await act("/api/control",{action:"start"}); if(next.dataset.nextAction === "finished") {setTaskFilter("finished");location.hash="#projects";}}
  const filter = event.target.closest("[data-idea-filter]");
  if(filter) {ideaFilter = filter.dataset.ideaFilter; document.querySelectorAll("[data-idea-filter]").forEach(b => {const active=b.dataset.ideaFilter === ideaFilter; b.classList.toggle("active",active);b.setAttribute("aria-pressed",String(active));}); ideaSignature = ""; renderBrain();}
  const close = event.target.closest("[data-close]"); if(close) $(close.dataset.close).close();
  const element = event.target.closest("[data-action]"); if(!element) return;
  const {action,id} = element.dataset;
  if(action === "work-existing") showProjectForm(id);
  if(action === "review-suggestion") showProjectForm("",id);
  if(action === "dismiss-suggestion") await act("/api/suggestion", {action:"dismiss",id});
  if(action === "advise-project") { $("advisor-target").value = id; await act("/api/advisor",{catalog_id:id,focus:$("advisor-form").elements.focus.value,provider:$("advisor-provider").value}); location.hash="#advisor"; }
  if(action === "login") { await act("/api/account", {action:"login",id}); toast("Complete the account sign-in in your browser"); }
  if(action === "toggle") { const p = state.profiles.find(p => p.id === id); await act("/api/account", {action:"toggle",id,enabled:!p.enabled}); }
  if(action === "pause-project" || action === "cancel-project") await act("/api/project", {action:action === "pause-project" ? "pause" : "cancel",id});
  if(action === "resume") { const p = state.projects.find(p => p.id === id); const f = $("resume-form"); f.elements.id.value = id; f.elements.guidance.value = p.guidance || ""; f.elements.max_steps.value = Math.min(200,Math.max(p.max_steps,p.steps+10)); $("resume-dialog").showModal(); }
  if(action === "log") { activeLog = id; await loadLog(id); $("log-dialog").showModal(); }
  if(action === "decline-reset") await act("/api/decision", {id,approve:false});
  if(action === "review-reset") { resetDecision = id; const d = state.decisions.find(d => d.id === id); const profile = state.profiles.find(p => p.id === d.profile_id); $("reset-detail").textContent = `${profile?.name || d.profile_id}. Pause active work before approving. The queue will continue waiting if you close this dialog.`; $("reset-dialog").showModal(); }
});
$("approve-reset").onclick = async () => { const b = $("approve-reset"); b.disabled = true; try { await api("/api/decision", {id:resetDecision,approve:true}); $("reset-dialog").close(); toast("Reset decision completed; refreshing quota"); await refresh(); } catch(error) {toast(error.message);} finally {b.disabled = false;} };
function updateNavigation() {
  if(location.hash === "#main-content") return;
  const page=RunquayUI.pageFor(location.hash);
  document.querySelectorAll(".page").forEach(p=>p.hidden=p.dataset.page !== page);
  document.querySelectorAll(".nav a").forEach(a=>{const active=a.hash === "#" + page; a.classList.toggle("active",active); if(active) a.setAttribute("aria-current","page"); else a.removeAttribute("aria-current");});
  $("page-title").textContent={overview:"Home",projects:"Tasks",advisor:"Ideas",accounts:"Accounts",settings:"Settings"}[page];
  if(location.hash === "#activity") $("activity").open=true;
  if(location.hash === "#projects" && taskFilter !== "finished") setTaskFilter("active");
  if(location.hash === "#approvals" || location.hash === "#activity") document.querySelector(location.hash).scrollIntoView({block:"start",behavior:"instant"});
  else window.scrollTo({top:0,behavior:"instant"});
}
document.addEventListener("invalid",event=>{let details=event.target.closest("details"); while(details) {details.open=true; details=details.parentElement.closest("details");}},true);
document.querySelector(".skip-link").onclick=event=>{event.preventDefault();$("main-content").focus();$("main-content").scrollIntoView();};
window.addEventListener("hashchange",updateNavigation); updateNavigation();

refresh(); setInterval(refresh,4000);
