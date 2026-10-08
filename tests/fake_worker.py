"""Deterministic subprocess fixture; makes no network calls and uses no allowance."""
import json
from pathlib import Path
import sys
import time

mode, output = sys.argv[1:3]
sys.stdin.read()
print(json.dumps({"type": "thread.started", "thread_id": "test-thread"}), flush=True)
if mode == "slow":
    time.sleep(60)
if mode == "failure":
    print(json.dumps({"type": "turn.failed", "error": {"message": "fixture failure"}}), flush=True)
    sys.exit(1)
result = {"status": mode if mode in ("continue", "complete", "blocked") else "complete" if mode == "advisor" else "continue", "summary": "Fixture milestone", "tests": "Fixture validation", "next_step": "Next task", "question": "Need user choice" if mode == "blocked" else ""}
if mode == "advisor":
    result['suggestions'] = [{'title':'Fixture idea','kind':'new','catalog_id':'','why':'Useful fixture','evidence':'Fixture README','goal':'Build a fixture with a passing check','first_milestone':'Implement fixture','effort':'Small'}]
Path(output).write_text(json.dumps(result), encoding="utf-8")
print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1}}), flush=True)
