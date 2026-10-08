# Verification record

Release preparation: 2026-10-08. The 46-test suite completed on Windows (45 passed, one POSIX-only skip) and Ubuntu (46 passed). Test commands and results are recorded separately from planned CI and account-dependent checks.

| Check | Status |
| --- | --- |
| Windows, Python 3.11 | Deterministic suite executed locally |
| Ubuntu 24.04 under WSL, Python 3.12 | Deterministic suite executed locally, including POSIX child-group cleanup |
| macOS | Data paths / LaunchAgent definition tested; runtime and launchctl installation not executed |
| GitHub Actions Windows / Ubuntu / macOS, Python 3.11 and 3.13 | Workflow prepared; not dispatched before publication |
| Codex model execution / native read-only advisor | Live tested on Windows with authenticated subscription and structured checkpoints |
| Claude Code | Installed 2.1.251 flags inspected; no approved model invocation executed |
| Gemini / Antigravity | Official CLI contracts inspected; output/command unit tests; no installed live vendor account check |
| Custom provider | Synthetic real subprocess dispatch, per-run approval, and checkpoint persistence tested |
| Onboarding | Browser validation on the local Windows dashboard; HTTP completion/import validation in tests |
| Release privacy | Allowlisted source/archive scan; excluded private state; clean extraction smoke check |

The suite covers subscription quota rejection, paid/unknown balances, reset approval/idempotency, interrupted recovery, pause, bounded retries, correct provider selection, dynamic account homes, structured vendor envelopes, malformed output, read-only advisor arguments, folder preservation, HTTP host/origin/session checks, source privacy exclusions, and Unix descendants.

No test claims to exhaust real accounts, consume real resets, prove vendor billing atomicity, verify every Linux distribution, or validate proprietary CLIs without a usable installed account. Run CI and manual vendor/OS smoke checks before upgrading an integration's support claim.

## Runquay branding verification — 2026-10-08

After the public rename, the suite passed again on Windows (45 passed, one POSIX-only skip) and Ubuntu 24.04 under WSL (46 passed). Both launcher help commands and JavaScript syntax checks passed. The rebuilt Runquay ZIP was extracted into a temporary folder, its suite passed, and fresh onboarding, static assets including the vector mark, custom account creation, one-invocation approval and synthetic worker completion were exercised successfully without model requests.

The live local service was restarted after confirming no active build or advisor run. Project, profile and task counts were preserved. Browser inspection confirmed the new title, onboarding name and compatibility descriptions. Private verification screenshots remain excluded from the source bundle. The allowlisted source/history pattern audit passed; it remains a detection check, not proof that arbitrary content cannot be sensitive.
