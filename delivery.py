"""Read-only handoff summaries. Never execute generated project files."""
from pathlib import Path
from security import redact


def result_details(project):
    root = Path(project["path"]).resolve()
    if not root.is_dir():
        raise ValueError("This project's folder is no longer available on this computer.")
    instructions = ""
    source = ""
    for name in ("START_HERE.md", "README.md", "README.txt"):
        file = root / name
        # A project handoff must not read through a symlink to a private file.
        if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(root):
            continue
        with file.open("rb") as stream:
            raw = stream.read(16001)
        instructions = redact(raw[:16000].decode("utf-8", errors="replace"))
        if len(raw) > 16000:
            instructions += "\n\nMore instructions are in the project folder."
        source = name
        break
    files = sorted(p.name for p in root.iterdir() if p.is_file() and not p.is_symlink()
                   and not p.name.startswith(".") and not any(word in p.name.lower()
                   for word in ("credential", "secret", "token", "auth")))[:30]
    return {"name": project["name"], "instructions": instructions, "source": source,
            "files": files, "has_webpage": (root / "index.html").is_file() and not (root / "index.html").is_symlink()}
