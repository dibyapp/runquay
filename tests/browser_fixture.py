"""Private disposable feature test server. Never discovers real chats or runs AI."""
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import tempfile
import threading
import time
import subprocess
import sys
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from supervisor import Handler, Supervisor
from task_history import task

out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='runquay-learnings-browser-') as directory:
    base=Path(directory);sup=Supervisor(base/'state','fixture-never-executed')
    sup.store.set('advisor_auto',False);sup.store.set('onboarded',True)
    sup.store.set('keep_awake',False)
    sup.profile_binary=lambda profile:'fixture-never-executed'
    sup.setup.snapshot=lambda:{'plans':{p:{'os':'Windows','ready':True,'automatic':False,'terminal':'Example instruction','docs':'https://example.com','names':[]} for p in ('codex','claude','gemini')},'status':{'state':'idle'},'detected':{'git':True}}
    sup.brain.discover=lambda:None
    sup.tool_status=lambda:[{'id':p,'name':name,'installed':True,'advisor':p in ('codex','claude','gemini'),'verification':'Fixture only'} for p,name in [('codex','Codex'),('claude','Claude Code'),('gemini','Gemini CLI'),('antigravity','Antigravity CLI'),('custom','Other AI')]]
    snapshot={'limits':{'rateLimitsByLimitId':{'codex':{'primary':{'usedPercent':10},'secondary':{'usedPercent':20},'credits':{'balance':'0','hasCredits':False,'unlimited':False}}}}}
    for p in ('codex','claude','gemini'):
        sup.store.execute('INSERT INTO profiles(id,name,home,provider,snapshot) VALUES(?,?,?,?,?)',(p,'Example '+p,str(base/p),p,json.dumps(snapshot)))
    rows=[]
    for n in range(20):
        provider=('claude','gemini','antigravity','custom')[n%4]
        root=base/f'product-{n+1:02}';root.mkdir()
        sup.store.execute("INSERT INTO catalog(id,name,path,source) VALUES(?,?,?,'Folder')",(f'product-{n}',f'Product {n+1:02}',str(root)))
        sup.store.execute('UPDATE catalog SET details=? WHERE id=?',(json.dumps({'exists':True,'files':[]}),f'product-{n}'))
        rows.append(task(provider,f'seo-{n}',f'SEO deployment for Product {n+1:02}',f'Checked sitemap URLs against canonical URLs after deployment. A stale base URL was corrected. No ranking change was measured. Example {n+1}.',str(root),1000+n,tool='Other AI' if provider=='custom' else ''))
    sup.store.set('other_tasks',[r for r in rows if r['provider']!='custom'])
    sup.store.set('imported_tasks',[r for r in rows if r['provider']=='custom'])
    sup.store.set('codex_tasks',[{'id':'dns-fixture','title':'DNS deployment review','preview':'Reduced DNS TTL before a planned migration and verified records afterward.','updated_at':2000}])
    more=[('security','Review workspace security','Verified inputs are escaped and secret files stay excluded.'),('dns','DNS cutover plan','Lowered DNS TTL before changing records; checked the resulting addresses.'),('devops','Deployment automation','Ran deployment checks in CI before changing the production service.'),('testing','Regression testing','Kept regression tests for the reported bug.'),('accessibility','Accessibility audit','Checked keyboard focus, contrast and reduced motion.'),('performance','Performance improvement','Measured rendering before and after reducing repeated layout work.')]
    sup.store.set('codex_tasks',[{'id':key,'title':title,'preview':preview,'updated_at':2000+i} for i,(key,title,preview) in enumerate(more)])
    real_popen=subprocess.Popen
    def fixture_popen(command,**kwargs):
        if command[0]!='fixture-never-executed':return real_popen(command,**kwargs)
        output=command[command.index('--output-last-message')+1]
        mode='advisor' if 'advisor-schema.json' in ' '.join(command) else 'slow' if sup.active_test_slow else 'complete'
        return real_popen([sys.executable,'-u',str(Path('tests/fake_worker.py').resolve()),mode,output],**kwargs)
    class FakeRpc:
        def close(self):pass
        def call(self,method,params):return {'data':[{'isDefault':True,'model':'fixture-model'}]}
    stop=threading.Event()
    sup.active_test_slow=False
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.supervisor=sup;server.token=secrets.token_urlsafe(32)
    (out/'browser-control.json').write_text(json.dumps({'url':f'http://127.0.0.1:{server.server_port}/#learnings','stop':str(base/'stop.flag')}),encoding='utf-8')
    def complete():
        while not (base/'stop.flag').exists():
            for batch in sup.store.rows("SELECT b.* FROM learning_batches b JOIN projects p ON p.id=b.id WHERE p.state='queued'"):
                time.sleep(.8)
                sup.store.execute("UPDATE projects SET state='running' WHERE id=?",(batch['id'],))
                refs=[s['id'] for s in json.loads(batch['sources'])]
                cards=[{'title':'Validate canonical and sitemap URLs after deployment','lesson':'Compare live canonical URLs with sitemap entries on each product site before asking search engines to index changes.','apply_when':'Product sites change a domain, base URL or deployment setting.','caveats':'The provided reports describe technical checks, not verified ranking gains.','tags':['seo','deployment'],'confidence':'reported','source_ids':refs},
                       {'title':'Test a migration before changing all products','lesson':'Try deployment changes on one product before applying them to the rest. <img src=x onerror=window.BAD=true>','apply_when':'Several products share deployment settings.','caveats':'This is a hypothesis from the source pattern; test it before reuse.','tags':['seo','devops'],'confidence':'hypothesis','source_ids':refs[:2]}]
                result={'status':'complete','summary':'Two lessons to review from the selected SEO reports.','tests':'Deterministic browser fixture; no AI calls.','next_step':'Review before reuse.','question':'','learnings':cards}
                sup.learnings.save(batch['id'],result)
                sup.store.execute("UPDATE projects SET state='complete',steps=1,checkpoint=? WHERE id=?",(json.dumps(result),batch['id']))
            pending=sup.pending_project()
            if not pending:
                pending=sup.store.one("SELECT * FROM projects WHERE kind='advisor' AND state='queued'")
            if pending and pending['kind'] in ('work','advisor'):
                profile=sup.store.one('SELECT * FROM profiles WHERE provider=?',(pending['provider'],))
                if pending['provider']!='codex':sup.select_external(pending,profile)
                else:
                    sup.active_test_slow=pending['name'].startswith('Browser slow task')
                    path=Path(pending['path'])
                    (path/'START_HERE.md').write_text('Open index.html in your browser. This is a fictional test result.',encoding='utf-8')
                    (path/'index.html').write_text('<!doctype html><title>Example result</title><h1>Example result</h1>',encoding='utf-8')
                    with patch('supervisor.subprocess.Popen',side_effect=fixture_popen):sup.run_step(pending,profile,FakeRpc())
            time.sleep(.15)
        server.shutdown()
    threading.Thread(target=complete,daemon=True).start()
    print('Disposable learnings browser fixture ready.',flush=True)
    try:server.serve_forever()
    finally:server.server_close();sup.children.close()
