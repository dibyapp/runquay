"use strict";
let setupStep = 0, setupDismissed = false, setupSignature = "", loginProfile = "", externalDecision = "", accountSignature = "", accountSaving = false;
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
  const provider=$("setup-provider").value, tool=state.tools.find(t=>t.id===provider), profile=RunquayUI.setupAccount(state,provider);
  $("setup-account-title").textContent=profile?.eligible ? `${tool.name} is ready` : profile ? `Check your ${tool.name} connection` : `Connect ${tool?.name || "your AI"}`;
  $("setup-account-note").textContent=profile?.eligible ? "Your account is verified. Choose Next to continue." : profile ? provider==="codex" ? "Your login was found. Check the connection before starting work." : "Use your existing login. Each run will ask for your approval." : "Use the login already on this computer. No account name or settings needed.";
  $("setup-accounts").innerHTML=profile && !profile.eligible ? `<div class="controls"><button type="button" class="secondary" data-action="login-guide" data-id="${esc(profile.id)}">Sign-in guide</button><button type="button" class="secondary" data-action="verify" data-id="${esc(profile.id)}">Check connection</button></div><details class="advanced"><summary>Connection details</summary><p>${esc(profile.reason || profile.error || "Checking sign-in and allowance…")}</p></details>` : "";
  $("setup-connect-account").hidden=Boolean(profile);
  if($("account-dialog").open) drawAccount();
  if($("login-guide").open) drawLoginGuide();
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
function showAccount(provider="", separate=false) {
  if(!state) return toast("Wait for the local app to connect.");
  const form=$("account-form"); form.reset(); form.querySelectorAll("details").forEach(d=>d.open=false);
  const installed=state.tools.filter(t=>t.installed), preferred=provider || $("setup-provider").value;
  form.elements.provider.value=installed.some(t=>t.id===preferred) ? preferred : installed[0]?.id || preferred || "codex";
  form.elements.separate.checked=separate; accountSignature=""; drawAccount(); $("account-dialog").showModal();
}
function drawAccount() {
  const form=$("account-form"), provider=form.elements.provider.value;
  if(provider==="antigravity") form.elements.separate.checked=false;
  const choice=RunquayUI.accountChoice(state,provider,form.elements.separate.checked), tool=choice.tool;
  const installed=state.tools.filter(t=>t.installed);
  const signature=JSON.stringify([installed.map(t=>[t.id,t.name]),provider]);
  if(signature!==accountSignature) {
    accountSignature=signature;
    $("account-detected").innerHTML=installed.map(t=>`<button type="button" class="secondary ${t.id===provider ? "selected" : ""}" data-account-tool="${esc(t.id)}" aria-pressed="${t.id===provider}">${esc(t.name)}</button>`).join("");
  }
  $("account-detected-note").textContent=installed.length ? "We found these tools on your computer." : "No AI tools found. Install a tool, or use More options.";
  $("account-connect-note").textContent=choice.connected ? `${tool.name}'s current login is already connected.` : !choice.existing ? `We'll guide you through signing in to another ${tool.name} account.` : `Use the ${tool?.name || "AI"} login already on this computer. Sign in afterward if needed.`;
  if(provider!=="codex" && !choice.connected) $("account-connect-note").textContent+=" Each run needs your approval because billing is unverified.";
  $("account-connect").textContent=choice.connected ? "Done" : !choice.existing ? "Continue to sign in" : `Connect ${tool?.name || "AI"}`;
  $("account-connect").disabled=accountSaving || Boolean(!choice.connected && provider!=="custom" && !tool?.installed && !form.elements.executable.value.trim());
  $("account-another").hidden=!choice.connected || provider==="antigravity";
  form.elements.separate.disabled=provider==="antigravity";
  $("account-separate-note").hidden=provider!=="antigravity";
  $("custom-command-label").hidden=provider!=="custom"; form.elements.command.required=provider==="custom";
  $("account-install-note").innerHTML=!tool?.installed && tool?.docs ? `<a href="${esc(tool.docs)}" target="_blank" rel="noopener noreferrer">Install ${esc(tool.name)} ↗</a>, then reopen this screen.` : "";
}
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
$("add-account").onclick = () => showAccount();
$("setup-add-account").onclick = () => showAccount($("setup-provider").value,true);
$("setup-connect-account").onclick = () => showAccount($("setup-provider").value);
$("setup-provider").onchange=()=>{renderSetup();drawSetup();};
$("account-provider").onchange = () => {$("account-form").elements.separate.checked=false;drawAccount();};
$("account-separate").onchange=drawAccount;
$("account-form").elements.executable.oninput=drawAccount;
$("account-another").onclick=()=>{$("account-form").elements.separate.checked=true;drawAccount();};
$("account-form").onsubmit = async event => {
  event.preventDefault(); const form = event.target;
  if(accountSaving) return;
  const data = Object.fromEntries(new FormData(form));
  const choice=RunquayUI.accountChoice(state,data.provider,form.elements.separate.checked);
  if(choice.connected) {$("account-dialog").close(); return;}
  data.name=data.name.trim() || choice.name; data.existing=choice.existing; data.action = "add";
  try {
    accountSaving=true; drawAccount();
    if(data.provider === "custom") data.command = JSON.parse(data.command);
    const result=await api("/api/account",data); $("account-dialog").close(); await refresh();
    if(!data.existing && result.id) openLoginGuide(result.id);
    else toast("Account connected. Sign in if needed.");
  } catch(error) {toast(error.message);}
  finally {accountSaving=false; drawAccount();}
};
$("import-project").onclick = () => $("import-dialog").showModal();
$("setup-import").onclick = () => $("import-dialog").showModal();
$("import-form").onsubmit = async event => {
  event.preventDefault();
  try {await api("/api/catalog/add",Object.fromEntries(new FormData(event.target))); $("import-dialog").close(); event.target.reset(); await refresh(); toast("Project folder connected");} catch(error) {toast(error.message);}
};
function openLoginGuide(id) {
  const profile=state.profiles.find(p=>p.id===id); if(!profile) return;
  loginProfile=id; $("login-command").textContent=profile.instructions.login;
  $("login-note").textContent=profile.instructions.note; $("login-fallback").open=false;
  drawLoginGuide(); $("login-guide").showModal();
}
function drawLoginGuide() {
  const profile=state.profiles.find(p=>p.id===loginProfile); if(!profile) return;
  const view=RunquayUI.loginView(state,profile);
  $("login-title").textContent=view.browser ? "Sign in with Codex" : "Sign in to your AI";
  $("login-intro").textContent=view.browser ? "Continue with your ChatGPT account on OpenAI's website. Runquay checks the connection afterward." : profile.current_login && profile.provider==="codex" ? "This connection uses your Codex app login. Sign in through Codex, or add another account for a separate browser sign-in." : "Use this tool's sign-in instructions below. Each run still needs your approval when billing is unverified.";
  $("browser-login").hidden=!view.browser;
  $("browser-login").disabled=loginStarting || view.blocked;
  $("browser-login").textContent=view.complete ? "Done" : view.waiting ? "Waiting for sign-in…" : "Sign in with Codex";
  $("cancel-browser-login").hidden=!view.waiting;
  $("login-status").textContent=view.message || (view.blocked ? "Finish the other browser sign-in first." : "");
  $("login-fallback").querySelector("summary").textContent=view.browser ? "Use terminal instead" : "Sign-in instructions";
}
let loginStarting=false;
$("browser-login").onclick=async()=>{
  const profile=state.profiles.find(p=>p.id===loginProfile);
  if(RunquayUI.loginView(state,profile).complete) {$("login-guide").close();return;}
  if(loginStarting) return;
  loginStarting=true;drawLoginGuide();
  try {await api("/api/account",{action:"login",id:loginProfile});await refresh();}
  catch(error) {$("login-status").textContent=error.message;toast(error.message);}
  finally {loginStarting=false;drawLoginGuide();}
};
$("cancel-browser-login").onclick=async()=>{await act("/api/account",{action:"cancel_login",id:loginProfile});};
document.addEventListener("click", async event => {
  const tool=event.target.closest("[data-account-tool]");
  if(tool) {$("account-provider").value=tool.dataset.accountTool; $("account-form").elements.separate.checked=false;drawAccount();return;}
  const e = event.target.closest("[data-action]"); if(!e) return;
  const {action,id} = e.dataset;
  if(action === "verify") {if(await act("/api/account",{action:"verify",id})) toast("Checking your connection…");}
  if(action === "login-guide") {
    openLoginGuide(id);
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
