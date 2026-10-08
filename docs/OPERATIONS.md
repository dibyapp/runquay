# Local operations

## Storage

Fresh installations use per-user storage: `%LOCALAPPDATA%/AutoWork` on Windows, `~/Library/Application Support/AutoWork` on macOS, and `$XDG_DATA_HOME/autowork` or `~/.local/share/autowork` on Linux. Older installations with `data/autowork.sqlite3` beside the source keep using that location. Additive migrations preserve accounts, work, proposals, decisions, and history.

Use `python autowork.py start --data <absolute-private-folder>` to choose a different location. The SQLite database, accounts, advisor scratch directories, run logs, and PID file live there. New workspaces default to a `workspaces` subfolder and can be changed in onboarding. Existing tasks retain their original paths.

Runtime data is excluded from Git and source releases. Do not use a shared/synced folder for credentials or sensitive projects. Stop the queue/server before backing up SQLite and never publish that backup.

## Startup and stop

`python autowork.py start` is a foreground server; Ctrl+C stops it. `python autowork.py service install` opts into sign-in startup. Preview service definitions first. Service managers can require an active user session and OS policies may block installation.

- Windows: included PowerShell scripts use limited Task Scheduler credentials, restart on failure, and a hidden worker. `Stop-AutoWork.ps1` stops the legacy/default installation. For a custom data/port foreground instance, use Ctrl+C in its terminal.
- Linux: `systemctl --user status autowork` / `systemctl --user stop autowork`. Uses `KillMode=control-group` and `UMask=0077`. User systemd must be available; other distros use their process manager.
- macOS: `launchctl print gui/$(id -u)/local.autowork.supervisor` shows its state. Uninstall startup to stop/unload it; keep the checkout at its installed absolute path.

Autostart currently uses default port/data resolution. Custom port/data servers should be configured explicitly in a reviewed user-service definition. Two instances must never share one data directory. A second listener on the same port is rejected before recovery can alter live work.

## Troubleshooting

Use `python autowork.py doctor` for no-model-request tool detection. In Accounts, open the generated sign-in guide, finish vendor login in your terminal, and verify the connection. Codex quota failures block scheduling. Other tools need one-run approval and may block on vendor trust/sandbox/permission requirements.

Private rotated supervisor logs and per-run output live in the data directory. Redact manually before sharing; not all confidential information has a recognizable pattern. An interrupted milestone requests review instead of assuming it did no work. Inspect the project and checkpoint, then Resume.

Limits are local polling observations. Runquay cannot prevent provider-side account changes or enforce an atomic billing cutoff. Device keep-awake is best effort and does not promise 24-hour availability through shutdown or updates.

Runquay retains the legacy AutoWork storage and service identifiers listed above. Existing installations require no data migration for the public rename. Both `runquay.py` and `autowork.py` launch the same supervisor.
