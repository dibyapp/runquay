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
  for(const route of ["overview","projects","advisor","accounts","settings"]) assert.equal(ui.pageFor("#"+route),route);
  assert.equal(ui.pageFor("#approvals"),"overview");
  assert.equal(ui.pageFor("#activity"),"settings");
  assert.equal(ui.pageFor("#missing"),"overview");
  assert.equal(ui.pageFor(""),"overview");
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
