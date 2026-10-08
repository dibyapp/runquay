"""Allowlisted source packaging. Never archives a working directory wholesale."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile
from security import PATTERNS

ROOT = Path(__file__).resolve().parent
IGNORED = {"__pycache__", "node_modules", ".git", "data", "projects", "accounts", ".venv"}
EXTENSIONS = {".py", ".md", ".json", ".js", ".css", ".html", ".yml", ".yaml", ".toml", ".sh", ".cmd", ".ps1", ".svg"}


def has_credential(text):
    for index, pattern in enumerate(PATTERNS):
        for match in pattern.finditer(text):
            # Exact historical unit-test literals, never real credential formats.
            if index == 2 and re.search(r'[:=][\s"\x27]*(?:test-key|test-token)$', match.group()):
                continue
            return True
    return False


def source_files(root=ROOT):
    root = Path(root).resolve()
    manifest = json.loads((root / "release-manifest.json").read_text(encoding="utf-8"))
    candidates = [root / name for name in manifest["files"]]
    for directory in manifest["directories"]:
        candidates += [p for p in (root / directory).rglob("*") if p.is_file() and p.suffix in EXTENSIONS and not IGNORED.intersection(p.relative_to(root).parts)]
    files = []
    for path in sorted(set(candidates)):
        if not path.is_file():
            raise ValueError("Release source missing: " + str(path.relative_to(root)))
        if not path.resolve().is_relative_to(root) or any(parent.is_symlink() for parent in [path, *path.parents] if parent.is_relative_to(root)):
            raise ValueError("Symlinks cannot enter a release")
        files.append(path)
    return files


def audit(files, root=ROOT):
    findings = []
    home = str(Path.home())
    private_paths = {home, home.replace("\\", "/"), home.replace("\\", "\\\\")}
    for file in files:
        text = file.read_text(encoding="utf-8")
        name = str(file.relative_to(root))
        if has_credential(text):
            findings.append(name + ": credential-like content")
        if any(value in text for value in private_paths if len(value) > 1):
            findings.append(name + ": private home directory")
        if re.search(r"\b[A-Za-z0-9._%+-]+@(?!example\.(?:com|org|net)\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text):
            findings.append(name + ": non-example email address")
    return findings


def history_audit(root=ROOT):
    # Check every historical blob, including files no longer in the working tree.
    probe = subprocess.run(["git", "rev-list", "--objects", "--all"], cwd=root, capture_output=True, text=True)
    if probe.returncode:
        if (Path(root) / ".git").exists():
            raise ValueError("Git history could not be audited; inspect the repository before releasing")
        return []  # No repository/history in a source ZIP.
    findings = []
    for row in probe.stdout.splitlines():
        oid, _, name = row.partition(" ")
        if not name:
            continue
        kind = subprocess.run(["git", "cat-file", "-t", oid], cwd=root, capture_output=True, text=True)
        if kind.stdout.strip() != "blob":
            continue
        value = subprocess.run(["git", "cat-file", "blob", oid], cwd=root, capture_output=True).stdout.decode("utf-8", errors="replace")
        if has_credential(value) or str(Path.home()) in value or str(Path.home()).replace("\\", "/") in value:
            findings.append("History contains sensitive content in " + name + " (" + oid[:8] + ")")
        if re.search(r"\b[A-Za-z0-9._%+-]+@(?!example\.(?:com|org|net)\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", value):
            findings.append("History contains a non-example email in " + name + " (" + oid[:8] + ")")
        if any(part in name.split("/") for part in ("data", "accounts", ".env", "auth.json")):
            findings.append("History contains private runtime path " + name)
    return findings


def build(check_only=False, root=ROOT):
    root = Path(root).resolve()
    files = source_files(root)
    findings = audit(files, root) + history_audit(root)
    if findings:
        raise SystemExit("Release audit failed:\n" + "\n".join(findings))
    print(f"Release audit passed: {len(files)} source files; no detected credential patterns, private home paths, or personal emails. Runtime data is excluded by allowlist.")
    if check_only:
        return
    directory = root / "dist"
    directory.mkdir(exist_ok=True)
    target = directory / "runquay-0.2.0-source.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            archive.write(file, Path("runquay") / file.relative_to(root))
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (directory / (target.name + ".sha256")).write_text(digest + "  " + target.name + "\n", encoding="ascii")
    print("Created " + target.name + " · SHA256 " + digest)


if __name__ == "__main__":
    build()
