# Verification record

Current interface verification: 2026-10-09. The 50-test Python suite completed on Windows (49 passed, one POSIX-only skip) and Ubuntu under WSL (50 passed). Nine JavaScript UI regression tests cover navigation, next-step decisions, task filters and scoped ideas. Test commands and results are recorded separately from CI and account-dependent checks.

| Check | Status |
| --- | --- |
| Windows, Python 3.11 | Deterministic suite executed locally |
| Ubuntu 24.04 under WSL, Python 3.12 | Deterministic suite executed locally, including POSIX child-group cleanup |
| macOS | Deterministic suite executed in GitHub Actions; vendor account execution and launchctl installation not manually tested |
| GitHub Actions Windows / Ubuntu / macOS, Python 3.11 and 3.13 | Initial publication matrix passed: [run 37819086726](https://github.com/dibyapp/runquay/actions/runs/37819086726) |
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

## Illustrated workflow verification — 0.2.1

Actual Windows onboarding, current Codex subscription verification, a real word-counter build, resumed completion and import of its generated folder were exercised. Seven generated-project tests passed independently and the CLI printed the expected count of 7. The run exposed a relative-data-path defect; `Store` now resolves the data directory before constructing worker result paths. A regression check launches a worker in a different directory and verifies completion. The [screenshot record](SCREENSHOTS.md) documents the initial failure and recovery. Reviewed public captures are explicitly hash-pinned; unrelated private screenshots remain excluded.

After these changes, `python -m unittest discover -s tests -q` completed with 49 tests on Windows (one POSIX-only skip) and Ubuntu 24.04 under WSL (no skips). The release audit passed for 61 allowlisted files, including ten reviewed screenshots.

## Simpler interface verification — 0.3.0

The revised app was tested through the Codex in-app browser against the live local Windows supervisor. The check covered all five pages, setup acknowledgement and retained workspace, task-form advanced validation, waiting/start/progress/results, finished filtering, logs, folder import, scoped read-only suggestions and editable idea review. A real Codex task built a UTF-8 text-cleaner CLI; seven generated tests passed independently. A reviewed suggestion added a README clarification and reran the checks.

A temporary external-tool connection and task tested approval acknowledgement and decline without executing that vendor. The account was unlinked and the original work settings restored. Existing private projects were not used for model execution in this check. Real limit exhaustion and reset redemption were not exercised.

The HTTP regression verifies the new UI assets are served without model requests. JavaScript tests also verify a ready account for another provider cannot make waiting work look eligible. Expanded details are retained across background renders. The Windows stop/start smoke check verified an already-exited scheduled worker no longer causes a null-command-line error. Actual public captures and their provenance are in [SCREENSHOTS.md](SCREENSHOTS.md).

The cross-platform CI matrix runs the Python suite, JavaScript syntax checks, UI regression tests, source/history privacy audit and ZIP build on Windows, Ubuntu and macOS with Python 3.11/3.13. CI results are available from the [Verify workflow](https://github.com/dibyapp/runquay/actions/workflows/ci.yml). Desktop browser/model execution was tested on Windows; macOS/Linux vendor sign-in and startup behavior remain separate integration checks.
