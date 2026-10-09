# Changelog

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
