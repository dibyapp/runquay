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
  const starters = [
    {id:"website",title:"A personal website",kind:"website",purpose:"A personal website where I can introduce myself, show my interests and share a contact section.",features:"Easy to read on a phone. Use sample text that I can replace later."},
    {id:"checklist",title:"A daily checklist",kind:"tracker",purpose:"A checklist for my daily tasks. I want to add tasks, mark them done and remove them.",features:"Save my list in this browser. Include a clear way to empty it."},
    {id:"budget",title:"A simple expense tracker",kind:"tracker",purpose:"A simple expense tracker where I can enter a description and amount and see a total.",features:"Save entries in this browser. Use made-up examples, with no bank connection or sign-in."}
  ];
  function createBrief(input) {
    const names={website:"My simple website",tracker:"My useful tracker",tool:"My small tool",other:"My new project"};
    if(!Object.hasOwn(names,input.kind)) throw new Error("Choose what you would like to make.");
    const purpose=String(input.purpose || "").trim();
    if(!purpose) throw new Error("Describe your idea in a sentence or two.");
    const name=String(input.name || "").trim() || names[input.kind];
    const audience=String(input.audience || "").trim() || "People who do not know programming";
    const features=String(input.features || "").trim() || "Keep it simple, readable and easy to use.";
    const goal=[purpose,"Who it is for: "+audience,"Must include: "+features,
      "Choose the simplest practical implementation for someone who does not know coding. For a simple website, tracker or browser tool, prefer a self-contained index.html with embedded CSS and JavaScript that opens by double-clicking it. Use no external fonts, scripts, APIs, accounts, packages or build steps unless the stated goal requires them. If that simple approach cannot satisfy the goal, explain the actual requirements rather than claiming it works.",
      "Use fictional placeholder content. For saved browser data, explain that it stays in this browser and can be cleared; do not claim it is backed up or secure storage.",
      "Write START_HERE.md with plain, numbered instructions: where to find the entry file, exactly how to open and use it, a small manual check the user can try, known limitations and what to do if it does not open. Explain any unavoidable technical term. Do not invent successful tests or promise deployment.",
      "Run meaningful checks and report their results. Do not buy, publish, deploy or install software automatically. If human action is needed, stop and ask one clear question."
    ].join("\n\n");
    if(name.length>100 || goal.length>30000) throw new Error("Please shorten your project name or description.");
    return {name,goal,provider:input.provider || "codex",max_steps:3,priority:0};
  }
  function plainInstructions(text) {
    return String(text || "").replace(/^```[^\n]*$/gm, "").replace(/^#{1,6}\s+/gm, "")
      .replace(/\*\*([^*\n]+)\*\*/g, "$1").replace(/`([^`\n]+)`/g, "$1");
  }
  return {pageFor,nextStep,visibleTasks,visibleIdeas,starters,createBrief,plainInstructions,label:state => labels[state] || state};
})();
if (typeof module !== "undefined") module.exports = RunquayUI;
