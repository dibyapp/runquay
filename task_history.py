"""Bounded, read-only local history adapters. No vendor CLI or model is launched."""
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import time

from security import redact

NAMES = {"codex": "Codex", "claude": "Claude Code", "gemini": "Gemini CLI",
         "antigravity": "Antigravity", "custom": "Other tools"}
MAX_FILES = 1000
HEAD_BYTES = 128 * 1024
TAIL_BYTES = 32 * 1024
MAX_JSON_BYTES = 2 * 1024 * 1024


def timestamp(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        result = value / 1000 if value > 100_000_000_000 else value
        return result if math.isfinite(result) and 0 <= result < 253_402_300_800 else None
    if isinstance(value, str):
        try:
            date = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return timestamp(date.replace(tzinfo=date.tzinfo or timezone.utc).timestamp())
        except (ValueError, OverflowError, OSError):
            pass
    return None


def text(value, limit=700):
    if isinstance(value, str):
        return redact(value[:limit * 2]).strip()[:limit]
    if isinstance(value, list):
        # Text only: attachments, images, thoughts and tool results are excluded.
        parts = [p.get("text", "") for p in value[:20] if isinstance(p, dict)
                 and p.get("type", "text") == "text" and isinstance(p.get("text"), str)]
        return text("\n".join(p[:limit] for p in parts), limit)
    return ""


def task(provider, ident, title="", preview="", cwd="", updated=None, tool="", source="Local history"):
    if not isinstance(ident, str) or not ident or len(ident) > 200:
        return None
    name = text(tool, 64) or NAMES[provider]
    preview = text(preview)
    title = text(title, 240) or (preview.splitlines()[0][:120] if preview else "Untitled task")
    cwd = cwd if isinstance(cwd, str) and len(cwd) <= 4096 and Path(cwd).is_absolute() else ""
    return {"id": ident, "key": provider + "-" + hashlib.sha256((name + "\0" + ident).encode()).hexdigest()[:32],
            "provider": provider, "tool": name, "title": title, "preview": preview, "path": cwd,
            "updated_at": timestamp(updated), "source": source}


def bind_tasks(tasks, library):
    from codex_brain import path_key
    roots = sorted(library, key=lambda p: len(path_key(p["path"])), reverse=True)
    result, seen = [], set()
    for original in tasks:
        if not original or original["key"] in seen:
            continue
        seen.add(original["key"])
        item = dict(original)
        key = path_key(item["path"]) if item["path"] else ""
        root = next((r for r in roots if key and (key == path_key(r["path"]) or
                    key.startswith(path_key(r["path"]) + os.sep))), None)
        item.update(catalog_id=root["id"] if root else "",
                    project_name=root["name"] if root else Path(item["path"]).name if item["path"] else "Folder not recorded")
        result.append(item)
    return sorted(result, key=lambda t: t["updated_at"] or 0, reverse=True)


def safe_file(path, root):
    """Reject links, junctions, special files and paths outside the history root."""
    path, root = Path(path).absolute(), Path(root).absolute()
    if not path.is_relative_to(root):
        return False
    for item in (path, *path.parents):
        if not item.is_relative_to(root):
            break
        info = item.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            return False
    return path.is_file()


def records(path, root):
    if not safe_file(path, root):
        return []
    with path.open("rb") as stream:
        size = os.fstat(stream.fileno()).st_size
        chunks = [stream.read(HEAD_BYTES)]
        if size > HEAD_BYTES:
            stream.seek(max(HEAD_BYTES, size - TAIL_BYTES))
            chunks.append(stream.read(TAIL_BYTES))
    result = []
    for n, chunk in enumerate(chunks):
        lines = chunk.splitlines()
        if n:
            lines = lines[1:]  # A seek can land in a partially written record.
        for line in lines:
            try:
                item = json.loads(line)
            except (ValueError, UnicodeError):
                continue
            if isinstance(item, dict):
                result.append(item)
    if size and not result:
        raise ValueError("Unreadable session metadata")
    return result


def small_json(path, root):
    if not safe_file(path, root):
        return None
    with path.open("rb") as stream:
        raw = stream.read(MAX_JSON_BYTES + 1)
    if len(raw) > MAX_JSON_BYTES:
        raise ValueError("History metadata is too large")
    return json.loads(raw)


def claude_task(path, root):
    rows = records(path, root)
    if not rows or any(r.get("isSidechain") or r.get("type") == "tag" and r.get("tag") == "__hidden" for r in rows):
        return None
    title, custom_title, preview, cwd = "", "", "", ""
    ident = path.stem
    for r in rows:
        if r.get("sessionId"):
            ident = r["sessionId"]
        if isinstance(r.get("cwd"), str) and not cwd:
            cwd = r["cwd"]
        if r.get("type") == "custom-title":
            custom_title = text(r.get("customTitle"), 240) or custom_title
        elif r.get("type") == "ai-title":
            title = text(r.get("aiTitle"), 240) or title
        elif r.get("type") == "summary" and not title:
            title = text(r.get("summary"), 240)
        if r.get("type") == "user" and not preview:
            message = r.get("message", {})
            content = message.get("content") if isinstance(message, dict) else None
            preview = text(content)
            if preview.startswith(("<local-command", "<command-name", "<system-reminder")):
                preview = ""
    if not preview and not title:
        return None
    return task("claude", ident, custom_title or title, preview, cwd, path.stat().st_mtime)


def gemini_task(path, root):
    metadata, preview = {}, ""
    if path.suffix == ".json":
        value = small_json(path, root)
        if not isinstance(value, dict):
            return None
        metadata = value
        rows = value.get("messages", [])
        if not isinstance(rows, list):
            return None
    else:
        rows = records(path, root)
    for r in rows:
        if not isinstance(r, dict):
            continue
        if r.get("sessionId"):
            metadata.update({k: r[k] for k in ("sessionId", "kind", "summary", "lastUpdated") if k in r})
        if isinstance(r.get("$set"), dict):
            metadata.update({k: r["$set"][k] for k in ("kind", "summary", "lastUpdated") if k in r["$set"]})
        if r.get("type") == "user" and not preview:
            preview = text(r.get("displayContent") or r.get("content"))
    if metadata.get("kind") == "subagent" or not preview:
        return None  # Empty version/startup sessions are not user tasks.
    project_root = path.parent.parent / ".project_root"
    cwd = ""
    if project_root.exists() and safe_file(project_root, root):
        with project_root.open("r", encoding="utf-8") as stream:
            cwd = stream.read(4096).strip()
    return task("gemini", metadata.get("sessionId", path.stem), metadata.get("summary"), preview,
                cwd, metadata.get("lastUpdated") or path.stat().st_mtime)


def antigravity_task(path, root, workspace=""):
    rows = records(path, root)
    preview, cwd = "", workspace
    for r in rows:
        if r.get("type") == "USER_INPUT" and not preview:
            content = r.get("content", "")
            if isinstance(content, str):
                request = re.search(r"<USER_REQUEST>([\s\S]*?)</USER_REQUEST>", content)
                preview = text(request.group(1) if request else content)
        if not cwd and isinstance(r.get("cwd"), str):
            cwd = r["cwd"]
        calls = r.get("tool_calls", [])
        for call in calls[:30] if isinstance(calls, list) else []:
            args = call.get("args", {}) if isinstance(call, dict) else {}
            if not cwd and isinstance(args, dict) and isinstance(args.get("Cwd"), str):
                cwd = args["Cwd"]
    if not preview:
        return None
    ident = path.parents[2].name
    return task("antigravity", ident, preview=preview, cwd=cwd, updated=path.stat().st_mtime,
                source="Local transcript · folder from recorded working directory" if cwd and not workspace else "Local transcript")


def history_roots(provider, profiles=(), home=None):
    home = Path(home or Path.home())
    if provider == "claude":
        configured = os.environ.get("CLAUDE_CONFIG_DIR")
        roots = [Path(configured)] if configured and Path(configured).is_absolute() else [home / ".claude"]
        roots += [Path(p["home"]) for p in profiles if p.get("provider") == provider]
    elif provider == "gemini":
        configured = os.environ.get("GEMINI_CLI_HOME")
        base = Path(configured) if configured and Path(configured).is_absolute() else home
        roots = [base / ".gemini"]
        roots += [Path(p["home"]) / ".gemini" for p in profiles if p.get("provider") == provider]
    else:
        roots = [home / ".gemini" / name for name in ("antigravity", "antigravity-cli", "antigravity-ide")]
    return list(dict.fromkeys(roots))


def read_local_tasks(provider, profiles=(), home=None):
    roots = history_roots(provider, profiles, home)
    patterns = {"claude": ["projects/*/*.jsonl"], "gemini": ["tmp/*/chats/session-*.json", "tmp/*/chats/session-*.jsonl"],
                "antigravity": ["brain/*/.system_generated/logs/transcript.jsonl"]}[provider]
    reader = {"claude": claude_task, "gemini": gemini_task, "antigravity": antigravity_task}[provider]
    files, tasks, skipped = [], [], 0
    limited, unavailable, binary = False, False, False
    for root in roots:
        if not root.exists():
            continue
        try:
            for pattern in patterns:
                for path in root.glob(pattern):
                    if len(files) >= MAX_FILES * 2:
                        limited = True
                        break
                    if safe_file(path, root):
                        files.append((path.stat().st_mtime, path, root))
            if provider == "antigravity":
                binary |= next(root.glob("conversations/*.pb"), None) is not None
        except OSError:
            unavailable = True
    files.sort(key=lambda entry: entry[0], reverse=True)
    limited |= len(files) > MAX_FILES
    for _, path, root in files[:MAX_FILES]:
        try:
            item = reader(path, root)
            if item:
                tasks.append(item)
        except (OSError, ValueError, TypeError, UnicodeError):
            skipped += 1
    if provider == "antigravity":
        # The official CLI cache can expose a workspace reference without a transcript.
        known = {t["id"] for t in tasks}
        for root in roots:
            cache = root / "cache/last_conversations.json"
            if not cache.exists():
                continue
            try:
                mapping = small_json(cache, root)
                if isinstance(mapping, dict):
                    for cwd, ident in list(mapping.items())[:MAX_FILES]:
                        if ident not in known and isinstance(cwd, str) and Path(cwd).is_absolute():
                            item = task(provider, ident, cwd=cwd, source="Cached reference · open Antigravity to verify")
                            if item:
                                tasks.append(item)
                                known.add(ident)
            except (OSError, ValueError, TypeError):
                skipped += 1
    tasks = bind_tasks(tasks, [])[:MAX_FILES]
    state = "unavailable" if unavailable and not tasks else "partial" if limited or skipped or binary else "ready" if tasks else "empty"
    note = "Local history read without starting AI work."
    if state == "empty":
        note = "No saved local tasks found. Sign-in or installing a tool alone does not create tasks."
    elif state == "unavailable":
        note = "Local history could not be read. Previously found tasks remain visible."
    elif state == "partial":
        note = "Some history may be missing: bounded reads, unreadable records or older formats."
    if provider == "antigravity" and binary:
        note += " Encrypted conversation files are not decoded; available local transcripts are shown."
    return tasks, {"provider": provider, "tool": NAMES[provider], "state": state, "limited": limited,
                   "count": len(tasks), "checked": time.time(), "note": note}


def import_tasks(payload):
    if not isinstance(payload, dict) or payload.get("version") != 1 or not isinstance(payload.get("tasks"), list):
        raise ValueError("Choose a Runquay history JSON export with version 1 and a tasks list.")
    name = text(payload.get("tool"), 64)
    if not name or not 1 <= len(payload["tasks"]) <= 100:
        raise ValueError("A history export needs a tool name and 1–100 tasks.")
    result = []
    for row in payload["tasks"]:
        if not isinstance(row, dict) or not isinstance(row.get("title"), str) or not row["title"].strip():
            raise ValueError("Every imported task needs an id and title.")
        cwd = row.get("cwd", "")
        if cwd and (not isinstance(cwd, str) or not Path(cwd).is_absolute()):
            raise ValueError("Imported folder paths must be absolute or omitted.")
        item = task("custom", row.get("id"), row["title"], row.get("preview", ""), cwd,
                    row.get("updated_at"), tool=name, source="Imported metadata")
        if not item:
            raise ValueError("Every imported task needs a short text id.")
        result.append(item)
    return result
