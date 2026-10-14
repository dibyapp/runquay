"use strict";
// Pure display decisions shared by the browser and navigation regression tests.
const RunquayUI = (() => {
  function savedTasks(tasks, search="", folder="", tool="") {
    const query=search.trim().toLocaleLowerCase();
    return tasks.filter(t=>(!folder || t.catalog_id===folder) && (!tool || t.tool===tool) && (!query || `${t.title} ${t.project_name} ${t.tool || ""}`.toLocaleLowerCase().includes(query)));
  }
  function recommendedTool(state) {
    const ready=(state.profiles||[]).find(p=>p.enabled && p.eligible && (state.tools||[]).some(t=>t.id===p.provider && t.advisor));
    return ready?.provider || (state.tools||[]).find(t=>t.installed && t.advisor)?.id || "codex";
  }
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
  function accountChoice(state, provider, separate=false) {
    const tool=(state.tools || []).find(t=>t.id===provider);
    const profiles=(state.profiles || []).filter(p=>p.provider===provider);
    const current=profiles.find(p=>p.current_login);
    return {tool,current,existing:provider==="antigravity" || !separate,
      name:(tool?.name || "AI")+" account "+(profiles.length+1),
      connected:Boolean(current && (provider==="antigravity" || !separate))};
  }
  function setupAccount(state, provider) {
    const profiles=(state.profiles || []).filter(p=>p.provider===provider);
    const current=profiles.find(p=>p.enabled && p.current_login);
    return profiles.find(p=>p.enabled && p.eligible) || (current?.snapshot?.account?.type==="chatgpt" ? current : null) || profiles.find(p=>p.enabled && !p.current_login) || current || null;
  }
  function needsSetupAccount(state, provider) {
    const profile=setupAccount(state,provider);
    return !profile || (provider==="codex" && profile.current_login && !profile.eligible && profile.snapshot?.account?.type!=="chatgpt");
  }
  function loginView(state, profile) {
    const own=state.login_status?.profile_id===profile?.id ? state.login_status : null;
    const waiting=Boolean(state.login_in_progress && own?.state==="waiting");
    const complete=own?.state==="complete";
    return {browser:Boolean(profile?.instructions?.browser_login),waiting,complete,
      blocked:Boolean(state.login_in_progress),message:own?.message || ""};
  }
  function toolIcon(provider) {
    return "/tool-icons/" + (["codex","claude","gemini","antigravity"].includes(provider) ? provider : "custom") + ".svg";
  }
  function historyGroups(tasks) {
    const groups=new Map();
    for(const item of tasks) {
      const key=item.catalog_id ? "project:"+item.catalog_id : item.projectless ? "no-project" : item.project_id ? "unconnected:"+item.project_id : item.path ? "folder:"+item.path : "unknown";
      if(!groups.has(key)) groups.set(key,{key,name:item.project_name || "Folder not recorded",tasks:[]});
      groups.get(key).tasks.push(item);
    }
    return [...groups.values()];
  }
  const cleanText=value=>typeof value==="string" ? value.replace(/\x1b\[[0-?]*[ -/]*[@-~]/g,"").replace(/\r/g,"") : "";
  const escapeHTML=value=>String(value ?? "").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  // Deliberately small Markdown subset. Raw HTML, images and local/unsafe URLs never execute.
  function markdown(value) {
    function inline(text) {
      return text.split(/(`[^`\n]+`|\[[^\]\n]+\]\([^\s)]+\))/g).map(part=>{
        if(part.startsWith("`") && part.endsWith("`")) return `<code>${escapeHTML(part.slice(1,-1))}</code>`;
        const link=part.match(/^\[([^\]\n]+)\]\(([^\s)]+)\)$/);
        if(link) {
          let safe=false;
          try {const url=new URL(link[2]);safe=["https:","http:"].includes(url.protocol) && !url.username && !url.password;} catch {}
          return safe ? `<a href="${escapeHTML(link[2])}" target="_blank" rel="noopener noreferrer">${escapeHTML(link[1])}</a>` : escapeHTML(link[1]);
        }
        return escapeHTML(part).replace(/\*\*([^*\n]+)\*\*/g,"<strong>$1</strong>");
      }).join("");
    }
    const lines=cleanText(value).split("\n"), html=[];
    let code=null,language="",paragraph=[],list=null;
    const flush=()=>{if(paragraph.length) html.push(`<p>${paragraph.map(inline).join("<br>")}</p>`);paragraph=[];if(list) {html.push(`</${list}>`);list=null;}};
    for(const line of lines) {
      if(/^\s*```/.test(line)) {
        if(code!==null) {html.push(`<pre><span class="code-language">${escapeHTML(language || "Code")}</span><code>${escapeHTML(code.join("\n"))}</code></pre>`);code=null;}
        else {flush();code=[];language=line.trim().slice(3).trim().slice(0,30);}
        continue;
      }
      if(code!==null) {code.push(line);continue;}
      if(!line.trim()) {flush();continue;}
      const heading=line.match(/^#{1,6}\s+(.+)/), bullet=line.match(/^\s*(?:([-*])|\d+[.)])\s+(.+)/);
      if(heading) {flush();html.push(`<h4>${inline(heading[1])}</h4>`);}
      else if(bullet) {if(paragraph.length) flush();const kind=bullet[1] ? "ul" : "ol";if(list!==kind) {flush();list=kind;html.push(`<${kind}>`);}html.push(`<li>${inline(bullet[2])}</li>`);}
      else {if(list) flush();paragraph.push(line);}
    }
    if(code!==null) html.push(`<pre><span class="code-language">${escapeHTML(language || "Code")}</span><code>${escapeHTML(code.join("\n"))}</code></pre>`);
    flush();return html.join("");
  }
  function sessionEvents(log) {
    const entries=[], positions=new Map(), diagnostics=[];
    let pending="",cut=false;
    const add=(entry,id)=>{if(id && positions.has(id)) entries[positions.get(id)]={...entries[positions.get(id)],...entry,key:id};else {const key=id || "event-"+entries.length;positions.set(key,entries.length);entries.push({...entry,key});}};
    function message(value,id) {
      const text=cleanText(value);if(!text.trim()) return;
      try {const structured=JSON.parse(text.replace(/^```(?:json)?\s*|\s*```$/g,""));if(structured && typeof structured.summary==="string") {result(structured,id);return;}} catch {}
      add({kind:"message",text},id);
    }
    function result(value,id) {
      if(typeof value==="string") {message(value,id);return;}
      if(!value || typeof value!=="object") return;
      if(typeof value.summary==="string") add({kind:"result",text:cleanText(value.summary),tests:cleanText(value.tests),next:cleanText(value.next_step),question:cleanText(value.question),status:cleanText(value.status)},id);
      else if(value.response && typeof value.response==="object") result(value.response,id);
      else if(typeof value.response==="string") message(value.response,id);
      else if(typeof value.result==="string") message(value.result,id);
    }
    function consume(record,index) {
      if(!record || typeof record!=="object") return;
      const type=record.type || "", item=record.item;
      // Private reasoning is never rendered, including in the diagnostic disclosure.
      if(/reasoning|thinking|analysis/.test(type) || /reasoning|thinking|analysis/.test(item?.type || "")) return;
      if(!type && typeof record.text==="string") {
        const text=cleanText(record.text);
        if(pending || /^\s*[\[{]/.test(text)) {
          pending+=text+"\n";
          try {const value=JSON.parse(pending);pending="";consume(value,index);} catch {if(pending.length>80000) pending="";}
          return;
        }
      }
      diagnostics.push(JSON.stringify(record));
      if(item && /^item\./.test(type)) {
        const key="item:"+(item.id ?? index);
        if(item.type==="agent_message") message(item.text,key);
        else if(item.type==="command_execution") add({kind:"activity",title:"Run command",command:cleanText(item.command),text:cleanText(item.aggregated_output),status:cleanText(item.status) || (type==="item.completed" ? "completed" : "in_progress"),exitCode:item.exit_code},key);
        else if(item.type==="file_change") add({kind:"activity",title:"Update files",text:(item.changes || []).map(c=>`${cleanText(c.kind) || "Update"} · ${cleanText(c.path)}`).join("\n"),status:cleanText(item.status) || "completed"},key);
        else if(["mcp_tool_call","web_search"].includes(item.type)) add({kind:"activity",title:item.type==="web_search" ? "Search the web" : "Use tool",command:cleanText(item.tool || item.query),text:cleanText(item.error?.message),status:cleanText(item.status) || "completed"},key);
      } else if(type==="assistant" && Array.isArray(record.message?.content)) {
        record.message.content.forEach((block,n)=>{
          if(block.type==="text") message(block.text,`assistant:${record.message.id || index}:${n}`);
          else if(block.type==="tool_use") add({kind:"activity",title:cleanText(block.name) || "Use tool",command:cleanText(block.input?.command),text:cleanText(block.input?.file_path),status:"in_progress"},"tool:"+(block.id || `${index}:${n}`));
        });
        // Keep diagnostics useful without retaining thinking blocks from vendor envelopes.
        diagnostics[diagnostics.length-1]=JSON.stringify({...record,message:{...record.message,content:record.message.content.filter(b=>!["thinking","redacted_thinking","reasoning"].includes(b.type))}});
      } else if(type==="user" && Array.isArray(record.message?.content)) {
        for(const block of record.message.content) if(block.type==="tool_result") {
          const id="tool:"+block.tool_use_id;
          const text=typeof block.content==="string" ? block.content : Array.isArray(block.content) ? block.content.filter(b=>b.type==="text").map(b=>cleanText(b.text)).join("\n") : "";
          add({kind:"activity",title:positions.has(id) ? entries[positions.get(id)].title : "Tool result",text:cleanText(text),status:block.is_error ? "failed" : "completed"},id);
        }
      } else if(["error","turn.failed"].includes(type)) add({kind:"error",text:cleanText(record.message || record.error?.message) || "The tool reported an error. Open Details for diagnostics."});
      else if(type==="stderr") {if(/error|failed|denied|not found|limit|quota/i.test(record.text || "")) add({kind:"notice",text:cleanText(record.text)});}
      else if(record.is_error || record.error || ["ERROR","CANCELED","INTERRUPTED"].includes(record.status)) add({kind:"error",text:cleanText(record.result || record.error?.message || record.error) || "The tool reported an error."});
      else if(record.structured_output) result(record.structured_output,"result:"+index);
      else if(record.summary || record.result || record.response) result(record,"result:"+index);
      else if(!type && typeof record.text==="string") {
        const text=cleanText(record.text);
        if(text.trim()) add({kind:"notice",text});
      }
    }
    const lines=String(log || "").split("\n");
    for(let index=0;index<lines.length;index++) {
      const line=lines[index];if(!line.trim() || line==="No output yet") continue;
      try {consume(JSON.parse(line),index);} catch {if(index===0) cut=true;}
    }
    return {entries,diagnostics:diagnostics.join("\n"),cut};
  }
  function commandPresentation(command) {
    const text=cleanText(command).trim();
    const wrapped=text.match(/\s(?:-Command|-c|-lc)\s+([\s\S]+)$/i);
    const preview=(wrapped ? wrapped[1].replace(/^["']|["']$/g,"") : text).trim();
    const title=/\b(unittest|pytest|npm test|npm run (?:test|lint|build)|node --test)\b/i.test(preview) ? "Run checks" : /\b(Get-Content|cat|head|tail)\b/i.test(preview) ? "Read files" : /\b(Get-ChildItem|Get-Location|rg|ls|find|pwd)\b/i.test(preview) ? "Explore project" : /\bgit (?:diff|status|log)\b/i.test(preview) ? "Review changes" : "Run command";
    return {title,preview};
  }
  return {commandPresentation,markdown,sessionEvents,toolIcon,historyGroups,savedTasks,codexTasks:savedTasks,pageFor,nextStep,visibleTasks,visibleIdeas,starters,createBrief,plainInstructions,accountChoice,setupAccount,needsSetupAccount,loginView,recommendedTool,label:state => labels[state] || state};
})();
if (typeof module !== "undefined") module.exports = RunquayUI;
