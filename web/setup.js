"use strict";
let setupStep = 0, setupDismissed = false, setupSignature = "", loginProfile = "", externalDecision = "";
function toolOptions(advisorOnly = false) {
  return state.tools.filter(t => !advisorOnly || t.advisor).map(t => `<option value="${t.id}">${esc(t.name)}${!t.installed && t.id !== "custom" ? " (not installed)" : ""}</option>`).join("");
}
function renderSetup() {
  const signature = JSON.stringify(state.tools);
  if(signature !== setupSignature) {
    setupSignature = signature;
    for(const id of ["account-provider","project-provider","advisor-provider","setup-provider"]) {
      const selected = $(id).value;
      $(id).innerHTML = toolOptions(["advisor-provider","setup-provider"].includes(id));
      $(id).value = selected || state.advisor_provider || "codex";
    }
    const toolCard = t => `<article class="tool-card"><h3>${esc(t.name)} ${badge(t.installed ? "Installed" : t.id === "custom" ? "Custom" : "Not installed")}</h3><p>${t.id === "codex" ? "Subscription usage is checked before work." : "Asks for approval before each run. Billing is unverified."}</p>${t.docs ? `<a target="_blank" rel="noopener noreferrer" href="${esc(t.docs)}">Installation guide ↗</a>` : ""}<details><summary>Support details</summary><p>${esc(t.verification)}</p></details></article>`;
    const installed = state.tools.filter(t => t.installed);
    const others = state.tools.filter(t => !t.installed);
    $("setup-tools").innerHTML = installed.map(toolCard).join("") + `<details class="other-tools"><summary>${installed.length ? "Other supported tools" : "Install a supported tool"}</summary>${others.map(toolCard).join("")}</details>`;
  }
  $("setup-accounts").innerHTML = state.profiles.length ? state.profiles.map(p => `<div class="setup-account"><div><b>${esc(p.name)}</b><small>${esc(state.tools.find(t => t.id === p.provider)?.name)} · ${p.eligible ? "Subscription verified" : esc(p.error || (p.provider === "codex" ? "Check sign-in and quota" : "Quota/auth unverified"))}</small></div><button type="button" class="secondary" data-action="login-guide" data-id="${p.id}">Sign-in guide</button></div>`).join("") : empty("No profiles connected", "Connect a tool account to begin.");
  $("setup-project-count").textContent = `${state.catalog.length} existing project folders found. You can use them from Tasks.`;
  if(!$("setup-workspace").value) $("setup-workspace").value = state.workspace_root;
  if(!state.onboarded && !setupDismissed && !$("setup-dialog").open) openSetup();
}
function drawSetup() {
  document.querySelectorAll(".setup-page").forEach(p => {p.hidden = Number(p.dataset.step) !== setupStep;});
  document.querySelectorAll(".setup-progress li").forEach((p,i) => p.classList.toggle("active", i === setupStep));
  $("setup-back").disabled = setupStep === 0;
  $("setup-step-text").textContent = `Step ${setupStep + 1} of 4`;
  $("setup-next").textContent = setupStep === 3 ? "Finish setup" : "Next";
  $("setup-review").textContent = `${state.tools.find(t => t.id === $("setup-provider").value)?.name || "Codex"} for project ideas · ${state.profiles.length} accounts · ${state.catalog.length} existing folders. New projects go in ${$("setup-workspace").value}. Setup keeps your current work start/pause state.`;
}
function openSetup() {if(!state) return toast("Wait for the local app to connect."); setupStep = 0; $("setup-ack").checked = false; drawSetup(); if(!$("setup-dialog").open) $("setup-dialog").showModal();}
function showAccount() {if(!state) return toast("Wait for the local app to connect."); $("account-form").reset(); $("account-form").querySelectorAll("details").forEach(d=>d.open=false); $("custom-command-label").hidden = true; $("account-dialog").showModal();}
$("setup-close").onclick = () => {setupDismissed = true; $("setup-dialog").close();};
$("setup-dialog").addEventListener("cancel", () => {setupDismissed = true;});
$("reopen-setup").onclick = openSetup;
$("setup-back").onclick = () => {setupStep = Math.max(0,setupStep-1); drawSetup();};
$("setup-next").onclick = async () => {
  if(setupStep < 3) {setupStep++; drawSetup(); return;}
  try {
    await api("/api/onboarding", {acknowledged:$("setup-ack").checked,provider:$("setup-provider").value,workspace_root:$("setup-workspace").value});
    $("setup-dialog").close(); setupDismissed = true; toast("Setup saved. Create a task to begin."); location.hash="#overview"; await refresh();
  } catch(error) {toast(error.message);}
};
$("add-account").onclick = showAccount;
$("setup-add-account").onclick = showAccount;
$("account-provider").onchange = () => {$("custom-command-label").hidden = $("account-provider").value !== "custom";};
$("account-form").onsubmit = async event => {
  event.preventDefault(); const form = event.target;
  const data = Object.fromEntries(new FormData(form)); data.existing = form.elements.existing.checked; data.action = "add";
  try {
    if(data.provider === "custom") data.command = JSON.parse(data.command);
    await api("/api/account",data); $("account-dialog").close(); await refresh(); toast("Account connected. Open its sign-in guide if needed.");
  } catch(error) {toast(error.message);}
};
$("import-project").onclick = () => $("import-dialog").showModal();
$("setup-import").onclick = () => $("import-dialog").showModal();
$("import-form").onsubmit = async event => {
  event.preventDefault();
  try {await api("/api/catalog/add",Object.fromEntries(new FormData(event.target))); $("import-dialog").close(); event.target.reset(); await refresh(); toast("Project folder connected");} catch(error) {toast(error.message);}
};
document.addEventListener("click", async event => {
  const e = event.target.closest("[data-action]"); if(!e) return;
  const {action,id} = e.dataset;
  if(action === "login-guide") {
    const profile = state.profiles.find(p => p.id === id); loginProfile = id;
    $("login-command").textContent = profile.instructions.login; $("login-note").textContent = profile.instructions.note;
    $("login-guide").showModal();
  }
  if(action === "remove-profile") {
    if(await act("/api/account",{action:"remove",id})) toast("Connection removed. Vendor credentials and history are kept.");
  }
  if(action === "review-external") {
    externalDecision = id; const d = state.decisions.find(d => d.id === id); const payload = JSON.parse(d.payload);
    $("external-project").textContent = `${payload.project} · ${payload.provider} · milestone ${payload.step+1}`;
    $("external-ack").checked = false; $("external-dialog").showModal();
  }
});
$("verify-profile").onclick = async () => {if(await act("/api/account",{action:"verify",id:loginProfile})) {$("login-guide").close(); toast("Checking the connection. Other tools verify authentication on the first approved run.");}};
$("approve-external").onclick = async () => {
  if(!$("external-ack").checked) return toast("Review the billing acknowledgement first");
  try {await api("/api/decision",{id:externalDecision,approve:true}); $("external-dialog").close(); await refresh(); toast("One invocation authorized");} catch(error) {toast(error.message);}
};
