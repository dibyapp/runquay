"""Runquay: a local AI coding workshop. Python 3.11+, stdlib only."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import ctypes
import datetime as dt
import hashlib
import http.server
import json
import logging
import os
from pathlib import Path
import queue
import re
import secrets
import shutil
import sqlite3
import subprocess
import threading
import time
import urllib.parse
import uuid
from codex_brain import CodexBrain, path_key
from platform_support import default_data, child_options, kill_group, private_directory, command_display, DataLock
import providers
import sys
import signal
from security import redact, sanitize

ROOT = Path(__file__).resolve().parent
SCHEMA = json.loads((ROOT / "result-schema.json").read_text(encoding="utf-8"))
LOG = logging.getLogger("autowork")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class PrivateLogFormatter(logging.Formatter):
    def format(self, record):
        return redact(super().format(record))


def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def find_codex():
    candidates = list((Path(os.environ.get("LOCALAPPDATA", "")) / "OpenAI/Codex/bin").glob("*/codex.exe"))
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    found = shutil.which("codex")
    if found and not candidates:
        candidates.append(Path(found))
    return str(candidates[0]) if candidates else ""


class ChildJob:
    """Windows closes the entire child process tree if this supervisor exits."""
    def __init__(self):
        self.handle = None
        self.processes = []
        if os.name != "nt":
            return
        from ctypes import wintypes as w

        class BASIC(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                        ("LimitFlags", w.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", w.DWORD),
                        ("Affinity", ctypes.c_size_t), ("PriorityClass", w.DWORD), ("SchedulingClass", w.DWORD)]

        class IO(ctypes.Structure):
            _fields_ = [(x, ctypes.c_uint64) for x in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount", "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

        class EXTENDED(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", BASIC), ("IoInfo", IO), ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
        self.kernel.CreateJobObjectW.restype = w.HANDLE
        self.kernel.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
        self.kernel.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
        self.kernel.CloseHandle.argtypes = [w.HANDLE]
        self.handle = self.kernel.CreateJobObjectW(None, None)
        info = EXTENDED()
        info.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.handle or not self.kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
            raise OSError(ctypes.get_last_error(), "Cannot create Windows child-process containment")

    def add(self, proc):
        if os.name != "nt":
            self.processes = [p for p in self.processes if not getattr(p, "_autowork_group_closed", False)]
            self.processes.append(proc)
        if self.handle and not self.kernel.AssignProcessToJobObject(self.handle, int(proc._handle)):
            proc.kill()
            raise OSError(ctypes.get_last_error(), "Cannot contain worker child process")

    def close(self):
        if os.name != "nt":
            for proc in self.processes:
                kill_group(proc)
            self.processes.clear()
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def stop_tree(proc):
    if proc is None:
        return
    if os.name != "nt":
        kill_group(proc)
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, creationflags=NO_WINDOW, timeout=15)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


def profile_env(home):
    return providers.environment("codex", home)


class Rpc:
    """Documented app-server stdio API. Never reads or serializes auth.json."""
    def __init__(self, binary, home, job=None):
        self.proc = subprocess.Popen(providers.native_command([binary, "app-server", "--stdio"]), stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True, encoding="utf-8", errors="replace", env=profile_env(home),
                                     cwd=ROOT, **child_options())
        if job:
            job.add(self.proc)
        self.inbox = queue.Queue()
        self.errors = []
        self.error_reader = threading.Thread(target=self._read_errors, daemon=True)
        self.error_reader.start()
        self.counter = 0
        self.lock = threading.Lock()
        threading.Thread(target=self._read, daemon=True).start()
        try:
            self.call("initialize", {"clientInfo": {"name": "autowork_local", "title": "Runquay Local", "version": "1.0.0"}})
            self._send({"method": "initialized", "params": {}})
        except Exception:
            self.close()
            raise

    def _read(self):
        try:
            for line in self.proc.stdout:
                try:
                    self.inbox.put(json.loads(line))
                except ValueError:
                    continue
        finally:
            self.inbox.put({"_closed": True})

    def _send(self, message):
        self.proc.stdin.write(json.dumps(message) + "\n")
        self.proc.stdin.flush()

    def _read_errors(self):
        for line in self.proc.stderr:
            self.errors.append(line.rstrip())
            self.errors = self.errors[-5:]

    def call(self, method, params=None, timeout=35):
        with self.lock:
            self.counter += 1
            ident = self.counter
            self._send({"id": ident, "method": method, "params": params or {}})
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                try:
                    message = self.inbox.get(timeout=max(.05, deadline - time.monotonic()))
                except queue.Empty:
                    break
                if message.get("_closed"):
                    self.error_reader.join(timeout=.5)
                    LOG.warning("Codex metadata process closed: %s", " | ".join(self.errors)[-2000:])
                    raise RuntimeError("Codex app-server closed")
                if message.get("id") == ident:
                    if "error" in message:
                        raise RuntimeError(message["error"].get("message", str(message["error"])))
                    return message.get("result", {})
            raise TimeoutError(f"Codex {method} did not respond")

    def close(self):
        stop_tree(self.proc)
        self.error_reader.join(timeout=2)
        for pipe in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
            if pipe:
                pipe.close()


def quota_gate(limits, ceiling=90):
    """Fail closed on unknown quota, API auth, paid balances, or exhausted buckets."""
    buckets = limits.get("rateLimitsByLimitId") or {"codex": limits.get("rateLimits")}
    bucket = buckets.get("codex")
    if not bucket:
        return False, "Subscription quota is unavailable; waiting for a verified reading", None
    credits = bucket.get("credits")
    if not isinstance(credits, dict) or credits.get("hasCredits") is not False or credits.get("unlimited") is not False:
        return False, "Paid credit status is positive or unknown; unattended use is blocked", None
    try:
        if float(credits.get("balance", "unknown")) != 0:
            return False, "Paid credit balance is present; unattended use is blocked", None
    except (ValueError, TypeError):
        return False, "Paid credit balance is unknown; unattended use is blocked", None
    if bucket.get("spendControlReached") or bucket.get("rateLimitReachedType"):
        return False, "Account reports a reached usage limit", next_reset(bucket)
    windows = [bucket.get("primary"), bucket.get("secondary"), bucket.get("individualLimit")]
    known = [w for w in windows if isinstance(w, dict) and isinstance(w.get("usedPercent"), (float, int))]
    if not known:
        return False, "No verified subscription quota windows", None
    reached = [w for w in known if w["usedPercent"] >= ceiling]
    if reached:
        resets = [w.get("resetsAt") for w in reached if isinstance(w.get("resetsAt"), (int, float))]
        return False, f"Quota reserve reached ({ceiling}%); waiting for refresh or an approved reset", max(resets) if resets else None
    if limits.get("ordinaryUsageAllowed") is False:
        return False, "Ordinary subscription usage is not allowed", next_reset(bucket)
    return True, "Subscription quota available; paid balance is zero", None


def next_reset(bucket):
    values = [w.get("resetsAt") for w in (bucket.get("primary"), bucket.get("secondary"))
              if isinstance(w, dict) and isinstance(w.get("resetsAt"), (int, float))]
    return min(values) if values else None


class Store:
    def __init__(self, directory):
        self.directory = Path(directory).expanduser().resolve()
        private_directory(self.directory)
        self.path = self.directory / "autowork.sqlite3"
        with self.connect() as db:
            db.executescript("""
              CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS profiles(id TEXT PRIMARY KEY, name TEXT NOT NULL, home TEXT NOT NULL UNIQUE,
                enabled INTEGER DEFAULT 1, snapshot TEXT DEFAULT '{}', checked REAL DEFAULT 0, error TEXT DEFAULT '');
              CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, name TEXT NOT NULL, goal TEXT NOT NULL,
                path TEXT NOT NULL UNIQUE, state TEXT DEFAULT 'queued', priority INTEGER DEFAULT 0,
                max_steps INTEGER DEFAULT 20, steps INTEGER DEFAULT 0, failures INTEGER DEFAULT 0,
                checkpoint TEXT DEFAULT '{}', model TEXT DEFAULT '', note TEXT DEFAULT '', guidance TEXT DEFAULT '', created TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, project_id TEXT NOT NULL, profile_id TEXT NOT NULL,
                state TEXT DEFAULT 'running', started TEXT NOT NULL, finished TEXT, result TEXT DEFAULT '', log TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS decisions(id TEXT PRIMARY KEY, profile_id TEXT NOT NULL, kind TEXT NOT NULL,
                state TEXT DEFAULT 'pending', payload TEXT DEFAULT '{}', result TEXT DEFAULT '', created TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, message TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS catalog(id TEXT PRIMARY KEY,name TEXT NOT NULL,path TEXT NOT NULL,
                source TEXT NOT NULL,details TEXT DEFAULT '{}',recent TEXT DEFAULT '[]',checked REAL DEFAULT 0);
              CREATE TABLE IF NOT EXISTS suggestions(id TEXT PRIMARY KEY,fingerprint TEXT UNIQUE,payload TEXT NOT NULL,
                run_id TEXT NOT NULL,created REAL NOT NULL,state TEXT DEFAULT 'proposed',project_id TEXT DEFAULT '');
            """)
            if "guidance" not in {row[1] for row in db.execute("PRAGMA table_info(projects)")}:
                db.execute("ALTER TABLE projects ADD COLUMN guidance TEXT DEFAULT ''")
            if "kind" not in {row[1] for row in db.execute("PRAGMA table_info(projects)")}:
                db.execute("ALTER TABLE projects ADD COLUMN kind TEXT DEFAULT 'work'")
            for table, column, definition in (("profiles", "provider", "TEXT DEFAULT 'codex'"), ("profiles", "options", "TEXT DEFAULT '{}'"),
                                              ("projects", "provider", "TEXT DEFAULT 'codex'")):
                if column not in {row[1] for row in db.execute(f"PRAGMA table_info({table})")}:
                    db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            db.execute("INSERT OR IGNORE INTO settings VALUES('running','false')")
            db.execute("INSERT OR IGNORE INTO settings VALUES('quota_ceiling','90')")
            db.execute("INSERT OR IGNORE INTO settings VALUES('turn_minutes','30')")
            db.execute("INSERT OR IGNORE INTO settings VALUES('keep_awake','true')")
            db.execute("INSERT OR IGNORE INTO settings VALUES('advisor_auto','true')")
            db.execute("INSERT OR IGNORE INTO settings VALUES('advisor_hours','6')")
            db.execute("INSERT OR IGNORE INTO settings VALUES('onboarded','false')")
            db.execute("INSERT OR IGNORE INTO settings VALUES('advisor_provider','\"codex\"')")
            db.execute("INSERT OR IGNORE INTO settings VALUES('workspace_root',?)", (json.dumps(str((self.directory / 'workspaces').resolve())),))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA journal_mode=WAL")
            with db:
                yield db
        finally:
            db.close()

    def execute(self, sql, args=()):
        with self.connect() as db:
            return db.execute(sql, args).rowcount

    def rows(self, sql, args=()):
        with self.connect() as db:
            return [dict(row) for row in db.execute(sql, args)]

    def one(self, sql, args=()):
        rows = self.rows(sql, args)
        return rows[0] if rows else None

    def setting(self, key):
        row = self.one("SELECT value FROM settings WHERE key=?", (key,))
        return json.loads(row["value"]) if row else None

    def set(self, key, value):
        self.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (key, json.dumps(value)))

    def event(self, message):
        message = redact(message)
        LOG.info(message)
        self.execute("INSERT INTO events(at,message) VALUES(?,?)", (utcnow(), message))
        self.execute("DELETE FROM events WHERE id < (SELECT MAX(id)-1000 FROM events)")


class Supervisor:
    def __init__(self, directory=None, binary=None):
        directory = directory or default_data(ROOT)
        self.store = Store(directory)
        self.binary = binary or find_codex()
        self.children = ChildJob()
        self.stop = threading.Event()
        self.wake = threading.Event()
        self.active_proc = None
        self.active_lock = threading.Lock()
        self.account_lock = threading.Lock()
        self.login_lock = threading.Lock()
        self.login_in_progress = False
        self.worker = None
        self.last_profile = None
        self.awake_proc = None
        self.profile_lock = threading.Lock()
        self.brain = CodexBrain(self)

    def profile_binary(self, profile):
        options = json.loads(profile.get("options", "{}"))
        provider = profile.get("provider", "codex")
        if provider == "codex" and not options.get("executable"):
            return self.binary
        return providers.resolve_executable(options.get("executable") or providers.TOOLS[provider]["executable"])

    def tool_status(self):
        return [{"id": key, **value, "installed": bool(self.binary if key == "codex" else providers.resolve_executable(value["executable"]) if value["executable"] else False),
                 "verification": "Live tested on Windows" if key == "codex" else "Contract tested; local live check required"}
                for key, value in providers.TOOLS.items()]

    def add_profile(self, data):
        provider = str(data.get("provider", "codex"))
        if provider not in providers.TOOLS:
            raise ValueError("Unknown AI tool")
        name = str(data.get("name", "")).strip()[:100]
        if not name:
            raise ValueError("Give this account a name")
        existing = data.get("existing") is True
        if provider == "antigravity" and not existing:
            raise ValueError("Antigravity CLI's isolated home override is unverified. Reuse its current login, or supply an isolated custom CLI wrapper.")
        ident = "profile-" + uuid.uuid4().hex[:12]
        home = Path.home() / providers.TOOLS[provider]["home"] if existing else (self.store.directory / "accounts" / ident).resolve()
        if provider == "antigravity":
            home = Path.home() / ".gemini/antigravity-cli"
        options = {"executable": str(data.get("executable", "")).strip()}
        if provider == "custom":
            options["command"] = providers.validate_custom(data.get("command"))
            options["executable"] = options["command"][0]
        # Never duplicate a login home or overwrite a vendor's existing config.
        with self.profile_lock:
            if self.store.one("SELECT id FROM profiles WHERE home=?", (str(home),)):
                raise ValueError("That login is already connected. Create an isolated profile for a different account.")
            if not existing:
                private_directory(home)
                if provider == "codex":
                    (home / "config.toml").write_text('forced_login_method = "chatgpt"\ncli_auth_credentials_store = "keyring"\n', encoding="utf-8")
            self.store.execute("INSERT INTO profiles(id,name,home,provider,options) VALUES(?,?,?,?,?)", (ident, name, str(home), provider, json.dumps(options)))
        self.wake.set()
        return ident

    def remove_profile(self, ident):
        # Unlink only. Keep vendor auth and historical logs recoverable.
        with self.idle_account():
            self.store.execute("DELETE FROM profiles WHERE id=?", (ident,))
            self.store.execute("UPDATE decisions SET state='expired' WHERE profile_id=? AND state='pending'", (ident,))

    def profile_instructions(self, profile):
        provider = profile.get("provider", "codex")
        executable = self.profile_binary(profile) or providers.TOOLS[provider]["executable"] or "your-cli"
        var = providers.TOOLS[provider]["home_var"]
        env = {var: profile["home"]} if var else {}
        args = [executable, "login"] if provider == "codex" else [executable, "auth", "login"] if provider == "claude" else [executable]
        return {"login": command_display(args, env), "note": "Run in your terminal; finish vendor sign-in there. Credentials are never entered in Runquay."}

    def refresh_external(self, profile):
        executable = self.profile_binary(profile)
        snapshot = {"installed": bool(executable), "quota": "unverified", "account": {}}
        # Detection makes no model request and does not inspect credential files.
        error = "" if executable else "CLI executable not found; install it from its official vendor or select its path"
        self.store.execute("UPDATE profiles SET snapshot=?,checked=?,error=? WHERE id=?", (json.dumps(snapshot), time.time(), error, profile["id"]))
        return snapshot

    def external_key(self, project, profile):
        value = json.dumps([project["id"], project["goal"], project.get("guidance"), project.get("model"), project["steps"],
                            project["failures"], profile["id"], profile.get("options"), profile["home"]])
        return hashlib.sha256(value.encode()).hexdigest()

    def select_external(self, project, profile):
        if not self.profile_binary(profile):
            return False
        key = self.external_key(project, profile)
        decision = self.store.one("SELECT * FROM decisions WHERE kind='external_run' AND json_extract(payload,'$.key')=? ORDER BY created DESC LIMIT 1", (key,))
        if decision and decision["state"] == "approved":
            self.store.execute("UPDATE decisions SET state='consumed',result='Authorized one invocation' WHERE id=? AND state='approved'", (decision["id"],))
            return True
        if not decision or decision["state"] in ("consumed", "expired"):
            payload = {"key": key, "project_id": project["id"], "project": project["name"], "provider": profile["provider"],
                       "step": project["steps"], "message": "This CLI's subscription quota and billing cannot be verified. Check vendor account/billing and permissions first. Approve only if you accept any vendor usage charges for ONE invocation. Runquay never buys credits or resets."}
            self.store.execute("INSERT INTO decisions(id,profile_id,kind,payload,created) VALUES(?,?,?,?,?)", (str(uuid.uuid4()), profile["id"], "external_run", json.dumps(payload), utcnow()))
        self.store.execute("UPDATE projects SET note='Waiting for one-run approval in the Approval inbox' WHERE id=?", (project["id"],))
        return False

    def decide_external(self, decision, approve):
        profile = self.store.one("SELECT * FROM profiles WHERE id=?", (decision["profile_id"],))
        payload = json.loads(decision["payload"])
        project = self.store.one("SELECT * FROM projects WHERE id=?", (payload["project_id"],))
        if decision["state"] != "pending" or not profile or not project or self.external_key(project, profile) != payload["key"]:
            raise ValueError("This approval is stale; refresh the queue")
        self.store.execute("UPDATE decisions SET state=?,result=? WHERE id=? AND state='pending'", ("approved" if approve else "declined", "One invocation authorized" if approve else "Run declined", decision["id"]))
        if not approve:
            self.store.execute("UPDATE projects SET state='attention',note='External invocation declined. Resume to request another approval.',failures=failures+1 WHERE id=? AND state='queued'", (project["id"],))
        self.wake.set()

    def set_awake(self, enabled):
        if os.name == "nt":
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000001 if enabled else 0x80000000)
            return
        if not enabled:
            stop_tree(self.awake_proc)
            self.awake_proc = None
        elif self.awake_proc is None:
            command = ["caffeinate", "-i"] if sys.platform == "darwin" else ["systemd-inhibit", "--what=sleep", "--who=Runquay", "--why=Local AI queue", "sleep", "infinity"]
            if shutil.which(command[0]):
                self.awake_proc = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **child_options())
                self.children.add(self.awake_proc)

    def bootstrap(self):
        # A first launch offers one existing login. Additional profiles are user-created.
        if not self.store.one("SELECT id FROM profiles"):
            self.add_profile({"provider": "codex", "name": "Codex · current login", "existing": True})
        # An interrupted process may have changed files. Surface that fact before resuming.
        self.store.execute("UPDATE projects SET state='attention',note='Supervisor restarted during a run. Review files, then Resume.' WHERE state='running'")
        self.store.execute("UPDATE runs SET state='interrupted',finished=? WHERE state='running'", (utcnow(),))
        self.store.execute("UPDATE decisions SET state='uncertain',result='Supervisor restarted during redemption; retry with the original request ID' WHERE state='redeeming'")
        self.brain.discover()

    def refresh(self, profile, rpc=None):
        owned = rpc is None
        try:
            if profile.get("provider", "codex") != "codex":
                return self.refresh_external(profile)
            rpc = rpc or Rpc(self.profile_binary(profile), profile["home"], self.children)
            account = rpc.call("account/read", {"refreshToken": True}).get("account")
            if not account or account.get("type") != "chatgpt":
                raise ValueError("Sign in with a ChatGPT subscription account; API-key authentication is disabled")
            limits = rpc.call("account/rateLimits/read")
            snapshot = {"account": {k: account[k] for k in ("type", "planType") if k in account}, "limits": sanitize(limits)}
            self.store.execute("UPDATE profiles SET snapshot=?,checked=?,error='' WHERE id=?", (json.dumps(snapshot), time.time(), profile["id"]))
            if quota_gate(limits, self.store.setting("quota_ceiling"))[0]:
                self.store.execute("UPDATE decisions SET state='expired',result='Subscription allowance is available again; no reset was consumed' WHERE profile_id=? AND state IN ('pending','declined')", (profile["id"],))
            return snapshot
        except Exception as exc:
            self.store.execute("UPDATE profiles SET error=?,checked=? WHERE id=?", (str(exc)[:500], time.time(), profile["id"]))
            raise
        finally:
            if owned and rpc:
                rpc.close()

    def refresh_all(self):
        with self.account_lock:
            for profile in self.store.rows("SELECT * FROM profiles WHERE enabled=1"):
                try:
                    self.refresh(profile)
                except Exception:
                    LOG.info("Account %s is unavailable", profile["id"])
        self.wake.set()

    def refresh_one_safely(self, profile):
        with self.account_lock:
            try:
                self.refresh(profile)
            except Exception:
                LOG.info("Account connection is unavailable")
        self.wake.set()

    def create_project(self, data):
        name = str(data.get("name", "")).strip()[:100]
        goal = str(data.get("goal", "")).strip()
        if not name or not goal or len(goal) > 30000:
            raise ValueError("Provide a project name and a goal (up to 30,000 characters)")
        ident = uuid.uuid4().hex[:12]
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:45] or "project"
        path = Path(self.store.setting("workspace_root")) / f"{slug}-{ident[:6]}"
        provider = str(data.get("provider", "codex"))
        if provider not in providers.TOOLS:
            raise ValueError("Unknown AI tool")
        steps = int(data.get("max_steps", 20))
        priority = int(data.get("priority", 0))
        model = str(data.get("model", "")).strip()
        if not 1 <= steps <= 200 or not -100 <= priority <= 100 or not re.fullmatch(r"[a-zA-Z0-9._:/-]{0,120}", model):
            raise ValueError("Invalid milestone count, priority, or model")
        if data.get("catalog_id"):
            catalog = self.store.one("SELECT * FROM catalog WHERE id=?", (data["catalog_id"],))
            if not catalog or not Path(catalog["path"]).is_dir():
                raise ValueError("Existing project folder is unavailable; refresh the library")
            path = Path(catalog["path"])
            if path_key(path) == path_key(ROOT):
                raise ValueError("Runquay is the running supervisor. Make changes through this chat, or use a separate checkout.")
            existing = next((p for p in self.store.rows("SELECT * FROM projects WHERE kind='work'") if path_key(p["path"]) == path_key(path)), None)
            if existing:
                if existing["state"] not in ("complete", "cancelled"):
                    raise ValueError("This workspace already has a task. Resume or manage it in the task queue.")
                self.store.execute("UPDATE projects SET name=?,goal=?,state='queued',steps=0,failures=0,checkpoint='{}',guidance='',note='',max_steps=?,priority=?,model=?,provider=? WHERE id=?",
                                   (name, goal, steps, priority, model, provider, existing["id"]))
                self.wake.set()
                return existing["id"]
        else:
            path.mkdir(parents=True)
            subprocess.run(["git", "init", "--quiet", str(path)], check=True, capture_output=True, creationflags=NO_WINDOW)
            (path / "PROJECT.md").write_text(f"# {name}\n\n{goal}\n", encoding="utf-8")
            (path / "AGENTS.md").write_text(
                "Work only on this project's stated goal. Keep durable progress in AUTOWORK_CHECKPOINT.md.\n"
                "Do not read credentials, modify other projects, purchase anything, deploy, publish, or message people.\n"
                "Run meaningful checks. Report blockers honestly. Ask through the structured final question when human input is necessary.\n"
                "Do not spawn other agents. The supervisor owns scheduling.\n", encoding="utf-8")
        self.store.execute("INSERT INTO projects(id,name,goal,path,priority,max_steps,model,created,provider) VALUES(?,?,?,?,?,?,?,?,?)",
                           (ident, name, goal, str(path), priority, steps, model, utcnow(), provider))
        self.store.event(f"Queued project: {name}")
        self.wake.set()
        return ident

    def request_reset(self, profile, snapshot):
        resets = snapshot.get("limits", {}).get("rateLimitResetCredits") or {}
        if not resets.get("availableCount"):
            return
        if self.store.one("SELECT id FROM decisions WHERE profile_id=? AND kind='earned_reset' AND state IN ('pending','declined')", (profile["id"],)):
            return
        self.store.execute("INSERT INTO decisions(id,profile_id,kind,payload,created) VALUES(?,?,?,?,?)",
                           (str(uuid.uuid4()), profile["id"], "earned_reset", json.dumps(resets), utcnow()))
        self.store.event(f"Approval requested: use an earned reset for {profile['name']}? Otherwise wait for refresh.")

    @contextmanager
    def idle_account(self):
        if not self.account_lock.acquire(blocking=False):
            raise ValueError("Pause the queue and wait for account checks to finish before redeeming a reset")
        try:
            yield
        finally:
            self.account_lock.release()

    def decide_reset(self, ident, approve):
        if not approve:
            self.store.execute("UPDATE decisions SET state='declined',result='Wait for the natural reset' WHERE id=? AND state='pending'", (ident,))
            return
        with self.idle_account():
            decision = self.store.one("SELECT * FROM decisions WHERE id=?", (ident,))
            if not decision or decision["state"] not in ("pending", "uncertain"):
                raise ValueError("This reset request is no longer pending")
            with self.active_lock:
                if self.active_proc is not None:
                    raise ValueError("Pause active work before redeeming a reset")
            profile = self.store.one("SELECT * FROM profiles WHERE id=?", (decision["profile_id"],))
            # Store before sending; retry the same request ID after an uncertain network result.
            self.store.execute("UPDATE decisions SET state='redeeming' WHERE id=?", (ident,))
            rpc = None
            try:
                rpc = Rpc(self.profile_binary(profile), profile["home"], self.children)
                fresh = self.refresh(profile, rpc)
                if not (fresh["limits"].get("rateLimitResetCredits") or {}).get("availableCount") and decision["state"] != "uncertain":
                    raise ValueError("No earned reset is available. Paid reset purchases are not supported.")
                result = rpc.call("account/rateLimitResetCredit/consume", {"idempotencyKey": ident})
                self.store.execute("UPDATE decisions SET state='approved',result=? WHERE id=?", (json.dumps(result), ident))
                self.refresh(profile, rpc)
                self.store.event(f"Approved reset for {profile['name']}: {result.get('outcome', 'unknown')}")
            except Exception as exc:
                self.store.execute("UPDATE decisions SET state='uncertain',result=? WHERE id=?", (str(exc), ident))
                raise
            finally:
                if rpc:
                    rpc.close()
        self.wake.set()

    def login(self, ident):
        profile = self.store.one("SELECT * FROM profiles WHERE id=?", (ident,))
        if not profile:
            raise ValueError("Account not found")
        if profile.get("provider", "codex") != "codex":
            raise ValueError("Use the displayed terminal sign-in instructions, then Verify connection")
        if Path(profile["home"]).resolve() == (Path.home() / ".codex").resolve():
            raise ValueError("Account 1 uses the app's existing login. Sign in through Codex, then Refresh accounts.")
        if not self.login_lock.acquire(blocking=False):
            raise ValueError("Finish the current browser sign-in first")
        self.login_in_progress = True

        def perform():
            proc = None
            try:
                self.store.execute("UPDATE profiles SET error='Complete sign-in in the browser' WHERE id=?", (ident,))
                proc = subprocess.Popen(providers.native_command([self.profile_binary(profile), "login", "-c", 'forced_login_method="chatgpt"', "-c", 'cli_auth_credentials_store="keyring"']),
                                        env=profile_env(profile["home"]), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                        cwd=ROOT, **child_options())
                self.children.add(proc)
                code = proc.wait(timeout=300)
                if code:
                    raise ValueError(f"Codex login exited with code {code}; retry Sign in")
                self.refresh(profile)
                self.store.event(f"Signed in: {profile['name']}")
            except Exception as exc:
                self.store.execute("UPDATE profiles SET error=? WHERE id=?", (str(exc), ident))
            finally:
                stop_tree(proc)
                self.login_in_progress = False
                self.login_lock.release()
                self.wake.set()
        threading.Thread(target=perform, daemon=True).start()

    def begin(self):
        self.worker = threading.Thread(target=self.loop, daemon=True, name="autowork-worker")
        self.worker.start()

    def loop(self):
        self.store.event("Supervisor is online on this device")
        while not self.stop.is_set():
            try:
                if time.time() - (self.store.setting("catalog_checked") or 0) > 300:
                    self.brain.discover()
                if self.store.setting("running"):
                    self.brain.maybe_plan()
                pending = self.store.one("SELECT * FROM projects WHERE state='queued' ORDER BY priority DESC,created ASC")
                active = bool(self.store.setting("running") and pending)
                needs_awake = bool(self.store.setting("running") and (pending or self.store.setting("advisor_auto")))
                self.set_awake(needs_awake and self.store.setting("keep_awake"))
                if active:
                    self.step(pending)
            except Exception:
                LOG.exception("Supervisor loop failed")
                self.store.event("Worker error; inspect data/supervisor.log. The queue will retry after a delay.")
            self.wake.wait(20)
            self.wake.clear()
        self.set_awake(False)

    def step(self, project):
        if project["steps"] >= project["max_steps"]:
            self.store.execute("UPDATE projects SET state='attention',note='Milestone cap reached. Review progress and raise the cap if needed.' WHERE id=?", (project["id"],))
            return
        selected = None
        with self.account_lock:
            for profile in self.store.rows("SELECT * FROM profiles WHERE enabled=1 AND provider=? ORDER BY id", (project.get("provider", "codex"),)):
                if profile["error"] and time.time() - profile["checked"] < 60:
                    continue
                rpc = None
                try:
                    if profile.get("provider", "codex") != "codex":
                        if self.select_external(project, profile):
                            selected = (profile, None)
                            break
                        continue
                    rpc = Rpc(self.profile_binary(profile), profile["home"], self.children)
                    snapshot = self.refresh(profile, rpc)
                    ok, reason, reset = quota_gate(snapshot["limits"], self.store.setting("quota_ceiling"))
                    if ok:
                        selected = (profile, rpc)
                        break
                    if "Quota reserve" in reason or "reached usage limit" in reason:
                        self.request_reset(profile, snapshot)
                    self.store.execute("UPDATE projects SET note=? WHERE id=?", (f"{profile['name']}: {reason}", project["id"]))
                except Exception:
                    LOG.info("Account %s not ready", profile["id"])
                if rpc:
                    rpc.close()
            if selected:
                # Serialize selection with reset approvals and pause/cancel actions.
                self.run_step(project, *selected)

    def run_step(self, project, profile, rpc):
        proc = None
        run_job = ChildJob()
        run_id = uuid.uuid4().hex
        log_path = self.store.directory / "runs" / f"{run_id}.jsonl"
        log_path.parent.mkdir(exist_ok=True)
        final_path = self.store.directory / "runs" / f"{run_id}.result.json"
        reason = ""
        last_errors = []
        is_advisor = project.get("kind") == "advisor"
        provider = project.get("provider", "codex")
        captured = []
        captured_size = 0
        try:
            with self.active_lock:
                fresh = self.store.one("SELECT state FROM projects WHERE id=?", (project["id"],))
                if not self.store.setting("running") or not fresh or fresh["state"] != "queued":
                    return
                if self.last_profile != profile["id"]:
                    self.store.event(f"Selected {profile['name']} for local work")
                    self.last_profile = profile["id"]
                self.store.execute("UPDATE projects SET state='running',note='' WHERE id=?", (project["id"],))
                self.store.execute("INSERT INTO runs(id,project_id,profile_id,started,log) VALUES(?,?,?,?,?)",
                                   (run_id, project["id"], profile["id"], utcnow(), str(log_path)))
                model = project["model"]
                if not model and provider == "codex":
                    catalog = rpc.call("model/list", {"includeHidden": False}).get("data", [])
                    default = next((m for m in catalog if m.get("isDefault")), None)
                    if not default or not default.get("model"):
                        raise ValueError("Account default model is unavailable. Specify an available model for this project.")
                    model = default["model"]
                prompt = self.brain.prompt(project, rpc) if is_advisor else (
                    f"Build this local project: {project['name']}\n\nGoal:\n{project['goal']}\n\n"
                    f"Supervisor checkpoint:\n{project['checkpoint']}\n\nUser guidance:\n{project.get('guidance', '')}\n\n"
                    "Inspect the existing files and AUTOWORK_CHECKPOINT.md first. Complete ONE useful milestone in this turn. "
                    "Implement real working code, run meaningful checks, and save a concise handoff in AUTOWORK_CHECKPOINT.md "
                    "so another signed-in account can continue from these files. Do not undo existing work. "
                    "Keep all project writes in this workspace. Do not deploy, publish, spend money, inspect credentials, "
                    "change account settings, or send messages. Do not use subagents. If blocked by permissions or missing "
                    "information, set status=blocked and put the exact request in question. Mark complete only when the "
                    "stated goal and its acceptance checks are met. Return the required structured result."
                )
                command = providers.command(provider, self.profile_binary(profile), project,
                                            ROOT / ("advisor-schema.json" if is_advisor else "result-schema.json"),
                                            final_path, model, json.loads(profile.get("options", "{}")).get("command"))
                proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        text=True, encoding="utf-8", errors="replace", cwd=project["path"],
                                        env=providers.environment(provider, profile["home"]), **child_options())
                run_job.add(proc)
                self.active_proc = proc
            if provider != "codex":
                schema = (ROOT / ("advisor-schema.json" if is_advisor else "result-schema.json")).read_text(encoding="utf-8")
                prompt += "\nReturn ONLY one JSON object conforming to this schema:\n" + schema
            proc.stdin.write(prompt)
            proc.stdin.close()
            events = queue.Queue()

            def read_stream(stream, source):
                try:
                    for line in stream:
                        events.put((source, line))
                finally:
                    events.put((source, None))
            for stream, source in ((proc.stdout, "stdout"), (proc.stderr, "stderr")):
                threading.Thread(target=read_stream, args=(stream, source), daemon=True).start()
            started = time.monotonic()
            check_at = started + 15
            ended_streams = 0
            with log_path.open("w", encoding="utf-8") as log:
                while ended_streams < 2:
                    try:
                        source, line = events.get(timeout=.5)
                        if line is None:
                            ended_streams += 1
                        else:
                            if source == "stdout":
                                if provider != "codex":
                                    captured_size += len(line)
                                    if captured_size > 8_000_000:
                                        reason = "Provider output exceeded the 8 MB capture limit"
                                    else:
                                        captured.append(line)
                                try:
                                    payload = json.loads(line)
                                except ValueError:
                                    payload = {"text": line.rstrip()}
                            else:
                                payload = {"type": "stderr", "text": line.rstrip()}
                            log.write(json.dumps(sanitize(payload), ensure_ascii=False) + "\n")
                            log.flush()
                            if payload.get("type") in ("error", "turn.failed", "stderr"):
                                last_errors.append(json.dumps(sanitize(payload))[-1600:])
                                last_errors = last_errors[-5:]
                    except queue.Empty:
                        pass
                    if proc.poll() is not None:
                        # Close the per-run job to stop detached dev servers and release their pipes.
                        run_job.close()
                        continue
                    state = self.store.one("SELECT state FROM projects WHERE id=?", (project["id"],))
                    enabled = self.store.one("SELECT enabled FROM profiles WHERE id=?", (profile["id"],))
                    if self.stop.is_set() or not self.store.setting("running") or not state or state["state"] != "running" or not enabled or not enabled["enabled"]:
                        reason = "Paused by user; existing files retained"
                    elif time.monotonic() - started > (min(10, self.store.setting("turn_minutes")) if is_advisor else self.store.setting("turn_minutes")) * 60:
                        reason = "Milestone time limit reached; inspect the checkpoint before retrying"
                    elif provider == "codex" and time.monotonic() >= check_at:
                        try:
                            snapshot = self.refresh(profile, rpc)
                            ok, why, reset = quota_gate(snapshot["limits"], self.store.setting("quota_ceiling"))
                            if not ok:
                                reason = "Quota stop: " + why
                                if "Quota reserve" in why or "reached usage limit" in why:
                                    self.request_reset(profile, snapshot)
                        except Exception:
                            reason = "Quota monitor is unavailable; paused to protect the credit rule"
                        check_at = time.monotonic() + 15
                    if reason:
                        stop_tree(proc)
                code = proc.wait(timeout=10)
            fresh = self.store.one("SELECT state FROM projects WHERE id=?", (project["id"],))
            if reason:
                if fresh["state"] == "running":
                    target = "queued" if reason.startswith("Quota stop:") else "attention"
                    self.store.execute("UPDATE projects SET state=?,note=? WHERE id=?", (target, reason, project["id"]))
                self.store.execute("UPDATE runs SET state='interrupted',finished=?,result=? WHERE id=?", (utcnow(), reason, run_id))
            elif code != 0:
                error = "\n".join(last_errors)[-3000:] or f"AI tool exited with code {code}"
                self.fail(project, run_id, error)
            else:
                result = providers.parse_result(provider, "".join(captured), final_path)
                if result.get("status") not in ("continue", "complete", "blocked") or any(not isinstance(result.get(k), str) for k in ("summary", "tests", "next_step", "question")):
                    raise ValueError("AI tool returned an invalid checkpoint")
                if is_advisor:
                    self.brain.save_suggestions(run_id, result)
                target = {"continue": "queued", "complete": "complete", "blocked": "attention"}[result["status"]]
                self.store.execute("UPDATE projects SET state=?,steps=steps+1,failures=0,checkpoint=?,note=? WHERE id=? AND state='running'",
                                   (target, json.dumps(result), result["question"] or result["next_step"], project["id"]))
                self.store.execute("UPDATE runs SET state='complete',finished=?,result=? WHERE id=?", (utcnow(), json.dumps(result), run_id))
                self.store.event(f"{project['name']}: {result['summary'][:180]}")
        except Exception as exc:
            LOG.exception("Milestone failed")
            stop_tree(proc)
            self.fail(project, run_id, str(exc))
        finally:
            run_job.close()
            with self.active_lock:
                self.active_proc = None
            for stream in (proc.stdout, proc.stderr) if proc else ():
                if stream:
                    stream.close()
            if rpc:
                rpc.close()

    def fail(self, project, run_id, error):
        self.store.execute("UPDATE runs SET state='failed',finished=?,result=? WHERE id=?", (utcnow(), error[:3000], run_id))
        fresh = self.store.one("SELECT * FROM projects WHERE id=?", (project["id"],))
        if fresh and fresh["state"] == "running":
            target = "attention" if fresh["failures"] >= 2 else "queued"
            self.store.execute("UPDATE projects SET state=?,failures=failures+1,note=? WHERE id=?", (target, error[:1500], project["id"]))
        self.store.event(f"{project['name']}: milestone failed; {error[:180]}")

    def state(self):
        profiles = self.store.rows("SELECT * FROM profiles ORDER BY id")
        for profile in profiles:
            profile["snapshot"] = json.loads(profile["snapshot"])
            profile["snapshot"].get("account", {}).pop("email", None)
            if profile.get("provider", "codex") != "codex":
                profile["eligible"] = False
                profile["reason"] = profile["error"] or "Approval required for every run; vendor quota and costs are unverified"
                profile["instructions"] = self.profile_instructions(profile)
                continue
            profile["instructions"] = self.profile_instructions(profile)
            profile["eligible"], profile["reason"], profile["reset_at"] = quota_gate(profile["snapshot"].get("limits", {}), self.store.setting("quota_ceiling"))
            if profile["error"]:
                profile["eligible"] = False
                profile["reason"] = profile["error"]
        projects = self.store.rows("SELECT * FROM projects WHERE kind='work' ORDER BY priority DESC,created DESC")
        for project in projects:
            project["checkpoint"] = json.loads(project["checkpoint"])
        catalog = self.store.rows("SELECT * FROM catalog ORDER BY name")
        for item in catalog:
            item["details"] = json.loads(item["details"])
            item["recent"] = json.loads(item["recent"])
            item["is_supervisor"] = path_key(item["path"]) == path_key(ROOT)
        suggestions = self.store.rows("SELECT * FROM suggestions ORDER BY (SELECT MAX(batch.created) FROM suggestions batch WHERE batch.run_id=suggestions.run_id) DESC,created ASC LIMIT 60")
        for item in suggestions:
            item["payload"] = json.loads(item["payload"])
        advisor = self.store.one("SELECT id,state,note,checkpoint FROM projects WHERE kind='advisor' ORDER BY created DESC LIMIT 1")
        return {"running": self.store.setting("running"), "quota_ceiling": self.store.setting("quota_ceiling"),
                "catalog": catalog, "catalog_error": self.store.setting("catalog_error"), "suggestions": suggestions,
                "advisor": advisor, "advisor_auto": self.store.setting("advisor_auto"), "advisor_hours": self.store.setting("advisor_hours"),
                "advisor_summary": self.store.setting("advisor_summary"), "advisor_completed": self.store.setting("advisor_completed"),
                "turn_minutes": self.store.setting("turn_minutes"), "keep_awake": self.store.setting("keep_awake"),
                "profiles": profiles, "projects": projects, "binary": self.binary,
                "tools": self.tool_status(), "onboarded": self.store.setting("onboarded"),
                "workspace_root": self.store.setting("workspace_root"), "platform": sys.platform,
                "advisor_provider": self.store.setting("advisor_provider"),
                "runs": self.store.rows("SELECT * FROM runs ORDER BY started DESC LIMIT 40"),
                "decisions": self.store.rows("SELECT * FROM decisions ORDER BY created DESC LIMIT 40"),
                "events": self.store.rows("SELECT * FROM events ORDER BY id DESC LIMIT 40"),
                "login_in_progress": self.login_in_progress}


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "Runquay/0.2"

    def log_message(self, fmt, *args):
        LOG.debug(fmt, *args)

    def valid_host(self):
        return self.headers.get("Host", "") in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

    def send_data(self, data, code=200, mime="application/json; charset=utf-8", cookie=False):
        body = json.dumps(data, ensure_ascii=False).encode() if mime.startswith("application/json") else data
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if cookie:
            self.send_header("Set-Cookie", f"autowork={self.server.token}; HttpOnly; SameSite=Strict; Path=/")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def authorized(self):
        cookies = dict(part.strip().split("=", 1) for part in self.headers.get("Cookie", "").split(";") if "=" in part)
        return secrets.compare_digest(cookies.get("autowork", ""), self.server.token)

    def do_GET(self):
        if not self.valid_host():
            return self.send_data({"error": "Invalid local host"}, 403)
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            return self.send_data({"error": "Cross-site access denied"}, 403)
        path = urllib.parse.urlparse(self.path).path
        static = {"/mark.svg": ("mark.svg", "image/svg+xml"), "/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"), "/setup.js": ("setup.js", "text/javascript; charset=utf-8"), "/style.css": ("style.css", "text/css; charset=utf-8")}
        if path in static:
            name, mime = static[path]
            return self.send_data((ROOT / "web" / name).read_bytes(), mime=mime, cookie=path == "/")
        if not self.authorized():
            return self.send_data({"error": "Open the dashboard first"}, 403)
        if path == "/api/state":
            state = self.server.supervisor.state()
            state["csrf"] = self.server.token
            return self.send_data(sanitize(state))
        if path.startswith("/api/run/"):
            run = self.server.supervisor.store.one("SELECT * FROM runs WHERE id=?", (path.split("/")[-1],))
            if not run:
                return self.send_data({"error": "Run not found"}, 404)
            file = Path(run["log"])
            if file.exists():
                with file.open("rb") as stream:
                    stream.seek(max(0, file.stat().st_size - 80000))
                    log = stream.read().decode("utf-8", errors="replace")
            else:
                log = "No output yet"
            return self.send_data({"run": sanitize(run), "log": redact(log)})
        self.send_data({"error": "Not found"}, 404)

    def do_POST(self):
        origin = self.headers.get("Origin")
        expected = {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}
        if not self.valid_host() or not self.authorized() or not secrets.compare_digest(self.headers.get("X-AutoWork-CSRF", ""), self.server.token) or (origin and origin not in expected):
            return self.send_data({"error": "Local session verification failed"}, 403)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 65536:
                raise ValueError("Invalid request size")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("Request must be a JSON object")
            sup = self.server.supervisor
            path = urllib.parse.urlparse(self.path).path
            if path == "/api/control":
                action = data["action"]
                if action not in ("start", "pause"):
                    raise ValueError("Unknown action")
                with sup.active_lock:
                    sup.store.set("running", action == "start")
                    if action == "pause":
                        stop_tree(sup.active_proc)
                sup.store.event("Queue started" if action == "start" else "Queue paused")
            elif path == "/api/projects":
                ident = sup.create_project(data)
                return self.send_data({"id": ident}, 201)
            elif path == "/api/catalog/refresh":
                sup.brain.discover()
            elif path == "/api/catalog/add":
                ident = sup.brain.add_folder(data.get("path", ""), data.get("name", ""))
                return self.send_data({"id": ident}, 201)
            elif path == "/api/onboarding":
                if data.get("acknowledged") is not True:
                    raise ValueError("Review the local workspace, provider billing, and permissions before finishing setup")
                provider = str(data.get("provider", "codex"))
                if provider not in providers.TOOLS:
                    raise ValueError("Unknown tool")
                workspace = Path(str(data.get("workspace_root", sup.store.setting("workspace_root")))).expanduser()
                if not workspace.is_absolute():
                    raise ValueError("Choose an absolute workspace folder path")
                workspace.mkdir(parents=True, exist_ok=True)
                sup.store.set("workspace_root", str(workspace.resolve()))
                if providers.TOOLS[provider]["advisor"]:
                    sup.store.set("advisor_provider", provider)
                sup.store.set("onboarded", True)
            elif path == "/api/advisor":
                ident = sup.brain.request_plan(str(data.get("catalog_id", "")), str(data.get("focus", "")), str(data.get("provider", sup.store.setting("advisor_provider"))))
                sup.wake.set()
                return self.send_data({"id": ident}, 202)
            elif path == "/api/suggestion":
                if data.get("action") == "start":
                    ident = sup.brain.start_suggestion(data["id"], data)
                    return self.send_data({"id": ident}, 201)
                if data.get("action") == "dismiss":
                    sup.store.execute("UPDATE suggestions SET state='dismissed' WHERE id=? AND state='proposed'", (data["id"],))
                else:
                    raise ValueError("Unknown suggestion action")
            elif path == "/api/project":
                project = sup.store.one("SELECT * FROM projects WHERE id=?", (data["id"],))
                if not project:
                    raise ValueError("Project not found")
                action = data["action"]
                with sup.active_lock:
                    if action == "resume" and project["state"] != "running":
                        steps = int(data.get("max_steps", project["max_steps"]))
                        if not project["steps"] < steps <= 200:
                            raise ValueError("Set the cap above completed milestones (maximum 200)")
                        sup.store.execute("UPDATE projects SET state='queued',failures=0,guidance=?,note='Queued with your guidance',max_steps=? WHERE id=?",
                                          (str(data.get("guidance", project.get("guidance", "")))[:10000], steps, project["id"]))
                    elif action in ("pause", "cancel"):
                        sup.store.execute("UPDATE projects SET state=?,note=? WHERE id=?", ("paused" if action == "pause" else "cancelled", "Paused by user" if action == "pause" else "Cancelled by user", project["id"]))
                        if project["state"] == "running":
                            stop_tree(sup.active_proc)
                    else:
                        raise ValueError("Unknown project action or project is already running")
            elif path == "/api/accounts/refresh":
                threading.Thread(target=sup.refresh_all, daemon=True).start()
            elif path == "/api/account":
                if data["action"] == "add":
                    ident = sup.add_profile(data)
                    return self.send_data({"id": ident}, 201)
                elif data["action"] == "remove":
                    sup.remove_profile(data["id"])
                elif data["action"] == "verify":
                    profile = sup.store.one("SELECT * FROM profiles WHERE id=?", (data["id"],))
                    if not profile:
                        raise ValueError("Account not found")
                    threading.Thread(target=lambda: sup.refresh_one_safely(profile), daemon=True).start()
                elif data["action"] == "login":
                    sup.login(data["id"])
                elif data["action"] == "toggle":
                    sup.store.execute("UPDATE profiles SET enabled=? WHERE id=?", (int(bool(data["enabled"])), data["id"]))
                else:
                    raise ValueError("Unknown account action")
            elif path == "/api/decision":
                decision = sup.store.one("SELECT * FROM decisions WHERE id=?", (data["id"],))
                if not decision:
                    raise ValueError("Decision not found")
                if decision["kind"] == "external_run":
                    sup.decide_external(decision, data.get("approve") is True)
                    return self.send_data({"ok": True})
                # Account lock is held by an active turn, so check before waiting on it.
                if data.get("approve") and sup.active_proc is not None:
                    raise ValueError("Pause the queue before approving a reset")
                sup.decide_reset(data["id"], data.get("approve") is True)
            elif path == "/api/settings":
                ceiling = int(data["quota_ceiling"])
                minutes = int(data["turn_minutes"])
                if not 50 <= ceiling <= 90 or not 2 <= minutes <= 120:
                    raise ValueError("Quota reserve must be 50–90%; milestone time must be 2–120 minutes")
                sup.store.set("quota_ceiling", ceiling)
                sup.store.set("turn_minutes", minutes)
                sup.store.set("keep_awake", bool(data.get("keep_awake")))
                sup.store.set("advisor_auto", bool(data.get("advisor_auto", sup.store.setting("advisor_auto"))))
                hours = int(data.get("advisor_hours", sup.store.setting("advisor_hours")))
                if not 1 <= hours <= 72:
                    raise ValueError("Advisor interval must be 1–72 hours")
                sup.store.set("advisor_hours", hours)
            else:
                return self.send_data({"error": "Not found"}, 404)
            sup.wake.set()
            self.send_data({"ok": True})
        except (KeyError, ValueError, TypeError) as exc:
            self.send_data({"error": str(exc)}, 400)
        except Exception as exc:
            LOG.exception("Request failed")
            self.send_data({"error": "Internal error; inspect the private supervisor log"}, 500)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data", type=Path, default=default_data(ROOT))
    parser.add_argument("--open", action="store_true", help="Open the guided local dashboard")
    parser.add_argument("--codex")
    args = parser.parse_args()
    if os.name != "nt":
        os.umask(0o077)
    private_directory(args.data)
    from logging.handlers import RotatingFileHandler
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[RotatingFileHandler(args.data / "supervisor.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")])
    for handler in logging.getLogger().handlers:
        handler.setFormatter(PrivateLogFormatter("%(asctime)s %(levelname)s %(message)s"))
    # Bind before recovery or worker startup, so a second launch cannot disturb live work.
    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    except OSError:
        LOG.error("Port %s is already in use; existing supervisor left running", args.port)
        return
    server.daemon_threads = True
    try:
        data_lock = DataLock(args.data)
    except RuntimeError as exc:
        LOG.error("%s", exc)
        server.server_close()
        return
    sup = Supervisor(args.data, args.codex)
    server.supervisor = sup
    server.token = secrets.token_urlsafe(32)
    sup.bootstrap()
    sup.begin()
    threading.Thread(target=sup.refresh_all, daemon=True).start()
    (args.data / "supervisor.pid").write_text(str(os.getpid()), encoding="ascii")
    def shutdown(signum, frame):
        sup.stop.set()
        sup.wake.set()
        threading.Thread(target=server.shutdown, daemon=True).start()
    signal.signal(signal.SIGTERM, shutdown)
    if args.open:
        import webbrowser
        webbrowser.open(f"http://127.0.0.1:{args.port}/")
    try:
        server.serve_forever(poll_interval=.5)
    except KeyboardInterrupt:
        pass
    finally:
        sup.stop.set()
        sup.wake.set()
        stop_tree(sup.active_proc)
        if sup.worker:
            sup.worker.join(timeout=15)
        sup.children.close()
        sup.set_awake(False)
        server.server_close()
        data_lock.close()


if __name__ == "__main__":
    main()
