"""Portable launcher: python autowork.py [start|doctor|service|release]."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def doctor():
    from supervisor import Supervisor
    sup = Supervisor()
    try:
        print(json.dumps({"python": sys.version.split()[0], "platform": sys.platform,
                          "git": bool(shutil.which("git")), "tools": sup.tool_status(),
                          "billing": "Codex verified quota; others require one-run approval", "telemetry": False}, indent=2))
    finally:
        sup.children.close()


def main():
    parser = argparse.ArgumentParser(description="Runquay — local AI coding agent orchestrator")
    sub = parser.add_subparsers(dest="command")
    start = sub.add_parser("start", help="Open the guided setup and run the local dashboard")
    start.add_argument("--port", type=int, default=8765)
    start.add_argument("--data", type=Path)
    start.add_argument("--no-browser", action="store_true")
    sub.add_parser("doctor", help="Check tool availability without sending model requests")
    service = sub.add_parser("service", help="Install or remove per-user startup")
    service.add_argument("action", choices=["install", "uninstall", "preview"])
    service.add_argument("--system", choices=["linux", "darwin", "win32"])
    release = sub.add_parser("release", help="Audit and create a source-only ZIP")
    release.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.command == "doctor":
        doctor()
    elif args.command == "service":
        from service_setup import manage
        manage(args.action, args.system)
    elif args.command == "release":
        from release import build
        build(check_only=args.check)
    else:
        cmd = [sys.executable, str(ROOT / "supervisor.py")]
        if args.command == "start":
            cmd += ["--port", str(args.port)]
            if args.data:
                cmd += ["--data", str(args.data)]
            if not args.no_browser:
                cmd += ["--open"]
        else:
            cmd += ["--open"]
        raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
