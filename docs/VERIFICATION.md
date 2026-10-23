# Verification record

## Recoverable requests and work library — 0.12.0

On Windows, 142 Python tests ran (139 passed, three environment-dependent skips), and 37 JavaScript unit checks passed. The pure library checks cover lifecycle, provider and project filters, unlinked and background chats, full-text matching, pinned views, sorting and no mutation of source state.

The local Chromium suite used fictional data and a deterministic worker with no vendor model calls. It exercised draft recovery after reload with the target folder and AI choice, explicit discard, Ctrl/⌘ Enter submission, library filters, pinning, request reuse, the existing account and approval flows, and five responsive widths. The suite used locally installed Chrome because the bundled Playwright browser version was unavailable; CI uses its own installed Chromium. Native vendor execution and cross-platform UI interaction were not repeated in this release.

Browser session storage holds unsent draft text in the current tab; local storage holds pin identifiers. Neither is included in release archives. Browser storage can be disabled or cleared by the user, so draft recovery is best effort. Clipboard copying requires a supported browser and a user action.

## Native conversation continuity — 0.11.3

On Windows, 142 Python tests ran (139 passed, three environment-dependent skips), and 35 JavaScript checks passed. New subprocess checks cover native session ID parsing, same-profile resume, account and phase boundaries, sandbox flags, approval preservation and exclusion of private IDs from the general browser state. A real Codex subscription check passed its zero-paid-credit quota gate, completed a disposable build, and then completed two read-only turns with the same native session ID. No paid credits or reset were authorized.

The local Chromium suite passed its complete fictional-data walkthrough: setup, account controls, task creation and follow-up, review handoffs, approval gates, learnings, pause/resume, and responsive pages. It does not invoke a vendor model. The installed Claude CLI advertises session persistence and `--resume`; simulated output and multi-profile tests passed, but a live Claude run awaits explicit acceptance of possible vendor charges. Gemini, Antigravity and custom adapters continue through portable file/checkpoint handoffs; native conversation resume for those tools is not claimed. No macOS/Linux machine or multiple real Claude logins was available in this local run. CI performs cross-OS checks after publication; these are not a substitute for live vendor execution on every OS.

## Claude account handoff — 0.11.2

On Windows, 139 Python tests passed with three environment-dependent skips. A simulated Claude CLI response exercised a usage-limit failure, durable one-hour cooldown, selection of a second connected profile and the separate approval required before that profile could launch. Error-classification cases covered an explicit limit, stderr 429, ordinary response text and an unrelated permission failure. JavaScript syntax validation passed. The local browser smoke suite could not run because Playwright is absent from this checkout; CI runs it separately. No live Claude account or billable request was used, and credential isolation across two real logins was not verified. An unrecognized CLI error follows the normal failure path.

## Installers — 0.11.1

Windows PowerShell 5.1 downloaded the existing public source ZIP, checked its SHA256 file and inspected and extracted its entries in verify-only mode without installing or launching AI work. The Unix installer was checked under Ubuntu/WSL with a locally generated audited tarball: it verified SHA256, installed into an isolated temporary user folder, reached guided setup with stub Python/Git commands, and reopened through its launcher. Real vendor invocations and paid usage were not part of these checks. Native macOS opening and real Python/Git package installation remain unverified; CI builds source packages on Windows, macOS and Linux and checks shell syntax on macOS and Linux.

## Auto team — 0.11.0

Windows checks cover 136 Python tests (133 passed, three POSIX-only skips) and 35 JavaScript tests. New subprocess tests exercise plan/build/review transitions, persisted handoffs after reopening storage, a bounded repair loop, external approval identity, stale-selection rejection, adapter permissions and clearing model overrides between providers.

The Chromium suite exercises the real local HTTP handler and deterministic subprocesses using fictional projects. It checks the visible team, a completed build waiting for a second-tool approval, approved review, saved handoffs after reload, original tool identity on earlier runs, follow-up work, declined review, label clipping and overlap at five widths, and reduced-motion behavior. The broader onboarding, accounts, settings, tasks and learnings walkthrough remains part of the same suite.

These are integration fixtures, not new live Codex/Claude/Gemini model calls. The previous real Codex checklist verification is recorded below; a live multi-provider run is not claimed. In-app automation remains unavailable, so local Chromium is used. Verification captures stay private; existing published screenshots are unchanged.

## UI and execution checks — 0.10.1

Windows verification on 2026-10-18 covers 130 Python tests (127 passed, three POSIX-only skips) and 34 JavaScript tests. Credential-storage regressions check keyring/file/auto/ephemeral modes, invalid configuration, subscription-only authentication, retained worker isolation, and no authentication-file reads by Runquay.

A real Codex build, submitted through the composer in a private isolated workspace, produced an offline checklist. Independent Chromium checks passed task creation, completion, All/Active/Done filters, deletion, persistence after reload, HTML-looking text, whitespace rejection, invalid-storage recovery and four responsive widths. The run completed through the normal worker after the credential-store fix. An earlier attempt failed when the metadata process ran out of memory; Runquay stopped rather than bypassing its quota monitor. No reset or paid-credit approval was used.

A Claude temperature-converter request was prepared through the same composer. The live invocation remains gated by one-run billing approval; a successful Claude build is **not claimed**. Authentication detection alone does not verify vendor billing. Real vendor sign-in changes, installations, paid/reset redemption, OS-native dialogs and native vendor execution on macOS/Linux were not repeated in this walkthrough.

The reproducible browser suite uses fictional history, real HTTP endpoints and a deterministic subprocess. It exercises all main pages at 320/390/768/1024/1440 widths, project search and keyboard selection, focus return, command navigation, motion controls, setup acknowledgement, settings persistence, account rename/enable/disable/remove, history import, saved previews, learnings review/exclusion/edit/keep/hide/reuse, failed-submit recovery, progress/results/follow-up, task pause/resume/cancel, global queue controls, advisor suggestions and one-run approval handling. Deliberately rejected requests produce expected 400/503 console responses. These checks do not prove every browser, provider or possible state is correct.

Run the browser suite with Node.js, Playwright and its Chromium browser installed: `python tests/browser_smoke.py`. Playwright is a development-only dependency; it is not needed to run Runquay. The fixture never launches vendor tools or imports real project histories. Captures and runtime data stay temporary. The in-app automation connection failed to initialize, so local Chromium was used. No new public screenshots were added in this release.


## Runquay Field — 0.10.0

Verified on Windows on 2026-10-17: 127 Python tests (124 passed, three POSIX skips) and 34 JavaScript tests. New request tests reject invalid/unkept lesson attachments before creating work, exclude source history from the fixed task context, and preserve retry identity after a lesson is hidden. Command-search tests use real titles and route data and exclude hidden lessons and raw logs.

The Chromium walkthrough used the real HTTP handler, fictional metadata and a deterministic worker subprocess. It exercised topic hit targets, animation pause, system reduced motion, canvas shutdown off-page, exact source review and exclusion, analysis-to-library-to-insight, escaped provider text, lesson-to-composer attachment, task-to-result, native previews, keyboard navigation, global vendor approval/decline and all five pages at 320/390/768/1024/1440 widths. No browser errors or content-security violations were observed. The UI keeps the strict same-origin policy; no inline-style exception was added.

The actual running installation was checked without submitting work or exporting personal screenshots. Connected accounts, the global queue setting and already-authorized waiting work were preserved during the idle upgrade. Three new public JPEGs use only fictional history and were reviewed visually, inspected for metadata and hash-pinned. Other verification captures stay excluded.

No new live vendor model calls, paid credits or resets were used. Topic geometry is a visual index of keyword matches, not a learned relationship graph. Full native chats are not fetched or resumed. Local Chromium was used because the in-app automation connection remains unavailable. CI covers Windows, macOS and Ubuntu with Python 3.11/3.13; this does not establish a manual native-vendor walkthrough on every OS.


## Everyday workspace — 0.9.0

Verified on Windows on 2026-10-17: 125 Python tests (122 passed, three POSIX
skips) and 33 JavaScript tests. New checks cover concurrent request retries,
idempotent schema upgrades, explicit provider selection, missing accounts,
selected folders, scoped work across multiple milestones, paused global queues,
installation blocking, per-run approval and HTTP pause disarming scoped work.
Task pause expires outstanding vendor approvals; approving a paused request is
rejected. Existing quota, paid-credit, permission and reset tests remain in place.

A Chromium walkthrough exercised the actual HTTP handler, UI and worker with
fictional projects and a deterministic subprocess. It covered a single composer,
safe new-folder default, saved-chat preview and folder selection, automatic
request execution, unrelated work staying paused, opening instructions, follow-up,
single-task start, visible vendor approval, pause, search, empty-account guidance,
inline errors retaining input, legacy Home navigation, and layouts from 320 to
1440 pixels. No browser errors or horizontal page overflow were observed. Test
captures were visually reviewed and stay private; no new public screenshots were
added. In-app browser automation remains unavailable, so this used local Chromium.

This release did not make new live vendor model calls. Native chat previews are
still bounded local metadata, not full conversations or live two-way sessions.
Desktop/macOS/Linux behavior beyond the CI matrix and previously recorded vendor
checks is not asserted. One unfinished work task per folder remains a limit.
The local upgrade preserves connected accounts and the global queue setting.
These checks do not establish that arbitrary AI-generated work is correct or safe.



## Automatic Collective Learnings experience — 0.8.0

Verified on Windows on 2026-10-17. The Python suite ran 114 tests (111 passed,
three POSIX-only skips), and 32 JavaScript checks passed. New checks cover
automatic relevance matching across tools, open-ended topics, bounded context
selection, duplicate active-request reuse, scoped execution while builds remain
paused, global pause disarming an analysis, and scoped continuation.

An automated Chromium walkthrough verified the actual HTTP handler and UI with
20 fictional product reports: automatic topic/tool/source selection, no model
calls on page opening, no unrelated fallback on empty matches, human-readable
context review, inline source exclusion, one explicit Analyze action, automatic
results, direct keep-and-attach reuse, editing/hiding/filtering, retained optional
controls, and desktop/mobile layouts. HTML in evidence remained escaped. These
browser results use deterministic reports, not real product outcomes. The
in-app browser automation connection remains unavailable; the check used local
Chromium. Verification captures stay private and are not release screenshots.

A real Codex analysis of three fictional reports exercised automatic source
selection and the actual worker while the general build queue stayed paused.
It returned two proposed lessons with valid citations, both in review state.
The account passed the existing quota/zero-paid-credit checks. No private
project history was sent and no credits or resets were requested. Live model
checks for Claude/Gemini remain unperformed. Local keyword matching and topic
counts are not semantic understanding or verified AI conclusions.


## Collective Learnings — 0.7.0

Verified on Windows on 2026-10-17. The Python suite ran 110 tests (107 passed,
three POSIX-only skips); 32 JavaScript checks passed. New tests cover mixed-tool
sources, best-effort minimization, exact source-review acknowledgement, changed
context rejection, idempotent queue requests, bounded input, valid citations,
atomic result validation, review/edit/dismiss, approved-only task reuse,
read-only worker dispatch, and HTTP session/CSRF enforcement.

An automated Chromium walkthrough used the real HTTP handler and UI with 20
fictional product reports from Claude, Gemini, Antigravity and an imported tool.
It checked selection, source preview, explicit consent, collection results,
HTML escaping, editing, approval, reuse in a new task, library filters, and
1440-pixel desktop / 390-pixel mobile layouts. These browser results use a
deterministic fixture rather than live vendor responses. The in-app browser
control connection was unavailable for this check; no in-app-browser result is
claimed. Private captures are excluded from publication.

A separate real Codex analysis on Windows used three explicitly fictional SEO
reports and an eligible account that passed the existing zero-paid-credit and
quota checks. It completed with two proposed lessons, valid citations and review
status. No real private project/chat history was sent, and no credits or resets
were requested. Claude/Gemini analysis commands are contract-tested in read-only
mode; their live model execution was not tested. Antigravity/custom histories
can contribute sources, but their analysis adapters remain disabled.

Native source material remains bounded titles/previews, not complete native
transcripts. A saved lesson is user-reviewed advice, not an independently
verified fact. Cross-platform results are available in the [Verify workflow](https://github.com/dibyapp/runquay/actions/workflows/ci.yml).


## Task conversation verification — 0.6.3

On 2026-10-14, the Windows Python suite completed with 99 tests (96 passed, three POSIX-only skips), and all 31 JavaScript UI checks passed. New regressions cover ordered Codex messages, deduplicated command events, file changes, failures, Claude tool results, structured Claude/Gemini reports, wrapped pretty JSON, partial log tails, safe Markdown and reasoning omission from both messages and technical details.

The actual Windows app was checked in the Codex in-app browser against existing real task logs, including a completed cafe build and a step awaiting clarification. Provider marks, account nicknames, plain messages, readable command labels, expandable output and separated checks/next-step reports rendered without browser errors. Saved task cards use compact project lists. The interface was updated without restarting the running supervisor or changing account credentials, task instructions or queue settings.

A separate disposable local server, using the real HTTP handler and UI with test events, verified live append, a started command becoming one completed activity, preserved scroll position and expanded details, Jump to latest, automatic following at the bottom, completion, switching recorded steps, and Claude/Gemini final reports. A 390 × 844 viewport check found no dialog overflow and kept the close control and footer visible. Test HTML stayed escaped; no reasoning sentinel appeared in the UI or technical disclosure. No vendor/model invocation or reset was used by these display checks. Disposable events are not public screenshots or evidence of live Claude/Gemini execution. Private captures and runtime data are excluded from the source release.

The viewer retains the existing 80 KB recent-log bound and installation-wide 40-run list. It does not claim complete imported transcripts or live chat continuation. Non-streaming adapters may only produce a final report. Cross-platform CI results remain available from the [Verify workflow](https://github.com/dibyapp/runquay/actions/workflows/ci.yml); desktop browser verification for this change was on Windows.

Current interface verification: 2026-10-09, version 0.5.1. The 70-test Python suite completed on Windows (68 passed, two platform/permission skips) and Ubuntu 24.04 under WSL (70 passed). Eighteen JavaScript UI tests cover the prior workflow and recommendations for verified accounts, installed tools and a fresh computer. Test commands and results are recorded separately from CI and account-dependent checks.

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


## Windows bootstrap verification - 0.5.1

The native setup.cmd --check entry point detected existing compatible Python and Git without installing software, launching a model, running a .ps1 file or changing execution policy. Windows CI checks this entry point and the optional PowerShell helper. The default batch launcher installs only missing fixed WinGet packages and uses known vendor locations within its own environment after installation; OS agreement and permission prompts remain interactive. The dashboard and Node/Gemini installation checks from 0.5.0 still apply.


## Existing Codex task discovery - 0.5.2

Windows passed 74 Python tests (72 passed, two POSIX skips); Ubuntu 24.04 under WSL passed all 74. The 19 UI tests and JavaScript syntax check passed. Tests cover read-only API calls, cursor pagination, duplicate/child/ephemeral exclusion, longest-folder matching, bounded preview retention, metadata-field allowlisting, failure preservation, private error suppression and search/filter combinations.

Actual in-app browser testing on the fresh Windows walkthrough found 42 saved Codex tasks. Project filtering returned eight tasks, an exact-title search returned one, and its read-only summary opened correctly. A new-task form opened without queuing work. Show more increased visible results from twelve to 24; refresh retained them; a saved-folder shortcut selected the correct project. The private walkthrough retained both account connections, unfinished onboarding, paused work, zero queued tasks and zero model runs. Original finished task history was preserved in its separate installation.

The reviewed screenshot contains only the task-history header. Private titles, previews, project names and paths are outside its capture. Source/runtime separation and release image hashes are audited before publication. Native live history discovery was tested on Windows; macOS and Linux rely on deterministic/API-contract checks in CI until separate desktop integration runs occur. This 0.5.2 check covered only the current Codex login. See the 0.6.0 verification below for the added native sources and profile behavior.

## Multiple-tool task history - 0.6.0

Windows ran 89 Python tests: 86 passed and three POSIX-specific checks were skipped. Ubuntu 24.04 under WSL passed all 89. All 20 UI checks and JavaScript syntax passed. Fixtures cover Claude session titles/text parts/sidechains/hidden entries; Gemini JSON/JSONL headers, updates and project markers; Antigravity request extraction, explicit cwd, stale cache and encrypted-format reporting; bounded reads, authentication-file exclusion, symlink rejection, corrupted files, isolated provider failures, folder boundaries, provider ID collisions, import validation/redaction/field allowlisting, HTTP origin checks and no task creation.

Actual in-app browser testing of the paused Windows walkthrough displayed 107 local tasks: Codex 42, Claude Code 21, Gemini CLI 3 and Antigravity 41. Claude filtering/show-more displayed all 21, exact-title search returned one, a summary opened, and an unconnected folder opened a review form without saving. A linked Claude task opened a separate new-task form with Claude preselected and an empty goal; it was closed without saving. Gemini filtering displayed three sessions. Antigravity filtering displayed its readable transcripts, with unknown folders and the encrypted-format warning. Refresh retained the tool selection. A saved-folder shortcut cleared the tool filter and displayed that folder's eleven tasks.

A deliberately invalid metadata export was rejected without changing history. A single test-only compatible export was imported through the real file picker, appeared under its own tool filter, and displayed an HTML-like title as plain text: no image element or alert was created. The temporary import was removed with a reversible private backup. No real vendor conversation was imported through this fixture or modified. The walkthrough retained both accounts, unfinished onboarding, paused work, zero queued tasks and zero model runs.

The public JPEG is an actual browser capture of the final default controls and total count; private titles, previews, folder names, paths and account information are outside its frame. The image is visually reviewed and hash-pinned in the release manifest. Histories remain in excluded local data. No vendor sign-in, model request, install, credit purchase or reset was performed for these checks.

Local native histories were exercised on Windows. Deterministic CI on macOS/Linux checks the parser and filesystem contracts, not live vendor desktop integrations. Older encrypted Antigravity files, missing bounded metadata, arbitrary vendor exports and cloud-only conversations remain unsupported or partial as documented in the [history guide](TASK_HISTORY.md). Additional-tool previews are not automatically added to AI planning context.

## Account labels - 0.6.1

The Python suite ran 93 tests: Windows passed 90 with three POSIX skips; Ubuntu 24.04 under WSL passed all 93. The 20 UI checks and JavaScript syntax passed. New checks cover masking malformed/missing emails, discarding full provider identity before persistence, preserving nicknames across refresh, rename input validation, unchanged account fields/work, and local-session/CSRF/origin enforcement.

In the actual Windows in-app browser, all three connected Codex profiles displayed masked sign-in hints and Rename controls. The rename dialog opened with its existing nickname; saving that unchanged nickname closed it successfully. Existing profile IDs/providers/enabled states, task IDs/states/steps, run records and scheduling/onboarding settings were preserved. All three connections remained eligible. No build, model turn, login or reset was started for this check. Full provider emails were absent from the returned account state. The read-only account refresh uses the existing official account and quota methods.

## Session titles, project membership and tool marks - 0.6.2

The Python suite ran 99 tests: Windows passed 96 with three POSIX skips, and Ubuntu 24.04 under WSL passed all 99. All 22 UI checks and JavaScript syntax passed. Regressions cover Windows extended drive/UNC prefixes, case/slash variants, path boundaries, native title fallback, read-only bounded metadata, explicit project membership, multiple roots, projectless sessions, cross-tool grouping, fixed local logo paths and static SVG delivery. SQLite metadata handles are closed explicitly so Windows does not retain a file lock.

Actual local verification found 50 Codex sessions: the old cache had 23 Untitled entries; after refresh all 50 titles matched the saved native metadata and none remained Untitled. All 19 explicit desktop project assignments matched, and all three explicitly projectless sessions were grouped as No project. Working directories remain available separately; a project assignment can differ from the execution folder.

The actual Windows in-app browser displayed project headings and loaded all four provider marks locally. Codex filtering showed 12 cards; Show more expanded to 24. Gemini and Antigravity filters loaded their matching logos, and the Claude filter loaded its own mark. Selecting one project showed only that project heading with both Codex and Claude sessions. Searching No project returned its three Codex sessions. A private verification capture contains the current Runquay project and its Codex session only; it is excluded from releases. Account connections, task/run records and scheduling settings were preserved. No vendor history was edited, no model turn was requested by discovery, and no reset was consumed.
