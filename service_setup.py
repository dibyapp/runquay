"""Opt-in per-user startup; never changes system-wide privileges."""
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def definition(system=None, home=None, executable=None, root=None):
    system, home = system or sys.platform, Path(home or Path.home())
    executable, root = executable or sys.executable, Path(root or ROOT)
    if system == "darwin":
        path = home / "Library/LaunchAgents/local.autowork.supervisor.plist"
        payload = {"Label": "local.autowork.supervisor", "ProgramArguments": [executable, str(root / "supervisor.py")],
                   "WorkingDirectory": str(root), "RunAtLoad": True, "KeepAlive": True, "ThrottleInterval": 15,
                   "Umask": 0o077}
        return path, plistlib.dumps(payload)
    if system == "linux":
        # systemd specifiers and control characters are never taken as literal paths.
        def unit_quote(value):
            value = str(value)
            if any(c in value for c in "\r\n\x00"):
                raise ValueError("Unsupported control character in service path")
            return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%').replace('$', '$$') + '"'
        path = home / ".config/systemd/user/autowork.service"
        text = "[Unit]\nDescription=Runquay local AI coding queue\nAfter=network.target\n\n[Service]\nType=simple\n"
        text += "ExecStart=" + unit_quote(executable) + " " + unit_quote(root / "supervisor.py") + "\n"
        text += "WorkingDirectory=" + unit_quote(root) + "\nRestart=on-failure\nRestartSec=15\nKillMode=control-group\nUMask=0077\n\n[Install]\nWantedBy=default.target\n"
        return path, text.encode()
    if system == "win32":
        return root / "Install-Autostart.ps1", b"Use the included per-user Windows Task Scheduler script."
    raise ValueError("Automatic startup supports Windows, macOS, and systemd Linux. On other Unix systems run the foreground launcher with your user service manager.")


def manage(action, system=None):
    system = system or sys.platform
    if system != sys.platform and action != "preview":
        raise ValueError("A different OS can only be previewed")
    path, content = definition(system)
    if action == "preview":
        print(content.decode())
        return
    if system == "win32":
        script = ROOT / ("Install-Autostart.ps1" if action == "install" else "Uninstall-Autostart.ps1")
        subprocess.run(["powershell.exe", "-NoProfile", "-File", str(script)], check=True)
        print("Startup updated. Start Runquay using the launcher or sign in again.")
        return
    if system == "linux":
        if action == "install":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "--user", "enable", "--now", "autowork.service"], check=True)
        else:
            subprocess.run(["systemctl", "--user", "disable", "--now", "autowork.service"], check=True)
            path.unlink(missing_ok=True)
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    elif system == "darwin":
        target = f"gui/{os.getuid()}"
        if action == "install":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            subprocess.run(["launchctl", "bootstrap", target, str(path)], check=True)
        else:
            subprocess.run(["launchctl", "bootout", target + "/local.autowork.supervisor"], check=True)
            path.unlink(missing_ok=True)
    print("Per-user startup " + ("installed" if action == "install" else "removed") + ".")
