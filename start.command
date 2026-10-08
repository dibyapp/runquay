#!/bin/sh
cd "$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)" || exit 1
if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
  printf '%s\n' 'Install Python 3.11 or newer from https://www.python.org/downloads/macos/' 'Then reopen this file. See docs/BEGINNERS.md for the setup guide.'
  printf '%s' 'Press Return to close: '
  read -r answer
  exit 2
fi
sh ./start.sh "$@"
result=$?
if [ "$result" -ne 0 ]; then
  printf '%s\n' 'Runquay could not start. Read the message above and docs/BEGINNERS.md.'
  printf '%s' 'Press Return to close: '
  read -r answer
fi
exit "$result"
