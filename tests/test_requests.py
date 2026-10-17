"""Explicit everyday requests must not wake unrelated work or bypass cost gates."""
import json
from pathlib import Path
import secrets
import tempfile
import unittest
import threading
import urllib.request
import http.cookiejar
from http.server import ThreadingHTTPServer
from supervisor import Supervisor, Store, Handler


class RequestTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='runquay-request-')
        self.base=Path(self.tmp.name)
        self.sup=Supervisor(self.base/'state','fixture-no-execution')
        self.sup.store.execute("INSERT INTO profiles(id,name,home,provider) VALUES('one','Example account',?,'codex')",(str(self.base/'account'),))
        self.sup.store.set('running',False)

    def tearDown(self):
        self.sup.children.close();self.tmp.cleanup()

    def data(self,**changes):
        return {'text':'Make a daily checklist','request_key':secrets.token_hex(16),**changes}

    def test_send_starts_only_its_request_and_keeps_global_queue_paused(self):
        old=self.sup.create_project({'name':'Older work','goal':'Wait for approval'})
        ident=self.sup.create_request(self.data())
        self.assertEqual(self.sup.pending_project()['id'],ident)
        self.assertFalse(self.sup.store.setting('running'))
        self.assertFalse(self.sup.work_allowed(self.sup.store.one('SELECT * FROM projects WHERE id=?',(old,))))
        requested=self.sup.store.one('SELECT * FROM projects WHERE id=?',(ident,))
        self.assertTrue(self.sup.work_allowed(requested))
        # The worker checks fresh consent, not its stale task snapshot.
        self.sup.store.execute('UPDATE projects SET run_requested=0')
        self.assertFalse(self.sup.work_allowed(requested))
        self.assertIsNone(self.sup.pending_project())

    def test_installation_temporarily_blocks_even_an_authorized_request(self):
        ident=self.sup.create_request(self.data())
        project=self.sup.store.one('SELECT * FROM projects WHERE id=?',(ident,))
        self.sup.setup.lock.acquire()
        try:
            self.assertIsNone(self.sup.pending_project())
            self.assertFalse(self.sup.work_allowed(project))
        finally:self.sup.setup.lock.release()
        self.assertEqual(self.sup.pending_project()['id'],ident)

    def test_retry_does_not_create_a_second_project_and_changed_request_is_rejected(self):
        data=self.data();ident=self.sup.create_request(data)
        self.assertEqual(self.sup.create_request(data),ident)
        with self.assertRaises(ValueError):self.sup.create_request({**data,'text':'Different work'})
        self.assertEqual(len(self.sup.store.rows('SELECT * FROM projects')),1)
        self.assertEqual(len(list((self.base/'state/workspaces').iterdir())),1)

    def test_explicit_folder_is_used_without_changing_other_projects(self):
        folder=self.base/'existing';folder.mkdir();(folder/'README.md').write_text('Keep me',encoding='utf-8')
        self.sup.store.execute("INSERT INTO catalog(id,name,path,source) VALUES('existing','Example project',?,'folder')",(str(folder),))
        ident=self.sup.create_request(self.data(catalog_id='existing'))
        self.assertEqual(Path(self.sup.store.one('SELECT path FROM projects WHERE id=?',(ident,))['path']),folder)
        self.assertEqual((folder/'README.md').read_text(encoding='utf-8'),'Keep me')
        self.assertFalse((folder/'AGENTS.md').exists())
        with self.assertRaises(ValueError):self.sup.create_request(self.data(catalog_id='existing'))

    def test_missing_or_disabled_accounts_do_not_create_work(self):
        self.sup.store.execute('UPDATE profiles SET enabled=0')
        with self.assertRaises(ValueError):self.sup.create_request(self.data())
        self.assertEqual(self.sup.store.rows('SELECT * FROM projects'),[])

    def test_other_provider_is_explicit_and_still_requires_per_run_approval(self):
        self.sup.store.execute("INSERT INTO profiles(id,name,home,provider) VALUES('claude','Example Claude',?,'claude')",(str(self.base/'claude'),))
        ident=self.sup.create_request(self.data(provider='claude'))
        project=self.sup.store.one('SELECT * FROM projects WHERE id=?',(ident,))
        self.assertEqual(project['provider'],'claude')
        profile=self.sup.store.one("SELECT * FROM profiles WHERE id='claude'")
        self.assertFalse(self.sup.select_external(project,profile))
        self.assertEqual(self.sup.store.one('SELECT kind,state FROM decisions'),{'kind':'external_run','state':'pending'})

    def test_invalid_request_and_setup_in_progress_make_no_workspace(self):
        for change in ({'text':''},{'text':'x'*10001},{'request_key':'bad'},{'provider':'missing'},{'catalog_id':'missing'}):
            with self.assertRaises(ValueError):self.sup.create_request(self.data(**change))
        self.sup.setup.lock.acquire()
        try:
            with self.assertRaises(ValueError):self.sup.create_request(self.data())
        finally:self.sup.setup.lock.release()
        self.assertEqual(self.sup.store.rows('SELECT * FROM projects'),[])

    def test_upgrade_is_idempotent_and_old_tasks_stay_paused(self):
        ident=self.sup.create_project({'name':'Older work','goal':'Wait'})
        Store(self.base/'state')
        self.assertEqual(self.sup.store.one('SELECT run_requested FROM projects WHERE id=?',(ident,))['run_requested'],0)
        self.assertIsNone(self.sup.pending_project())

    def test_concurrent_retries_create_one_workspace(self):
        data=self.data();results=[]
        threads=[threading.Thread(target=lambda:results.append(self.sup.create_request(data))) for _ in range(4)]
        for thread in threads:thread.start()
        for thread in threads:thread.join()
        self.assertEqual(len(results),4)
        self.assertEqual(len(set(results)),1)
        self.assertEqual(len(self.sup.store.rows('SELECT * FROM projects')),1)

    def test_http_pause_disarms_scoped_work_and_expires_vendor_approval(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        server.supervisor=self.sup;server.token=secrets.token_urlsafe(32)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            url=f'http://127.0.0.1:{server.server_port}'
            opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
            opener.open(url+'/').close()
            def post(path,data):
                request=urllib.request.Request(url+path,data=json.dumps(data).encode(),headers={'Content-Type':'application/json','X-AutoWork-CSRF':server.token,'Origin':url})
                with opener.open(request) as response:return json.load(response)
            ident=post('/api/requests',self.data())['id']
            project=self.sup.store.one('SELECT * FROM projects WHERE id=?',(ident,))
            self.assertTrue(self.sup.work_allowed(project))
            post('/api/control',{'action':'pause'})
            self.assertFalse(self.sup.work_allowed(project))
            self.assertIsNone(self.sup.pending_project())
            post('/api/project',{'id':ident,'action':'resume','run_now':True})
            self.assertTrue(self.sup.work_allowed(project))
            payload=json.dumps({'project_id':ident})
            self.sup.store.execute("INSERT INTO decisions(id,profile_id,kind,payload,created) VALUES('approval','one','external_run',?,'2026-01-01')",(payload,))
            post('/api/project',{'id':ident,'action':'pause'})
            self.assertFalse(self.sup.work_allowed(project))
            self.assertEqual(self.sup.store.one("SELECT state FROM decisions WHERE id='approval'")['state'],'expired')
        finally:
            server.shutdown();server.server_close();thread.join()
