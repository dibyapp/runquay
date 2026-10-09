import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import task_history as history
from supervisor import Supervisor


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="runquay-history-")
        self.home = Path(self.temporary.name)
        self.workspace = self.home / "website"
        self.workspace.mkdir()
        self.env = patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": "", "GEMINI_CLI_HOME": ""})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(self.temporary.cleanup)

    def jsonl(self, relative, rows):
        path = self.home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        return path

    def test_claude_titles_prompts_folders_and_read_only_files(self):
        path = self.jsonl(".claude/projects/project/session.jsonl", [
            {"type":"user","sessionId":"one","cwd":str(self.workspace),"message":{"content":[
                {"type":"tool_result","content":"private tool output"},{"type":"text","text":"Improve homepage"}]}},
            {"type":"custom-title","customTitle":"Website update"},
            {"type":"ai-title","aiTitle":"Older automatic title"},
            {"type":"assistant","message":{"content":"Do not retain assistant thoughts"}}])
        before = path.read_bytes()
        tasks, status = history.read_local_tasks("claude", home=self.home)
        self.assertEqual(status["state"],"ready")
        self.assertEqual(len(tasks),1)
        self.assertEqual(tasks[0]["title"],"Website update")
        self.assertEqual(tasks[0]["preview"],"Improve homepage")
        self.assertEqual(tasks[0]["path"],str(self.workspace))
        self.assertEqual(path.read_bytes(),before)

    def test_claude_subagents_empty_sessions_and_hidden_tags_are_excluded(self):
        for filename, rows in {"side": [{"isSidechain":True,"type":"user","message":{"content":"Subagent"}}],
                               "hidden": [{"type":"user","message":{"content":"Hidden"}},{"type":"tag","tag":"__hidden"}],
                               "empty": [{"type":"queue-operation"}]}.items():
            self.jsonl(f".claude/projects/project/{filename}.jsonl",rows)
        self.jsonl(".claude/projects/project/main/subagents/agent-one.jsonl",[{"type":"user","message":{"content":"Child"}}])
        self.assertEqual(history.read_local_tasks("claude",home=self.home)[0],[])

    def test_gemini_legacy_json_and_jsonl_sessions_skip_startup_and_subagents(self):
        folder = self.home/".gemini/tmp/project/chats"
        folder.mkdir(parents=True)
        (folder.parent/".project_root").write_text(str(self.workspace),encoding="utf-8")
        value={"sessionId":"one","lastUpdated":"2026-10-09T12:00:00Z","messages":[{"type":"user","content":[{"text":"Build menu"}]}]}
        (folder/"session-one.json").write_text(json.dumps(value),encoding="utf-8")
        self.jsonl(".gemini/tmp/project/chats/session-two.jsonl",[
            {"sessionId":"two","projectHash":"project","kind":"main"},
            {"id":"message","type":"user","content":[{"text":"Add checkout"}]},
            {"$set":{"summary":"Checkout","lastUpdated":"2026-10-09T13:00:00Z"}}])
        self.jsonl(".gemini/tmp/project/chats/session-empty.jsonl",[{"sessionId":"empty","kind":"main"}])
        self.jsonl(".gemini/tmp/project/chats/session-subagent.jsonl",[{"sessionId":"child","kind":"subagent"},{"type":"user","content":"Child"}])
        tasks,status=history.read_local_tasks("gemini",home=self.home)
        self.assertEqual([t["id"] for t in tasks],["two","one"])
        self.assertEqual(tasks[0]["title"],"Checkout")
        self.assertTrue(all(t["path"]==str(self.workspace) for t in tasks))
        self.assertEqual(status["count"],2)

    def test_antigravity_transcripts_keep_only_the_user_request_and_explicit_folder(self):
        self.jsonl(".gemini/antigravity/brain/conversation-one/.system_generated/logs/transcript.jsonl",[
            {"type":"USER_INPUT","content":"<USER_REQUEST>Build a page</USER_REQUEST><ADDITIONAL_METADATA>Private editor data</ADDITIONAL_METADATA>"},
            {"type":"PLANNER_RESPONSE","thinking":"Private thoughts","tool_calls":[{"args":{"Cwd":str(self.workspace),"CommandLine":"private command"}}]},
            {"type":"VIEW_FILE","content":"Private file data"}])
        tasks,status=history.read_local_tasks("antigravity",home=self.home)
        self.assertEqual(tasks[0]["id"],"conversation-one")
        self.assertEqual(tasks[0]["preview"],"Build a page")
        self.assertEqual(tasks[0]["path"],str(self.workspace))
        self.assertNotIn("Private",json.dumps(tasks))
        self.assertEqual(status["state"],"ready")

    def test_antigravity_cache_references_and_encrypted_files_are_honest(self):
        root=self.home/".gemini/antigravity-cli"
        (root/"cache").mkdir(parents=True)
        (root/"cache/last_conversations.json").write_text(json.dumps({str(self.workspace):"cached"}),encoding="utf-8")
        (root/"conversations").mkdir()
        binary=root/"conversations/private.pb"
        binary.write_bytes(b"encrypted conversation")
        tasks,status=history.read_local_tasks("antigravity",home=self.home)
        self.assertEqual(tasks[0]["source"],"Cached reference · open Antigravity to verify")
        self.assertEqual(tasks[0]["updated_at"],None)
        self.assertEqual(status["state"],"partial")
        self.assertIn("not decoded",status["note"])
        self.assertEqual(binary.read_bytes(),b"encrypted conversation")

    def test_missing_folders_do_not_get_inferred_from_prompt_text(self):
        self.jsonl(".gemini/antigravity/brain/one/.system_generated/logs/transcript.jsonl",[
            {"type":"USER_INPUT","content":f"<USER_REQUEST>Read {self.workspace}</USER_REQUEST>"}])
        self.assertEqual(history.read_local_tasks("antigravity",home=self.home)[0][0]["path"],"")

    def test_configured_and_isolated_profile_homes_are_discovered_and_deduplicated(self):
        self.jsonl("separate/projects/project/session.jsonl",[{"type":"user","sessionId":"one","message":{"content":"A task"}}])
        profiles=[{"provider":"claude","home":str(self.home/"separate")}, {"provider":"claude","home":str(self.home/"separate")}]
        tasks,_=history.read_local_tasks("claude",profiles,home=self.home)
        self.assertEqual(len(tasks),1)
        with patch.dict(os.environ,{"CLAUDE_CONFIG_DIR":str(self.home/"separate")}):
            self.assertEqual(history.read_local_tasks("claude",home=self.home)[0][0]["id"],"one")

    def test_corrupt_and_oversized_files_do_not_poison_valid_history(self):
        folder=self.home/".gemini/tmp/project/chats";folder.mkdir(parents=True)
        (folder/"session-bad.json").write_text("invalid",encoding="utf-8")
        (folder/"session-big.json").write_bytes(b"x"*(history.MAX_JSON_BYTES+1))
        (folder/"session-valid.json").write_text(json.dumps({"sessionId":"one","messages":[{"type":"user","content":"Valid"}]}),encoding="utf-8")
        tasks,status=history.read_local_tasks("gemini",home=self.home)
        self.assertEqual(len(tasks),1)
        self.assertEqual(status["state"],"partial")

    def test_file_reads_are_bounded_and_never_open_vendor_credentials(self):
        self.jsonl(".claude/projects/project/session.jsonl",[{"type":"user","sessionId":"one","message":{"content":"A task"}}])
        credential=self.home/".claude/.credentials.json"
        credential.write_text('{"access_token":"example"}',encoding="utf-8")
        opened=[];real_open=Path.open
        def tracked_open(path,*args,**kwargs):
            opened.append(path)
            return real_open(path,*args,**kwargs)
        with patch.object(Path,"open",tracked_open):
            history.read_local_tasks("claude",home=self.home)
        self.assertNotIn(credential,opened)
        large=self.jsonl("large.jsonl",[{"type":"user","message":{"content":"First"}}])
        with large.open("ab") as stream:stream.write(b"x"*(history.HEAD_BYTES+history.TAIL_BYTES+100))
        self.assertEqual(len(history.records(large,self.home)),1)

    @unittest.skipIf(os.name=="nt","Symlink creation can require Windows privileges")
    def test_history_symlinks_cannot_read_outside_the_vendor_root(self):
        outside=self.jsonl("outside.jsonl",[{"type":"user","message":{"content":"Private"}}])
        folder=self.home/".claude/projects/project";folder.mkdir(parents=True)
        (folder/"session.jsonl").symlink_to(outside)
        self.assertEqual(history.read_local_tasks("claude",home=self.home)[0],[])
        self.assertFalse(history.safe_file(outside,self.home/".claude"))

    def test_import_validation_redaction_namespacing_and_metadata_allowlist(self):
        payload={"version":1,"tool":"Other editor","tasks":[{"id":"one","title":"<script>Task</script>",
                 "preview":"password="+"example-value-123", "cwd":str(self.workspace),"api_key":"ignored","turns":["ignored"]}]}
        tasks=history.import_tasks(payload)
        self.assertEqual(tasks[0]["provider"],"custom")
        self.assertIn("REDACTED",tasks[0]["preview"])
        self.assertFalse({"api_key","turns"}&tasks[0].keys())
        payload["tool"]="Another editor"
        self.assertNotEqual(history.import_tasks(payload)[0]["key"],tasks[0]["key"])
        for bad in ({}, {"version":1,"tool":"Editor","tasks":[]},
                    {"version":1,"tool":"Editor","tasks":[{"id":"one","title":"Task","cwd":"relative"}]}):
            with self.assertRaises(ValueError):history.import_tasks(bad)

    def test_binding_handles_nested_projects_and_provider_id_collisions(self):
        tasks=[history.task("claude","same",cwd=str(self.workspace/"nested/src")),
               history.task("gemini","same",cwd=str(self.workspace)+"-other")]
        library=[{"id":"root","name":"Root","path":str(self.workspace)},
                 {"id":"nested","name":"Nested","path":str(self.workspace/"nested")}]
        result=history.bind_tasks(tasks,library)
        self.assertEqual(len(result),2)
        self.assertEqual(result[0]["catalog_id"],"nested")
        self.assertEqual(result[1]["catalog_id"],"")

    def test_timestamp_validation_handles_iso_ms_and_nonfinite_values(self):
        self.assertEqual(history.timestamp(1_700_000_000_000),1_700_000_000)
        self.assertEqual(history.timestamp("2026-10-09T12:00:00Z"),1_791_547_200)
        for value in (float("nan"),float("inf"),-1,True,"not a date"):
            self.assertIsNone(history.timestamp(value))

    def test_failed_provider_refresh_keeps_other_providers_and_never_queues_work(self):
        sup=Supervisor(self.home/"runquay","fixture")
        self.addCleanup(sup.children.close)
        previous=history.task("claude","one","Saved")
        sup.store.set("other_tasks",[previous])
        def read(provider,profiles):
            if provider=="claude":raise RuntimeError("private error detail")
            return [history.task(provider,"two","Available")],{"provider":provider,"tool":history.NAMES[provider],"state":"ready"}
        with patch("codex_brain.read_local_tasks",side_effect=read):sup.brain.discover_other_tasks()
        state=sup.state()
        self.assertEqual(len(state["history_tasks"]),3)
        self.assertNotIn("private error detail",json.dumps(state["history_sources"]))
        self.assertEqual(state["projects"],[])
        self.assertEqual(state["runs"],[])
        sup.brain.import_history({"version":1,"tool":"Editor","tasks":[{"id":"one","title":"Imported"}]})
        sup.brain.import_history({"version":1,"tool":"Editor","tasks":[{"id":"one","title":"Updated"}]})
        self.assertEqual(len(sup.store.setting("imported_tasks")),1)
        self.assertEqual(sup.store.setting("imported_tasks")[0]["title"],"Updated")
        self.assertEqual(sup.store.rows("SELECT * FROM projects"),[])


if __name__ == "__main__":unittest.main()
