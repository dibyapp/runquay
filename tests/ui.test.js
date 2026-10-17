"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const ui = require("../web/ui.js");

test("setup recommends a verified account, then an installed tool, then Codex",()=>{
  const tools=[{id:"codex",advisor:true,installed:false},{id:"claude",advisor:true,installed:true},{id:"antigravity",advisor:false,installed:true}];
  assert.equal(ui.recommendedTool({tools,profiles:[]}),"claude");
  assert.equal(ui.recommendedTool({tools,profiles:[{provider:"codex",enabled:true,eligible:true}]}),"codex");
  assert.equal(ui.recommendedTool({tools:[],profiles:[]}),"codex");
});
const base = {running:true, projects:[], decisions:[], profiles:[{provider:"codex",enabled:true,eligible:true}]};

test("legacy bookmarks and unknown routes always resolve to an accessible page",()=>{
  for(const route of ["overview","projects","advisor","learnings","accounts","settings"]) assert.equal(ui.pageFor("#"+route),route);
  assert.equal(ui.pageFor("#approvals"),"overview");
  assert.equal(ui.pageFor("#activity"),"settings");
  assert.equal(ui.pageFor("#missing"),"overview");
  assert.equal(ui.pageFor(""),"overview");
});
test("collective analysis has an actionable Home state while remaining separate from build tasks",()=>{
  const learnings={batches:[{topic:"SEO",state:"queued"}]};
  assert.equal(ui.nextStep({...base,running:false,learnings}).action,"start");
  assert.equal(ui.nextStep({...base,learnings}).href,"#learnings");
  assert.match(ui.nextStep({...base,learnings:{batches:[{topic:"DNS",state:"running"}]}}).title,/Collecting/);
});
test("pending and uncertain decisions remain actionable even with active work",()=>{
  for(const state of ["pending","uncertain","redeeming"]) assert.equal(ui.nextStep({...base,projects:[{state:"running",name:"Work"}],decisions:[{state}]}).href,"#approvals");
  assert.notEqual(ui.nextStep({...base,decisions:[{state:"declined"}]}).href,"#approvals");
});
test("a queued task in a paused app offers start, not another task",()=>{
  assert.equal(ui.nextStep({...base,running:false,projects:[{state:"queued",provider:"codex"}]}).action,"start");
});
test("an account from another provider cannot make a waiting task look ready",()=>{
  const state={...base,projects:[{state:"queued",provider:"claude"}]};
  assert.equal(ui.nextStep(state).href,"#accounts");
  assert.equal(ui.nextStep({...state,profiles:[{provider:"claude",enabled:false,eligible:true}]}).href,"#accounts");
  assert.equal(ui.nextStep({...state,profiles:[{provider:"claude",enabled:true,eligible:true}]}).href,"#projects");
});
test("a queued planner uses its own provider when checking availability",()=>{
  assert.equal(ui.nextStep({...base,advisor:{state:"queued",provider:"gemini"}}).href,"#accounts");
  assert.equal(ui.nextStep({...base,running:false,advisor:{state:"queued",provider:"codex"}}).action,"start");
});
test("blocked, paused and completed tasks have a concrete recovery or review step",()=>{
  assert.equal(ui.nextStep({...base,projects:[{state:"attention",name:"Fix"}]}).href,"#projects");
  assert.equal(ui.nextStep({...base,projects:[{state:"paused"}]}).href,"#projects");
  assert.equal(ui.nextStep({...base,projects:[{state:"complete"}]}).action,"finished");
  assert.equal(ui.nextStep({...base,profiles:[]}).action,"account");
});
test("task filters retain paused and blocked work and separate finished tasks",()=>{
  const tasks=["queued","running","paused","attention","complete","cancelled"].map(state=>({state}));
  assert.deepEqual(ui.visibleTasks(tasks,"active").map(p=>p.state),["queued","running","paused","attention"]);
  assert.deepEqual(ui.visibleTasks(tasks,"finished").map(p=>p.state),["complete","cancelled"]);
  assert.equal(ui.visibleTasks(tasks,"all").length,6);
});
test("unrecognized vendor statuses remain readable",()=>{
  assert.equal(ui.label("complete"),"Done");
  assert.equal(ui.label("attention"),"Needs you");
  assert.equal(ui.label("Not installed"),"Not installed");
});

test("selecting a project hides unrelated and dismissed ideas",()=>{
  const ideas=[
    {state:"proposed",payload:{kind:"existing",catalog_id:"one"}},
    {state:"proposed",payload:{kind:"existing",catalog_id:"two"}},
    {state:"proposed",payload:{kind:"new",catalog_id:""}},
    {state:"dismissed",payload:{kind:"existing",catalog_id:"one"}}
  ];
  assert.deepEqual(ui.visibleIdeas(ideas,"all","one"),[ideas[0]]);
  assert.deepEqual(ui.visibleIdeas(ideas,"new",""),[ideas[2]]);
  assert.equal(ui.visibleIdeas(ideas,"all","").length,3);
});

test("a beginner brief supplies opening instructions and bounded work",()=>{
  const brief=ui.createBrief({kind:"tracker",purpose:"A list for my groceries",features:"Large buttons",provider:"claude"});
  assert.equal(brief.name,"My useful tracker");
  assert.equal(brief.provider,"claude");
  assert.equal(brief.max_steps,3);
  assert.match(brief.goal,/A list for my groceries/);
  assert.match(brief.goal,/Large buttons/);
  assert.match(brief.goal,/START_HERE.md/);
  assert.match(brief.goal,/Do not buy, publish, deploy or install/);
  assert.match(brief.goal,/do not claim it is backed up/);
});

test("blank and oversized beginner input is rejected without inventing a goal",()=>{
  assert.throws(()=>ui.createBrief({kind:"website",purpose:"  "}),/Describe your idea/);
  assert.throws(()=>ui.createBrief({kind:"unknown",purpose:"Build"}),/Choose what/);
  assert.throws(()=>ui.createBrief({kind:"website",purpose:"Build",name:"x".repeat(101)}),/shorten/);
  assert.equal(ui.createBrief({kind:"website",purpose:" Build ",name:" My page "}).name,"My page");
});

test("opening instructions remove formatting markers while retaining literal HTML",()=>{
  assert.equal(ui.plainInstructions('# Open it\n1. Open `index.html` and choose **Next**.\n<script>unsafe()</script>'),
    'Open it\n1. Open index.html and choose Next.\n<script>unsafe()</script>');
});

test("detected current logins are reused without creating duplicate accounts",()=>{
  const state={tools:[{id:"codex",name:"Codex",installed:true}],profiles:[{id:"one",provider:"codex",current_login:true}]};
  assert.equal(ui.accountChoice(state,"codex").connected,true);
  assert.equal(ui.accountChoice(state,"codex").existing,true);
  assert.equal(ui.accountChoice(state,"codex",true).connected,false);
  assert.equal(ui.accountChoice(state,"codex",true).existing,false);
  assert.equal(ui.accountChoice(state,"codex",true).name,"Codex account 2");
});

test("a separate profile does not pretend to be the current login",()=>{
  const state={tools:[{id:"claude",name:"Claude Code",installed:true}],profiles:[{provider:"claude",current_login:false}]};
  assert.equal(ui.accountChoice(state,"claude").connected,false);
  assert.equal(ui.accountChoice(state,"claude").existing,true);
  assert.equal(ui.accountChoice(state,"antigravity",true).existing,true);
});

test("onboarding selects a verified enabled account for the chosen tool",()=>{
  const ready={id:"ready",provider:"codex",eligible:true,enabled:true};
  const state={profiles:[{provider:"codex",enabled:true,current_login:true},ready,{provider:"claude",eligible:true,enabled:true}]};
  assert.equal(ui.setupAccount(state,"codex"),ready);
  ready.enabled=false;
  assert.equal(ui.setupAccount(state,"codex"),state.profiles[0]);
  assert.equal(ui.setupAccount(state,"gemini"),null);
});

test("browser sign-in progress is scoped to the selected account",()=>{
  const profile={id:"one",instructions:{browser_login:true}};
  assert.equal(ui.loginView({},profile).browser,true);
  const state={login_in_progress:true,login_status:{profile_id:"two",state:"waiting",message:"Finish in browser"}};
  assert.equal(ui.loginView(state,profile).waiting,false);
  assert.equal(ui.loginView(state,profile).blocked,true);
  state.login_status.profile_id="one";
  assert.equal(ui.loginView(state,profile).waiting,true);
  state.login_in_progress=false;state.login_status.state="complete";
  assert.equal(ui.loginView(state,profile).complete,true);
  assert.equal(ui.loginView({},{}).browser,false);
});

test("fresh Codex setup preserves shared credentials and reuses a separate login profile",()=>{
  const current={provider:"codex",enabled:true,current_login:true,snapshot:{}};
  const state={profiles:[current]};
  assert.equal(ui.needsSetupAccount(state,"codex"),true);
  const separate={provider:"codex",enabled:true,current_login:false};
  state.profiles.push(separate);
  assert.equal(ui.setupAccount(state,"codex"),separate);
  assert.equal(ui.needsSetupAccount(state,"codex"),false);
  current.snapshot.account={type:"chatgpt"};
  assert.equal(ui.setupAccount(state,"codex"),current);
  assert.equal(ui.needsSetupAccount(state,"codex"),false);
});

test("existing Codex tasks search and project filters stay separate from queue status",()=>{
  const tasks=[{id:"one",title:"Fix checkout",project_name:"Shop",catalog_id:"shop"},
    {id:"two",title:"Build menu",project_name:"Cafe",catalog_id:"cafe"},
    {id:"three",title:"Notes",project_name:"No saved folder",catalog_id:""}];
  assert.deepEqual(ui.codexTasks(tasks," CHECKOUT ").map(t=>t.id),["one"]);
  assert.deepEqual(ui.codexTasks(tasks,"cafe").map(t=>t.id),["two"]);
  assert.deepEqual(ui.codexTasks(tasks,"","shop").map(t=>t.id),["one"]);
  assert.deepEqual(ui.codexTasks(tasks,"menu","shop"),[]);
  assert.equal(ui.codexTasks(tasks).length,3);
  assert.equal(tasks.length,3);
});

test("all vendor histories filter by tool without mixing providers",()=>{
  const tasks=[{id:"same",title:"Homepage",project_name:"Shop",catalog_id:"shop",tool:"Claude Code"},
    {id:"same",title:"Homepage",project_name:"Shop",catalog_id:"shop",tool:"Gemini CLI"},
    {id:"three",title:"Notes",project_name:"Unknown",catalog_id:"",tool:"Antigravity"}];
  assert.equal(ui.savedTasks(tasks,"","","Claude Code").length,1);
  assert.equal(ui.savedTasks(tasks,"gemini").length,1);
  assert.equal(ui.savedTasks(tasks,"homepage","shop","Gemini CLI").length,1);
  assert.equal(ui.savedTasks(tasks,"homepage","shop","Antigravity").length,0);
});

test("history grouping respects project IDs and keeps projectless sessions separate",()=>{
  const items=[{id:"a",catalog_id:"one",project_name:"App"},{id:"b",catalog_id:"two",project_name:"App"},
    {id:"c",catalog_id:"one",project_name:"App",tool:"Claude Code"},{id:"d",projectless:true,project_name:"No project",path:"/app"}];
  const groups=ui.historyGroups(items);
  assert.equal(groups.length,3);
  assert.deepEqual(groups[0].tasks.map(t=>t.id),["a","c"]);
  assert.equal(groups[2].name,"No project");
  assert.equal(items.length,4);
});

test("tool logo paths use a fixed local allowlist with a generic custom fallback",()=>{
  for(const provider of ["codex","claude","gemini","antigravity"]) assert.equal(ui.toolIcon(provider),`/tool-icons/${provider}.svg`);
  for(const provider of [undefined,"custom","../../private","https://untrusted.example/track"]) assert.equal(ui.toolIcon(provider),"/tool-icons/custom.svg");
});

const eventLog=events=>events.map(e=>JSON.stringify(e)).join("\n")+"\n";
test("Codex events become ordered messages and deduplicated command activity",()=>{
  const parsed=ui.sessionEvents(eventLog([
    {type:"thread.started",thread_id:"private-id"},{type:"turn.started"},
    {type:"item.completed",item:{id:"a",type:"agent_message",text:"I will inspect the app."}},
    {type:"item.started",item:{id:"b",type:"command_execution",command:"python -m unittest",status:"in_progress",aggregated_output:""}},
    {type:"item.completed",item:{id:"b",type:"command_execution",command:"python -m unittest",status:"completed",aggregated_output:"OK",exit_code:0}},
    {type:"item.completed",item:{id:"c",type:"agent_message",text:JSON.stringify({status:"complete",summary:"Built the app.",tests:"All checks passed.",next_step:"Review the files.",question:""})}}
  ]));
  assert.deepEqual(parsed.entries.map(e=>e.kind),["message","activity","result"]);
  assert.equal(parsed.entries[1].text,"OK");assert.equal(parsed.entries[1].status,"completed");
  assert.equal(parsed.entries[2].tests,"All checks passed.");
  assert.equal(parsed.cut,false);
});

test("private reasoning is excluded from messages and technical details",()=>{
  const parsed=ui.sessionEvents(eventLog([
    {type:"item.completed",item:{id:"r",type:"reasoning",text:"PRIVATE_REASONING"}},
    {type:"thinking",text:"PRIVATE_REASONING"},
    {type:"assistant",message:{id:"msg",content:[{type:"thinking",thinking:"PRIVATE_REASONING"},{type:"analysis",text:"PRIVATE_REASONING"},{type:"redacted_thinking",data:"PRIVATE_REASONING"},{type:"text",text:"Here is the result."}]}}
  ]));
  assert.equal(parsed.entries.length,1);
  assert.equal(parsed.entries[0].text,"Here is the result.");
  assert.ok(!JSON.stringify(parsed).includes("PRIVATE_REASONING"));
  const pretty={type:"assistant",message:{content:[{type:"thinking",thinking:"PRIVATE_REASONING"},{type:"text",text:"Public response"}]}};
  const wrapped=ui.sessionEvents(eventLog(JSON.stringify(pretty,null,2).split("\n").map(text=>({text}))));
  assert.equal(wrapped.entries[0].text,"Public response");
  assert.ok(!JSON.stringify(wrapped).includes("PRIVATE_REASONING"));
  const tail='cut byte fragment\n'+eventLog([{text:'  "thinking": "PRIVATE_REASONING",'},{text:'  "type": "thinking"'},{text:'}'}]);
  assert.equal(ui.sessionEvents(tail).entries.length,0);
  assert.ok(!JSON.stringify(ui.sessionEvents(tail)).includes("PRIVATE_REASONING"));
});

test("Claude tool events keep results together and provider envelopes show readable reports",()=>{
  const parsed=ui.sessionEvents(eventLog([
    {type:"assistant",message:{id:"a",content:[{type:"tool_use",id:"tool1",name:"Read",input:{file_path:"README.md"}}]}},
    {type:"user",message:{content:[{type:"tool_result",tool_use_id:"tool1",content:[{type:"text",text:"Project documentation"}]}]}},
    {type:"result",structured_output:{status:"blocked",summary:"A choice is needed.",tests:"Not run",question:"Which theme?"}},
    {response:"Gemini response"},{result:"Other tool response"},{response:{summary:"Nested provider report",tests:"OK"}}
  ]));
  assert.equal(parsed.entries.length,5);assert.equal(parsed.entries[0].title,"Read");
  assert.equal(parsed.entries[0].text,"Project documentation");assert.equal(parsed.entries[0].status,"completed");
  assert.equal(parsed.entries[1].question,"Which theme?");
  assert.equal(parsed.entries[2].text,"Gemini response");
  assert.equal(parsed.entries[4].kind,"result");
});

test("pretty printed provider JSON wrapped by the logger is reassembled without showing JSON fragments",()=>{
  const output={response:JSON.stringify({status:"complete",summary:"Ready",tests:"OK"})};
  const lines=JSON.stringify(output,null,2).split("\n").map(text=>({text}));
  const parsed=ui.sessionEvents(eventLog(lines));
  assert.equal(parsed.entries.length,1);assert.equal(parsed.entries[0].kind,"result");
  assert.equal(parsed.entries[0].text,"Ready");
});

test("bounded log tails and partial writes retain complete events and do not invent messages",()=>{
  const log='broken tail\n'+eventLog([{type:"item.completed",item:{id:"a",type:"agent_message",text:"Readable"}},{type:"turn.completed",usage:{input_tokens:1}}])+'{"type":"item.';
  const parsed=ui.sessionEvents(log);
  assert.equal(parsed.cut,true);assert.equal(parsed.entries.length,1);assert.equal(parsed.entries[0].text,"Readable");
  assert.equal(ui.sessionEvents("No output yet").entries.length,0);
  assert.equal(ui.sessionEvents(eventLog([{type:"unknown",data:"internal metadata"}])).entries.length,0);
});

test("errors, command failures and file edits remain visible without raw event envelopes",()=>{
  const parsed=ui.sessionEvents(eventLog([
    {type:"item.completed",item:{id:"a",type:"file_change",status:"completed",changes:[{kind:"update",path:"app.js"}]}},
    {type:"item.completed",item:{id:"b",type:"command_execution",command:"check",status:"completed",exit_code:1,aggregated_output:"Failed"}},
    {type:"turn.failed",error:{message:"Allowance reached"}},
    {type:"stderr",text:"\u001b[31mERROR: unavailable\u001b[0m"},
    {type:"result",is_error:true,result:"Provider failed"},{error:{message:"Vendor error"},status:"ERROR"}
  ]));
  assert.equal(parsed.entries[0].text,"update · app.js");assert.equal(parsed.entries[1].exitCode,1);
  assert.equal(parsed.entries[2].kind,"error");assert.equal(parsed.entries[3].text,"ERROR: unavailable");
  assert.equal(parsed.entries[4].kind,"error");
  assert.equal(parsed.entries[5].text,"Vendor error");
});

test("Markdown renders readable content while escaping executable HTML and unsafe links",()=>{
  const rendered=ui.markdown('# Result\n\n**Ready** with `code`\n\n- One\n- Two\n\n```js\n<script>alert(1)</script>\n```\n\n<img src=x onerror=alert(1)>\n[bad](javascript:alert) [local](file:///secret) [safe](https://example.com/a?x=1&y=2)');
  assert.ok(rendered.includes('<h4>Result</h4>'));assert.ok(rendered.includes('<strong>Ready</strong>'));
  assert.ok(rendered.includes('<ul><li>One</li><li>Two</li></ul>'));
  assert.ok(rendered.includes('&lt;script&gt;'));assert.ok(!rendered.includes('<script>'));assert.ok(!rendered.includes('<img'));
  assert.ok(!rendered.includes('href="javascript:'));assert.ok(!rendered.includes('href="file:'));
  assert.ok(rendered.includes('href="https://example.com/a?x=1&amp;y=2"'));assert.ok(rendered.includes('rel="noopener noreferrer"'));
  assert.ok(!ui.markdown('[bad](https://name:password@example.com)').includes('href='));
});

test("incomplete Markdown fences remain escaped and do not style adjacent messages",()=>{
  assert.equal(ui.markdown('```html\n<img src=x>'),'<pre><span class="code-language">html</span><code>&lt;img src=x&gt;</code></pre>');
  assert.equal(ui.markdown('1. First\n2. Second'),'<ol><li>First</li><li>Second</li></ol>');
  assert.equal(ui.markdown(null),"");
});

test("command previews keep the actual operation while hiding shell wrapper clutter",()=>{
  const command='"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content README.md"';
  assert.deepEqual(ui.commandPresentation(command),{title:"Read files",preview:"Get-Content README.md"});
  assert.equal(ui.commandPresentation('bash -lc "node --test tests/ui.test.js"').title,"Run checks");
  assert.equal(ui.commandPresentation('rg --files').title,"Explore project");
  assert.equal(ui.commandPresentation('git diff --stat').title,"Review changes");
  assert.equal(ui.commandPresentation('custom-command').preview,'custom-command');
});
