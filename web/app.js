"use strict";
let state, token, resetDecision, activeLog, pollBusy = false, previousPending = new Set();
let ideaFilter = "all", catalogSignature = "", ideaSignature = "";
const $ = id => document.getElementById(id);
const esc = text => String(text ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const badge = text => `<span class="badge ${esc(text)}">${esc(text)}</span>`;
const when = value => value ? new Date(typeof value === "number" ? value * 1000 : value).toLocaleString(undefined, {dateStyle:"medium",timeStyle:"short"}) : "Not yet";
const empty = (title, sub) => `<div class="empty"><b>${esc(title)}</b><p>${esc(sub)}</p></div>`;
function toast(message) { $("toast").textContent = message; $("toast").style.display = "block"; clearTimeout(toast.timer); toast.timer = setTimeout(() => $("toast").style.display = "none", 6000); }
async function api(path, data) {
  const response = await fetch(path, data === undefined ? {} : {method:"POST",headers:{"Content-Type":"application/json","X-AutoWork-CSRF":token},body:JSON.stringify(data)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Request failed");
  return result;
}
async function act(path, data) { try { await api(path, data); await refresh(); } catch(error) { toast(error.message); } }
function meter(window, label) {
  if (!window || typeof window.usedPercent !== "number") return `<div class="meter-label"><span>${label}</span><span>Unknown</span></div><div class="meter"></div>`;
  const used = Math.max(0, Math.min(100, window.usedPercent));
  return `<div class="meter-label"><span>${label} · ${used}% used</span><span>${100-used}% left</span></div><progress class="meter" max="100" value="${used}" aria-label="${label} usage"></progress><div class="account-check">Refreshes ${esc(when(window.resetsAt))}</div>`;
}
function showProjectForm(catalogId = "", suggestionId = "") {
  const form = $("project-form"); form.reset();
  const suggestion = state.suggestions?.find(s => s.id === suggestionId);
  const payload = suggestion?.payload;
  const selected = state.catalog?.find(p => p.id === (payload?.catalog_id || catalogId));
  form.elements.catalog_id.value = selected?.id || "";
  form.elements.suggestion_id.value = suggestionId;
  form.elements.name.value = payload?.title || selected?.name || "";
  form.elements.goal.value = payload ? `${payload.goal}\n\nFirst milestone: ${payload.first_milestone}\n\nProject evidence: ${payload.evidence}` : "";
  $("project-dialog-title").textContent = suggestion ? "Review the advisor’s proposal" : selected ? "Start work on " + selected.name : "Create a project";
  $("project-workspace").textContent = selected ? "Existing workspace: " + selected.path : "New workspace root: " + state.workspace_root;
  $("project-dialog").showModal();
}
function renderBrain() {
  const library = state.catalog || [];
  $("project-count").textContent = library.length;
  $("queue-count").textContent = state.projects.length;
  $("catalog-error").textContent = state.catalog_error || "Codex saved roots and connected folders refresh every five minutes.";
  const signature = JSON.stringify(library);
  if (catalogSignature !== signature) {
    catalogSignature = signature;
    $("catalog-list").innerHTML = library.length ? library.map(p => `<article class="catalog-card"><div class="project-top"><h3>${esc(p.name)}</h3>${badge(p.is_supervisor ? "system" : p.details.exists ? "connected" : "missing")}</div><div class="catalog-path">${esc(p.path)}</div><div class="catalog-files">${esc(p.details.files.slice(0,7).join(" · ") || "No top-level files found")}</div>${p.recent?.length ? `<div class="catalog-recent">${esc(p.recent[0].title)}<small>${esc(p.recent[0].preview?.slice(0,140) || "Recent Codex activity")}</small></div>` : ""}<div class="controls"><button class="secondary" data-action="work-existing" data-id="${esc(p.id)}" ${p.is_supervisor || !p.details.exists ? "disabled" : ""}>${p.is_supervisor ? "This system" : "Start work"}</button><button class="text-button" data-action="advise-project" data-id="${esc(p.id)}">Ask AI ↗</button></div></article>`).join("") : empty("Connect your project folders", "Use Connect folder, or sync saved Codex projects.");
    const selected = $("advisor-target").value;
    $("advisor-target").innerHTML = '<option value="">All my projects</option>' + library.map(p => `<option value="${esc(p.id)}">${esc(p.name)}</option>`).join("");
    if(library.some(p => p.id === selected)) $("advisor-target").value = selected;
  }
  const advisor = state.advisor;
  const busy = advisor && ["queued","running"].includes(advisor.state);
  $("advisor-status").textContent = advisor?.state === "running" ? "The advisor is analyzing" : advisor?.state === "queued" ? "Queued" : state.advisor_completed ? "Suggestions ready" : "Ready to think";
  $("advisor-status").className = "badge " + (advisor?.state || "ready");
  $("generate-ideas").disabled = Boolean(busy);
  $("generate-ideas").textContent = advisor?.state === "running" ? "Analyzing projects…" : advisor?.state === "queued" ? "Advisor queued…" : "✧ Ask AI";
  $("advisor-detail").textContent = busy ? (advisor.state === "running" ? "The advisor is reading project evidence and preparing concrete proposals. Live output is available in Recent activity." : state.running ? "The advisor will run when an eligible account and the worker are available." : "The advisor is queued. Start the queue to let the advisor analyze your projects.") : (advisor?.state === "attention" ? advisor.note : state.advisor_summary || "The advisor will propose useful improvements and new projects based on what you are already building.");
  const ideas = (state.suggestions || []).filter(s => s.state === "proposed" && (ideaFilter === "all" || s.payload.kind === ideaFilter));
  const ideasHash = JSON.stringify(ideas);
  if(ideaSignature !== ideasHash) {
    ideaSignature = ideasHash;
    $("suggestion-list").innerHTML = ideas.length ? ideas.map(s => {const p = s.payload; const target = library.find(c => c.id === p.catalog_id); return `<article class="suggestion"><div class="idea-meta">${badge(p.kind === "new" ? "new project" : "improvement")}<span>${esc(target?.name || "New local project")}</span><span>· ${esc(p.effort)}</span></div><h3>${esc(p.title)}</h3><p>${esc(p.why)}</p><div class="first-step">First milestone: ${esc(p.first_milestone)}</div><details><summary>Evidence and proposed goal</summary><p>${esc(p.evidence)}</p><p>${esc(p.goal)}</p></details><div class="controls"><button data-action="review-suggestion" data-id="${s.id}">Review & queue ↗</button><button class="text-button" data-action="dismiss-suggestion" data-id="${s.id}">Dismiss</button></div></article>`;}).join("") : empty(busy ? "The advisor is preparing your suggestions" : "No suggestions in this view yet", busy ? "This is a real AI analysis, grounded in your local projects." : "Ask AI above to discover improvements and new project ideas.");
  }
}
function render() {
  const running = state.projects.find(p => p.state === "running");
  const advising = state.advisor?.state === "running";
  $("status").textContent = state.running ? running ? "Working" : advising ? "Thinking" : "Ready" : "Paused";
  $("status-detail").textContent = running ? running.name : advising ? "The advisor is analyzing your existing projects" : state.running ? "Waiting for a project or an eligible account" : "Start the queue when you are ready";
  $("queued").textContent = state.projects.filter(p => p.state === "queued").length;
  $("ready").innerHTML = `${state.profiles.filter(p => p.eligible && p.enabled).length} <em>/ ${state.profiles.length}</em>`;
  $("completed").textContent = state.projects.filter(p => p.state === "complete").length;
  renderBrain();
  if (typeof renderSetup === "function") renderSetup();
  $("connection").innerHTML = '<span class="dot"></span> SUPERVISOR ONLINE';
  $("binary").textContent = "Installed CLI: " + (state.binary || "Not found");
  $("project-list").innerHTML = state.projects.length ? state.projects.map(p => `<article class="project"><div class="project-top"><h3>${esc(p.name)}</h3>${badge(p.state)}</div><p class="project-goal">${esc(p.goal)}</p>${p.checkpoint.summary ? `<div class="project-detail">${esc(p.checkpoint.summary)}</div><p class="hint">Checks: ${esc(p.checkpoint.tests)}</p>` : ""}${p.note ? `<div class="project-detail">${esc(p.note)}</div>` : ""}<div class="project-meta"><span>${p.steps} / ${p.max_steps} milestones</span><span>Priority ${p.priority}</span><span>${esc(p.model || "Account default model")}</span><span>${esc(p.path)}</span></div><div class="project-actions">${p.state !== "running" && p.state !== "queued" ? `<button class="secondary" data-action="resume" data-id="${p.id}">Resume / add guidance</button>` : ""}${["running","queued"].includes(p.state) ? `<button class="secondary" data-action="pause-project" data-id="${p.id}">Pause project</button>` : ""}${p.state !== "cancelled" ? `<button class="text-button" data-action="cancel-project" data-id="${p.id}">Cancel</button>` : ""}</div></article>`).join("") : empty("Your next project starts here", "Add a goal, define what finished means, and let the advisor work through the milestones.");
  $("account-list").innerHTML = state.profiles.map(p => {
    const account = p.snapshot.account || {};
    const limits = p.snapshot.limits || {};
    const buckets = limits.rateLimitsByLimitId || {};
    const bucket = buckets.codex || limits.rateLimits || {};
    const earned = limits.rateLimitResetCredits;
    return `<article class="account"><div class="account-head"><h3>${esc(p.name)}</h3>${badge(!p.enabled ? "disabled" : p.eligible ? "ready" : "waiting")}</div><div class="email">${esc(p.provider === "codex" ? account.type === "chatgpt" ? "Subscription connected" : "Sign-in required" : (p.snapshot.installed ? "CLI found · billing and auth unverified" : "CLI not found"))} ${account.planType ? " · " + esc(account.planType) : ""}</div>${p.provider === "codex" ? meter(bucket.primary,"Short window") + meter(bucket.secondary,"Long window") : `<div class="account-reason">${esc(state.tools.find(t => t.id === p.provider)?.name)} · one-run approval required</div>`}<div class="account-reason">${esc(p.reason)}</div><div class="account-check">Earned resets: ${earned?.availableCount ?? "unknown"} · Checked ${esc(when(p.checked))}</div><div class="account-actions"><button class="secondary" data-action="login-guide" data-id="${p.id}">Sign-in guide</button><button class="text-button" data-action="remove-profile" data-id="${p.id}">Unlink</button><button class="text-button" data-action="toggle" data-id="${p.id}">${p.enabled ? "Disable" : "Enable"}</button></div></article>`;
  }).join("");
  const decisions = state.decisions.filter(d => ["pending","uncertain","redeeming"].includes(d.state));
  $("approval-count").textContent = decisions.length || "";
  document.title = decisions.length ? `(${decisions.length}) Approval needed · Runquay` : (running ? "Working · " : "") + "Runquay · Local AI coding queue";
  $("decision-list").innerHTML = decisions.length ? decisions.map(d => {
    const profile = state.profiles.find(p => p.id === d.profile_id);
    if(d.kind === "external_run") { const payload = JSON.parse(d.payload); return `<div class="decision"><div><h3>${esc(profile?.name)} · authorize one invocation?</h3><p>${esc(payload.project)} · ${esc(payload.provider)}</p><p>Vendor quota and costs are unverified. Check billing before approving.</p></div><div class="controls"><button class="secondary" data-action="decline-reset" data-id="${d.id}">Decline run</button><button data-action="review-external" data-id="${d.id}">Review invocation</button></div></div>`; }
    return `<div class="decision"><div><h3>${esc(profile?.name || d.profile_id)} · Use one earned reset?</h3><p>${d.state === "uncertain" ? "The previous result is uncertain. Retry uses the same request ID to prevent a second redemption." : "Wait for the natural quota refresh, or explicitly redeem an existing reset."}</p><p>${esc(when(d.created))}</p></div><div class="controls"><button class="secondary" data-action="decline-reset" data-id="${d.id}">Wait for refresh</button><button data-action="review-reset" data-id="${d.id}" ${d.state === "redeeming" ? "disabled" : ""}>Review reset</button></div></div>`;
  }).join("") : empty("No decisions waiting", "Resets will appear here when an account reaches the quota reserve.");
  for (const d of decisions) {
    if (!previousPending.has(d.id) && window.Notification && Notification.permission === "granted") new Notification("Runquay: reset decision needed", {body:"An account reached its quota reserve. Open the local dashboard to decide."});
  }
  previousPending = new Set(decisions.map(d => d.id));
  $("run-list").innerHTML = state.runs.length ? state.runs.map(r => `<div class="activity-row"><div class="row-content">${esc(state.projects.find(p => p.id === r.project_id)?.name || (r.project_id.startsWith("advisor-") ? "AI project advisor" : r.project_id))} ${badge(r.state)}<small>${esc(when(r.started))} · ${esc(r.profile_id)}</small></div><button class="secondary" data-action="log" data-id="${r.id}">Output ↗</button></div>`).join("") : '<p class="hint">Run history appears after the first milestone starts.</p>';
  $("event-list").innerHTML = state.events.map(e => `<div class="activity-row"><div class="row-content">${esc(e.message)}<small>${esc(when(e.at))}</small></div></div>`).join("");
  if (!$("settings-form").contains(document.activeElement)) {
    $("settings-form").elements.quota_ceiling.value = state.quota_ceiling;
    $("settings-form").elements.turn_minutes.value = state.turn_minutes;
    $("settings-form").elements.keep_awake.checked = state.keep_awake;
    $("settings-form").elements.advisor_auto.checked = state.advisor_auto;
    $("settings-form").elements.advisor_hours.value = state.advisor_hours;
  }
}
async function refresh() {
  if (pollBusy) return;
  pollBusy = true;
  try { state = await api("/api/state"); token = state.csrf; render(); if(activeLog && $("log-dialog").open) await loadLog(activeLog); }
  catch(error) { $("connection").textContent = "SUPERVISOR UNREACHABLE"; }
  finally { pollBusy = false; }
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
$("refresh").onclick = async () => { await act("/api/accounts/refresh", {}); toast("Checking accounts…"); };
$("new-project").onclick = () => showProjectForm();
$("sync-projects").onclick = async () => { await act("/api/catalog/refresh", {}); toast("Synced your saved Codex projects"); };
$("advisor-form").onsubmit = async event => { event.preventDefault(); const data = Object.fromEntries(new FormData(event.target)); await act("/api/advisor", data); };
$("project-form").onsubmit = async event => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.target));
  try { await api(data.suggestion_id ? "/api/suggestion" : "/api/projects", data.suggestion_id ? {...data,id:data.suggestion_id,action:"start"} : data); $("project-dialog").close(); event.target.reset(); toast("Project added to the queue"); await refresh(); } catch(error) { toast(error.message); }
};
$("resume-form").onsubmit = async event => { event.preventDefault(); const data = Object.fromEntries(new FormData(event.target)); try { await api("/api/project", {...data,action:"resume"}); $("resume-dialog").close(); await refresh(); } catch(error) { toast(error.message); } };
$("settings-form").onsubmit = async event => {event.preventDefault(); const data = Object.fromEntries(new FormData(event.target)); await act("/api/settings", {...data, keep_awake:event.target.elements.keep_awake.checked,advisor_auto:event.target.elements.advisor_auto.checked}); toast("Settings saved");};
$("notifications").onclick = async () => {if(!window.Notification) return toast("This browser does not support notifications"); const permission = await Notification.requestPermission(); toast(permission === "granted" ? "Notifications enabled while this dashboard is open" : "Notifications were not enabled");};
document.addEventListener("click", async event => {
  const filter = event.target.closest("[data-idea-filter]");
  if(filter) {ideaFilter = filter.dataset.ideaFilter; document.querySelectorAll("[data-idea-filter]").forEach(b => b.classList.toggle("active",b.dataset.ideaFilter === ideaFilter)); ideaSignature = ""; renderBrain();}
  const close = event.target.closest("[data-close]"); if(close) $(close.dataset.close).close();
  const element = event.target.closest("[data-action]"); if(!element) return;
  const {action,id} = element.dataset;
  if(action === "work-existing") showProjectForm(id);
  if(action === "review-suggestion") showProjectForm("",id);
  if(action === "dismiss-suggestion") await act("/api/suggestion", {action:"dismiss",id});
  if(action === "advise-project") { $("advisor-target").value = id; await act("/api/advisor",{catalog_id:id,focus:$("advisor-form").elements.focus.value,provider:$("advisor-provider").value}); $("advisor").scrollIntoView({behavior:"smooth"}); }
  if(action === "login") { await act("/api/account", {action:"login",id}); toast("Complete the account sign-in in your browser"); }
  if(action === "toggle") { const p = state.profiles.find(p => p.id === id); await act("/api/account", {action:"toggle",id,enabled:!p.enabled}); }
  if(action === "pause-project" || action === "cancel-project") await act("/api/project", {action:action === "pause-project" ? "pause" : "cancel",id});
  if(action === "resume") { const p = state.projects.find(p => p.id === id); const f = $("resume-form"); f.elements.id.value = id; f.elements.guidance.value = p.guidance || ""; f.elements.max_steps.value = Math.min(200,Math.max(p.max_steps,p.steps+10)); $("resume-dialog").showModal(); }
  if(action === "log") { activeLog = id; await loadLog(id); $("log-dialog").showModal(); }
  if(action === "decline-reset") await act("/api/decision", {id,approve:false});
  if(action === "review-reset") { resetDecision = id; const d = state.decisions.find(d => d.id === id); const profile = state.profiles.find(p => p.id === d.profile_id); $("reset-detail").textContent = `${profile?.name || d.profile_id}. Pause active work before approving. The queue will continue waiting if you close this dialog.`; $("reset-dialog").showModal(); }
});
$("approve-reset").onclick = async () => { const b = $("approve-reset"); b.disabled = true; try { await api("/api/decision", {id:resetDecision,approve:true}); $("reset-dialog").close(); toast("Reset decision completed; refreshing quota"); await refresh(); } catch(error) {toast(error.message);} finally {b.disabled = false;} };
function updateNavigation() {document.querySelectorAll('.nav a').forEach(a => a.classList.toggle('active',a.hash === (location.hash || '#overview')));}
window.addEventListener('hashchange',updateNavigation); updateNavigation();
refresh(); setInterval(refresh,4000);
