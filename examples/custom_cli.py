"""Wire-contract demo only. Does not call any AI service or edit project files."""
import json
import sys

sys.stdin.read()
print(json.dumps({"status":"blocked", "summary":"Custom adapter contract demonstration", "tests":"No model request or project change was made", "next_step":"Implement a vendor CLI bridge", "question":"Replace this example with your authenticated, permission-scoped wrapper."}))
