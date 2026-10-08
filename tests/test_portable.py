import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_support import data_home, child_options, command_display, DataLock
import providers
from supervisor import Supervisor, ChildJob, stop_tree, ROOT
from service_setup import definition
from security import redact, sanitize


RESULT = {"status": "complete", "summary": "Synthetic milestone", "tests": "Synthetic checks", "next_step": "", "question": ""}


class PortableTests(unittest.TestCase):
    def test_only_one_supervisor_can_own_a_data_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            first = DataLock(directory)
            try:
                with self.assertRaises(RuntimeError): DataLock(directory)
            finally:
                first.close()
            second = DataLock(directory); second.close()

    def test_os_data_directories(self):
        self.assertEqual(str(data_home("linux", "/demo", {"XDG_DATA_HOME": "/state"})).replace("\\", "/"), "/state/autowork")
        self.assertTrue(str(data_home("darwin", "/demo", {})).replace("\\", "/").endswith("Library/Application Support/AutoWork"))
        self.assertTrue(str(data_home("win32", "/demo", {})).replace("\\", "/").endswith("AppData/Local/AutoWork"))

    def test_service_paths_with_spaces_and_specifiers(self):
        path, text = definition("linux", "/demo", "/runtime/python", "/projects/space % repo")
        self.assertIn(b"space %% repo", text)
        self.assertIn(b"KillMode=control-group", text)
        _, text = definition("darwin", "/demo", "/runtime/python", "/projects/space repo")
        values = plistlib.loads(text)
        self.assertEqual(values["ProgramArguments"], ["/runtime/python", str(Path("/projects/space repo/supervisor.py"))])
        self.assertTrue(values["KeepAlive"])

    def test_provider_environments_are_separate_and_strip_credentials(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fixture", "GEMINI_API_KEY": "fixture", "CODEX_HOME": "wrong"}):
            env = providers.environment("claude", "profile-a")
        self.assertNotIn("ANTHROPIC_API_KEY", env)
        self.assertNotIn("GEMINI_API_KEY", env)
        self.assertNotIn("CODEX_HOME", env)
        self.assertEqual(env["CLAUDE_CONFIG_DIR"], "profile-a")
        self.assertEqual(providers.environment("gemini", "profile-b")["GEMINI_CLI_HOME"], "profile-b")

    def test_builtin_commands_and_native_read_only_modes(self):
        for provider, flag, mode in [("codex", "--sandbox", "read-only"), ("claude", "--permission-mode", "plan"), ("gemini", "--approval-mode", "plan")]:
            cmd = providers.command(provider, "fixture-cli", {"path":str(ROOT), "kind":"advisor"}, ROOT/"advisor-schema.json", "unused", "fixture-model")
            self.assertIn(mode, cmd)
            self.assertNotIn("--dangerously-skip-permissions", cmd)
        for provider in ("antigravity", "custom"):
            with self.assertRaises(ValueError):
                providers.command(provider, "fixture", {"path":str(ROOT), "kind":"advisor"}, ROOT/"advisor-schema.json", "unused")

    def test_vendor_result_envelopes(self):
        self.assertEqual(providers.parse_result("claude", json.dumps({"structured_output":RESULT}), "unused"), RESULT)
        for provider in ("gemini", "antigravity"):
            self.assertEqual(providers.parse_result(provider, json.dumps({"response":json.dumps(RESULT)}), "unused"), RESULT)
            with self.assertRaises(ValueError): providers.parse_result(provider,json.dumps({"error":"fixture"}),"unused")
        with self.assertRaises(ValueError): providers.parse_result("claude", '{"is_error":true}', "unused")

    def test_custom_uses_stdin_and_rejects_shell_string(self):
        with self.assertRaises(ValueError): providers.validate_custom("tool; arbitrary command")
        with self.assertRaises(ValueError): providers.validate_custom(["tool", "{prompt}"])
        cmd = providers.command("custom", "fixture", {"path":"workspace"}, ROOT/"result-schema.json", "unused", custom=["fixture","{workspace}","{schema}"])
        self.assertEqual(cmd[1], "workspace")

    def test_redacts_nested_and_text_credentials(self):
        secret = "sk-" + "a"*30
        self.assertNotIn(secret,redact("Value " + secret))
        self.assertEqual(sanitize({"access_token":"fixture"})["access_token"],"[REDACTED CREDENTIAL]")

    @unittest.skipIf(os.name == "nt", "POSIX-specific process-group containment")
    def test_posix_kills_descendant_after_parent_exits(self):
        with tempfile.TemporaryDirectory() as directory:
            pidfile = Path(directory)/"child.pid"
            script = "import subprocess,sys; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); open(sys.argv[1],'w').write(str(p.pid))"
            proc = subprocess.Popen([sys.executable,"-c",script,str(pidfile)], **child_options())
            job = ChildJob(); job.add(proc); proc.wait(timeout=5)
            child = int(pidfile.read_text()); job.close()
            # Linux reports terminated children as zombies until PID 1 reaps them.
            for _ in range(30):
                status = Path(f"/proc/{child}/stat")
                if not status.exists() or status.read_text().split()[2] == "Z": break
                time.sleep(.05)
            if sys.platform.startswith("linux"):
                self.assertTrue(not status.exists() or status.read_text().split()[2] == "Z")


class AccountTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.sup = Supervisor(Path(self.temp.name)/"state", "fixture-codex")

    def tearDown(self):
        self.sup.children.close(); self.temp.cleanup()

    def test_unlimited_isolated_profiles_and_duplicate_existing_login(self):
        ids = [self.sup.add_profile({"name":f"Account {i}","provider":"codex"}) for i in range(12)]
        self.assertEqual(len(set(ids)),12)
        self.assertEqual(len({p["home"] for p in self.sup.store.rows("SELECT * FROM profiles")}),12)
        self.sup.add_profile({"name":"Current","provider":"codex","existing":True})
        with self.assertRaises(ValueError): self.sup.add_profile({"name":"Duplicate","provider":"codex","existing":True})

    def test_antigravity_isolation_fails_explicitly(self):
        with self.assertRaisesRegex(ValueError,"unverified"):
            self.sup.add_profile({"name":"AGY","provider":"antigravity"})

    def test_external_approval_is_single_invocation_and_invalidates_on_goal_change(self):
        ident = self.sup.add_profile({"name":"Fixture","provider":"custom","command":[sys.executable,"--version"]})
        profile = self.sup.store.one("SELECT * FROM profiles WHERE id=?",(ident,))
        self.sup.store.execute("INSERT INTO projects(id,name,goal,path,created,provider) VALUES('p','Fixture','Build a fixture',?,'today','custom')",(self.temp.name,))
        project = self.sup.store.one("SELECT * FROM projects")
        self.assertFalse(self.sup.select_external(project,profile))
        self.assertFalse(self.sup.select_external(project,profile))
        self.assertEqual(len(self.sup.store.rows("SELECT * FROM decisions")),1)
        decision = self.sup.store.one("SELECT * FROM decisions")
        self.sup.decide_external(decision,True)
        self.assertTrue(self.sup.select_external(project,profile))
        self.assertFalse(self.sup.select_external(project,profile))
        self.sup.store.execute("UPDATE projects SET goal='Different task'")
        with self.assertRaises(ValueError): self.sup.decide_external(decision,True)

    def test_external_dispatch_is_pinned_to_selected_tool(self):
        self.sup.add_profile({"name":"Codex","provider":"codex"})
        project = {"id":"none","provider":"claude","steps":0,"max_steps":3}
        with patch("supervisor.Rpc") as rpc:
            self.sup.step(project)
            rpc.assert_not_called()

    def test_custom_worker_runs_real_subprocess_without_shell(self):
        fixture = Path(__file__).with_name("fake_provider.py")
        ident = self.sup.add_profile({"name":"Fixture","provider":"custom","command":[sys.executable,str(fixture)]})
        self.sup.store.set("running",True)
        self.sup.store.execute("INSERT INTO projects(id,name,goal,path,created,provider) VALUES('p','Fixture','Build fixture',?,'today','custom')",(self.temp.name,))
        project = self.sup.store.one("SELECT * FROM projects")
        self.sup.step(project)
        self.assertEqual(self.sup.store.one("SELECT state FROM projects")["state"],"queued")
        self.sup.decide_external(self.sup.store.one("SELECT * FROM decisions"),True)
        self.sup.step(project)
        self.assertEqual(self.sup.store.one("SELECT state FROM projects")["state"],"complete")
        self.assertEqual(self.sup.store.one("SELECT state FROM decisions")["state"],"consumed")

    def test_manual_folder_is_preserved_after_sync(self):
        root = Path(self.temp.name)/"existing"; root.mkdir()
        ident = self.sup.brain.add_folder(str(root))
        self.sup.brain.discover(Path(self.temp.name)/"missing-codex-state")
        self.assertEqual(self.sup.state()["catalog"][0]["id"],ident)


if __name__ == "__main__": unittest.main()
