"""Optional real Codex integration check. Uses a small amount of subscription allowance."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from supervisor import Supervisor, Rpc, NO_WINDOW, quota_gate, utcnow

with tempfile.TemporaryDirectory(prefix="autowork-live-check-") as folder:
    base = Path(folder)
    work = base / "workspace"
    work.mkdir()
    subprocess.run(["git", "init", "--quiet", str(work)], check=True, creationflags=NO_WINDOW)
    sup = Supervisor(base / "state")
    try:
        sup.store.set("running", True)
        sup.store.set("turn_minutes", 2)
        profile = {"id":"current", "name":"Current account", "home":str(Path.home()/".codex")}
        sup.store.execute("INSERT INTO profiles(id,name,home) VALUES(?,?,?)", (profile["id"],profile["name"],profile["home"]))
        snap = sup.refresh(profile)
        assert quota_gate(snap["limits"])[0], "Account is not eligible for a subscription-only check"
        goal = "Integration check only: create SMOKE_OK.txt containing exactly AUTOWORK_OK and verify its content using a short Python command. Do not install dependencies. Return complete after checking the file."
        sup.store.execute("INSERT INTO projects(id,name,goal,path,created) VALUES(?,?,?,?,?)", ("smoke","Codex integration check",goal,str(work),utcnow()))
        sup.run_step(sup.store.one("SELECT * FROM projects"), profile, Rpc(sup.binary,profile["home"],sup.children))
        project = sup.store.one("SELECT state,note,checkpoint FROM projects")
        run = sup.store.one("SELECT state,result,log FROM runs")
        print(json.dumps({"binary":sup.binary,"project":project,"run":run["state"],"result":run["result"]},ensure_ascii=False))
        if project["state"] != "complete":
            print(Path(run["log"]).read_text(encoding="utf-8")[-10000:])
            raise SystemExit(1)
        assert (work/"SMOKE_OK.txt").read_text().strip() == "AUTOWORK_OK"
        print("LIVE CHECK PASSED: authenticated subscription, native workspace sandbox, shell verification, structured checkpoint.")
    finally:
        sup.children.close()
