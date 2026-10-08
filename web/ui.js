"use strict";
// Pure display decisions shared by the browser and navigation regression tests.
const RunquayUI = (() => {
  const routes = {overview:"overview",projects:"projects",advisor:"advisor",accounts:"accounts",settings:"settings",approvals:"overview",activity:"settings"};
  const labels = {queued:"Waiting",running:"Working",paused:"Paused",attention:"Needs you",complete:"Done",cancelled:"Cancelled"};
  function pageFor(hash) { return routes[String(hash || "").replace(/^#/, "")] || "overview"; }
  function nextStep(state) {
    const tasks = state.projects || [];
    if ((state.decisions || []).some(d => ["pending","uncertain","redeeming"].includes(d.state))) return {title:"Your approval is needed",text:"Review the request below. You can keep waiting without approving a reset or a paid tool run.",label:"Review decisions",href:"#approvals"};
    const running = tasks.find(p => p.state === "running");
    if (running) return {title:"Your AI is working",text:running.name + ". Follow progress in Tasks, or pause work here.",label:"View task",href:"#projects"};
    if (state.advisor?.state === "running") return {title:"Finding ideas for you",text:"The AI is reading the selected project context. Suggestions will appear in Ideas.",label:"View ideas",href:"#advisor"};
    const attention = tasks.find(p => p.state === "attention");
    if (attention) return {title:"A task needs your help",text:attention.name + ". Read the task note, then continue with guidance.",label:"Review task",href:"#projects"};
    const queued = tasks.filter(p => p.state === "queued");
    if (queued.length || state.advisor?.state === "queued") {
      if (!state.running) return {title:"Ready when you are",text:"Your work is saved and waiting. Start work to let the AI begin.",label:"Start work",action:"start"};
      const providers = new Set(queued.map(p => p.provider || "codex"));
      if (state.advisor?.state === "queued") providers.add(state.advisor.provider || state.advisor_provider || "codex");
      const ready = (state.profiles || []).some(p => p.enabled && p.eligible && providers.has(p.provider || "codex"));
      return ready ? {title:"Your task is next",text:"Work will begin when the current account check finishes.",label:"View tasks",href:"#projects"} : {title:"Waiting for an available account",text:"Check sign-in and usage for the tool this task uses. You can also wait for its allowance to refresh.",label:"Check accounts",href:"#accounts"};
    }
    if (tasks.some(p => p.state === "paused")) return {title:"A task is paused",text:"Open Tasks and choose Continue when you want to pick it up again.",label:"View tasks",href:"#projects"};
    if (tasks.some(p => p.state === "complete")) return {title:"Your result is ready to review",text:"Open the finished task, inspect its files, and check the reported tests before accepting the work.",label:"Review results",action:"finished"};
    if (!(state.profiles || []).length) return {title:"Connect your AI account",text:"Add the coding tool and account you want to use, then create a task.",label:"Add account",action:"account"};
    return {title:"Start with one small task",text:"Tell the AI what to build or improve. Choose an existing folder or create a new project.",label:"Create a task",action:"new"};
  }
  function visibleTasks(tasks, filter) {
    return tasks.filter(p => filter === "all" || (filter === "finished" ? ["complete","cancelled"].includes(p.state) : !["complete","cancelled"].includes(p.state)));
  }
  function visibleIdeas(ideas, filter, target) {
    return ideas.filter(s => s.state === "proposed" && (filter === "all" || s.payload.kind === filter) && (!target || s.payload.catalog_id === target));
  }
  return {pageFor,nextStep,visibleTasks,visibleIdeas,label:state => labels[state] || state};
})();
if (typeof module !== "undefined") module.exports = RunquayUI;
