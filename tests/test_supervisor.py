import http.cookiejar
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from supervisor import Handler, ROOT, Supervisor, Store, profile_env, quota_gate
from http.server import ThreadingHTTPServer


def allowance(used=20, balance="0"):
    return {"rateLimitsByLimitId": {"codex": {"primary": {"usedPercent": used, "resetsAt": 900},
            "secondary": {"usedPercent": 40, "resetsAt": 1200},
            "credits": {"hasCredits": balance != "0", "unlimited": False, "balance": balance}}}}


class GateTests(unittest.TestCase):
    def test_available_subscription(self):
        self.assertTrue(quota_gate(allowance())[0])

    def test_reserve_and_reset(self):
        self.assertEqual(quota_gate(allowance(90))[::2], (False, 900))
        limits = allowance(95)
        limits["rateLimitsByLimitId"]["codex"]["secondary"]["usedPercent"] = 100
        self.assertEqual(quota_gate(limits)[2], 1200)

    def test_positive_unknown_and_unlimited_credits_blocked(self):
        for balance in ("1", "unknown", None):
            self.assertFalse(quota_gate(allowance(balance=balance))[0])
        q = allowance()
        del q["rateLimitsByLimitId"]["codex"]["credits"]
        self.assertFalse(quota_gate(q)[0])
        q = allowance()
        q["rateLimitsByLimitId"]["codex"]["credits"]["unlimited"] = True
        self.assertFalse(quota_gate(q)[0])

    def test_unknown_quota_and_denied_ordinary_usage(self):
        self.assertFalse(quota_gate({})[0])
        q = allowance()
        q["ordinaryUsageAllowed"] = False
        self.assertFalse(quota_gate(q)[0])

    def test_environment_never_inherits_api_keys(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "CODEX_API_KEY": "test-key", "CODEX_ACCESS_TOKEN": "test-token"}):
            env = profile_env("fixture-home")
        self.assertNotIn("OPENAI_API_KEY", env)
        self.assertNotIn("CODEX_API_KEY", env)
        self.assertNotIn("CODEX_ACCESS_TOKEN", env)
        self.assertEqual(env["CODEX_HOME"], "fixture-home")


class RelativeDataTests(unittest.TestCase):
    def test_worker_result_survives_a_different_workspace_cwd(self):
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder).resolve()
            work = base / "workspace"
            work.mkdir()
            sup = None
            try:
                os.chdir(base)
                sup = Supervisor("state", "test-codex")
                sup.store.set("running", True)
                sup.store.execute("INSERT INTO projects(id,name,goal,path,created) VALUES('relative','Relative path','Check result',?,'2026-10-08')", (str(work),))
                profile = {"id": "relative-account", "home": str(base), "name": "Fixture"}
                sup.store.execute("INSERT INTO profiles(id,name,home) VALUES(?,?,?)", (profile["id"], profile["name"], profile["home"]))
                real_popen = subprocess.Popen
                fixture = ROOT / "tests/fake_worker.py"
                class FakeRpc:
                    def close(self): pass
                    def call(self, method, params):
                        return {"data": [{"isDefault": True, "model": "fixture-model"}]}
                def popen(command, **kwargs):
                    if command[0] != "test-codex":
                        return real_popen(command, **kwargs)
                    output = command[command.index("--output-last-message") + 1]
                    self.assertTrue(Path(output).is_absolute())
                    return real_popen([sys.executable, "-u", str(fixture), "complete", output], **kwargs)
                with patch("supervisor.subprocess.Popen", side_effect=popen):
                    sup.run_step(sup.store.one("SELECT * FROM projects"), profile, FakeRpc())
                self.assertEqual(sup.store.one("SELECT state FROM projects")["state"], "complete")
            finally:
                if sup:
                    sup.children.close()
                os.chdir(original)


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="autowork-tests-")
        self.sup = Supervisor(Path(self.temp.name), "test-codex")
        self.store = self.sup.store
        self.store.set("running", True)
        self.profile = {"id": "fixture-account", "home": self.temp.name, "name": "Fixture account"}
        self.store.execute("INSERT INTO profiles(id,name,home) VALUES(?,?,?)", (self.profile["id"], self.profile["name"], self.profile["home"]))
        self.store.execute("INSERT INTO projects(id,name,goal,path,created) VALUES('fixture','Fixture','A test goal',?,'2026-10-08')", (self.temp.name,))

    def tearDown(self):
        self.sup.children.close()
        self.temp.cleanup()

    def run_fixture(self, mode):
        real_popen = subprocess.Popen
        fixture = Path(__file__).with_name("fake_worker.py")
        class FakeRpc:
            def close(self): pass
            def call(self, method, params):
                return {"data": [{"isDefault": True, "model": "fixture-model"}]}
        def popen(command, **kwargs):
            if command[0] != "test-codex":
                return real_popen(command, **kwargs)
            self.assertIn("read-only" if mode == "advisor" else "workspace-write", command)
            self.assertIn('forced_login_method="chatgpt"', command)
            self.assertIn("--ignore-user-config", command)
            output = command[command.index("--output-last-message") + 1]
            return real_popen([sys.executable, "-u", str(fixture), mode, output], **kwargs)
        project = self.store.one("SELECT * FROM projects WHERE id='fixture'")
        with patch("supervisor.subprocess.Popen", side_effect=popen):
            self.sup.run_step(project, self.profile, FakeRpc())

    def test_milestones_progress_and_complete(self):
        self.run_fixture("continue")
        p = self.store.one("SELECT * FROM projects")
        self.assertEqual((p["state"], p["steps"]), ("queued", 1))
        self.run_fixture("complete")
        p = self.store.one("SELECT * FROM projects")
        self.assertEqual((p["state"], p["steps"]), ("complete", 2))
        self.assertEqual(len(self.store.rows("SELECT * FROM runs WHERE state='complete'")), 2)

    def test_blocked_project_requests_attention(self):
        self.run_fixture("blocked")
        p = self.store.one("SELECT * FROM projects")
        self.assertEqual(p["state"], "attention")
        self.assertEqual(p["note"], "Need user choice")

    def test_advisor_uses_read_only_and_persists_suggestions(self):
        self.store.execute("UPDATE projects SET kind='advisor',goal='{}'")
        self.run_fixture('advisor')
        self.assertEqual(self.store.one('SELECT state FROM projects')['state'], 'complete')
        self.assertEqual(len(self.store.rows('SELECT * FROM suggestions')), 1)
        self.assertEqual(self.sup.state()['projects'], [])

    def test_three_failures_stop_automatic_retry(self):
        for _ in range(3): self.run_fixture("failure")
        p = self.store.one("SELECT * FROM projects")
        self.assertEqual((p["state"], p["failures"]), ("attention", 3))

    def test_pause_stops_active_child(self):
        thread = threading.Thread(target=self.run_fixture, args=("slow",))
        thread.start()
        deadline = time.time() + 10
        while self.sup.active_proc is None and time.time() < deadline: time.sleep(.05)
        self.assertIsNotNone(self.sup.active_proc)
        self.store.set("running", False)
        thread.join(12)
        self.assertFalse(thread.is_alive())
        self.assertEqual(self.store.one("SELECT state FROM runs")["state"], "interrupted")

    def test_restart_preserves_work_and_uncertain_reset(self):
        self.store.execute("UPDATE projects SET state='running'")
        self.store.execute("INSERT INTO decisions(id,profile_id,kind,state,created) VALUES('reset-1','fixture-account','earned_reset','redeeming','today')")
        self.sup.bootstrap()
        self.assertEqual(self.store.one("SELECT state FROM projects")["state"], "attention")
        self.assertEqual(self.store.one("SELECT state FROM decisions")["state"], "uncertain")
        self.assertTrue(Store(self.temp.name).setting("running"))

    def test_reset_requires_explicit_approval_and_is_deduplicated(self):
        snapshot = {"limits": {"rateLimitResetCredits": {"availableCount": 2}}}
        self.sup.request_reset(self.profile, snapshot)
        self.sup.request_reset(self.profile, snapshot)
        self.assertEqual(len(self.store.rows("SELECT * FROM decisions")), 1)
        d = self.store.one("SELECT * FROM decisions")
        self.sup.decide_reset(d["id"], False)
        self.sup.request_reset(self.profile, snapshot)
        self.assertEqual(len(self.store.rows("SELECT * FROM decisions")), 1)
        self.assertEqual(self.store.one("SELECT state FROM decisions")["state"], "declined")

    def test_exhausted_account_hands_off_to_available_account(self):
        self.store.execute("INSERT INTO profiles(id,name,home) VALUES('second','Second account',?)", (self.temp.name + '-second',))
        class FakeRpc:
            def __init__(self, *args): pass
            def close(self): pass
        chosen = []
        def refreshed(profile, rpc):
            return {"limits": allowance(100 if profile['id'] == 'fixture-account' else 10)}
        def run(project, profile, rpc): chosen.append(profile['id'])
        with patch('supervisor.Rpc', FakeRpc), patch.object(self.sup,'refresh',side_effect=refreshed), patch.object(self.sup,'run_step',side_effect=run):
            self.sup.step(self.store.one('SELECT * FROM projects'))
        self.assertEqual(chosen, ['second'])

    def test_approved_reset_uses_durable_idempotency_key(self):
        self.sup.request_reset(self.profile, {"limits": {"rateLimitResetCredits": {"availableCount": 1}}})
        decision = self.store.one('SELECT * FROM decisions')
        calls = []
        class FakeRpc:
            def __init__(self, *args): pass
            def close(self): pass
            def call(self, method, params):
                calls.append((method,params))
                return {'outcome':'reset'}
        snapshot = {"limits": {"rateLimitResetCredits": {"availableCount": 1}}}
        with patch('supervisor.Rpc', FakeRpc), patch.object(self.sup,'refresh',return_value=snapshot):
            self.sup.decide_reset(decision['id'], True)
        self.assertEqual(calls, [('account/rateLimitResetCredit/consume', {'idempotencyKey':decision['id']})])
        self.assertEqual(self.store.one('SELECT state FROM decisions')['state'], 'approved')


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="autowork-http-")
        self.sup = Supervisor(Path(self.temp.name), "test-codex")
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.supervisor = self.sup
        self.server.token = "fixture-secret"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.sup.children.close()
        self.temp.cleanup()

    def test_api_requires_local_cookie_and_csrf(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx: self.client.open(self.url + "/api/state")
        self.assertEqual(ctx.exception.code, 403)
        self.client.open(self.url + "/").close()
        with self.client.open(self.url + "/api/state") as response: state = json.load(response)
        self.assertEqual(state["csrf"], "fixture-secret")
        request = urllib.request.Request(self.url + "/api/control", data=b'{"action":"start"}', headers={"Content-Type":"application/json"})
        with self.assertRaises(urllib.error.HTTPError): self.client.open(request)
        request.add_header("X-AutoWork-CSRF", state["csrf"])
        self.client.open(request).close()
        self.assertTrue(self.sup.store.setting("running"))

    def test_rebinding_host_rejected(self):
        request = urllib.request.Request(self.url + "/", headers={"Host":"attacker.example"})
        with self.assertRaises(urllib.error.HTTPError) as ctx: self.client.open(request)
        self.assertEqual(ctx.exception.code, 403)

    def test_focused_interface_assets_are_served_without_model_requests(self):
        for asset, marker in (("ui.js", b"RunquayUI"), ("beginner.js", b"showBeginner"), ("simple.css", b".next-step")):
            with self.client.open(self.url + "/" + asset) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(marker, response.read())

    def test_delivery_is_local_json_and_folder_open_requires_csrf(self):
        ident = self.sup.create_project({"name":"Delivery example","goal":"Create an example"})
        project = self.sup.store.one("SELECT * FROM projects WHERE id=?", (ident,))
        (Path(project['path'])/'START_HERE.md').write_text('1. Open the result. <script>unsafe()</script>', encoding='utf-8')
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.client.open(self.url + '/api/delivery/' + ident)
        self.assertEqual(ctx.exception.code, 403)
        self.client.open(self.url + '/').close()
        with self.client.open(self.url + '/api/delivery/' + ident) as response:
            self.assertTrue(response.headers['Content-Type'].startswith('application/json'))
            self.assertIn('<script>', json.load(response)['instructions'])
        request = urllib.request.Request(self.url+'/api/project/folder', data=json.dumps({'id':ident,'path':'untrusted override'}).encode(), headers={'Content-Type':'application/json'})
        with patch('supervisor.open_folder') as opener:
            with self.assertRaises(urllib.error.HTTPError):
                self.client.open(request)
            opener.assert_not_called()
            request.add_header('X-AutoWork-CSRF', 'fixture-secret')
            self.client.open(request).close()
            opener.assert_called_once_with(project['path'])

    def post(self, path, data, origin=None):
        self.client.open(self.url + "/").close()
        headers = {"Content-Type":"application/json", "X-AutoWork-CSRF":self.server.token}
        if origin: headers["Origin"] = origin
        request = urllib.request.Request(self.url + path,data=json.dumps(data).encode(),headers=headers)
        with self.client.open(request) as response: return json.load(response)

    def test_onboarding_acknowledgement_and_persistence(self):
        with self.assertRaises(urllib.error.HTTPError): self.post("/api/onboarding",{"acknowledged":False})
        workspace = str(Path(self.temp.name)/"new workspaces")
        self.post("/api/onboarding",{"acknowledged":True,"workspace_root":workspace,"provider":"claude"})
        self.assertTrue(self.sup.store.setting("onboarded"))
        self.assertEqual(self.sup.store.setting("advisor_provider"),"claude")
        self.assertTrue(Path(workspace).is_dir())
        self.assertFalse(self.sup.store.setting("running"))
        self.assertTrue(Store(self.temp.name).setting("onboarded"))

    def test_onboarding_rejects_relative_workspace_and_unknown_provider(self):
        for data in ({"acknowledged":True,"workspace_root":"relative"}, {"acknowledged":True,"provider":"unknown"}):
            with self.assertRaises(urllib.error.HTTPError): self.post("/api/onboarding",data)

    def test_cross_site_read_and_foreign_origin_write_rejected(self):
        request = urllib.request.Request(self.url + "/", headers={"Sec-Fetch-Site":"cross-site"})
        with self.assertRaises(urllib.error.HTTPError) as ctx: self.client.open(request)
        self.assertEqual(ctx.exception.code,403)
        with self.assertRaises(urllib.error.HTTPError) as ctx: self.post("/api/control",{"action":"start"},"https://attacker.example")
        self.assertEqual(ctx.exception.code,403)

    def test_import_folder_and_add_many_accounts_through_api(self):
        folder = Path(self.temp.name)/"existing"; folder.mkdir()
        result = self.post("/api/catalog/add",{"path":str(folder),"name":"Fixture workspace"})
        self.assertTrue(result["id"].startswith("folder-"))
        for i in range(5): self.post("/api/account",{"action":"add","name":f"Fixture {i}","provider":"codex"})
        self.assertEqual(len(self.sup.state()["profiles"]),5)

    def test_json_array_request_is_rejected_cleanly(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx: self.post("/api/control",[])
        self.assertEqual(ctx.exception.code,400)


if __name__ == "__main__": unittest.main()
