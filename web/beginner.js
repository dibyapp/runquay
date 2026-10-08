"use strict";
let beginnerReview=false, resultProject="";

function beginnerNote() {
  $("beginner-work-note").textContent=state?.running
    ? "Work is on. Adding this task can start your AI as soon as an account is available."
    : "Work is paused. Your task will be saved; choose Start work on Home when you are ready.";
}
function showBeginner(starterId="") {
  if(!state) return toast("Wait for the local app to connect.");
  const form=$("beginner-form"); form.reset();
  form.querySelectorAll("details").forEach(d=>d.open=false);
  $("beginner-provider").innerHTML=toolOptions();
  form.elements.provider.value=state.profiles.find(p=>p.enabled && p.eligible)?.provider || state.profiles.find(p=>p.enabled)?.provider || state.advisor_provider || "codex";
  const starter=RunquayUI.starters.find(s=>s.id===starterId);
  if(starter) {form.elements.kind.value=starter.kind; form.elements.name.value=starter.title; form.elements.purpose.value=starter.purpose; form.elements.features.value=starter.features;}
  drawBeginner(false); $("beginner-dialog").showModal();
}
function drawBeginner(review) {
  beginnerReview=review;
  $("beginner-fields").hidden=review; $("beginner-review").hidden=!review;
  $("beginner-step").textContent=review ? "2 of 2 · Check your idea" : "1 of 2 · Your idea";
  $("beginner-title").textContent=review ? "Does this sound right?" : "What would you like to make?";
  beginnerNote();
}
$("starter-list").innerHTML=RunquayUI.starters.map(s=>`<button class="secondary" data-starter="${s.id}">${esc(s.title)}</button>`).join("");
$("home-new").onclick=()=>showBeginner();
$("new-project").onclick=()=>showBeginner();
$("beginner-back").onclick=()=>drawBeginner(false);
$("use-task-form").onclick=()=>{$("beginner-dialog").close();showProjectForm();};
$("beginner-form").onsubmit=async event=>{
  event.preventDefault();
  try {
    const fields=Object.fromEntries(new FormData(event.target));
    const brief=RunquayUI.createBrief(fields);
    if(!beginnerReview) {
      $("beginner-summary").innerHTML=`<h3>${esc(brief.name)}</h3><p>${esc(fields.purpose)}</p>${fields.audience.trim() ? `<p>For: ${esc(fields.audience)}</p>` : ""}${fields.features.trim() ? `<p>Must include: ${esc(fields.features)}</p>` : ""}<p>AI tool: ${esc(state.tools.find(t=>t.id===brief.provider)?.name || brief.provider)}</p>`;
      drawBeginner(true); return;
    }
    $("beginner-save").disabled=true;
    await api("/api/projects",brief);
    $("beginner-dialog").close(); setTaskFilter("active"); location.hash="#projects";
    toast(state.running ? "Task added. Your AI can begin when an account is available." : "Idea saved. Choose Start work on Home when you are ready.");
    await refresh();
  } catch(error) {toast(error.message);}
  finally {$("beginner-save").disabled=false;}
};
async function showResult(id) {
  try {
    const result=await api("/api/delivery/"+encodeURIComponent(id));
    resultProject=id;
    $("result-title").textContent=result.name;
    $("result-intro").textContent="Your AI reported this task finished. Try the result yourself before relying on it.";
    $("result-open-tip").textContent=result.has_webpage
      ? "Look for index.html in the folder. For a self-contained webpage, double-click it to open it in your browser. Check the instructions for any extra requirements."
      : "Read the instructions below for how to open and use your project. Some projects need extra setup.";
    $("result-instructions").textContent=RunquayUI.plainInstructions(result.instructions) || "Your AI has not left opening instructions yet. Choose Ask for help to request simple steps.";
    $("result-files").innerHTML=result.files.map(name=>`<li>${esc(name)}</li>`).join("") || "<li>No visible files found.</li>";
    $("result-dialog").showModal();
  } catch(error) {toast(error.message);}
}
$("result-folder").onclick=async()=>{if(await act("/api/project/folder",{id:resultProject})) toast("Asked your computer to open the project folder.");};
$("result-help").onclick=()=>{
  const project=state.projects.find(p=>p.id===resultProject);
  if(!project) return toast("This task is no longer available. Refresh and try again.");
  $("result-dialog").close();
  const form=$("resume-form");form.elements.id.value=project.id;
  form.elements.guidance.value="I do not know coding. Please explain exactly how to open and use this project, in plain numbered steps. Update START_HERE.md. If anything is missing, explain what I need to do. My difficulty is: ";
  form.elements.max_steps.value=Math.min(200,Math.max(project.max_steps,project.steps+3));
  $("resume-dialog").showModal();
};
document.addEventListener("click",event=>{
  const starter=event.target.closest("[data-starter]");if(starter) showBeginner(starter.dataset.starter);
  const result=event.target.closest('[data-action="result"]');if(result) showResult(result.dataset.id);
});
$("copy-login").onclick=async()=>{
  try {await navigator.clipboard.writeText($("login-command").textContent);toast("Instruction copied. Paste it into your terminal, then follow the tool's sign-in steps.");}
  catch(error) {toast("Copy was unavailable. Select the instruction above and copy it manually.");}
};
