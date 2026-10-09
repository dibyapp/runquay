"""Allowlisted source packaging. Never archives a working directory wholesale."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile
import tomllib
from security import PATTERNS

ROOT = Path(__file__).resolve().parent
IGNORED = {"__pycache__", "node_modules", ".git", "data", "projects", "accounts", ".venv"}
EXTENSIONS = {".py", ".md", ".json", ".js", ".css", ".html", ".yml", ".yaml", ".toml", ".sh", ".cmd", ".ps1", ".svg"}


def public_images(root=ROOT):
    manifest_path = Path(root) / "release-manifest.json"
    images = json.loads(manifest_path.read_text(encoding="utf-8")).get("public_images", {}) if manifest_path.exists() else {}
    for name, digests in images.items():
        if not name.startswith("docs/images/") or ".." in Path(name).parts or Path(name).suffix != ".jpg":
            raise ValueError("Public images must be explicitly reviewed JPEGs under docs/images")
        if not isinstance(digests, list) or not digests or any(not re.fullmatch(r"[0-9a-f]{64}", digest) for digest in digests):
            raise ValueError("Every public image needs its reviewed SHA256 digest")
    return images


def image_findings(name, raw, images):
    if name not in images or hashlib.sha256(raw).hexdigest() not in images[name]:
        return [name + ": image is not pinned to reviewed public content"]
    if len(raw) > 5_000_000 or not raw.startswith(b"\xff\xd8\xff") or not raw.endswith(b"\xff\xd9"):
        return [name + ": unsupported or oversized public image"]
    if b"Exif\x00\x00" in raw or b"http://ns.adobe.com/xap/" in raw:
        return [name + ": image contains unreviewed EXIF/XMP metadata"]
    return []


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
    candidates += [root / name for name in public_images(root)]
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
    images = public_images(root)
    home = str(Path.home())
    private_paths = {home, home.replace("\\", "/"), home.replace("\\", "\\\\")}
    for file in files:
        name = file.relative_to(root).as_posix()
        if file.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            findings.extend(image_findings(name, file.read_bytes(), images))
            continue
        text = file.read_text(encoding="utf-8")
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
    images = public_images(root)
    for row in probe.stdout.splitlines():
        oid, _, name = row.partition(" ")
        if not name:
            continue
        kind = subprocess.run(["git", "cat-file", "-t", oid], cwd=root, capture_output=True, text=True)
        if kind.stdout.strip() != "blob":
            continue
        raw = subprocess.run(["git", "cat-file", "blob", oid], cwd=root, capture_output=True).stdout
        if Path(name).suffix.lower() in {".jpg", ".jpeg", ".png"}:
            findings.extend(image_findings(name, raw, images))
            continue
        value = raw.decode("utf-8", errors="replace")
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
    print(f"Release audit passed: {len(files)} files; text scanned for credentials, private home paths and personal emails. Public images are pinned to reviewed hashes; runtime data is excluded by allowlist.")
    if check_only:
        return
    directory = root / "dist"
    directory.mkdir(exist_ok=True)
    version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("Release version must be numeric major.minor.patch")
    target = directory / f"runquay-{version}-source.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            name = Path("runquay") / file.relative_to(root)
            if file.name in {"start.command", "start.sh", "setup.command", "setup.sh"}:
                info = zipfile.ZipInfo.from_file(file, name.as_posix())
                info.create_system = 3
                info.external_attr = 0o100755 << 16
                archive.writestr(info, file.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
            else:
                archive.write(file, name)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (directory / (target.name + ".sha256")).write_text(digest + "  " + target.name + "\n", encoding="ascii")
    print("Created " + target.name + " · SHA256 " + digest)


if __name__ == "__main__":
    build()
