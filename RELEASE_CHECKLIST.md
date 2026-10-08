# Before publishing

1. Run tests, JS syntax checks, and the release audit. Review `docs/VERIFICATION.md`; run the OS CI matrix in a private repository if possible.
2. Complete fresh onboarding on every advertised OS. Validate each vendor CLI/version using your own account; approved model invocations may cost allowance or money.
3. Run `python runquay.py release`. Extract the ZIP into a new empty directory and inspect every file and checksum. Confirm there are no databases, personal paths, accounts, real screenshots, logs, generated projects, or credentials.
4. Start the extracted source using `python runquay.py start --data <private-test-directory> --port 8766`. Never share a data directory between live instances.
5. Seed a clean Git repository from inspected source. Do not upload the original working folder or carry private history into the public repository.
6. Confirm Runquay name/handle/domain availability and perform appropriate trademark checks; the initial web search is not clearance. Confirm license holder, description, topics, and issue templates. Use the repository description and relevant topics below. Enable secret scanning, private vulnerability reporting, and suitable branch protection.
7. Publish source/checksum with accurate compatibility notes. A configured CI workflow is not a completed run; uninstalled tools and macOS need real validation before claiming live support.

Publishing is a separate manual step. This preparation creates no public repository, package, deployment, or release.

## Repository description

Open-source AI coding agent orchestrator for Codex, Claude Code and Gemini CLI. Local task queues, checkpoints, account profiles and approvals.

## GitHub topics

Use these feature-specific topics when creating the repository:

`ai-coding-agent`, `agent-orchestration`, `codex`, `claude-code`, `gemini-cli`, `antigravity`, `workflow-automation`, `task-scheduler`, `developer-tools`, `self-hosted`, `local-first`, `python`, `windows`, `macos`, `linux`

Keep compatibility limitations visible in the README. Update keywords when capabilities change; avoid adding unrelated products or claims of unrestricted, free, or fully offline AI execution.
