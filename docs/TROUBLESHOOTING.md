# Runquay troubleshooting

Start with:

```sh
python runquay.py doctor
```

Use `python3` on macOS/Linux if needed. Doctor detects tools without sending model requests. It is not a live authentication or billing check for every adapter. If the dashboard opens, read the task note, account reason and recent activity before retrying.

## Installation and connection

| Symptom | Check and action |
| --- | --- |
| `python` or `py` is not recognized | Install Python 3.11+, enable PATH where applicable, reopen the terminal and verify the version. Try `python3` on macOS/Linux. |
| `git` is missing | Install Git, reopen the terminal and check `git --version`. New project creation needs Git. |
| Vendor CLI is not found | Use its official setup link in onboarding. Confirm it runs in the same user/session. If installed outside PATH, connect a profile with its executable path. |
| Browser does not open | Visit `http://127.0.0.1:8765/` manually. Keep the foreground terminal open and inspect private startup logs if no server responds. |
| Port is already used | Another instance may be running. Open its dashboard or stop that instance; do not delete its database. For a separate test instance use both a different port and a different data directory. |
| Dashboard rejects a request | Open its exact loopback URL and refresh to obtain the current session. Do not use an external host, tunnel, stale tab from a restarted server or cross-origin client. |
| Settings do not save | Check allowed ranges: quota 50–90%, milestone 2–120 minutes, advisor interval 1–72 hours. Read the displayed error. |

An isolated foreground test instance can be started with:

Windows PowerShell:

```powershell
py -3 runquay.py start --data "$env:LOCALAPPDATA\RunquayTest" --port 8766
```

macOS/Linux:

```sh
python3 runquay.py start --data "$HOME/.local/share/runquay-test" --port 8766
```

These are example private data locations, not a storage-name migration. Never point two live instances at the same data directory. The original application still uses its documented legacy AutoWork storage paths.

## Authentication and quota

| Symptom | Check and action |
| --- | --- |
| Codex says sign-in required | Open that profile's sign-in guide and run the generated command in your terminal. Finish official vendor authentication, then verify. Runquay requires subscription auth, not API-key auth. |
| Additional account appears to use the same login | Check whether **Use current login** was selected. Isolated profiles have their own vendor home where supported; use the generated command for that exact profile. Do not copy auth files. |
| Current login is already connected | Runquay prevents duplicate login homes. Create an isolated supported profile for another account instead. |
| Paid balance is positive or unknown | The Codex guard blocks work. Review vendor account/billing state. Waiting or resolving the account state is safer than repeatedly retrying an unknown balance. |
| Codex waits below the vendor's hard limit | The configured reserve intentionally stops earlier, up to 90% used. Check both quota windows and the account reason. |
| All Codex accounts are unavailable | Wait for natural refresh, resolve authentication, or connect another permitted account. No paid reset is purchased automatically. |
| Reset request is uncertain after restart | The original redemption may have succeeded. Review the decision and account state; retries use the original idempotency ID. Do not create repeated independent redemptions. |
| Claude/Gemini/Antigravity shows CLI found but is not ready | Detection does not verify billing or authentication. Review the account and authorize one invocation only if you accept the possible vendor charges. |

No provider account was live-tested merely because its name appears in the UI. See [TOOLS.md](TOOLS.md) for the exact integration scope.

## Projects, advisor and execution

| Symptom | Check and action |
| --- | --- |
| Existing project is missing | Use **Sync projects** for saved Codex roots, or **Connect folder** with an existing absolute directory. Discovery does not search the entire disk. |
| Queue has tasks but nothing runs | Check **Start queue**, task provider, eligible matching profiles, approvals, task note and whether another milestone is active. |
| Ask AI stays queued | Planning is a queued task. Start the supervisor, ensure a supported planning profile is available and review any required invocation approval. |
| Suggestions are empty | Run the advisor first, check its status/error and remove restrictive suggestion filters. Suggestions are not generated merely by opening the page. |
| Antigravity/custom is absent from planning | Their read-only advisor policy is unverified, so those advisors are disabled. Choose a supported planning tool. |
| AI tool requests trust or tool permission | Review the vendor's project trust/sandbox configuration and grant only permissions you intend. Runquay does not turn on permission bypass to fix this. |
| Gemini sandbox fails | Check the sandbox runtime required by the vendor on your OS. Contract tests do not prove a particular sandbox installation works. |
| Task reaches Attention | Read the note and inspect files. Resolve the blocker, answer with **Resume / add guidance**, and raise the cap above completed milestones when appropriate. |
| Timeout or restart interrupted a task | Files may already have changed. Check the checkpoint and diff before resuming; interruption is not an automatic rollback. |
| Custom wrapper produces invalid output | Emit exactly one checkpoint JSON object on stdout, with diagnostic output on stderr. Test against the documented schema. |
| Finished app stops responding | Worker-launched dev servers stop with the milestone. Launch the finished app separately using its own instructions. |
| Generated result fails your checks | Preserve the evidence, describe the failed command and required behavior, then resume with guidance. An agent's Complete status is not a substitute for review. |

## Startup and shutdown

Use `python runquay.py service preview` before enabling startup. Windows startup requires the Python installation's `pythonw.exe` and a usable Task Scheduler user session. macOS uses a user LaunchAgent; Linux startup needs a working user systemd manager or a separately configured user process manager.

If startup stops working after moving the checkout or changing Python, reinstall it from the final location. Do not leave multiple services targeting the same database. See [OPERATIONS.md](OPERATIONS.md) for service identifiers and stop commands.

Keep-awake is best effort. Test your actual sleep/lid/network policies; a local queue cannot survive shutdown as an active process. On standalone Unix runs, a hard-killed supervisor can leave child groups; prefer the documented user service for continuous operation.

## Report a reproducible bug

Open a [bug report](https://github.com/dibyapp/runquay/issues/new/choose) with OS, Python version, vendor CLI/version, steps, expected behavior, actual behavior and a small non-sensitive reproducer. Include sanitized relevant output rather than the full data directory.

Do not upload account snapshots, authentication files, databases, personal project screenshots or complete private logs. Credential-shaped text can be redacted automatically, but proprietary filenames, prompts and business data need manual review. Use [private vulnerability reporting](https://github.com/dibyapp/runquay/security/advisories/new) for security vulnerabilities.
