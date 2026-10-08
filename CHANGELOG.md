# Changelog

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
