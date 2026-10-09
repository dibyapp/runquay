import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from supervisor import Supervisor
from codex_brain import saved_projects, read_codex_tasks


class BrainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='autowork-brain-')
        self.base = Path(self.temp.name)
        self.workspace = self.base/'existing'
        self.workspace.mkdir()
        (self.workspace/'README.md').write_text('Existing project instructions',encoding='utf-8')
        (self.workspace/'AGENTS.md').write_text('Preserve these rules',encoding='utf-8')
        self.sup = Supervisor(self.base/'state','fixture-codex')
        self.state_file = self.base/'global.json'
        self.state_file.write_text(json.dumps({'local-projects':{'p1':{'id':'p1','name':'Existing project','rootPaths':[str(self.workspace)]}},'project-order':['p1']}),encoding='utf-8')
        self.sup.brain.discover(self.state_file)

    def tearDown(self):
        self.sup.children.close()
        self.temp.cleanup()

    def test_saved_library_is_discovered_and_metadata_is_unchanged(self):
        original=self.state_file.read_bytes()
        entries=saved_projects(self.state_file)
        self.assertEqual(entries[0]['name'],'Existing project')
        self.assertEqual(self.sup.state()['catalog'][0]['details']['readme'],'Existing project instructions')
        self.assertEqual(original,self.state_file.read_bytes())

    def test_codex_tasks_page_and_match_the_most_specific_folder(self):
        nested = self.workspace/'nested'
        roots = [{'id':'p1','name':'Root','path':str(self.workspace)},
                 {'id':'p2','name':'Nested','path':str(nested)}]
        task = {'id':'one','name':'Existing task','cwd':str(nested/'src'),'preview':'Summary','updatedAt':123}
        rpc = Mock()
        rpc.call.side_effect = [ {'data':[task,dict(task)],'nextCursor':'next'},
                                {'data':[{'id':'two','cwd':str(self.workspace)+'-other'},
                                         {'id':'child','parentThreadId':'one'},
                                         {'id':'ephemeral','ephemeral':True}],'nextCursor':None}]
        tasks, limited = read_codex_tasks(rpc,roots)
        self.assertFalse(limited)
        self.assertEqual([t['id'] for t in tasks],['one','two'])
        self.assertEqual(tasks[0]['catalog_id'],'p2')
        self.assertEqual(tasks[1]['catalog_id'],'')
        self.assertEqual(tasks[1]['title'],'Untitled Codex task')
        for call in rpc.call.call_args_list:
            self.assertEqual(call.args[0],'thread/list')
            self.assertTrue(call.args[1]['useStateDbOnly'])
            self.assertFalse(call.args[1]['archived'])
            self.assertIn('exec',call.args[1]['sourceKinds'])
        self.assertEqual(rpc.call.call_args_list[1].args[1]['cursor'],'next')

    def test_task_discovery_caches_metadata_without_queuing_work(self):
        task={'id':'one','name':'<unsafe title>','cwd':str(self.workspace),'preview':'x'*900,
              'email':'fixture@example.com','token':'should-not-be-copied','turns':[{'secret':'private'}]}
        rpc=Mock()
        rpc.call.return_value={'data':[task],'nextCursor':None}
        with patch('supervisor.Rpc',return_value=rpc):self.sup.brain.discover_tasks()
        result=self.sup.state()['codex_tasks'][0]
        self.assertEqual(result['title'],'<unsafe title>')
        self.assertEqual(len(result['preview']),700)
        self.assertEqual(result['catalog_id'],'p1')
        self.assertFalse({'email','token','turns'} & result.keys())
        self.assertEqual(self.sup.store.rows('SELECT * FROM projects'),[])
        self.assertEqual(self.sup.store.rows('SELECT * FROM runs'),[])
        rpc.close.assert_called_once()
        self.assertEqual(self.sup.state()['catalog'][0]['recent'][0]['id'],'one')

    def test_failed_task_refresh_retains_cache_and_hides_vendor_error(self):
        self.sup.store.set('codex_tasks',[{'id':'saved'}])
        self.sup.store.set('codex_tasks_checked',123)
        with patch('supervisor.Rpc',side_effect=RuntimeError('private credential')):
            self.sup.brain.discover_tasks()
        state=self.sup.state()
        self.assertEqual(state['codex_tasks'],[{'id':'saved'}])
        self.assertEqual(state['codex_tasks_checked'],123)
        self.assertNotIn('private credential',state['codex_tasks_error'])
        self.assertFalse(self.sup.brain.discovery_lock.locked())

    def test_bounded_pagination_and_repeated_cursor_detection(self):
        rpc=Mock()
        rpc.call.return_value={'data':[],'nextCursor':'next'}
        self.assertEqual(read_codex_tasks(rpc,[],max_pages=1),([],True))
        with self.assertRaises(ValueError):read_codex_tasks(rpc,[])
        rpc.call.return_value={'data':'bad'}
        with self.assertRaises(ValueError):read_codex_tasks(rpc,[])

    def test_queuing_existing_project_preserves_all_files(self):
        before={p.name:p.read_bytes() for p in self.workspace.iterdir()}
        ident=self.sup.create_project({'catalog_id':'p1','name':'Existing task','goal':'Implement a useful change'})
        self.assertEqual(self.sup.store.one('SELECT path FROM projects WHERE id=?',(ident,))['path'],str(self.workspace))
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.workspace.iterdir()})
        self.assertFalse((self.workspace/'.git').exists())
        with self.assertRaises(ValueError):
            self.sup.create_project({'catalog_id':'p1','name':'Duplicate','goal':'Another change'})

    def test_plan_requests_are_deduplicated(self):
        with patch.object(self.sup.brain,'discover',return_value=1):
            first=self.sup.brain.request_plan()
            second=self.sup.brain.request_plan()
        self.assertEqual(first,second)
        self.assertEqual(len(self.sup.store.rows("SELECT * FROM projects WHERE kind='advisor'")),1)

    def test_invalid_suggestion_does_not_poison_saved_ideas(self):
        result={'summary':'Test','suggestions':[{'title':'Broken','kind':'existing','catalog_id':'missing','why':'test','evidence':'test','goal':'test','first_milestone':'test','effort':'Small'}]}
        with self.assertRaises(ValueError): self.sup.brain.save_suggestions('fixture',result)
        self.assertEqual(self.sup.store.rows('SELECT * FROM suggestions'),[])

    def test_existing_suggestion_queues_the_correct_workspace_once(self):
        idea={'title':'Improve existing project','kind':'existing','catalog_id':'p1','why':'Useful','evidence':'README.md','goal':'Add a meaningful test','first_milestone':'Inspect the implementation','effort':'Small'}
        self.sup.brain.save_suggestions('fixture',{'summary':'A proposal','suggestions':[idea]})
        ident=self.sup.store.one('SELECT id FROM suggestions')['id']
        project_id=self.sup.brain.start_suggestion(ident)
        self.assertEqual(self.sup.store.one('SELECT path FROM projects WHERE id=?',(project_id,))['path'],str(self.workspace))
        self.assertEqual(self.sup.store.one('SELECT state FROM suggestions')['state'],'queued')
        with self.assertRaises(ValueError): self.sup.brain.start_suggestion(ident)


if __name__=='__main__':unittest.main()
