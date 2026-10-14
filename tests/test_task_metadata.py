import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock

from codex_brain import clean_path, path_key, path_contains, desktop_metadata, read_codex_tasks
from task_history import bind_tasks, task


class TaskMetadataTests(unittest.TestCase):
    def test_windows_extended_paths_case_slashes_and_unc_match_boundaries(self):
        self.assertEqual(path_key(r'\\?\C:\Work\App'),path_key('c:/work/app'))
        self.assertEqual(path_key(r'\\?\UNC\server\share\app'),path_key(r'\\server\share\app'))
        self.assertTrue(path_contains(r'\\?\C:\Work\App\src',r'C:\Work\App'))
        self.assertFalse(path_contains(r'C:\Work\App-other',r'C:\Work\App'))
        self.assertEqual(clean_path('/home/work/app'),'/home/work/app')
        self.assertFalse(path_contains('/home/work/app-other','/home/work/app'))

    def test_title_precedence_stored_fallback_preview_and_explicit_membership(self):
        rpc=Mock()
        rpc.call.return_value={'data':[{'id':'renamed','name':'Current name','preview':'Old goal'},
                                      {'id':'stored','name':None,'preview':'Long prompt'},
                                      {'id':'preview','preview':'A useful goal\nMore details'}]}
        metadata={'threads':{'renamed':{'name':'Stale name','title':'Original'},'stored':{'title':'Saved task title'}},
                  'assignments':{'renamed':'project'},'projectless':['preview']}
        tasks,_=read_codex_tasks(rpc,[],metadata=metadata)
        self.assertEqual([t['title'] for t in tasks],['Current name','Saved task title','A useful goal'])
        self.assertEqual(tasks[0]['project_id'],'project')
        self.assertTrue(tasks[2]['projectless'])
        self.assertEqual(rpc.call.call_args.args[0],'thread/list')
        self.assertTrue(rpc.call.call_args.args[1]['useStateDbOnly'])

    def test_desktop_metadata_is_read_only_bounded_and_ignores_extra_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);dbfile=root/'state.sqlite';state=root/'state.json'
            state.write_text(json.dumps({'thread-project-assignments':{'one':{'projectKind':'local','projectId':'p','credential':'ignored'}},
                                         'projectless-thread-ids':['two',None],'private_extra':'ignored'}))
            with sqlite3.connect(dbfile) as db:
                db.execute('CREATE TABLE threads(id TEXT,title TEXT,name TEXT,archived INTEGER,secret TEXT)')
                db.execute('INSERT INTO threads VALUES(?,?,?,?,?)',('one','x'*1000,'Renamed',0,'Do not read'))
                db.execute("INSERT INTO threads VALUES('archived','Old','Old',1,'private')")
            db.close()
            before=(state.read_bytes(),hashlib.sha256(dbfile.read_bytes()).digest())
            result=desktop_metadata(state,dbfile)
            self.assertEqual(result['assignments'],{'one':'p'})
            self.assertEqual(result['projectless'],['two'])
            self.assertEqual(len(result['threads']['one']['title']),240)
            self.assertEqual(result['threads']['one']['name'],'Renamed')
            self.assertNotIn('archived',result['threads'])
            self.assertNotIn('secret',json.dumps(result))
            self.assertEqual(before,(state.read_bytes(),hashlib.sha256(dbfile.read_bytes()).digest()))
            state.write_text('invalid')
            self.assertEqual(desktop_metadata(state,root/'missing')['threads'],{})

    def test_explicit_project_and_projectless_override_working_folder(self):
        library=[{'id':'one','name':'First','path':'/workspace/first'},
                 {'id':'two','name':'Second','path':'/workspace/second'},
                 {'id':'two-1','name':'Second','path':'/workspace/other-root'}]
        items=[dict(task('codex','assigned'),path='/workspace/first',project_id='two'),
               dict(task('codex','none'),path='/workspace/first',projectless=True),
               dict(task('codex','missing'),path='/workspace/first',project_id='unknown'),
               dict(task('codex','root-two'),path='/workspace/other-root/src',project_id='two')]
        result={t['id']:t for t in bind_tasks(items,library)}
        self.assertEqual(result['assigned']['catalog_id'],'two')
        self.assertEqual(result['none']['project_name'],'No project')
        self.assertEqual(result['none']['catalog_id'],'')
        self.assertEqual(result['missing']['project_name'],'Project not connected')
        self.assertEqual(result['root-two']['catalog_id'],'two-1')

    def test_extended_paths_bind_all_tool_histories_to_the_saved_project(self):
        items=[dict(task(provider,provider),path=r'\\?\C:\Projects\App\src') for provider in ('codex','claude','gemini','antigravity')]
        library=[{'id':'app','name':'Correct project','path':'c:/projects/app'}]
        result=bind_tasks(items,library)
        self.assertTrue(all(t['catalog_id']=='app' for t in result))
        self.assertTrue(all(not t['path'].startswith('\\\\?\\') for t in result))
