# Changelog

## 0.10.0 — Runquay Field

- Replaced the sidebar with a floating navigation dock, an atmospheric workspace, compact work rows and on-demand drawers. The creation surface opens directly into a message rather than a marketing headline.
- Collective Learnings becomes an interactive topic field built from real local source matches. Read one insight at a time; supporting evidence, editing and library filters stay available on demand.
- Added keyboard command search, ambient motion with stationary hit targets, an explicit motion pause, system reduced-motion support and canvas scheduling that stops away from Learnings or when the tab is hidden.
- A lesson’s Use this action attaches it visibly to the everyday composer. Only kept lessons can be sent; task context excludes source histories and stays fixed. Retrying an existing request reuses its original snapshot even if a lesson is later hidden.
- Approval requests are available from every page. Existing sign-in, billing, quota, reset and publication controls remain in place. Added actual browser screenshots with fictional history and reviewed image hashes.


## 0.9.0 — One request, one place

- A single everyday composer replaces the default two-step idea form and separate start-queue action. A new isolated project and a connected AI are selected for you, with optional project and provider choices shown before sending.
- Requests, results and saved native conversations share a searchable list with tool icons and plain progress. Payment decisions appear where you work. Detailed histories, queue controls, models and limits are secondary.
- Explicit sends, single-task starts and follow-ups can run without enabling unrelated queued work. Global pause disarms scoped work; task pause also expires outstanding vendor approvals. Request keys prevent duplicate workspace creation on retries, including concurrent sends.
- Native chat previews remain read-only. One unfinished task per folder, billing approvals, reset consent and the publication privacy gate are preserved.


## 0.8.0 - Easier Collective Learnings

- Ask a question or choose a suggested topic; Runquay automatically finds matching work, fits the context budget, and recommends a connected analysis tool.
- Replace source-picking forms and raw JSON with a readable context review and inline removal. One explicit Analyze action sends the reviewed snapshot.
- Run an authorized analysis while the build queue remains paused; preserve quota/billing approvals and support pausing, cancelling and scoped continuation.
- Simplify lesson cards, topic browsing, source context and progress. Use in a task keeps and attaches a lesson in one action; optional controls stay under Adjust.
- Refresh source availability locally, reuse duplicate active analyses, handle no matches honestly, and fix the dashboard startup race between deferred scripts.


## 0.7.0 - Collective Learnings

- Collect reusable lessons from selected work across projects and AI tools, with any topic/tag rather than a fixed taxonomy.
- Preview the exact bounded summaries before queuing read-only analysis through connected Codex, Claude Code or Gemini accounts; keep existing usage checks and approvals.
- Store source-backed AI suggestions for review, editing, saving and dismissal; distinguish reported observations from hypotheses and reject unknown citations.
- Search by topic and reuse up to 12 explicitly chosen saved lessons in new tasks or existing-project tasks, without copying source summaries.
- Include native/imported chat previews and completed Runquay reports; Antigravity/custom history can contribute sources while their analysis modes remain unsupported.
- Keep collections in private runtime storage and exclude them from source packages. No automatic publication or native vendor-memory edits.


## 0.6.3 - Readable task conversations

- Replace raw event output with a conversation view: your request, provider messages, file activity and structured step reports.
- Expand commands only when needed; show readable activity labels, command results, failures, checks and requests for input.
- Follow live progress without losing reading position or expanded details, with Jump to latest and a selector for recorded work steps.
- Render a safe local Markdown subset and omit reasoning events from messages and technical details. Keep the existing bounded recent-log window explicit.
- Simplify saved-chat cards into compact project lists. Tool marks and account nicknames remain visible.

## 0.6.2 - Accurate session titles and project grouping

- Normalize Windows extended drive and UNC paths before matching saved project folders across tools.
- Prefer Codex custom names, then bounded read-only saved title metadata, then a prompt preview when no title exists.
- Respect explicit Codex desktop project assignments and chats marked No project. Keep working folders separate from project membership.
- Group session cards under project headings with filtered counts and retain search, tool filters, folder shortcuts and pagination.
- Show locally served tool marks and visible labels on session, task and account cards. Unknown custom tools use a generic terminal icon; no external image requests are made.

## 0.6.1 - Recognizable account labels

- Show a masked Codex sign-in hint while discarding the full provider email before caching.
- Add Rename to account cards for local nicknames without changing login homes, credentials, eligibility or queued work.
- Validate names and protect the rename endpoint with the existing local-session, CSRF and origin checks.

## 0.6.0 - Saved tasks across AI tools

- Combine Codex, Claude Code, Gemini CLI and readable Antigravity histories in Existing AI tasks, with project/tool filters, bounded summaries, folder shortcuts and per-source status.
- Detect configured Claude/Gemini homes and registered profiles without reading authentication files or starting vendor processes. Preserve provider namespaces and use explicit working directories for folder matching.
- Accept compatible metadata JSON imports for other tools, with size/schema validation, deduplication, field allowlisting and plain-text display.
- Explain unknown folders, stale cached references, older encrypted formats and cloud-history limitations. New native/imported previews are not automatically sent to the advisor.
- Add a detailed guide, an actual privacy-reviewed browser capture, native-format/security regressions and end-to-end browser checks.


## 0.5.2 - Existing Codex tasks

- Show existing local Codex tasks without running the advisor: search, project filters, bounded summaries, refresh and folder shortcuts.
- Read non-archived top-level task metadata with pagination, retain previous results on failure, and keep saved history separate from the Runquay queue.
- Browsing does not resume chats, request model turns or create tasks. Discovery/filtering regression checks cover these boundaries.


## 0.5.1 - Windows first-launch compatibility

- setup.cmd prepares missing Python/Git directly through fixed WinGet commands, without executing a PowerShell script file or changing execution policy.
- Known vendor paths are refreshed only within the launcher after installation; existing tools remain reused.
- Windows CI checks both the native batch entry point and the optional PowerShell helper without installing software.


## 0.5.0 — OS-aware automatic setup

- First-launch setup files detect Windows, macOS or Linux and prepare missing Python/Git with the matching package manager.
- The dashboard recommends an installed tool, lists missing dependencies and offers Install missing tools for Codex, Claude Code and Gemini CLI.
- Missing Node.js uses an official checksum-verified private runtime; vendor packages use a separate user tools prefix. Existing tools are reused.
- Connection names/settings are filled automatically. Next creates a needed connection and waits for fresh state before showing the account step.
- OS passwords and agreement prompts remain in the terminal; unsupported installers get official/manual guidance. Work and sign-in cannot start during setup.
- Actual Windows Node/Gemini installation, launcher detection checks, security regression tests, platform CI and updated illustrated setup guides.

## 0.4.2 — Browser sign-in for Codex

- Separate Codex accounts offer Sign in with Codex, launching the official ChatGPT browser OAuth flow without a copied terminal command.
- Sign-in progress, cancellation and automatic connection checking keep the next step clear. Only one browser login runs at a time.
- Terminal instructions remain collapsed as a fallback; current shared app logins and other providers retain their existing sign-in instructions.
- Login uses the separate profile and vendor keyring, with local session/CSRF protection. Active sign-ins cannot be unlinked.
- Actual Windows browser launch/cancel testing, reviewed screenshot, authentication lifecycle tests and updated beginner guides.

## 0.4.1 — Fewer account choices

- Detected AI tools appear as simple buttons. Account names are chosen automatically; existing connections are recognized without submitting duplicates.
- Verified onboarding accounts show one ready message and Next. Extra accounts and connection details stay collapsed.
- Account names, separate logins, uninstalled tools and custom commands move under More options. Separate accounts open their sign-in guide immediately.
- Installed tools are distinguished from verified authentication. Other tools still need approval for every run; billing and reset safeguards are retained.
- Actual browser checks and reviewed screenshots document the simpler flow; temporary test connections were removed without touching vendor credentials.

## 0.4.0 — A guided start for people who do not code

- Two-screen idea guide with everyday questions, editable website/checklist/expense starters, optional name/tool choices, and review before submission.
- Guided goals request a simple practical implementation, plain opening instructions in START_HERE.md and meaningful checks. Three-session caps bound new guided tasks.
- Finished tasks offer See what was made, text-only instructions, Open project folder and an editable Ask for help message. Opening the result screen does not execute generated code.
- Clearer onboarding language, terminal explanation, copyable sign-in instructions and an illustrated beginner guide.
- Friendly Python/Git prerequisite checks, Windows error visibility and a Mac start.command launcher. Source ZIPs preserve executable permissions for shell launchers.
- Local-session/CSRF checks protect folder opening. Handoff reads are bounded, skip symlinks and render as text; tests cover these boundaries.

## 0.3.0 — A simpler workspace

- Five focused pages: Home, Tasks, Ideas, Accounts, and Settings. Home explains the next action for waiting work, active tasks, approvals and completed results.
- Shorter task and account forms, plain task states, separate in-progress/finished filters, and advanced controls under details.
- Existing folders remain available from Tasks. Selecting a project in Ideas filters saved proposals to that project; each idea stays editable before work starts.
- Expanded task, folder, account and idea details survive background refreshes. Errors no longer produce misleading success messages in the updated settings and connection actions.
- Accessible dialog labels, focus indicators, a skip link, and navigation that remains available on small screens. Legacy bookmarks still resolve.
- Fix Windows stop helper when its scheduled worker has already exited and its command line is unavailable.
- Updated guides, actual browser screenshots, UI decision regression tests, and static-asset HTTP checks. Real Codex build and read-only planning were exercised; other vendors were not invoked.

## 0.2.1 — Illustrated guides and relative data-path fix

- Detailed setup, workflow and troubleshooting guides, with actual application screenshots and a real Codex execution record.
- Resolve data directories before launching workers so a relative `--data` path does not lose structured results when the worker uses a different working directory.
- Explicit, hash-pinned documentation screenshot allowlist; changed or unreviewed raster images and EXIF/XMP metadata are rejected by release auditing.
- Versioned source archives now use project metadata. Existing 0.2.0 releases remain unchanged.

## 0.2.0 — Runquay open-source preparation

- Public rename from AutoWork to Runquay, original vector branding, cited market research and launch kit.
- New `runquay.py` launcher; existing entry point, data, services and checkpoint contract remain compatible.

- Four-step onboarding, tool detection, official sign-in guides, workspace selection, and folder import.
- Dynamic account profiles without an application count cap; additive schema migrations retain existing state.
- Per-task Codex, Claude Code, Gemini CLI, Antigravity CLI, and custom headless adapters.
- Read-only planning where supported; explicit approval for tools with unverified billing.
- Portable paths, Unix child groups, graceful shutdown, macOS LaunchAgent and Linux user-service definitions.
- MIT license, contribution/security guides, release allowlist and audit, ZIP/checksum, multi-OS CI configuration.

## 0.1.0 — Local prototype

- Windows Codex queue, three fixed profiles, quota reserve, earned-reset approvals, existing-project discovery, and Codex advisor.
