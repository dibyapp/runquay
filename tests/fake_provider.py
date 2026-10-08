"""Synthetic custom CLI for approval/dispatch integration tests."""
import json
import sys
sys.stdin.read()
print(json.dumps({"status":"complete","summary":"Fixture complete","tests":"Fixture verification","next_step":"","question":""}))
