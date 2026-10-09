#!/bin/sh
# Interactive first-launch bootstrap. No provider login or paid operation.
set -eu
cd "$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
setup_os=$(uname -s)
case "$setup_os" in Darwin) printf '%s\n' 'Runquay setup: macOS detected.';; Linux) printf '%s\n' 'Runquay setup: Linux detected.';; *) printf '%s\n' 'This OS needs manual Python/Git setup. See docs/SETUP.md.'; exit 2;; esac
setup_python=''
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 2)' 2>/dev/null; then setup_python="$candidate"; break; fi
done
setup_git=false
if command -v git >/dev/null 2>&1 && git --version >/dev/null 2>&1; then setup_git=true; fi
if [ "${1:-}" = '--check' ]; then printf 'Python 3.11+: %s; Git: %s\n' "${setup_python:-missing}" "$setup_git"; exit 0; fi
if [ -z "$setup_python" ] || [ "$setup_git" = false ]; then
  printf '%s\n' 'Installing missing Python/Git only. Finish any OS permission prompts in this terminal.'
  if [ "$setup_os" = Darwin ]; then
    PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"; export PATH
    if ! command -v brew >/dev/null 2>&1; then
      printf '%s\n' 'Homebrew is needed for missing essentials. Starting its official installer; review and finish its prompts here.'
      setup_brew_installer=$(mktemp)
      trap 'rm -f "$setup_brew_installer"' EXIT HUP INT TERM
      curl --proto '=https' --tlsv1.2 -fsSL 'https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh' -o "$setup_brew_installer"
      /bin/bash "$setup_brew_installer"
      if ! command -v brew >/dev/null 2>&1; then printf '%s\n' 'Homebrew did not finish. Read its message above, then reopen setup.command.'; exit 2; fi
    fi
    export HOMEBREW_NO_ANALYTICS=1 HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1
    if [ -z "$setup_python" ]; then brew install python@3.13; fi
    if [ "$setup_git" = false ]; then brew install git; fi
  elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    if [ -z "$setup_python" ]; then sudo apt-get install -y python3; fi
    if [ "$setup_git" = false ]; then sudo apt-get install -y git; fi
  elif command -v dnf >/dev/null 2>&1; then
    if [ -z "$setup_python" ]; then sudo dnf install -y python3; fi
    if [ "$setup_git" = false ]; then sudo dnf install -y git; fi
  elif command -v pacman >/dev/null 2>&1; then
    if [ -z "$setup_python" ]; then sudo pacman -S --needed python; fi
    if [ "$setup_git" = false ]; then sudo pacman -S --needed git; fi
  elif command -v zypper >/dev/null 2>&1; then
    if [ -z "$setup_python" ]; then sudo zypper install python313; fi
    if [ "$setup_git" = false ]; then sudo zypper install git; fi
  else
    printf '%s\n' 'No supported package manager found. Install Python 3.11+ and Git using docs/SETUP.md, then reopen this file.'; exit 2
  fi
fi
setup_python=''
for candidate in python3.13 python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 2)' 2>/dev/null; then setup_python="$candidate"; break; fi
done
if [ -z "$setup_python" ]; then printf '%s\n' 'Your distribution has an older Python. Install Python 3.11+ from https://www.python.org/downloads/ and reopen this file.'; exit 2; fi
printf '%s\n' 'Essentials are ready. Opening the guided dashboard. Keep this window open while Runquay runs.'
exec "$setup_python" runquay.py start
