"""Small, dependency-free operating system boundary for AutoWork."""
from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import sys


def data_home(system=None, home=None, env=None):
    system, home, env = system or sys.platform, Path(home or Path.home()), os.environ if env is None else env
    if system == "win32":
        return Path(env.get("LOCALAPPDATA", home / "AppData/Local")) / "AutoWork"
    if system == "darwin":
        return home / "Library/Application Support/AutoWork"
    return Path(env.get("XDG_DATA_HOME", home / ".local/share")) / "autowork"


def default_data(root):
    # Preserve installations created before the portable release.
    legacy = Path(root) / "data"
    return legacy if (legacy / "autowork.sqlite3").exists() else data_home()


def child_options():
    return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)} if os.name == "nt" else {"start_new_session": True}


def kill_group(proc):
    """Children are launched in their own POSIX session, including npm wrappers."""
    if os.name != "nt" and not getattr(proc, "_autowork_group_closed", False):
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc._autowork_group_closed = True


def private_directory(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        path.chmod(0o700)
    return path


def command_display(args, env=None):
    """Instructions only; the execution path never uses a shell."""
    import shlex
    if os.name == "nt":
        prefix = " ".join("$env:" + k + "='" + str(v).replace("'", "''") + "';" for k, v in (env or {}).items())
        return (prefix + " & " + " ".join("'" + str(a).replace("'", "''") + "'" for a in args)).strip()
    return " ".join([*(k + "=" + shlex.quote(str(v)) for k, v in (env or {}).items()), *(shlex.quote(str(a)) for a in args)])


class DataLock:
    """One supervisor per data directory, even on different HTTP ports."""
    def __init__(self, directory):
        self.handle = (Path(directory) / "supervisor.lock").open("a+b")
        try:
            if self.handle.seek(0, 2) == 0:
                self.handle.write(b"0"); self.handle.flush()
            self.handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.handle.close()
            raise RuntimeError("Another Runquay supervisor is using this data directory") from None

    def close(self):
        self.handle.close()
