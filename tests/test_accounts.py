import http.cookiejar
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

from security import account_hint
from supervisor import Handler, Supervisor


class AccountIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="runquay-identity-")
        self.sup = Supervisor(Path(self.temp.name), "test-codex")
        self.ident = self.sup.add_profile({"provider":"codex", "name":"Original", "existing":False})

    def tearDown(self):
        self.sup.children.close()
        self.temp.cleanup()

    def test_refresh_keeps_only_masked_identity_and_never_invents_a_name(self):
        calls=[]
        class Rpc:
            def call(self, method, params=None):
                calls.append(method)
                if method == "account/read":
                    return {"account":{"type":"chatgpt", "planType":"plus", "email":"alex.smith@example.com",
                                       "name":"Private vendor name", "accessToken":"must never be retained"}}
                return {"rateLimits":{"primary":{"usedPercent":0}}}
        profile=self.sup.store.one("SELECT * FROM profiles WHERE id=?",(self.ident,))
        self.sup.refresh(profile,Rpc())
        saved=self.sup.store.one("SELECT * FROM profiles WHERE id=?",(self.ident,))
        account=json.loads(saved['snapshot'])['account']
        self.assertEqual(account['signInHint'],'al•••@e•••.com')
        self.assertEqual(saved['name'],'Original')
        for secret in ('alex.smith@example.com','Private vendor name','must never be retained'):
            self.assertNotIn(secret,saved['snapshot'])
        self.assertEqual(set(account),{'type','planType','signInHint'})
        self.assertEqual(calls,['account/read','account/rateLimits/read'])
        self.sup.rename_profile(self.ident,'Work')
        self.sup.refresh(self.sup.store.one("SELECT * FROM profiles WHERE id=?",(self.ident,)),Rpc())
        self.assertEqual(self.sup.store.one("SELECT name FROM profiles WHERE id=?",(self.ident,))['name'],'Work')

    def test_missing_or_malformed_email_has_no_identity_hint(self):
        for value in (None, {}, 'not an email', 'private@example.com\nmore', '<script>@example.com', 'x'*255+'@example.com'):
            self.assertEqual(account_hint(value),'')
        self.assertEqual(account_hint('ab@example.com'),'a•••@e•••.com')
        self.assertEqual(account_hint('a@example.com'),'•••@e•••.com')

    def test_rename_changes_only_the_local_label_and_rejects_unsafe_input(self):
        before=self.sup.store.one("SELECT * FROM profiles WHERE id=?",(self.ident,))
        self.sup.rename_profile(self.ident,'  Work — main  ')
        after=self.sup.store.one("SELECT * FROM profiles WHERE id=?",(self.ident,))
        self.assertEqual(after.pop('name'),'Work — main')
        before.pop('name')
        self.assertEqual(after,before)
        for value in (None, 1, '', '  ', 'x'*81, 'one\ntwo','one\x00two','password='+'x'*16):
            with self.assertRaises(ValueError): self.sup.rename_profile(self.ident,value)
        with self.assertRaises(ValueError): self.sup.rename_profile('missing','Work')
        self.assertEqual(self.sup.store.rows('SELECT * FROM projects'),[])
        self.assertEqual(self.sup.store.rows('SELECT * FROM runs'),[])

    def test_http_rename_requires_local_session_csrf_and_origin(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        server.supervisor=self.sup
        server.token='fixture-secret'
        worker=threading.Thread(target=server.serve_forever,daemon=True)
        worker.start()
        base='http://127.0.0.1:'+str(server.server_port)
        client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        def rename(headers):
            data=json.dumps({'action':'rename','id':self.ident,'name':'Personal'}).encode()
            with client.open(urllib.request.Request(base+'/api/account',data=data,headers=headers)) as response:
                return json.load(response)
        try:
            for headers in ({},{'X-AutoWork-CSRF':server.token}):
                with self.assertRaises(urllib.error.HTTPError) as error: rename(headers)
                self.assertEqual(error.exception.code,403)
            client.open(base+'/').close()
            with self.assertRaises(urllib.error.HTTPError) as error:
                rename({'X-AutoWork-CSRF':server.token,'Origin':'https://untrusted.example'})
            self.assertEqual(error.exception.code,403)
            self.assertEqual(self.sup.store.one('SELECT name FROM profiles')['name'],'Original')
            self.assertTrue(rename({'X-AutoWork-CSRF':server.token,'Origin':base})['ok'])
            self.assertEqual(self.sup.store.one('SELECT name FROM profiles')['name'],'Personal')
        finally:
            server.shutdown();server.server_close();worker.join()


if __name__ == '__main__':
    unittest.main()
