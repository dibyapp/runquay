#!/bin/sh
cd "$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)" || exit 1
sh ./setup.sh "$@"
result=$?
if [ "$result" -ne 0 ]; then printf '%s' 'Read the setup message above. Press Return to close: '; read -r answer; fi
exit "$result"
