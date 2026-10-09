# Verification record

Current interface verification: 2026-10-09, version 0.5.0. The 70-test Python suite completed on Windows (68 passed, two platform/permission skips) and Ubuntu 24.04 under WSL (70 passed). Eighteen JavaScript UI tests cover the prior workflow and recommendations for verified accounts, installed tools and a fresh computer. Test commands and results are recorded separately from CI and account-dependent checks.

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


## Beginner workflow verification — 0.4.0

The live Windows app was tested in the Codex in-app browser: required idea validation, editable starter, retained fields after Back, optional name, review, saving while paused, starting work and a real one-step Codex completion. The fictional Sunny Corner cafe produced a self-contained menu, START_HERE.md and a check script. Independent execution of the script passed. A local HTTP preview confirmed Drinks shows two items, Snacks shows one, and All restores three, including keyboard activation. The result dialog showed the actual opening instructions as text; Open project folder returned success. Ask for help opened an editable follow-up and was closed without submitting another model request. Original accounts and settings were retained.

The worker's headless screenshot attempt was denied by Windows. The later interactive browser check used the actual generated page over local HTTP. The in-app browser rejected a direct file:// URL; this restriction was not bypassed, and direct double-click opening remains unverified. Native macOS launcher interaction, sign-in clipboard interaction, other-vendor model requests and paid resets were not exercised. The three new public images are actual reviewed captures, not mockups.

Regression checks cover authenticated delivery access, CSRF protection for folder opening, ignoring caller-supplied paths, bounded text reads, credential-name exclusion, symlink containment, plain-text rendering and OS-specific folder-opening commands. The source ZIP is checked for an exact allowlist and executable Unix launcher permissions. Python/Git and an authenticated AI helper remain prerequisites; Runquay is not a bundled one-click AI installation.

## Simpler account setup verification — 0.4.1

In the separate paused Windows walkthrough, the real Codex account was detected and verified. Its setup step showed Codex is ready and Next without an account form. The account dialog displayed only installed-tool buttons, the connection message, the main action and collapsed More options. Names and the full provider selector were confirmed hidden until requested. Done closed an existing connection without adding a duplicate. Selecting the installed Claude tool and Connect created a named connection without typed fields; approval remained required and no vendor run was authorized. Sign in to another account created an isolated Codex profile and opened its sign-in guide without starting authentication. Both temporary connections were removed, retaining vendor credentials. Antigravity was disabled when absent, with separate login unavailable; custom setup remained accessible. There were no browser console errors, model requests, purchases or resets. The walkthrough remained paused and not onboarded, ready for the user's next step.


## Codex browser sign-in verification — 0.4.2

The actual Windows dashboard was tested in the Codex in-app browser. A temporary isolated connection launched the installed official Codex CLI with forced ChatGPT authentication and the vendor keyring. The local OAuth callback listener started; the UI displayed waiting progress and Cancel sign-in. Cancellation stopped the login and restored the retry action. The temporary connection was unlinked, preserving vendor credential storage, both user profiles, onboarding state and the paused queue. The fallback remains collapsed in the reviewed public screenshot.

Lifecycle tests simulate successful login and automatic refresh, cancellation, executable failure, rejection of concurrent logins, rejection of unlink during login, and protection of the shared app login. HTTP tests require the local cookie and CSRF token before login/cancel callbacks can run. The UI test scopes status to its own profile. JavaScript syntax, both local Python suites and the 16 UI checks passed.

No live OAuth consent or successful sign-in completion was performed by the agent. macOS/Linux browser sign-in and keyring behavior need their own desktop integration checks; the cross-platform deterministic CI matrix does not establish those. No model requests, paid credit purchases or reset actions were made in this check. See the [actual capture](SCREENSHOTS.md).


## Automatic setup verification — 0.5.0

The real Windows walkthrough in the Codex in-app browser detected Windows/Python/Git, recommended the verified Codex account, and displayed Node.js and Gemini CLI as the missing software after selecting Gemini. Install missing tools downloaded the official Node.js 22 archive and verified its checksum, installed the fixed official Gemini package in the private user prefix, and checked its version. An independent version-only invocation returned 0 and Gemini CLI 0.63.0. The UI reported Tools are ready and enabled Next.

Next created a connection without a name or path; the wizard progressed to the suggested project-folder step. The temporary Gemini profile was unlinked. Both user Codex profiles, paused work, zero model runs and unfinished onboarding were preserved. The installed Node/Gemini software remains available. No sign-in, model execution, paid credit purchase or reset occurred.

Deterministic setup tests cover Windows/macOS/Linux fixed Git package recipes, OS permission boundaries, unsupported CPU/platform handling, checksum failure, archive traversal and special-file rejection, fixed npm package/registry/user prefix, setup concurrency, error recovery, native Codex reuse without Node, and local-session/CSRF protection. Work and login are blocked during setup. First-launch detection ran on Windows and Ubuntu without installation; CI repeats the detection check on all three OS families.

Live Windows Python/Git installation was not executed because those were already present. Native macOS/Homebrew installation, Linux privileged package installation, provider sign-in and other vendor installation remain separate desktop integration checks. The setup guide describes restricted systems, older Python distributions and unsupported package managers honestly.
