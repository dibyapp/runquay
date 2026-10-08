# Runquay brand and launch kit

**Name:** Runquay · **Pronunciation:** RUN-key · **Repository:** [dibyapp/runquay](https://github.com/dibyapp/runquay)

**Creator and maintainer:** Dibyaprakash Pradhan.

**Tagline:** Your agents. One local queue.

**Descriptor:** Open-source AI coding agent orchestrator.

**One sentence:** Runquay turns project goals into a local task queue for Codex, Claude Code, Gemini CLI and extensible coding tools, with checkpoints and explicit approvals.

**Primary audience:** solo developers and maintainers with existing repositories and coding CLI accounts. First use case: queue a bounded improvement in a real project and inspect the result.

## Visual identity

- Ink `#101216`: canvas and icon foreground.
- Panel `#181b21`: working surfaces.
- Signal mint `#bcf27b`: primary action, active state, queued progress.
- Warm amber `#f4b68b`: checkpoint attention; keep text labels so color never carries state alone.
- Text `#e6e8ed`, secondary `#a4acb9`: readable dark-theme text.
- Typography: system sans serif, no hosted fonts or external asset requests.
- Mark: three queued bars, a run arrow and a vertical arrival/checkpoint line. Keep it legible at 24 px. Do not use AI-provider logos as our identity.

Assets: [mark.svg](../web/mark.svg), [brand-card.svg](../web/brand-card.svg). Original vector assets shipped under the repository's MIT license. The card is a 1280 × 640 source graphic; export a PNG if a publishing platform requires raster media. Do not claim an SVG is an already-uploaded GitHub social preview.

## Copy ready for publication

Repository About:

> Open-source AI coding agent orchestrator for Codex, Claude Code and Gemini CLI. Local task queues, checkpoints, account profiles and approvals.

Launch title:

> Runquay: a local task queue for your AI coding tools

Launch paragraph:

> I built Runquay to give project goals a persistent queue on my own computer. Connect an existing repository, choose your coding CLI, and work through bounded milestones with saved checkpoints and explicit approvals. The source is MIT licensed. Codex execution has been live-tested on Windows; other adapters and macOS have documented verification limits. I'd value feedback on setup and recovery from interrupted tasks.

Optional repository call to action:

> If Runquay helps your workflow, star the repository to follow its progress. Reproducible bug reports and small contributions are welcome.

Use first-person launch copy only if the publisher is comfortable representing this work as their project. Add the real repository link when created; no invented URL or ownership claim.

## Demo outline

1. Show a disposable existing repository and one clear acceptance criterion.
2. Walk through tool detection and the four setup steps without showing credentials or real account identifiers.
3. Choose the tool, queue the goal, and show the active milestone.
4. Show a completed checkpoint, checks and the actual code difference; completion still needs review.
5. Demonstrate pause/resume using a synthetic worker or an explicitly approved real invocation. Identify simulated quota states clearly.

Avoid "unlimited AI", "free coding", "guaranteed 24/7", "works with every AI", "fully offline", "zero risk", automatic paid resets, or promises of stars. Current account-count freedom is not unlimited provider usage. Antigravity and custom tools belong in the compatibility table with their limits.

## Rename compatibility

Runquay is the public name of the former AutoWork prototype. `python runquay.py start` is the preferred launcher; `python autowork.py start` remains supported. Existing storage locations, database names, service identifiers, environment variables, CSRF headers and `AUTOWORK_CHECKPOINT.md` remain unchanged. This avoids splitting existing state or breaking integrations. Do not mass-rename these identifiers as a branding edit.

The local dashboard stays private and has a no-index directive. Public discovery copy belongs in the README, package metadata and future public documentation. See [BRAND_RESEARCH.md](BRAND_RESEARCH.md) for evidence, naming limitations and search intent hypotheses.
