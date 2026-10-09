"""Portable launcher: python autowork.py [start|doctor|service|release]."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def startup_problems():
    problems = []
    if sys.version_info < (3, 11):
        problems.append("Install Python 3.11 or newer from https://www.python.org/downloads/ and reopen Runquay.")
    if not shutil.which("git"):
        problems.append("Install Git from https://git-scm.com/downloads, then reopen Runquay. It keeps each new project's work separate.")
    return problems


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
    setup = sub.add_parser('setup', help='Detect this OS and install missing tools for the chosen AI')
    setup.add_argument('--provider', choices=['codex','claude','gemini','antigravity'], default='codex')
    setup.add_argument('--install', action='store_true', help='Install the displayed missing tools; OS permission prompts appear here')
    service = sub.add_parser("service", help="Install or remove per-user startup")
    service.add_argument("action", choices=["install", "uninstall", "preview"])
    service.add_argument("--system", choices=["linux", "darwin", "win32"])
    release = sub.add_parser("release", help="Audit and create a source-only ZIP")
    release.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.command == 'setup':
        from install_setup import cli
        cli(args.provider, args.install)
    elif args.command == "doctor":
        doctor()
    elif args.command == "service":
        from service_setup import manage
        manage(args.action, args.system)
    elif args.command == "release":
        from release import build
        build(check_only=args.check)
    else:
        problems = startup_problems()
        if problems:
            print("Runquay needs a little setup before it can open:\n\n" + "\n\n".join(problems))
            print("\nSee docs/BEGINNERS.md in the downloaded folder for the step-by-step guide.")
            raise SystemExit(2)
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
